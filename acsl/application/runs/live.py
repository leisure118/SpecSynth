"""Live execution for replay, single, termination, inter-modular and batch modes."""
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


class RunLiveMixin:
    def _run_replay(self, task: RunTask) -> dict:
        case = get_demo_case(task.demo_case_id or "")
        if task.mode not in {"single", "termination", "inter-modular"}:
            raise RuntimeError(f"Replay mode is not configured for {task.mode}.")

        source_ref = case.get("source_dir") or case.get("source_file")
        source_root = resolve_project_path(source_ref) if source_ref else None
        if source_root and source_root.exists() and source_root.is_dir():
            input_dirname = str(case.get("input_artifact_dir") or source_root.name)
            input_path = resolve_project_path(task.task_dir) / "artifacts" / "input" / input_dirname
            shutil.copytree(source_root, input_path)
        elif source_root and source_root.exists():
            input_path = self.store.copy_artifact(task.task_id, source_root, "input")
        else:
            input_path = self.store.write_text_artifact(
                task.task_id,
                "input",
                "replay_source.c",
                case.get("source_code") or case.get("single_result_code") or case.get("inter_modular_result_code") or "",
            )
        task.input_file = project_relative_path(input_path)
        task.metadata = {
            "case_id": case["id"],
            "case_modes": case["modes"],
            "input_manifest": _build_manifest(input_path),
        }
        self.store.write_task(task)

        self._advance_phase(task, "static_analysis", "completed", "Loaded curated replay case.")
        time.sleep(0.05)
        if task.mode == "inter-modular":
            self._advance_phase(task, "extended_call_graph", "completed", "Replayed curated call graph and module split summary.")
            self._advance_phase(task, "generate_specifications", "completed", "Replayed merged translation-unit specification artifact.")
            self._advance_phase(task, "formal_verifying", "completed", "Replayed verifier-approved inter-modular result.")
            self.store.write_text_artifact(task.task_id, "output", "merged_translation_unit.c", case["inter_modular_result_code"])
            self.store.write_text_artifact(task.task_id, "logs", "run.log", case["inter_modular_log"])
            return self._build_result(
                task,
                status="Pass",
                summary=case["result_summary"]["inter-modular"],
                source_code=case["source_code"],
                result_code=case["inter_modular_result_code"],
                command=case.get("inter_modular_command", "replay://inter-modular"),
                logs={
                    "summary": [
                        "curated inter-modular replay",
                        "merged translation unit restored",
                        "verifier-approved",
                    ],
                    "raw": case["inter_modular_log"],
                },
                specifications=case["inter_modular_specifications"],
                highlights=case["highlights"],
                paper_keywords=case["paper_keywords"],
                proof_stats=case.get("inter_modular_proof_stats") or {
                    "proved_goals": max(1, len(case["inter_modular_specifications"]["contracts"]) + len(case["inter_modular_specifications"]["loop_invariants"])),
                    "total_goals": max(1, len(case["inter_modular_specifications"]["contracts"]) + len(case["inter_modular_specifications"]["loop_invariants"])),
                },
                engine_detail={"runner": "replay-inter-modular"},
                evidence_summary=case.get("inter_modular_evidence_summary", []),
                call_graph_summary=case.get("inter_modular_call_graph_summary", {}),
                module_results=case.get("inter_modular_module_results", []),
                merged_translation_unit=case["inter_modular_result_code"],
                split_outputs=case.get("inter_modular_split_outputs", []),
            )
        if task.mode == "termination":
            self._advance_phase(task, "generate_specifications", "completed", "Replayed verified stage-1 artifact.")
            self._advance_phase(task, "formal_verifying", "completed", "Replayed stage-2 verification trace.")
            self._advance_phase(task, "iterative_repair", "completed", "Replayed total-correctness repair trace.")
            self._advance_phase(task, "termination", "completed", "Replayed ranking-function synthesis.")
            self.store.write_text_artifact(task.task_id, "output", "stage1_verified.c", case["single_result_code"])
            self.store.write_text_artifact(task.task_id, "output", "stage2_variant_injected.c", case["termination_stage2_code"])
            self.store.write_text_artifact(task.task_id, "output", "stage2_verified.c", case["termination_result_code"])
            self.store.write_text_artifact(task.task_id, "logs", "run.log", self._termination_logs(case)["raw"])
            return self._build_result(
                task,
                status="Pass",
                summary=case["result_summary"]["termination"],
                source_code=case["source_code"],
                result_code=case["termination_result_code"],
                partial_correctness_code=case["single_result_code"],
                command=case.get("termination_command", "replay://termination"),
                logs=self._termination_logs(case),
                specifications=case["termination_specifications"],
                highlights=case["highlights"],
                paper_keywords=case["paper_keywords"],
                proof_stats={"proved_goals": 1, "total_goals": 1},
                timing_stats=case.get("termination_timing_stats") or None,
                engine_detail={"runner": "replay-termination"},
            )

        self._advance_phase(task, "generate_specifications", "completed", "Replayed synthesized ACSL clauses.")
        self._advance_phase(task, "formal_verifying", "completed", "Replayed verifier-approved result.")
        self._advance_phase(task, "iterative_repair", "completed", "Captured proof-aware iterative repair trace.")
        single_logs = self._single_logs(case)
        single_proof_stats = _proof_stats_from_text(single_logs.get("raw", "")) or {}
        if not single_proof_stats.get("total_goals"):
            single_proof_stats = {
                "proved_goals": len(case["single_specifications"]["loop_invariants"]),
                "total_goals": len(case["single_specifications"]["loop_invariants"]),
            }
        if any(marker in single_logs.get("raw", "") for marker in ("[wp]", "[verifier]", "Proved goals")):
            single_proof_stats = _normalize_proof_stats(
                single_proof_stats.get("proved_goals", 0),
                single_proof_stats.get("total_goals", 0),
            )
        self.store.write_text_artifact(task.task_id, "output", "single_result.c", case["single_result_code"])
        self.store.write_text_artifact(task.task_id, "logs", "run.log", single_logs["raw"])
        return self._build_result(
            task,
            status="Pass",
            summary=case["result_summary"]["single"],
            source_code=case["source_code"],
            result_code=case["single_result_code"],
            partial_correctness_code=None,
            command=case.get("single_command", "replay://single"),
            logs=single_logs,
            specifications=case["single_specifications"],
            highlights=case["highlights"],
            paper_keywords=case["paper_keywords"],
            proof_stats=single_proof_stats,
            timing_stats=case.get("single_timing_stats") or None,
            engine_detail={"runner": "replay-single"},
        )

    def _run_live(self, task: RunTask, payload: RunRequest) -> dict:
        if payload.verification_tool=="verifast" and not payload.verification_only and (not payload.assistant or payload.assistant.get("agent")=="default"):
            raise ValueError("VeriFast 规约生成需要选择 Agent。")
        if payload.verification_tool == "verifast" and payload.verification_only:
            from acsl.application.verifier_execution import execute_verifast
            return execute_verifast(self, task, payload)
        if payload.verification_only:
            from acsl.application.agent_execution import execute_verification_only
            return execute_verification_only(self, task, payload)
        if payload.assistant and payload.assistant.get("agent", "default") != "default" and task.mode != "rust-verify":
            from acsl.application.agent_execution import execute_agent
            return execute_agent(self, task, payload)
        if task.mode.startswith("rust-"):
            from acsl.application.rust_execution import execute_rust
            return execute_rust(self, task, payload)
        capabilities = self.refresh_capabilities()
        task.capabilities = capabilities.as_dict()
        self.store.write_task(task)
        detail = capabilities.mode_detail(task.mode)
        if not detail["ready"]:
            raw = "\n".join(detail["details"])
            return self._unavailable_result(
                task,
                detail["summary"],
                raw=raw,
                actionable_hint=detail["actionable_hint"],
            )

        source = self._materialize_input(task, payload)
        task.metadata["input_manifest"] = _build_manifest(source)
        task.input_file = project_relative_path(source)
        self.store.write_task(task)

        if task.mode == "single":
            return self._run_live_single(task, payload, source)
        if task.mode == "termination":
            return self._run_live_termination(task, payload, source)
        if task.mode == "inter-modular":
            return self._run_live_inter_modular(task, payload, source)
        if task.mode == "batch":
            return self._run_live_batch(task, payload, source)
        raise RuntimeError(f"Unsupported mode: {task.mode}")

    def _materialize_input(self, task: RunTask, payload: RunRequest) -> Path:
        if payload.demo_case_id:
            case = get_demo_case(payload.demo_case_id)
            source_file = case.get("source_file")
            source_dir = case.get("source_dir")
            source = resolve_project_path(source_dir or source_file)
            if not source.exists():
                raise FileNotFoundError(f"Demo input not found: {source}")
            task.metadata["case_id"] = case["id"]
            if source.is_dir():
                target = resolve_project_path(task.task_dir) / "artifacts" / "input" / source.name
                shutil.copytree(source, target)
                return target
            return self.store.copy_artifact(task.task_id, source, "input")

        upload = self.store.read_upload(payload.file_id or "")
        if upload is None:
            raise FileNotFoundError("Uploaded file metadata is missing.")
        source = resolve_project_path(upload["stored_path"])
        if upload.get("kind") == "bundle":
            target = resolve_project_path(task.task_dir) / "artifacts" / "input" / (upload.get("root_dir") or source.name)
            shutil.copytree(source, target)
            return target
        return self.store.copy_artifact(task.task_id, source, "input")

    def _run_live_single(self, task: RunTask, payload: RunRequest, source: Path) -> dict:
        self._advance_phase(task, "static_analysis", "completed", "Prepared single-file input for AutoSpec.")

        cached = None if payload.agent_instructions else self._find_verified_single_cache(task, source)
        if cached is not None:
            cached_task, cached_result = cached
            self._advance_phase(task, "generate_specifications", "completed", "Reused a verifier-approved specification cache; no LLM call was required.")
            self._advance_phase(task, "formal_verifying", "completed", "Reused proof evidence from an identical source snapshot.")
            self._advance_phase(task, "iterative_repair", "completed", "No repair iteration required for the verified cache hit.")
            cached_success_log = _successful_iteration_log(
                ((cached_result.get("logs") or {}).get("raw") or ""),
                proof_stats=cached_result.get("proof_stats") or {},
            )
            cache_log = cached_success_log
            self.store.write_text_artifact(task.task_id, "logs", "run.log", cache_log)
            self.store.write_text_artifact(task.task_id, "output", "final_verified.c", cached_result.get("result_code", ""))
            return self._build_result(
                task,
                status="Pass",
                summary="Reused a verifier-approved result for identical source code.",
                source_code=source.read_text(encoding="utf-8", errors="ignore"),
                result_code=cached_result.get("result_code", ""),
                partial_correctness_code=None,
                command=f"cache://single/{cached_task.task_id}",
                logs={"summary": ["verified cache hit", "LLM call skipped", "proof evidence reused"], "raw": cache_log},
                specifications=cached_result.get("specifications") or {},
                highlights=["verified result cache", "zero LLM calls", "verifier-approved"],
                proof_stats=cached_result.get("proof_stats") or {},
                timing_stats=_timing_stats(llm_time_sec=0.0, solve_time_sec=0.0, iteration_count=0, tokens_usage=0),
                engine_detail={
                    "runner": "verified-single-cache",
                    "cache_hit": True,
                    "cached_from_task_id": cached_task.task_id,
                    "source_sha256": _sha256(source),
                },
                evidence_summary=[f"identical source SHA-256 matched task {cached_task.task_id}", "cached proof goals were fully closed"],
            )

        self._advance_phase(task, "generate_specifications", "running", "Calling legacy single-file synthesis.")

        output_dir = resolve_project_path(task.task_dir) / "artifacts" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        command = build_single_command(
            source.relative_to(settings.root_dir).as_posix(),
            output_dir.relative_to(settings.root_dir).as_posix(),
            payload.model_name,
            payload.enable_mutation,
        )
        timeout_sec = payload.timeout_sec or int(os.getenv("AUTOSPEC_SINGLE_TIMEOUT", "120"))
        try:
            completed = run_command(command, settings.root_dir, timeout=timeout_sec, **({"agent_instructions": payload.agent_instructions} if payload.agent_instructions else {}))
            raw = (completed.stdout or "") + "\n" + (completed.stderr or "")
        except subprocess.TimeoutExpired as exc:
            raw = _timeout_output(exc)
            self.store.write_text_artifact(task.task_id, "logs", "run.log", raw or str(exc))
            legacy = self._collect_single_live_output(source.parent, output_dir, raw, returncode=None, timeout_sec=timeout_sec)
            legacy["status"] = "Timeout"
            legacy["summary"] = "Single live execution timed out before a stable verifier-approved artifact was produced."
            legacy["failure_excerpt"] = raw.strip().splitlines()[-1] if raw.strip() else f"Timeout after {timeout_sec}s"
            self._advance_phase(task, "generate_specifications", "failed", "Single live execution timed out.")
            self._advance_phase(task, "formal_verifying", "failed", legacy["verification_detail"])
            self._advance_phase(task, "iterative_repair", "skipped", "Skipped after timeout.")
            return self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=source.read_text(encoding="utf-8", errors="ignore"),
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=" ".join(command),
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications=legacy["specifications"],
                highlights=["live execution", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail=legacy["engine_detail"],
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
            )
        legacy = self._collect_single_live_output(source.parent, output_dir, raw, returncode=completed.returncode, timeout_sec=timeout_sec)
        stored_raw = (
            _successful_iteration_log(raw, proof_stats=legacy["proof_stats"])
            if legacy["status"] == "Pass"
            else raw
        )
        self.store.write_text_artifact(task.task_id, "logs", "run.log", stored_raw)
        self._compact_successful_single_artifacts(source, output_dir, legacy)
        self._advance_phase(task, "generate_specifications", "completed", "AutoSpec single-file execution returned.")
        self._advance_phase(
            task,
            "formal_verifying",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["verification_detail"],
        )
        self._advance_phase(
            task,
            "iterative_repair",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["iteration_detail"],
        )
        return self._build_result(
            task,
            status=legacy["status"],
            summary=legacy["summary"],
            source_code=source.read_text(encoding="utf-8", errors="ignore"),
            result_code=legacy["result_code"],
            partial_correctness_code=None,
            command=" ".join(command),
            logs={"summary": legacy["log_summary"], "raw": stored_raw},
            specifications=legacy["specifications"],
            highlights=["live execution", *legacy["highlights"]],
            proof_stats=legacy["proof_stats"],
            timing_stats=legacy["timing_stats"],
            engine_detail=legacy["engine_detail"],
            failure_excerpt=legacy["failure_excerpt"],
            failure_analysis=legacy["failure_analysis"],
            evidence_summary=legacy["evidence_summary"],
        )

    def _find_verified_single_cache(self, task: RunTask, source: Path) -> tuple[RunTask, dict] | None:
        """Find a completed proof for exactly the same single-file source."""
        source_sha = _sha256(source)
        for candidate in self.store.list_tasks(limit=1000):
            if candidate.task_id == task.task_id or candidate.mode != "single" or candidate.status != "pass":
                continue
            if task.demo_case_id and candidate.demo_case_id != task.demo_case_id:
                continue
            manifest = candidate.metadata.get("input_manifest") or []
            if not any(item.get("sha256") == source_sha for item in manifest):
                continue
            result = self.store.read_result(candidate.task_id)
            # Always reuse evidence from a real verifier run.  Chaining cache
            # hits would preserve only cache metadata instead of the successful
            # synthesis/verification iteration requested for run.log.
            if ((result or {}).get("engine_detail") or {}).get("cache_hit"):
                continue
            proof = (result or {}).get("proof_stats") or {}
            if (
                result
                and result.get("status") == "Pass"
                and result.get("result_code")
                and proof.get("total_goals", 0) > 0
                and proof.get("proved_goals") == proof.get("total_goals")
                and not proof.get("open_goals", 0)
            ):
                return candidate, result
        return None

    @staticmethod
    def _compact_successful_single_artifacts(source: Path, output_dir: Path, legacy: dict) -> None:
        """Keep only the final successful iteration instead of every repair trace."""
        if legacy.get("status") != "Pass" or not legacy.get("result_code"):
            return
        shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "final_verified.c").write_text(legacy["result_code"], encoding="utf-8")
        proof = legacy.get("proof_stats") or {}
        (output_dir / "final_result").write_text(
            f"Pass\nproved_goals={proof.get('proved_goals', 0)}\ntotal_goals={proof.get('total_goals', 0)}\n",
            encoding="utf-8",
        )
        pickle_path = Path(str(source) + ".pickle")
        if pickle_path.exists():
            pickle_path.unlink()

    def _run_live_termination(self, task: RunTask, payload: RunRequest, source: Path) -> dict:
        source_text = source.read_text(encoding="utf-8", errors="ignore")
        if not payload.upstream_task_id and not _termination_input_ready(source_text):
            summary = "终止性验证需要已具备 loop invariant 的 stage-1 文件；当前上传文件仍是原始源码。"
            detail = "请先在单函数分析中生成并验证部分正确性结果，再将该结果用于终止性验证。"
            self._fail_remaining_phases(task, summary)
            return self._build_result(
                task,
                status="Invalid",
                summary=summary,
                source_code=source_text,
                result_code="",
                command=None,
                partial_correctness_code=None,
                logs={"summary": [summary], "raw": detail},
                specifications={},
                highlights=["termination input rejected"],
                failure_excerpt=detail,
                failure_analysis={
                    "category": "input",
                    "label": "Input Not Ready",
                    "summary": summary,
                    "evidence": [
                        "当前文件中未检测到 loop invariant，termination 链路无法注入 loop variant。"
                    ],
                    "actionable_hint": detail,
                },
                evidence_summary=["missing loop invariant", "stage-1 partial-correctness artifact required"],
            )

        self._advance_phase(task, "static_analysis", "completed", "Prepared stage-1 verified input for termination analysis.")
        stage1_dir = resolve_project_path(task.task_dir) / "artifacts" / "stage1"
        stage2_dir = resolve_project_path(task.task_dir) / "artifacts" / "stage2"
        verified_dir = resolve_project_path(task.task_dir) / "artifacts" / "verified"
        for folder in (stage1_dir, stage2_dir, verified_dir):
            folder.mkdir(parents=True, exist_ok=True)

        stage1_file = stage1_dir / f"{source.stem}_verified.c"
        if payload.upstream_task_id:
            previous = self.store.read_result(payload.upstream_task_id)
            if previous and previous.get("result_code"):
                stage1_file.write_text(previous["result_code"], encoding="utf-8")
            else:
                stage1_file.write_text(source_text, encoding="utf-8")
        else:
            stage1_file.write_text(source_text, encoding="utf-8")

        self._advance_phase(task, "generate_specifications", "completed", "Stage-1 snapshot was prepared.")
        self._advance_phase(task, "formal_verifying", "running", "Generating ranking functions and calling Frama-C.")

        commands = build_termination_commands(
            stage1_dir.relative_to(settings.root_dir).as_posix(),
            stage2_dir.relative_to(settings.root_dir).as_posix(),
            verified_dir.relative_to(settings.root_dir).as_posix(),
            payload.model_name,
            service=self.capabilities.termination_service,
        )
        raw_parts: list[str] = []
        for command in commands:
            completed = run_command(command, settings.root_dir, **({"agent_instructions": payload.agent_instructions} if payload.agent_instructions else {}))
            raw_parts.append((completed.stdout or "") + "\n" + (completed.stderr or ""))
            if completed.returncode != 0:
                raw = "\n".join(raw_parts)
                self.store.write_text_artifact(task.task_id, "logs", "run.log", raw)
                self._advance_phase(task, "formal_verifying", "failed", "Termination chain returned a non-zero exit code.")
                return self._unavailable_result(task, "Termination live execution failed before producing verified output.", raw, " ".join(command))

        raw = "\n".join(raw_parts)
        self.store.write_text_artifact(task.task_id, "logs", "run.log", raw)
        legacy = self._collect_termination_live_output(stage2_dir, verified_dir, raw)
        self._advance_phase(
            task,
            "formal_verifying",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["verification_detail"],
        )
        self._advance_phase(
            task,
            "iterative_repair",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["iteration_detail"],
        )
        self._advance_phase(
            task,
            "termination",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["termination_detail"],
        )
        return self._build_result(
            task,
            status=legacy["status"],
            summary=legacy["summary"],
            source_code=source.read_text(encoding="utf-8", errors="ignore"),
            result_code=legacy["result_code"],
            partial_correctness_code=stage1_file.read_text(encoding="utf-8", errors="ignore"),
            command=" && ".join(" ".join(command) for command in commands),
            logs={"summary": legacy["log_summary"], "raw": raw},
            specifications=legacy["specifications"],
            highlights=["live execution", "termination chain", *legacy["highlights"]],
            proof_stats=legacy["proof_stats"],
            engine_detail=legacy["engine_detail"],
            failure_excerpt=legacy["failure_excerpt"],
        )

    def _run_live_inter_modular(self, task: RunTask, payload: RunRequest, source: Path) -> dict:
        if not source.is_dir():
            return self._unavailable_result(task, "Inter-modular mode requires a bundled multi-file project directory.")

        workspace_root = resolve_project_path(task.task_dir) / "artifacts" / "workspace"
        project_root = workspace_root / source.name
        shutil.copytree(source, project_root)
        input_files = [path for path in sorted(project_root.rglob("*")) if path.suffix in {".c", ".h"}]
        if not input_files:
            return self._unavailable_result(task, "Inter-modular input directory does not contain .c or .h files.")

        self._advance_phase(task, "static_analysis", "completed", f"Prepared {len(input_files)} source files for inter-modular execution.")
        self._advance_phase(task, "extended_call_graph", "completed", f"Workspace call graph seed includes {sum(path.suffix == '.c' for path in input_files)} C files and {sum(path.suffix == '.h' for path in input_files)} headers.")
        self._advance_phase(task, "generate_specifications", "running", "Executing merged translation-unit workflow.")

        command = build_inter_modular_command(
            [path.relative_to(workspace_root).as_posix() for path in input_files],
            payload.model_name,
            workspace_root.relative_to(settings.root_dir).as_posix(),
        )
        timeout_sec = payload.timeout_sec or 600
        try:
            completed = run_command(command, settings.root_dir, timeout=timeout_sec, **({"agent_instructions": payload.agent_instructions} if payload.agent_instructions else {}))
            raw = (completed.stdout or "") + "\n" + (completed.stderr or "")
        except subprocess.TimeoutExpired as exc:
            raw = _timeout_output(exc)
            self.store.write_text_artifact(task.task_id, "logs", "run.log", raw or str(exc))
            legacy = self._collect_inter_modular_output(project_root, workspace_root, raw, returncode=None, timeout_sec=timeout_sec)
            legacy["status"] = "Timeout"
            legacy["summary"] = "Inter-modular execution timed out before final proof closure."
            self._advance_phase(task, "generate_specifications", "failed", "Inter-modular synthesis timed out.")
            self._advance_phase(task, "formal_verifying", "failed", legacy["verification_detail"])
            return self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=_concat_sources(source),
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=" ".join(command),
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications=legacy["specifications"],
                highlights=["live execution", "inter-modular synthesis", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail=legacy["engine_detail"],
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
                call_graph_summary=legacy["call_graph_summary"],
                module_results=legacy["module_results"],
                merged_translation_unit=legacy["merged_translation_unit"],
                split_outputs=legacy["split_outputs"],
                project_verification=legacy["project_verification"],
            )
        self.store.write_text_artifact(task.task_id, "logs", "run.log", raw)

        legacy = self._collect_inter_modular_output(project_root, workspace_root, raw, returncode=completed.returncode, timeout_sec=timeout_sec)
        build_failed = legacy.get("failure_analysis", {}).get("category") == "merge-build"
        self._advance_phase(
            task,
            "generate_specifications",
            "failed" if build_failed else "completed",
            "Merged project preflight failed; the LLM was not invoked." if build_failed else "Inter-modular synthesis completed.",
        )
        self._advance_phase(
            task,
            "formal_verifying",
            "skipped" if build_failed else "completed" if legacy["status"] == "Pass" else "failed",
            "Skipped because the merged project did not compile." if build_failed else legacy["verification_detail"],
        )
        return self._build_result(
            task,
            status=legacy["status"],
            summary=legacy["summary"],
            source_code=_concat_sources(source),
            result_code=legacy["result_code"],
            partial_correctness_code=None,
            command=" ".join(command),
            logs={"summary": legacy["log_summary"], "raw": raw},
            specifications=legacy["specifications"],
            highlights=["live execution", "inter-modular synthesis", *legacy["highlights"]],
            proof_stats=legacy["proof_stats"],
            timing_stats=legacy["timing_stats"],
            engine_detail=legacy["engine_detail"],
            failure_excerpt=legacy["failure_excerpt"],
            failure_analysis=legacy["failure_analysis"],
            evidence_summary=legacy["evidence_summary"],
            call_graph_summary=legacy["call_graph_summary"],
            module_results=legacy["module_results"],
            merged_translation_unit=legacy["merged_translation_unit"],
            split_outputs=legacy["split_outputs"],
            project_verification=legacy["project_verification"],
        )

    def _run_live_batch(self, task: RunTask, payload: RunRequest, source: Path) -> dict:
        if not source.is_dir():
            return self._unavailable_result(task, "Batch mode requires a directory or bundle upload.")

        output_root = resolve_project_path(task.task_dir) / "artifacts" / "output"
        workspace_root = resolve_project_path(task.task_dir) / "artifacts" / "workspace"
        results_root = output_root / "experiment_results"
        output_root.mkdir(parents=True, exist_ok=True)
        workspace_root.mkdir(parents=True, exist_ok=True)
        results_root.mkdir(parents=True, exist_ok=True)
        files = [path for path in sorted(source.rglob("*.c")) if path.is_file()]
        if not files:
            return self._unavailable_result(task, "Batch directory does not contain .c files.")

        self._advance_phase(task, "static_analysis", "completed", f"Scanned batch directory with {len(files)} C files.")
        self._advance_phase(task, "generate_specifications", "running", "Launching directory-level batch execution.")

        command = build_batch_command(
            source.relative_to(settings.root_dir).as_posix(),
            payload.model_name,
            workspace_root.relative_to(settings.root_dir).as_posix(),
            results_root.relative_to(settings.root_dir).as_posix(),
            output_root.relative_to(settings.root_dir).as_posix(),
        )
        timeout_sec = payload.timeout_sec or int(os.getenv("AUTOSPEC_BATCH_TIMEOUT", "180"))
        task.metadata["timeout_sec"] = timeout_sec
        self.store.write_task(task)
        try:
            completed = run_command(command, settings.root_dir, timeout=timeout_sec, **({"agent_instructions": payload.agent_instructions} if payload.agent_instructions else {}))
            raw = (completed.stdout or "") + "\n" + (completed.stderr or "")
        except subprocess.TimeoutExpired as exc:
            raw = _timeout_output(exc)
            self.store.write_text_artifact(task.task_id, "logs", "run.log", raw or str(exc))
            legacy = self._collect_batch_output(output_root, workspace_root, results_root, raw, returncode=None, timeout_sec=timeout_sec)
            legacy["status"] = "Timeout"
            legacy["summary"] = "Batch execution hit the configured timeout; partial file-level evidence was still collected."
            self._advance_phase(task, "generate_specifications", "failed", "Batch execution timed out.")
            self._advance_phase(task, "formal_verifying", "failed", legacy["verification_detail"])
            return self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=_concat_sources(source),
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=" ".join(command),
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications={},
                highlights=["live execution", "batch evaluation", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail=legacy["engine_detail"],
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
                aggregate_metrics=legacy["aggregate_metrics"],
                items=legacy["items"],
            )
        self.store.write_text_artifact(task.task_id, "logs", "run.log", raw)
        legacy = self._collect_batch_output(output_root, workspace_root, results_root, raw, returncode=completed.returncode, timeout_sec=timeout_sec)
        self._advance_phase(task, "generate_specifications", "completed", "Batch synthesis finished.")
        self._advance_phase(
            task,
            "formal_verifying",
            "completed" if legacy["status"] == "Pass" else "failed",
            legacy["verification_detail"],
        )
        return self._build_result(
            task,
            status=legacy["status"],
            summary=legacy["summary"],
            source_code=_concat_sources(source),
            result_code=legacy["result_code"],
            partial_correctness_code=None,
            command=" ".join(command),
            logs={"summary": legacy["log_summary"], "raw": raw},
            specifications={},
            highlights=["live execution", "batch evaluation", *legacy["highlights"]],
            proof_stats=legacy["proof_stats"],
            timing_stats=legacy["timing_stats"],
            engine_detail=legacy["engine_detail"],
            failure_excerpt=legacy["failure_excerpt"],
            failure_analysis=legacy["failure_analysis"],
            evidence_summary=legacy["evidence_summary"],
            aggregate_metrics=legacy["aggregate_metrics"],
            items=legacy["items"],
        )
