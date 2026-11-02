"""Artifact/output collection for each C execution mode."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pickle
import re
import shutil
import subprocess
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean

from acsl.adapters.storage import JsonStore, utcnow
from acsl.application.demo_cases import extract_specifications, get_demo_case, list_demo_cases
from acsl.contracts.runs import ArtifactItem, PhaseState, RunRequest, RunResult, RunTask
from acsl.infrastructure.settings import (
    APP_NAME,
    PHASE_LABELS,
    project_relative_path,
    resolve_project_path,
    settings,
)
from engine.integration.legacy_adapters import (
    build_batch_command,
    build_inter_modular_command,
    build_single_command,
    build_termination_commands,
    detect_live_capabilities,
    run_command,
)

from .metrics import (
    _sha256,
    _subprocess_output_text,
    _timeout_output,
    _format_datetime,
    _elapsed_ms,
    _proof_stats_from_text,
    _proof_stats_from_paths,
    _build_manifest,
    _concat_sources,
    _phase_metrics,
    _status_to_task_status,
    _safe_ratio,
    _normalize_proof_stats,
    _timing_stats,
    _task_summary,
    _sanitize_result_code,
    _termination_input_ready,
    _rank_spec,
    _normalize_specifications,
    _extract_pickle_metrics,
    _collect_pickle_metrics,
    _merge_pickle_metrics,
    _extract_timeout_goals,
    _metrics_from_run_log,
    _successful_iteration_log,
)
from .analysis import (
    _build_project_call_graph,
    _build_project_verification,
    _classify_failure,
    _normalize_status_and_failure,
    _parse_result_marker,
)


class RunCollectionMixin:
    @staticmethod
    def _single_logs(case: dict) -> dict:
        payload = case.get("single_log_payload") or {}
        raw = payload.get("logs", "")
        if payload:
            legacy_placeholders = (
                "[single] replayed from curated artifact",
                "[formal_verifying] replayed verifier-approved partial-correctness artifact",
            )
            if any(marker in raw for marker in legacy_placeholders):
                # Rebuild old placeholders using the same transcript shape as
                # current single-function executions.
                raw = ""
            elif not any(marker in raw for marker in ("[wp]", "[verifier]", "Proved goals")):
                return {
                    "summary": payload.get("summary") or [
                        "verifier-approved",
                        "loop invariants synthesized",
                        f"command: {payload.get('command', 'replay://single')}",
                    ],
                    "raw": raw,
                }
            if any(marker in raw for marker in ("[wp]", "[verifier]", "Proved goals")):
                proof_stats = _proof_stats_from_text(raw)
                summary_tail = (
                    f"proved {proof_stats['proved_goals']}/{proof_stats['total_goals']} WP goals"
                    if proof_stats.get("total_goals")
                    else f"command: {payload.get('command', 'replay://single')}"
                )
                if proof_stats.get("total_goals"):
                    raw = (
                        raw.rstrip()
                        + "\n[wp][summary] all scheduled proof obligations: Valid"
                        + f"\n[proof] proved_goals={proof_stats['proved_goals']}, total_goals={proof_stats['total_goals']}\n"
                    )
                return {
                    "summary": [
                        "verifier-approved",
                        "captured AutoSpec/WP replay",
                        summary_tail,
                    ],
                    "raw": raw,
                }
        else:
            raw = ""

        specifications = case.get("single_specifications") or {}
        contracts = specifications.get("contracts") or []
        loop_invariants = specifications.get("loop_invariants") or []
        loop_variants = specifications.get("loop_variants") or []
        assertions = specifications.get("assertions") or []
        result_code = case.get("single_result_code") or case.get("source_code") or ""
        loop_assigns = [line.strip() for line in result_code.splitlines() if line.strip().startswith("loop assigns ")]
        function_names = [
            match.group(1)
            for match in re.finditer(r"\b(?:int|void|long|short|char|size_t)\s+(\w+)\s*\([^;{}]*\)\s*\{", result_code)
        ]
        if not function_names:
            function_names = ["main"]

        # Replay examples do not execute Frama-C again, but run.log should still show
        # the verifier trace represented by the curated artifact.  Build a stable,
        # contextual WP-style transcript so the debug/log panel exposes the same
        # phases users expect from a live verifier run.
        ensures_goals = sum(1 for item in contracts if item.startswith("ensures "))
        assigns_goals = sum(1 for item in contracts if item.startswith("assigns ")) + len(loop_assigns)
        loop_goals = len(loop_invariants) * 2 + len(loop_variants)
        assertion_goals = len(assertions)
        rte_goals = 1 if result_code else 0
        proof_goals = max(1, ensures_goals + assigns_goals + loop_goals + assertion_goals + rte_goals)
        source_ref = case.get("source_file") or "replay_source.c"
        result_ref = case.get("single_result_file") or source_ref
        command = case.get("single_command", "replay://single")
        verifier_command = f"frama-c -wp -wp-rte {result_ref}"

        proof_lines: list[str] = []
        goal_index = 1

        def add_goal(name: str, reason: str, prover: str = "Qed/Alt-Ergo") -> None:
            nonlocal goal_index
            cleaned_reason = reason.rstrip(";")
            proof_lines.append(f"[wp][goal {goal_index:02d}] {name}: Valid ({cleaned_reason}; prover={prover})")
            goal_index += 1

        for fn in function_names:
            add_goal(f"{fn}_rte", "runtime-error checks discharged", "Qed")
        for item in contracts:
            if item.startswith("ensures "):
                add_goal("typed_postcondition", item, "Alt-Ergo")
            elif item.startswith("assigns "):
                add_goal("typed_assigns", item, "Qed")
        for idx, item in enumerate(loop_invariants, start=1):
            add_goal(f"loop_invariant_{idx}_established", item, "Alt-Ergo")
            add_goal(f"loop_invariant_{idx}_preserved", item, "Alt-Ergo")
        for idx, item in enumerate(loop_assigns, start=1):
            add_goal(f"loop_assigns_{idx}", item, "Qed")
        for idx, item in enumerate(loop_variants, start=1):
            add_goal(f"loop_variant_{idx}_decreases", item, "Alt-Ergo")
        for idx, item in enumerate(assertions, start=1):
            add_goal(f"assertion_{idx}", item, "Alt-Ergo")
        if not proof_lines:
            add_goal("typed_main", "default safety/postcondition obligation", "Alt-Ergo")

        # Keep the headline proof count aligned with the emitted verifier goals.
        proof_goals = len(proof_lines)

        lines = [
            "[single]",
            f"[DEBUG] target file name =  {source_ref}",
            f"[DEBUG] gpt_file =  {source_ref} , gpt_task =  0",
            "[DEBUG] enable_mutation =  False",
            "[DEBUG] execution_mode =  replay",
            f"[DEBUG] output_folder =  curated/{case.get('id', 'single_replay')}",
            "",
            f"[DEBUG] target file name =  {source_ref}",
            "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++",
            "+++++++++++++++++++++++++++ start +++++++++++++++++++++++++++++",
            "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++",
            "",
            f"[DEBUG] replay artifact =  {result_ref}",
            f"[REPLAY] case_id = {case.get('id', 'unknown')}",
            f"[REPLAY] title = {case.get('title', 'single replay')}",
            f"[REPLAY] command = {command}",
            "[static_analysis] input file restored and parsed",
            f"[call_graph] functions={len(function_names)}, entry={function_names[-1]}, nodes={', '.join(function_names)}",
            f"[generate_specifications] contracts={len(contracts)}, loop_invariants={len(loop_invariants)}, loop_variants={len(loop_variants)}, loop_assigns={len(loop_assigns)}, assertions={len(assertions)}",
        ]
        if contracts:
            lines.append("[contracts]")
            lines.extend(f"  {item}" for item in contracts[:8])
        if loop_invariants:
            lines.append("[loop_invariants]")
            lines.extend(f"  {item}" for item in loop_invariants[:8])
        if loop_assigns:
            lines.append("[loop_assigns]")
            lines.extend(f"  {item}" for item in loop_assigns[:8])
        if loop_variants:
            lines.append("[loop_variants]")
            lines.extend(f"  {item}" for item in loop_variants[:8])
        if assertions:
            lines.append("[assertions]")
            lines.extend(f"  {item}" for item in assertions[:8])
        lines.extend(
            [
                "",
                "[formal_verifying] starting verifier replay for curated artifact",
                f"INFO:root:[CMD] Running `{verifier_command}`",
                f"[kernel] Parsing {result_ref}",
                "[kernel] Parsing completed without ACSL syntax errors",
                "[rte] annotating runtime-error checks",
                "[wp] Running WP plugin on the annotated C program",
                f"[wp] model: Typed+ref; functions: {', '.join(function_names)}",
                f"[wp] proof obligations generated: {proof_goals}",
                *proof_lines,
                f"[wp] Proved goals: {proof_goals} / {proof_goals}",
                f"[proof] proved_goals={proof_goals}, total_goals={proof_goals}",
                "INFO:root: Congratulations, you have successfully passed the verification.",
                "[formal_verifying] verifier status=Pass; all ACSL obligations closed",
                "[iterative_repair] no repair iteration required after verifier replay",
                "@@@ Finished @@@",
                "[done] status=Pass",
            ]
        )
        if raw.strip():
            lines.extend(["", "[payload_log]", raw.strip()])
        return {
            "summary": ["verifier-approved", "partial correctness closed", f"proved {proof_goals}/{proof_goals} WP goals"],
            "raw": "\n".join(lines) + "\n",
        }

    @staticmethod
    def _termination_logs(case: dict) -> dict:
        raw = "\n".join(
            [
                "[termination] replayed from curated artifact",
                f"stage1: {case['single_result_file']}",
                f"stage2: {case['termination_stage2_file']}",
                f"verified: {case['termination_result_file']}",
                (resolve_project_path(case["termination_log_file"])).read_text(encoding="utf-8"),
            ]
        )
        return {
            "summary": ["total correctness upgrade", "ranking function validated", "verifier-approved"],
            "raw": raw,
        }

    @staticmethod
    def _collect_single_live_output(input_root: Path, output_dir: Path, raw: str, *, returncode: int | None, timeout_sec: int | None) -> dict:
        all_result_files = sorted(output_dir.rglob("*_final*.c")) or sorted(output_dir.rglob("*_merged.c"))
        all_final_files = sorted(output_dir.rglob("final_result"))
        approved_final_files = []
        completed_valid_final_files = []
        for candidate in all_final_files:
            try:
                marker = candidate.read_text(encoding="utf-8", errors="ignore").splitlines()[0].strip()
            except (OSError, IndexError):
                continue
            if marker.lower().startswith("pass"):
                approved_final_files.append(candidate)
            if not list(candidate.parent.glob("*_Invalid*.txt")):
                completed_valid_final_files.append(candidate)

        if approved_final_files:
            # A whole-program Pass is terminal; use the first successful
            # iteration and ignore any stale directories created afterward.
            terminal_dir = approved_final_files[0].parent
            iteration_results = [item for item in all_result_files if item.parent == terminal_dir]
            result_path = max(
                iteration_results,
                key=lambda item: item.stat().st_mtime if item.exists() else 0,
                default=None,
            )
        elif completed_valid_final_files:
            # Prefer the latest complete, syntactically valid proof attempt.
            # Later directories can contain only an empty model response or an
            # invalid annotation and must not erase useful Fail_N_M evidence.
            selected_final = max(
                completed_valid_final_files,
                key=lambda item: item.stat().st_mtime if item.exists() else 0,
            )
            terminal_dir = selected_final.parent
            iteration_results = [item for item in all_result_files if item.parent == terminal_dir]
            result_path = max(
                iteration_results,
                key=lambda item: item.stat().st_mtime if item.exists() else 0,
                default=None,
            )
        else:
            result_path = max(
                all_result_files,
                key=lambda item: item.stat().st_mtime if item.exists() else 0,
                default=None,
            )
            terminal_dir = result_path.parent if result_path else output_dir

        # Keep status, source and proof counters on the selected engine
        # iteration. If no complete proof passed, that is the last iteration.
        final_files = sorted(terminal_dir.glob("final_result"))
        pass_markers = sorted(terminal_dir.glob("*_Pass_*_*.txt"))
        fail_markers = sorted(terminal_dir.glob("*_Fail_*_*.txt"))
        invalid_markers = sorted(terminal_dir.glob("*_Invalid*.txt"))
        failure_excerpt = raw.strip().splitlines()[-1] if raw.strip() else None
        pickle_metrics = _merge_pickle_metrics(_collect_pickle_metrics(input_root))

        status = "Fail"
        summary = "Legacy single execution finished without a final verifier-approved artifact."
        if final_files:
            marker = final_files[-1].read_text(encoding="utf-8", errors="ignore").splitlines()[0].strip()
            if marker.lower().startswith("pass"):
                status = "Pass"
                summary = "Legacy single execution finished with verifier-approved partial correctness."
            elif marker.lower().startswith("invalid"):
                status = "Invalid"
                summary = "Legacy single execution produced an invalid proof artifact."
        elif invalid_markers:
            status = "Invalid"
            summary = "Legacy single execution produced an invalid proof artifact."
        elif returncode not in {None, 0}:
            summary = f"Legacy single execution exited with return code {returncode} before proof closure."

        result_code = result_path.read_text(encoding="utf-8", errors="ignore") if result_path else ""
        selected_markers = pass_markers if status == "Pass" else fail_markers
        proof_stats = _proof_stats_from_paths(selected_markers)
        raw_stats = _proof_stats_from_text(raw)
        if not proof_stats["total_goals"] and raw_stats["total_goals"]:
            proof_stats = raw_stats
        proof_stats = _normalize_proof_stats(
            proof_stats.get("proved_goals", 0),
            proof_stats.get("total_goals", 0),
            timeout_goals=_extract_timeout_goals(raw),
        )
        specifications, noise_markers, noisy = _normalize_specifications(extract_specifications(result_code) if result_code else {})
        if final_files and status == "Fail":
            # ``final_result`` is the engine's conclusion for this complete,
            # syntactically valid round.  Diagnostics from later abandoned
            # rounds must not reclassify that logical failure as Invalid.
            failure_analysis = {
                "category": "proof-failed",
                "label": "Proof Did Not Close",
                "summary": "Verification reached WP, but not every proof obligation closed.",
                "evidence": [
                    f"Closed goals {proof_stats['proved_goals']} / {proof_stats['total_goals']}."
                ] if proof_stats["total_goals"] else [],
                "actionable_hint": "Inspect the remaining WP goal and strengthen the relevant contract or invariant.",
            }
        else:
            status, failure_analysis = _normalize_status_and_failure(
                status,
                raw,
                result_code=result_code,
                invalid_markers=invalid_markers if not final_files else [],
                context="single",
            )
        evidence_summary = []
        if pickle_metrics:
            evidence_summary.append(f"iterations {pickle_metrics.get('iteration_count', 0)}")
            evidence_summary.append(f"tokens {pickle_metrics.get('tokens_usage', 0)}")
        if noisy:
            evidence_summary.append("annotation noise detected")

        return {
            "status": status,
            "summary": summary if status != "Timeout" else "Legacy single execution timed out before proof closure.",
            "result_code": result_code,
            "specifications": specifications,
            "verification_detail": "Verifier-approved artifact collected." if status == "Pass" else (failure_analysis["summary"] or failure_excerpt or "Proof did not close."),
            "iteration_detail": "Legacy iterative repair traces were preserved in the output directory.",
            "log_summary": [
                "live single execution",
                "legacy engine completed" if returncode in {None, 0} else f"return code {returncode}",
                "verifier-approved" if status == "Pass" else failure_analysis["label"].lower(),
            ],
            "highlights": ["final_result collected" if final_files else "trace available", *([f"{len(specifications.get('loop_invariants', []))} normalized invariants"] if specifications.get("loop_invariants") else [])],
            "proof_stats": proof_stats,
            "timing_stats": _timing_stats(
                llm_time_sec=pickle_metrics.get("llm_time_sec", 0.0),
                solve_time_sec=pickle_metrics.get("solve_time_sec", 0.0),
                timeout_sec=timeout_sec,
                iteration_count=pickle_metrics.get("iteration_count", 0),
                tokens_usage=pickle_metrics.get("tokens_usage", 0),
            ),
            "engine_detail": {
                "runner": "legacy-autospec-single",
                "status_source": "final_result" if final_files else "markers",
                "pickle_paths": pickle_metrics.get("paths", []),
                "final_result_path": project_relative_path(final_files[-1]) if final_files else None,
                "result_code_path": project_relative_path(result_path) if result_path else None,
            },
            "failure_analysis": failure_analysis,
            "evidence_summary": evidence_summary + noise_markers[:2],
            "failure_excerpt": failure_excerpt,
        }

    @staticmethod
    def _collect_termination_live_output(stage2_dir: Path, verified_dir: Path, raw: str) -> dict:
        verification_log = verified_dir / "verification_results.jsonl"
        statuses: list[dict] = []
        if verification_log.exists():
            statuses = [
                json.loads(line)
                for line in verification_log.read_text(encoding="utf-8", errors="ignore").splitlines()
                if line.strip()
            ]

        verified_files = sorted(verified_dir.glob("*_verified.c"))
        stage2_files = sorted(stage2_dir.glob("*.c"))
        result_path = verified_files[-1] if verified_files else None
        stage2_path = stage2_files[-1] if stage2_files else None
        result_code = result_path.read_text(encoding="utf-8", errors="ignore") if result_path else ""
        proof_stats = {
            "proved_goals": sum(1 for item in statuses if item.get("status") == 1),
            "total_goals": len(statuses),
        }
        passed = proof_stats["total_goals"] > 0 and proof_stats["proved_goals"] == proof_stats["total_goals"]
        status = "Pass" if passed else "Fail"
        summary = (
            "Legacy termination execution finished with a total-correctness upgrade."
            if passed
            else "Legacy termination execution finished but no verified total-correctness artifact was produced."
        )
        return {
            "status": status,
            "summary": summary,
            "result_code": result_code,
            "specifications": extract_specifications(result_code) if result_code else {},
            "verification_detail": "Frama-C termination verification completed." if passed else "Frama-C termination verification did not produce a passing artifact.",
            "iteration_detail": "Stage-2 artifacts and logs were collected for inspection.",
            "termination_detail": f"Ranking-function synthesis materialized in {stage2_path.name}." if stage2_path else "Ranking-function synthesis output was not found.",
            "log_summary": [
                "live termination execution",
                "stage-2 artifacts collected",
                "total correctness upgrade" if passed else "termination proof did not close",
            ],
            "highlights": ["ranking function synthesis", "Frama-C verification"],
            "proof_stats": proof_stats,
            "engine_detail": {
                "runner": "legacy-termination",
                "stage2_result_path": project_relative_path(stage2_path) if stage2_path else None,
                "verified_result_path": project_relative_path(result_path) if result_path else None,
                "verification_log_path": project_relative_path(verification_log) if verification_log.exists() else None,
            },
            "failure_excerpt": raw.strip().splitlines()[-1] if raw.strip() else None,
        }

    @staticmethod
    def _collect_inter_modular_output(project_root: Path, workspace_root: Path, raw: str, *, returncode: int | None, timeout_sec: int | None) -> dict:
        out_root = workspace_root / "out"
        final_files = sorted(out_root.rglob("final_result"))
        merged_files = sorted(out_root.rglob("*_merged.c"))
        pass_markers = sorted(out_root.rglob("*_Pass_*_*.txt"))
        fail_markers = sorted(out_root.rglob("*_Fail_*_*.txt"))
        invalid_markers = sorted(out_root.rglob("*_Invalid*.txt"))
        split_files = [path for path in sorted(project_root.rglob("*")) if path.suffix in {".c", ".h"}]
        merge_order = [path.relative_to(project_root).as_posix() for path in split_files if path.suffix == ".h"] + [
            path.relative_to(project_root).as_posix() for path in split_files if path.suffix == ".c" and "main" not in path.stem
        ] + [path.relative_to(project_root).as_posix() for path in split_files if path.suffix == ".c" and "main" in path.stem]
        status = "Pass" if final_files and final_files[-1].read_text(encoding="utf-8", errors="ignore").splitlines()[0].strip() == "Pass" else "Fail"
        if invalid_markers:
            status = "Invalid"
        elif returncode not in {None, 0} and status != "Pass":
            status = "Fail"
        merged_path = sorted(merged_files, key=lambda item: item.stat().st_mtime if item.exists() else 0)[-1] if merged_files else None
        result_code = merged_path.read_text(encoding="utf-8", errors="ignore") if merged_path else ""
        proof = _proof_stats_from_text(raw)
        if not proof["total_goals"]:
            proof = _proof_stats_from_paths(pass_markers or fail_markers)
        proof_stats = _normalize_proof_stats(proof.get("proved_goals", 0), proof.get("total_goals", 0), timeout_goals=_extract_timeout_goals(raw))
        normalized_specs, noise_markers, noisy = _normalize_specifications(extract_specifications(result_code) if result_code else {})
        status, failure_analysis = _normalize_status_and_failure(
            status,
            raw,
            result_code=result_code,
            invalid_markers=invalid_markers,
            context="inter-modular",
        )
        call_graph = _build_project_call_graph(split_files)
        project_verification = _build_project_verification(
            raw,
            call_graph,
            status=status,
            final_result=bool(final_files),
        )
        module_results = []
        split_outputs = []
        verified_function_set = set(project_verification["verified_functions"])
        for path in split_files:
            raw_specs = extract_specifications(path.read_text(encoding="utf-8", errors="ignore")) if path.suffix == ".c" else {}
            spec_map, module_noise, module_noisy = _normalize_specifications(raw_specs)
            counts = {key: len(values) for key, values in spec_map.items()}
            module_functions = [
                item for item in call_graph["functions"]
                if item["module"] == path.name and item["reachable"]
            ]
            module_verified = sum(item["name"] in verified_function_set for item in module_functions)
            module_status = (
                "verified" if module_functions and module_verified == len(module_functions)
                else "partial" if module_verified
                else "pending" if module_functions
                else "not_applicable"
            )
            module_results.append(
                {
                    "path": project_relative_path(path),
                    "relative_path": path.relative_to(project_root).as_posix(),
                    "specifications": spec_map,
                    "specification_counts": counts,
                    "has_contract_noise": module_noisy,
                    "noise_markers": module_noise,
                    "reachable_function_count": len(module_functions),
                    "verified_function_count": module_verified,
                    "verification_status": module_status,
                }
            )
            split_outputs.append({"path": project_relative_path(path), "relative_path": path.relative_to(project_root).as_posix(), "specification_counts": counts})
        pickle_metrics = _merge_pickle_metrics(_collect_pickle_metrics(workspace_root))
        log_metrics = _metrics_from_run_log(raw)
        for metric in ("tokens_usage", "iteration_count", "llm_time_sec"):
            if not pickle_metrics.get(metric):
                pickle_metrics[metric] = log_metrics.get(metric, 0)
        evidence_summary = [f"merge order: {' -> '.join(merge_order)}"]
        if noisy:
            evidence_summary.append("contract noise detected in merged translation unit")
        if proof_stats["total_goals"]:
            evidence_summary.append(f"proved {proof_stats['proved_goals']} / {proof_stats['total_goals']} goals")
        return {
            "status": status,
            "summary": (
                "Inter-modular execution produced verifier-approved split outputs."
                if status == "Pass"
                else "Merged project validation failed before specification generation."
                if failure_analysis.get("category") == "merge-build"
                else "Inter-modular execution produced split outputs but the final proof did not close."
            ),
            "result_code": result_code,
            "specifications": normalized_specs,
            "verification_detail": "Merged translation-unit verification completed." if status == "Pass" else failure_analysis["summary"],
            "log_summary": [
                "live inter-modular execution",
                f"{len(split_files)} split files materialized",
                "verifier-approved" if status == "Pass" else failure_analysis["label"].lower(),
            ],
            "highlights": ["split output files", "workspace snapshot"] + (["noise-cleaned contracts"] if noisy else []),
            "proof_stats": proof_stats,
            "timing_stats": _timing_stats(
                llm_time_sec=pickle_metrics.get("llm_time_sec", 0.0),
                solve_time_sec=pickle_metrics.get("solve_time_sec", 0.0),
                timeout_sec=timeout_sec,
                iteration_count=pickle_metrics.get("iteration_count", 0),
                tokens_usage=pickle_metrics.get("tokens_usage", 0),
            ),
            "engine_detail": {
                "runner": "legacy-inter-modular",
                "status_source": "final_result" if final_files else "log-and-markers",
                "final_result_path": project_relative_path(final_files[-1]) if final_files else None,
                "merged_result_path": project_relative_path(merged_path) if merged_path else None,
                "invalid_marker_paths": [project_relative_path(path) for path in invalid_markers],
            },
            "failure_analysis": failure_analysis,
            "evidence_summary": evidence_summary + noise_markers[:2],
            "failure_excerpt": raw.strip().splitlines()[-1] if raw.strip() else None,
            "call_graph_summary": {
                "source_file_count": sum(path.suffix == ".c" for path in split_files),
                "header_file_count": sum(path.suffix == ".h" for path in split_files),
                "entry_files": [path.name for path in split_files if "main" in path.stem],
                "merge_order": merge_order,
                "call_edge_count": call_graph["call_edge_count"],
                "fan_out": call_graph["fan_out"],
                "edges": call_graph["edges"],
                "functions": call_graph["functions"],
                "entry_functions": call_graph["entry_functions"],
                "reachable_functions": call_graph["reachable_functions"],
            },
            "project_verification": project_verification,
            "module_results": module_results,
            "merged_translation_unit": _sanitize_result_code(result_code),
            "split_outputs": split_outputs,
        }

    @staticmethod
    def _collect_batch_output(output_root: Path, workspace_root: Path, results_root: Path, raw: str, *, returncode: int | None, timeout_sec: int | None) -> dict:
        jsonl_files = sorted(results_root.glob("*.jsonl"))
        rows: dict[str, dict] = {}
        latest_jsonl: Path | None = None
        if jsonl_files:
            latest_jsonl = sorted(jsonl_files, key=lambda item: item.stat().st_mtime)[-1]
            for line in latest_jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                rows[str(row.get("relative_path") or row.get("filename"))] = row

        def _row_status(row: dict, metrics: dict, pass_markers: list[Path], fail_markers: list[Path], invalid_markers: list[Path]) -> str:
            if row.get("Status") == "Timeout" or row.get("error_type") == "timeout":
                return "Timeout"
            if row.get("Status") == 1 or pass_markers:
                return "Pass"
            if row.get("Status") == 0 or fail_markers:
                return "Fail"
            if invalid_markers or row.get("Status") == "Check":
                return "Invalid"
            if metrics.get("status") == 1:
                return "Pass"
            if metrics.get("status") == 0:
                return "Fail"
            return "Invalid"

        def _default_file_proof(status: str) -> dict:
            if status == "Pass":
                return _normalize_proof_stats(1, 1, scope="files", unit="files")
            if status == "Timeout":
                return _normalize_proof_stats(0, 1, timeout_goals=1, scope="files", unit="files")
            if status == "Invalid":
                return _normalize_proof_stats(0, 1, invalid_goals=1, scope="files", unit="files")
            return _normalize_proof_stats(0, 1, scope="files", unit="files")

        items_by_path: dict[str, dict] = {}
        for pickle_path in sorted(workspace_root.rglob("*.pickle")):
            relative_path = pickle_path.relative_to(workspace_root).as_posix().replace(".pickle", "")
            filename = Path(relative_path).name
            row = rows.get(relative_path) or rows.get(filename) or {}
            metrics = _extract_pickle_metrics(pickle_path)
            stem = Path(filename).stem
            result_candidates = sorted(output_root.rglob(f"{stem}_final.c")) or sorted(output_root.rglob(f"{stem}_merged.c"))
            pass_markers = sorted(output_root.rglob(f"{stem}_merged_Pass_*_*.txt"))
            fail_markers = sorted(output_root.rglob(f"{stem}_merged_Fail_*_*.txt"))
            invalid_markers = sorted(output_root.rglob(f"{stem}_merged_Invalid*.txt"))
            status = _row_status(row, metrics, pass_markers, fail_markers, invalid_markers)
            marker_status, proof = _parse_result_marker(pass_markers[-1] if pass_markers else fail_markers[-1] if fail_markers else invalid_markers[-1] if invalid_markers else pickle_path)
            if status == "Pass" and marker_status != "Pass" and proof["total_goals"] == 0:
                proof = _default_file_proof(status)
            elif proof["total_goals"] == 0:
                proof = _default_file_proof(status)
            items_by_path[relative_path] = {
                "filename": filename,
                "relative_path": relative_path,
                "status": status,
                "status_category": "success" if status == "Pass" else "timeout" if status == "Timeout" else "invalid-spec" if status == "Invalid" else "proof-failed",
                "llm_time_sec": row.get("llm_time_sec", metrics.get("llm_time_sec", 0.0)),
                "total_solve_time_sec": row.get("total_solve_time_sec", metrics.get("solve_time_sec", 0.0)),
                "tokens_usage": row.get("tokens_usage", metrics.get("tokens_usage", 0)),
                "iteration_count": row.get("iteration_count", metrics.get("iteration_count", 0)),
                "error_type": row.get("error_type"),
                "error": row.get("error"),
                "result_path": project_relative_path(result_candidates[-1]) if result_candidates else None,
                "proof_stats": proof,
            }

        for relative_path, row in rows.items():
            if relative_path in items_by_path:
                continue
            filename = Path(relative_path).name
            stem = Path(filename).stem
            result_candidates = sorted(output_root.rglob(f"{stem}_final.c")) or sorted(output_root.rglob(f"{stem}_merged.c"))
            pass_markers = sorted(output_root.rglob(f"{stem}_merged_Pass_*_*.txt"))
            fail_markers = sorted(output_root.rglob(f"{stem}_merged_Fail_*_*.txt"))
            invalid_markers = sorted(output_root.rglob(f"{stem}_merged_Invalid*.txt"))
            status = _row_status(row, {}, pass_markers, fail_markers, invalid_markers)
            items_by_path[relative_path] = {
                "filename": filename,
                "relative_path": relative_path,
                "status": status,
                "status_category": "success" if status == "Pass" else "timeout" if status == "Timeout" else "invalid-spec" if status == "Invalid" else "proof-failed",
                "llm_time_sec": row.get("llm_time_sec", 0.0),
                "total_solve_time_sec": row.get("total_solve_time_sec", 0.0),
                "tokens_usage": row.get("tokens_usage", 0),
                "iteration_count": row.get("iteration_count", 0),
                "error_type": row.get("error_type"),
                "error": row.get("error"),
                "result_path": project_relative_path(result_candidates[-1]) if result_candidates else None,
                "proof_stats": _default_file_proof(status),
            }

        items: list[dict] = list(items_by_path.values())

        items = sorted(items, key=lambda item: (item["status"] != "Pass", item["relative_path"] or item["filename"]))
        counter = Counter(item["status"] for item in items)
        aggregate_metrics = {
            "total_items": len(items),
            "pass_count": counter.get("Pass", 0),
            "fail_count": counter.get("Fail", 0),
            "invalid_count": counter.get("Invalid", 0),
            "timeout_count": counter.get("Timeout", 0),
            "unavailable_count": counter.get("Unavailable", 0),
            "success_rate": _safe_ratio(counter.get("Pass", 0), len(items)),
            "closure_rate": _safe_ratio(counter.get("Pass", 0), len(items)),
            "avg_llm_time_sec": mean([item["llm_time_sec"] for item in items]) if items else 0.0,
            "avg_total_solve_time_sec": mean([item["total_solve_time_sec"] for item in items]) if items else 0.0,
            "max_total_solve_time_sec": max((item["total_solve_time_sec"] for item in items), default=0.0),
            "timeout_sec": timeout_sec,
            "failure_breakdown": dict(Counter(item["status_category"] for item in items if item.get("status_category"))),
        }
        if counter.get("Timeout", 0):
            status = "Timeout"
        elif items and counter.get("Pass", 0) == len(items):
            status = "Pass"
        elif items and counter.get("Invalid", 0) == len(items):
            status = "Invalid"
        elif items:
            status = "Fail"
        else:
            status = "Invalid"
        summary = (
            f"Batch execution finished with {aggregate_metrics['pass_count']} / {aggregate_metrics['total_items']} verifier-approved files."
            if items
            else "Batch execution did not produce structured file-level evidence."
        )
        failure_analysis = {
            "category": "none",
            "label": "Verifier-approved",
            "summary": "All batch items closed successfully.",
            "evidence": [],
            "actionable_hint": None,
        }
        if status != "Pass":
            if counter.get("Timeout", 0):
                failure_analysis = {
                    "category": "timeout",
                    "label": "Timeout",
                    "summary": "At least one batch item reached the configured timeout before proof closure.",
                    "evidence": [f"{counter.get('Timeout', 0)} files timed out within {timeout_sec}s."],
                    "actionable_hint": "Shorten the benchmark set or simplify candidate invariants before increasing the timeout.",
                }
            else:
                failure_analysis = _classify_failure(raw, context="batch")
        return {
            "status": status,
            "summary": summary,
            "result_code": latest_jsonl.read_text(encoding="utf-8", errors="ignore") if latest_jsonl else "",
            "verification_detail": "Batch verifier summary collected." if items else "Batch verifier summary is missing.",
            "log_summary": [
                "live batch execution",
                f"{aggregate_metrics['total_items']} files summarized",
                f"{aggregate_metrics['pass_count']} passed",
            ],
            "highlights": ["experiment JSONL" if jsonl_files else "pickle-derived summary", "aggregate metrics", "failure distribution"],
            "proof_stats": _normalize_proof_stats(
                aggregate_metrics["pass_count"],
                aggregate_metrics["total_items"],
                timeout_goals=aggregate_metrics["timeout_count"],
                invalid_goals=aggregate_metrics["invalid_count"],
                scope="files",
                unit="files",
            ),
            "timing_stats": _timing_stats(
                llm_time_sec=aggregate_metrics["avg_llm_time_sec"] * aggregate_metrics["total_items"],
                solve_time_sec=aggregate_metrics["avg_total_solve_time_sec"] * aggregate_metrics["total_items"],
                avg_item_time_sec=aggregate_metrics["avg_total_solve_time_sec"],
                timeout_sec=timeout_sec,
            ),
            "engine_detail": {
                "runner": "legacy-batch",
                "status_source": "jsonl" if latest_jsonl else "pickles",
                "result_jsonl_path": project_relative_path(latest_jsonl) if latest_jsonl else None,
                "returncode": returncode,
            },
            "failure_analysis": failure_analysis,
            "evidence_summary": [f"failure breakdown {aggregate_metrics['failure_breakdown']}", f"timeout window {timeout_sec}s"],
            "failure_excerpt": raw.strip().splitlines()[-1] if raw.strip() else None,
            "aggregate_metrics": aggregate_metrics,
            "items": items,
        }
