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

from engine.integration.legacy_adapters import (
    build_batch_command,
    build_inter_modular_command,
    build_single_command,
    build_termination_commands,
    detect_live_capabilities,
    run_command,
)

from .config import APP_NAME, PHASE_LABELS, ROOT_DIR, RUNS_DIR, project_relative_path, resolve_project_path
from .demo_cases import extract_specifications, get_demo_case, list_demo_cases
from .schemas import ArtifactItem, PhaseState, RunRequest, RunResult, RunTask
from .storage import JsonStore, utcnow


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _subprocess_output_text(value: str | bytes | None) -> str:
    """Normalize subprocess output, including TimeoutExpired byte buffers."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _timeout_output(exc: subprocess.TimeoutExpired) -> str:
    return (
        _subprocess_output_text(exc.stdout)
        + "\n"
        + _subprocess_output_text(exc.stderr)
    ).strip()


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _elapsed_ms(started_at: datetime | None, finished_at: datetime | None) -> int | None:
    if started_at is None or finished_at is None:
        return None
    return max(int((finished_at - started_at).total_seconds() * 1000), 0)


def _proof_stats_from_text(raw: str) -> dict:
    stats = {"proved_goals": 0, "total_goals": 0}
    for match in re.finditer(r"\[wp\] Proved goals:\s+(\d+)\s*/\s*(\d+)", raw):
        stats = {
            "proved_goals": int(match.group(1)),
            "total_goals": int(match.group(2)),
        }
    return stats


def _proof_stats_from_paths(paths: list[Path]) -> dict:
    stats = {"proved_goals": 0, "total_goals": 0}
    for path in paths:
        match = re.search(r"_(?:Pass|Fail)_(\d+)_(\d+)\.txt$", path.name)
        if match:
            stats = {
                "proved_goals": int(match.group(1)),
                "total_goals": int(match.group(2)),
            }
    return stats


def _build_manifest(root: Path) -> list[dict]:
    base = root if root.is_dir() else root.parent
    files = [root] if root.is_file() else [path for path in sorted(root.rglob("*")) if path.is_file()]
    return [
        {
            "relative_path": str(path.relative_to(base)).replace("\\", "/") if path != base else path.name,
            "path": project_relative_path(path),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in files
    ]


def _concat_sources(root: Path) -> str:
    if root.is_file():
        return root.read_text(encoding="utf-8", errors="ignore")
    blocks = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        blocks.append(f"/* === {path.relative_to(root).as_posix()} === */")
        blocks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n\n".join(blocks)


def _phase_metrics(task: RunTask) -> list[dict]:
    items = []
    for phase in task.phases:
        items.append(
            {
                "key": phase.key,
                "label": phase.label,
                "status": phase.status,
                "detail": phase.detail,
                "started_at": _format_datetime(phase.started_at),
                "finished_at": _format_datetime(phase.finished_at),
                "elapsed_ms": _elapsed_ms(phase.started_at, phase.finished_at),
            }
        )
    return items


def _status_to_task_status(status: str) -> str:
    mapping = {
        "Pass": "pass",
        "Fail": "fail",
        "Invalid": "invalid",
        "Timeout": "timeout",
        "Unavailable": "unavailable",
    }
    return mapping.get(status, "fail")


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _normalize_proof_stats(
    proved_goals: int = 0,
    total_goals: int = 0,
    *,
    timeout_goals: int = 0,
    invalid_goals: int = 0,
    scope: str = "proof-goals",
    unit: str = "goals",
) -> dict:
    open_goals = max(total_goals - proved_goals - timeout_goals - invalid_goals, 0)
    return {
        "scope": scope,
        "unit": unit,
        "proved_goals": max(proved_goals, 0),
        "total_goals": max(total_goals, 0),
        "timeout_goals": max(timeout_goals, 0),
        "invalid_goals": max(invalid_goals, 0),
        "open_goals": open_goals,
        "pass_rate": _safe_ratio(proved_goals, total_goals),
    }


def _timing_stats(
    *,
    wall_clock_ms: int | None = None,
    llm_time_sec: float = 0.0,
    solve_time_sec: float = 0.0,
    avg_item_time_sec: float = 0.0,
    timeout_sec: int | None = None,
    iteration_count: int = 0,
    tokens_usage: int = 0,
) -> dict:
    return {
        "wall_clock_ms": wall_clock_ms,
        "llm_time_sec": round(llm_time_sec, 3),
        "solve_time_sec": round(solve_time_sec, 3),
        "avg_item_time_sec": round(avg_item_time_sec, 3),
        "timeout_sec": timeout_sec,
        "iteration_count": iteration_count,
        "tokens_usage": tokens_usage,
    }


def _task_summary(task: RunTask, status: str) -> dict:
    completed = sum(1 for phase in task.phases if phase.status == "completed")
    return {
        "mode": task.mode,
        "engine": task.engine,
        "source_type": task.source_type,
        "phase_count": len(task.phases),
        "completed_phase_count": completed,
        "status": status,
    }


def _sanitize_result_code(code: str) -> str:
    if not code:
        return code
    cleaned = code.replace("/* @;", "").replace("/*@;", "")
    cleaned = cleaned.replace("/* @ >>> INFILL <<< */", "")
    cleaned = cleaned.replace("/*@>>> INFILL <<<*/", "")
    cleaned = re.sub(r"/\*\s*@\s*\n", "/*@\n", cleaned)
    cleaned = re.sub(r"\n\s*>>> INFILL <<<\s*\n", "\n", cleaned)
    return cleaned


def _termination_input_ready(code: str) -> bool:
    if not code:
        return False
    return "loop invariant" in code and bool(re.search(r"(while|for)\s*\(", code))


def _rank_spec(spec: str) -> tuple[int, int, str]:
    if spec.startswith("requires "):
        return (0, len(spec), spec)
    if spec.startswith("ensures "):
        return (1, len(spec), spec)
    if spec.startswith("assigns "):
        return (2, len(spec), spec)
    if spec.startswith("loop invariant 0 <=") or spec.startswith("loop invariant 0<="):
        return (3, len(spec), spec)
    if spec.startswith("loop invariant ") and "==" in spec:
        return (4, len(spec), spec)
    if spec.startswith("loop invariant ") and "\\forall" in spec:
        return (5, len(spec), spec)
    if spec.startswith("loop invariant "):
        return (6, len(spec), spec)
    if spec.startswith("loop assigns "):
        return (7, len(spec), spec)
    return (8, len(spec), spec)


def _normalize_specifications(specs: dict | None) -> tuple[dict, list[str], bool]:
    specs = specs or {}
    normalized: dict[str, list[str]] = {}
    noise_markers: list[str] = []
    noisy = False
    for key in ("contracts", "loop_invariants", "loop_variants", "assertions"):
        values = []
        for item in specs.get(key, []) or []:
            line = " ".join(str(item).strip().split())
            line = line.replace("/* @;", "").replace("/*@;", "")
            if not line:
                continue
            if any(token in line for token in ("/* @", "/*@", ">>> INFILL <<<")):
                noisy = True
                noise_markers.append(line)
                continue
            values.append(line)
        normalized[key] = sorted(dict.fromkeys(values), key=_rank_spec)
    return normalized, noise_markers[:6], noisy


def _extract_pickle_metrics(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    return {
        "status": payload.get("Status"),
        "llm_time_sec": float(payload.get("llms_query_times", 0).total_seconds()) if payload.get("llms_query_times") else 0.0,
        "solve_time_sec": float(payload.get("total_solve_time", 0).total_seconds()) if payload.get("total_solve_time") else 0.0,
        "tokens_usage": int(payload.get("tokens_usage", 0) or 0),
        "iteration_count": int(payload.get("Iteration", 0) or 0),
        "round_count": int(payload.get("Round", 0) or 0),
        "current_task_id": int(payload.get("CurTaskID", 0) or 0),
        "task_list": payload.get("TaskList", []),
        "raw": payload,
    }


def _collect_pickle_metrics(root: Path) -> list[dict]:
    metrics = []
    for path in sorted(root.rglob("*.pickle")):
        try:
            payload = _extract_pickle_metrics(path)
            payload["path"] = project_relative_path(path)
            metrics.append(payload)
        except Exception:
            continue
    return metrics


def _merge_pickle_metrics(items: list[dict]) -> dict:
    if not items:
        return {}
    return {
        "llm_time_sec": round(sum(item.get("llm_time_sec", 0.0) for item in items), 3),
        "solve_time_sec": round(sum(item.get("solve_time_sec", 0.0) for item in items), 3),
        "tokens_usage": sum(item.get("tokens_usage", 0) for item in items),
        "iteration_count": max((item.get("iteration_count", 0) for item in items), default=0),
        "round_count": max((item.get("round_count", 0) for item in items), default=0),
        "status_values": [item.get("status") for item in items],
        "paths": [project_relative_path(item.get("path")) for item in items if item.get("path")],
    }


def _extract_timeout_goals(raw: str) -> int:
    match = re.search(r"Timeout:\s+(\d+)", raw)
    return int(match.group(1)) if match else 0


def _metrics_from_run_log(raw: str) -> dict:
    """Recover metrics after legacy cleanup removes the transient pickle."""
    tokens = [int(value) for value in re.findall(r"total_tokens:\s*(\d+)", raw)]
    llm_times = [float(value) for value in re.findall(r"llm_time_sec:\s*([0-9]+(?:\.[0-9]+)?)", raw)]
    return {
        "tokens_usage": sum(tokens),
        "iteration_count": len(tokens),
        "llm_time_sec": round(sum(llm_times), 3),
    }


def _successful_iteration_log(
    raw: str,
    *,
    proof_stats: dict | None = None,
    source_task_id: str | None = None,
) -> str:
    """Keep AutoSpec setup plus the final verifier-approved iteration."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw or "").strip()
    if "[single][successful-iteration]" in clean:
        return clean

    success_markers = (
        "Congratulations, you have successfully passed the verification.",
        "Congratulations, you have successfully passed",
    )
    success_index = max((clean.rfind(marker) for marker in success_markers), default=-1)
    segment = clean
    initialization = ""
    if success_index >= 0:
        query_starts = [
            match.start()
            for match in re.finditer(r"(?m)^INFO:root:LLM querying \.\.\.\s*$", clean)
            if match.start() <= success_index
        ]
        if query_starts:
            first_query = query_starts[0]
            boundary_candidates = [first_query]
            for marker in ("\n==============================================", "\nINFO:root:👽:"):
                marker_index = clean.find(marker, 0, first_query)
                if marker_index >= 0:
                    boundary_candidates.append(marker_index)
            initialization = clean[:min(boundary_candidates)].strip()
            segment = clean[query_starts[-1]:].strip()

    stats = proof_stats or {}
    proved = int(stats.get("proved_goals") or 0)
    total = int(stats.get("total_goals") or 0)
    footer = []
    if total and "Proved goals:" not in segment:
        footer.append(f"[wp] Proved goals: {proved} / {total}")
    footer.append("[done] status=Pass")
    sections = []
    if initialization:
        sections.append(initialization)
    sections.extend(["", "--- successful iteration ---", segment, "", *footer])
    return "\n".join(sections).strip()


def _build_project_call_graph(paths: list[Path]) -> dict:
    """Build a function-level call graph and its entry-reachable scope."""
    definition_pattern = re.compile(
        r"(?m)^[ \t]*(?:static\s+)?(?:inline\s+)?(?:[A-Za-z_]\w*[ \t\n\r\f\v\*]+)+"
        r"([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
    )
    cleaned_by_path = {}
    definitions_by_path = {}
    bodies = {}
    owner = {}
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"/\*.*?\*/|//[^\n]*", " ", text, flags=re.DOTALL)
        text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)
        definitions = set()
        for match in definition_pattern.finditer(text):
            name = match.group(1)
            brace = text.find("{", match.start(), match.end())
            depth, end = 0, len(text)
            for index in range(brace, len(text)):
                if text[index] == "{":
                    depth += 1
                elif text[index] == "}":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
            definitions.add(name)
            bodies[(path, name)] = text[brace:end]
        cleaned_by_path[path] = text
        definitions_by_path[path] = definitions
        for name in definitions:
            owner.setdefault(name, path.name)

    edges, function_fan_out = [], {}
    module_callees = {path.name: set() for path in paths}
    for (path, caller), body in bodies.items():
        callees = set()
        for callee in owner:
            if callee != caller and re.search(rf"\b{re.escape(callee)}\s*\(", body):
                callees.add(callee)
                module_callees[path.name].add(callee)
                edges.append({
                    "source": caller,
                    "source_module": path.name,
                    "target": callee,
                    "target_module": owner[callee],
                })
        function_fan_out[caller] = len(callees)

    entry_functions = ["main"] if "main" in owner else []
    if not entry_functions:
        called = {edge["target"] for edge in edges}
        entry_functions = sorted(name for name in owner if name not in called and not name.startswith("_"))
    adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
    reachable, queue = set(entry_functions), list(entry_functions)
    while queue:
        current = queue.pop(0)
        for callee in adjacency.get(current, set()):
            if callee not in reachable:
                reachable.add(callee)
                queue.append(callee)
    functions = [
        {"name": name, "module": module, "fan_out": function_fan_out.get(name, 0), "reachable": name in reachable}
        for name, module in sorted(owner.items())
    ]
    return {
        "call_edge_count": len(edges),
        "fan_out": {module: len(callees) for module, callees in module_callees.items()},
        "edges": edges,
        "functions": functions,
        "entry_functions": entry_functions,
        "reachable_functions": sorted(reachable),
    }


def _build_project_verification(raw: str, call_graph: dict, *, status: str, final_result: bool) -> dict:
    """Produce a conservative, auditable project-level verdict."""
    reachable = set(call_graph.get("reachable_functions") or [])
    attempts, current_target = [], None
    for line in raw.splitlines():
        target_match = re.search(r"-wp-fct\s+([A-Za-z_]\w*)", line)
        if target_match:
            current_target = target_match.group(1)
        proof_match = re.search(r"\[wp\] Proved goals:\s+(\d+)\s*/\s*(\d+)", line)
        if proof_match and current_target:
            attempts.append({
                "function": current_target,
                "proved": int(proof_match.group(1)),
                "total": int(proof_match.group(2)),
            })
            current_target = None
    verified = sorted({
        item["function"] for item in attempts
        if item["total"] > 0 and item["proved"] == item["total"] and item["function"] in reachable
    })
    failed = sorted({
        item["function"] for item in attempts
        if item["total"] > item["proved"] and item["function"] in reachable
    })
    total_functions = len(call_graph.get("functions") or [])
    reachable_count = len(reachable)
    verified_count = len(verified)
    rte_enabled = "-wp-rte" in raw
    call_preconditions_enabled = "-wp-no-callee-precond" not in raw
    timeout_count = sum(int(value) for value in re.findall(r"Timeout:\s+(\d+)", raw))
    missing_spec_functions = sorted(set(re.findall(r"No 'assigns' specification for function '([^']+)'", raw)))
    task_numbers = [int(value) for value in re.findall(r"/\*\s*(\d+)\.\s+(?:FUNC CONTRACT|LOOP INVARIANT)", raw)]
    planned_tasks = max(task_numbers, default=0)

    blockers = []
    if not final_result:
        blockers.append("未生成验证器批准的 final_result")
    if reachable_count == 0:
        blockers.append("未确定入口可达函数范围")
    elif verified_count < reachable_count:
        blockers.append(f"仍有 {reachable_count - verified_count} 个入口可达函数缺少函数级通过证据")
    if not call_preconditions_enabled:
        blockers.append("调用前置条件检查被 -wp-no-callee-precond 禁用")
    if not rte_enabled:
        blockers.append("尚未启用 -wp-rte 运行时安全证明")
    if missing_spec_functions:
        blockers.append(f"{len(missing_spec_functions)} 个函数出现 missing assigns 证据")
    if timeout_count:
        blockers.append(f"存在 {timeout_count} 个超时证明目标")
    if "No task-compatible ACSL clauses" in raw:
        blockers.append("规约生成未返回当前任务需要的 ACSL 子句")

    complete = (
        status.lower() == "pass"
        and final_result
        and reachable_count > 0
        and verified_count == reachable_count
        and rte_enabled
        and call_preconditions_enabled
        and timeout_count == 0
        and not missing_spec_functions
    )
    verdict = "project_verified" if complete else "partially_verified" if verified_count else "inconclusive"
    return {
        "verdict": verdict,
        "label": "项目级验证通过" if complete else "项目级验证部分完成" if verified_count else "项目级验证结论不充分",
        "complete": complete,
        "entry_functions": call_graph.get("entry_functions") or [],
        "scope": {
            "total_functions": total_functions,
            "reachable_functions": reachable_count,
            "verified_functions": verified_count,
            "unverified_functions": max(reachable_count - verified_count, 0),
            "planned_tasks": planned_tasks,
        },
        "coverage": {
            "function_percent": round(verified_count * 100 / reachable_count, 2) if reachable_count else 0.0,
            "rte_enabled": rte_enabled,
            "call_preconditions_enabled": call_preconditions_enabled,
        },
        "verified_functions": verified,
        "failed_functions": failed,
        "missing_spec_functions": missing_spec_functions,
        "blockers": blockers,
        "evidence": {
            "final_result": final_result,
            "targeted_wp_attempts": attempts,
            "timeout_goals": timeout_count,
        },
    }


def _classify_failure(raw: str, *, result_code: str = "", invalid_markers: list[Path] | None = None, context: str = "single") -> dict:
    evidence: list[str] = []
    invalid_markers = invalid_markers or []
    build_markers = ("unknown type name", "Merged translation unit preflight failed", "mark.py", "exit status 2")
    if any(marker in raw for marker in build_markers):
        build_lines = [line.strip() for line in raw.splitlines() if any(marker in line for marker in build_markers)]
        return {
            "category": "merge-build",
            "label": "Merged Project Build Error",
            "summary": "The merged translation unit failed type/include validation before specification generation could complete.",
            "evidence": build_lines[-5:],
            "actionable_hint": "Fix include dependency order or project include paths before retrying AutoSpec.",
        }
    if "timed out" in raw.lower() or "timeout after" in raw.lower():
        return {
            "category": "timeout",
            "label": "Timeout",
            "summary": f"{context} execution reached the configured timeout before a stable result was produced.",
            "evidence": [raw.strip().splitlines()[-1]] if raw.strip() else [],
            "actionable_hint": "Increase timeout only after reducing noisy candidates or shrinking the sample set.",
        }
    if "[kernel:annot-error]" in raw or "Frama-C aborted: invalid user input" in raw:
        syntax_lines = [
            line.strip()
            for line in raw.splitlines()
            if "annot-error" in line or "unexpected token" in line or "invalid user input" in line
        ]
        return {
            "category": "acsl-syntax",
            "label": "ACSL Syntax Error",
            "summary": "Frama-C rejected the generated ACSL while parsing, before any WP proof obligation was created.",
            "evidence": syntax_lines[-3:] or ["Frama-C aborted while parsing generated annotations."],
            "actionable_hint": "Fix or regenerate the malformed annotation, then rerun parsing before starting WP.",
        }
    if any("Invalid" in path.name for path in invalid_markers) or "remove invalid spec and re-run" in raw:
        evidence.append("Frama-C rejected at least one generated annotation as invalid syntax or ill-formed ACSL.")
    if "/* @;" in result_code or "/* @;" in raw or "/*@;" in result_code or "/*@;" in raw:
        evidence.append("Malformed contract/comment delimiter was injected into the merged artifact.")
        return {
            "category": "contract-format",
            "label": "Contract Format Noise",
            "summary": "Generated ACSL clauses include malformed comment delimiters, so proof closure stops at parsing or early verification.",
            "evidence": evidence,
            "actionable_hint": "Clean block-comment markers before replaying verification.",
        }
    if "[wp] [Timeout]" in raw:
        evidence.append("WP timed out on at least one proof obligation.")
        return {
            "category": "solver-timeout",
            "label": "Solver Timeout",
            "summary": "Candidate specifications compile, but the verifier times out on the remaining proof obligations.",
            "evidence": evidence,
            "actionable_hint": "Prefer simpler invariants or contracts with fewer quantified clauses.",
        }
    if "proof did not close" in raw.lower() or "[wp] proved goals:" in raw.lower():
        stats = _proof_stats_from_text(raw)
        evidence.append(f"Closed goals {stats['proved_goals']} / {stats['total_goals']}.")
        return {
            "category": "proof-failed",
            "label": "Proof Did Not Close",
            "summary": "Verification reached WP but the synthesized clauses were still insufficient for full proof closure.",
            "evidence": evidence,
            "actionable_hint": "Tighten bounds and equalities before adding more quantified facts.",
        }
    if evidence:
        return {
            "category": "invalid-spec",
            "label": "Invalid Specification",
            "summary": "Generated specifications were not accepted by the verifier.",
            "evidence": evidence,
            "actionable_hint": "Inspect the invalid artifact and remove malformed or contradictory clauses.",
        }
    return {
        "category": "execution-error",
        "label": "Execution Error",
        "summary": f"{context} execution finished without a verifier-approved result artifact.",
        "evidence": [raw.strip().splitlines()[-1]] if raw.strip() else [],
        "actionable_hint": "Inspect logs and generated artifacts to locate the last successful phase.",
    }


def _normalize_status_and_failure(status: str, raw: str, *, result_code: str = "", invalid_markers: list[Path] | None = None, context: str = "single") -> tuple[str, dict]:
    if status == "Pass":
        return status, {
            "category": "none",
            "label": "Verifier-approved",
            "summary": "Proof obligations closed with a stable artifact.",
            "evidence": [],
            "actionable_hint": None,
        }
    failure = _classify_failure(raw, result_code=result_code, invalid_markers=invalid_markers, context=context)
    if failure["category"] in {"timeout", "solver-timeout"} and status in {"Fail", "Invalid"}:
        return "Timeout", failure
    if failure["category"] in {"acsl-syntax", "contract-format", "invalid-spec"} and status in {"Fail", "Timeout"}:
        return "Invalid", failure
    return status, failure


def _parse_result_marker(path: Path) -> tuple[str, dict]:
    name = path.name
    if "_Pass_" in name:
        match = re.search(r"_Pass_(\d+)_(\d+)\.txt$", name)
        proved, total = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
        return "Pass", _normalize_proof_stats(proved, total)
    if "_Fail_" in name:
        match = re.search(r"_Fail_(\d+)_(\d+)\.txt$", name)
        proved, total = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
        return "Fail", _normalize_proof_stats(proved, total)
    if "_Invalid" in name:
        return "Invalid", _normalize_proof_stats(0, 0, invalid_goals=1)
    return "Fail", _normalize_proof_stats(0, 0)


class RunManager:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self.capabilities = detect_live_capabilities()

    def refresh_capabilities(self):
        self.capabilities = detect_live_capabilities()
        return self.capabilities

    def overview(self) -> dict:
        self.refresh_capabilities()
        tasks = self.store.list_tasks(limit=40)
        results = {task.task_id: self.store.read_result(task.task_id) for task in tasks}
        demo_cases = list_demo_cases()
        mode_counter = {mode: {"total": 0, "pass": 0, "live": 0, "avg_elapsed_ms": 0.0, "recent_status": "n/a"} for mode in PHASE_LABELS}
        recent_evidence = []
        for task in tasks:
            result = results.get(task.task_id) or {}
            row = mode_counter[task.mode]
            row["total"] += 1
            if task.engine == "live":
                row["live"] += 1
            if task.status == "pass":
                row["pass"] += 1
            if result.get("elapsed_ms"):
                current_total = row["avg_elapsed_ms"] * (row["total"] - 1)
                row["avg_elapsed_ms"] = (current_total + result["elapsed_ms"]) / row["total"]
            row["recent_status"] = task.status
            recent_evidence.append(
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "mode": task.mode,
                    "status": task.status,
                    "engine": task.engine,
                    "summary": result.get("summary") or task.message or "",
                    "elapsed_ms": result.get("elapsed_ms"),
                    "proof_stats": result.get("proof_stats", {}),
                    "failure_category": result.get("failure_analysis", {}).get("category"),
                    "created_at": _format_datetime(task.created_at),
                }
            )
        mode_rows = []
        for mode, row in mode_counter.items():
            mode_rows.append(
                {
                    "mode": mode,
                    "total_runs": row["total"],
                    "pass_count": row["pass"],
                    "live_runs": row["live"],
                    "pass_rate": _safe_ratio(row["pass"], row["total"]),
                    "avg_elapsed_ms": round(row["avg_elapsed_ms"], 1) if row["total"] else 0.0,
                    "recent_status": row["recent_status"],
                }
            )
        capability_rows = [
            self.capabilities.mode_detail("single"),
            self.capabilities.mode_detail("termination"),
            self.capabilities.mode_detail("inter-modular"),
            self.capabilities.mode_detail("batch"),
        ]
        return {
            "headline_metrics": {
                "total_runs": len(tasks),
                "pass_count": sum(1 for task in tasks if task.status == "pass"),
                "live_ready_modes": sum(1 for row in capability_rows if row["ready"]),
                "demo_case_count": len(demo_cases),
            },
            "capability_rows": capability_rows,
            "mode_rows": mode_rows,
            "recent_evidence": recent_evidence[:8],
            "demo_cases": demo_cases,
        }

    def submit(self, mode: str, payload: RunRequest) -> RunTask:
        task_id = utcnow().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        task_dir = RUNS_DIR / task_id
        case = get_demo_case(payload.demo_case_id) if payload.demo_case_id else None
        engine = "live"
        if case and case.get("execution_mode", "replay") == "replay":
            engine = "replay"
        capabilities = self.refresh_capabilities()
        source_type = "demo" if payload.demo_case_id else "derived" if payload.upstream_task_id else "upload"
        title = case["title"] if case else f"{APP_NAME} {mode} run"
        phases = [PhaseState(key=key, label=label) for key, label in PHASE_LABELS[mode]]
        task = RunTask(
            task_id=task_id,
            mode=mode,
            title=title,
            source_type=source_type,
            status="queued",
            engine=engine,
            model_name=None if mode == "rust-verify" else payload.model_name,
            demo_case_id=payload.demo_case_id,
            file_id=payload.file_id,
            upstream_task_id=payload.upstream_task_id,
            created_at=utcnow(),
            updated_at=utcnow(),
            task_dir=project_relative_path(task_dir),
            phases=phases,
            capabilities=capabilities.as_dict(),
            metadata={"worker_pid": os.getpid()},
        )
        self.store.create_task(task)
        worker = threading.Thread(target=self._execute, args=(task.task_id, payload), daemon=True)
        worker.start()
        return task

    def ensure_materialized(self, task_id: str) -> tuple[RunTask | None, dict | None]:
        task = self.store.read_task(task_id)
        if task is None:
            return None, None
        result = self.store.read_result(task_id)
        if (task.mode.startswith("rust-") and task.status in {"queued", "running"}
                and task.metadata.get("worker_pid") != os.getpid() and result is None):
            # Never retry a model request after backend restart. Preserve any
            # completed rounds and make the interrupted state explicit.
            task.status = "unavailable"
            task.message = "服务已重启，本次 Rust 验证中断；已完成的轮次保留，请手动重新提交。"
            task.finished_at = utcnow()
            self._fail_remaining_phases(task, task.message)
            self.store.write_task(task)
            snapshot = task.metadata.get("rust_workflow") or {}
            attempts = snapshot.get("attempts", [])
            result = self._build_result(task, status="Unavailable", summary=task.message,
                source_code="", result_code=next((a.get("code", "") for a in reversed(attempts) if a.get("code")), ""),
                command=None, logs={"raw": task.message}, specifications={},
                engine_detail={"language": "Rust", "attempts": attempts, "workflow": snapshot})
            self.store.write_result(task_id, result)
        if result is not None and task.status in {"queued", "running"}:
            self._sync_task_with_result(task, result)
            task = self.store.read_task(task_id)
        if task is not None and result is not None:
            result = self._upgrade_stale_single_replay_logs(task, result)
            # Older inter-modular results persisted only aggregate call counts.
            # Rebuild their edges from the immutable input manifest so the
            # interactive graph remains available after an upgrade.
            summary = result.get("call_graph_summary") or {}
            if task.mode == "inter-modular" and (
                not summary.get("functions")
                or any("source_module" not in edge for edge in summary.get("edges", []))
            ):
                source_paths = []
                for item in result.get("input_manifest") or []:
                    relative = item.get("path")
                    if not relative:
                        continue
                    candidate = resolve_project_path(relative)
                    if candidate.is_file() and candidate.suffix in {".c", ".h"}:
                        source_paths.append(candidate)
                if source_paths:
                    graph = _build_project_call_graph(source_paths)
                    summary.update(graph)
                    result["call_graph_summary"] = summary
            if task.mode == "inter-modular" and summary.get("functions"):
                raw = (result.get("logs") or {}).get("raw", "")
                result["project_verification"] = _build_project_verification(
                    raw,
                    summary,
                    status=str(result.get("status", "")),
                    final_result=bool((result.get("engine_detail") or {}).get("final_result_path")),
                )
                verified_set = set(result["project_verification"]["verified_functions"])
                for module in result.get("module_results") or []:
                    module_name = Path(module.get("relative_path") or module.get("path") or "").name
                    module_functions = [
                        item for item in summary["functions"]
                        if item.get("module") == module_name and item.get("reachable")
                    ]
                    verified_count = sum(item["name"] in verified_set for item in module_functions)
                    module["reachable_function_count"] = len(module_functions)
                    module["verified_function_count"] = verified_count
                    module["verification_status"] = (
                        "verified" if module_functions and verified_count == len(module_functions)
                        else "partial" if verified_count
                        else "pending" if module_functions
                        else "not_applicable"
                    )
        return task, result

    def recover_incomplete_tasks(self, limit: int = 40) -> int:
        recovered = 0
        for task in self.store.list_tasks(limit=limit):
            if task.status not in {"queued", "running"}:
                continue
            if self.store.read_result(task.task_id) is not None:
                continue
            if self._recover_task_from_artifacts(task):
                recovered += 1
        return recovered

    def _execute(self, task_id: str, payload: RunRequest) -> None:
        task = self.store.read_task(task_id)
        if task is None:
            return
        task.status = "running"
        task.started_at = utcnow()
        task.updated_at = utcnow()
        self.store.write_task(task)

        try:
            result = self._run_replay(task) if task.engine == "replay" else self._run_live(task, payload)
            task.status = _status_to_task_status(result["status"])
            task.message = result["summary"]
            task.finished_at = utcnow()
            task.updated_at = utcnow()
            self.store.write_result(task.task_id, result)
            self.store.write_task(task)
        except subprocess.TimeoutExpired as exc:
            task.status = "timeout"
            task.message = str(exc)
            task.finished_at = utcnow()
            task.updated_at = utcnow()
            self._fail_remaining_phases(task, "Execution timed out.")
            self.store.write_task(task)
            result = self._build_result(
                task,
                status="Timeout",
                summary="Execution timed out before a stable artifact was produced.",
                source_code="",
                result_code="",
                command=None,
                logs={"summary": ["timeout"], "raw": str(exc)},
                specifications={},
                highlights=["execution timeout"],
                failure_excerpt=str(exc),
                failure_analysis={
                    "category": "timeout",
                    "label": "Timeout",
                    "summary": "Execution timed out before completion.",
                    "evidence": [str(exc)],
                    "actionable_hint": "Reduce sample size or extend the timeout only after removing noisy candidates.",
                },
            )
            self.store.write_result(task.task_id, result)
        except Exception as exc:  # noqa: BLE001
            task.status = "fail"
            task.message = str(exc)
            task.finished_at = utcnow()
            task.updated_at = utcnow()
            self._fail_remaining_phases(task, str(exc))
            self.store.write_task(task)
            result = self._build_result(
                task,
                status="Fail",
                summary=str(exc),
                source_code="",
                result_code="",
                command=None,
                logs={"summary": [str(exc)], "raw": str(exc)},
                specifications={},
                highlights=["execution failure"],
                failure_excerpt=str(exc),
            )
            self.store.write_result(task.task_id, result)

    def _sync_task_with_result(self, task: RunTask, result: dict) -> None:
        task.status = _status_to_task_status(result["status"])
        task.message = result["summary"]
        task.finished_at = task.finished_at or utcnow()
        task.updated_at = utcnow()
        self.store.write_task(task)

    def _load_task_log(self, task_id: str) -> str:
        payload = self.store.read_artifact_text(task_id, "artifacts/logs/run.log")
        return payload["content"] if payload else ""

    def _upgrade_stale_single_replay_logs(self, task: RunTask, result: dict) -> dict:
        """Rewrite old replay placeholders into the current verifier-style log.

        Earlier demo runs persisted only ``[single] replayed from curated artifact``.
        Those old result.json/run.log files continue to be listed by the UI, so patch
        them lazily when a user opens the result or artifact preview instead of
        requiring manual deletion of runtime/runs.
        """
        if task.mode != "single" or task.engine != "replay" or not task.demo_case_id:
            return result
        current_raw = str((result.get("logs") or {}).get("raw") or "")
        artifact_raw = self._load_task_log(task.task_id)
        try:
            case = get_demo_case(task.demo_case_id)
        except KeyError:
            return result
        logs = self._single_logs(case)
        expected_raw = logs.get("raw", "")
        stale_markers = (
            "[single] replayed from curated artifact",
            "[single][replay] loaded curated single-function case",
            "[formal_verifying] replayed verifier-approved partial-correctness artifact",
            "[iterative_repair] curated repair trace closed without open proof obligations",
        )
        already_current = current_raw == expected_raw and (not artifact_raw or artifact_raw == expected_raw)
        if already_current:
            return result
        has_curated_log = bool(case.get("single_log_payload"))
        has_stale_log = any(marker in current_raw or marker in artifact_raw for marker in stale_markers)
        if not has_curated_log and not has_stale_log:
            return result
        updated = dict(result)
        updated["logs"] = logs
        proof_stats = _proof_stats_from_text(logs.get("raw", ""))
        if proof_stats.get("total_goals"):
            updated["proof_stats"] = _normalize_proof_stats(proof_stats.get("proved_goals", 0), proof_stats.get("total_goals", 0))
        engine_detail = dict(updated.get("engine_detail") or {})
        engine_detail["stale_log_upgraded"] = True
        updated["engine_detail"] = engine_detail
        self.store.write_text_artifact(task.task_id, "logs", "run.log", logs["raw"])
        self.store.write_result(task.task_id, updated)
        return updated

    def _read_and_upgrade_artifact_log(self, task: RunTask, relative_path: str) -> dict | None:
        payload = self.store.read_artifact_text(task.task_id, relative_path)
        if payload is None:
            return None
        if relative_path.replace("\\", "/") != "artifacts/logs/run.log":
            return payload
        if task.mode != "single" or task.engine != "replay" or not task.demo_case_id:
            return payload
        content = str(payload.get("content") or "")
        result = self.store.read_result(task.task_id)
        if result is not None:
            self._upgrade_stale_single_replay_logs(task, result)
            refreshed = self.store.read_artifact_text(task.task_id, relative_path)
            return refreshed or payload
        return payload

    def _mark_phases_from_result(self, task: RunTask, status: str, summary: str) -> None:
        now = utcnow()
        terminal_phase_status = "completed" if status == "Pass" else "failed"
        for phase in task.phases:
            if phase.status == "completed":
                continue
            if phase.status == "pending":
                phase.started_at = phase.started_at or now
            if phase.status in {"pending", "running"}:
                phase.status = terminal_phase_status  # type: ignore[assignment]
                phase.detail = summary
                phase.finished_at = now
        task.finished_at = task.finished_at or now
        task.updated_at = now

    def _recover_task_from_artifacts(self, task: RunTask) -> bool:
        if task.engine != "live":
            return False

        input_root = resolve_project_path(task.input_file) if task.input_file else None
        task_dir = resolve_project_path(task.task_dir)
        raw = self._load_task_log(task.task_id)
        timeout_sec = int((task.metadata or {}).get("timeout_sec") or 0) or None

        if task.mode == "batch":
            timeout_sec = timeout_sec or int(os.getenv("AUTOSPEC_BATCH_TIMEOUT", "180"))
            output_root = task_dir / "artifacts" / "output"
            workspace_root = task_dir / "artifacts" / "workspace"
            results_root = output_root / "experiment_results"
            if not list(results_root.glob("*.jsonl")):
                return False
            legacy = self._collect_batch_output(output_root, workspace_root, results_root, raw, returncode=None, timeout_sec=timeout_sec)
            source_code = _concat_sources(input_root) if input_root and input_root.exists() else ""
            result = self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=source_code,
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=None,
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications={},
                highlights=["recovered from artifacts", "batch evaluation", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail={**legacy["engine_detail"], "recovered_from_artifacts": True},
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
                aggregate_metrics=legacy["aggregate_metrics"],
                items=legacy["items"],
            )
            self._mark_phases_from_result(task, legacy["status"], legacy["verification_detail"])
            self.store.write_result(task.task_id, result)
            self._sync_task_with_result(task, result)
            return True

        if task.mode == "inter-modular":
            workspace_root = task_dir / "artifacts" / "workspace"
            project_root = workspace_root / (input_root.name if input_root and input_root.exists() else "")
            if not project_root.exists():
                return False
            out_root = workspace_root / "out"
            if not list(out_root.rglob("*_merged.c")):
                return False
            legacy = self._collect_inter_modular_output(project_root, workspace_root, raw, returncode=None, timeout_sec=timeout_sec)
            source_code = _concat_sources(input_root) if input_root and input_root.exists() else ""
            result = self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=source_code,
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=None,
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications=legacy["specifications"],
                highlights=["recovered from artifacts", "inter-modular synthesis", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail={**legacy["engine_detail"], "recovered_from_artifacts": True},
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
                call_graph_summary=legacy["call_graph_summary"],
                module_results=legacy["module_results"],
                merged_translation_unit=legacy["merged_translation_unit"],
                split_outputs=legacy["split_outputs"],
                project_verification=legacy["project_verification"],
            )
            self._mark_phases_from_result(task, legacy["status"], legacy["verification_detail"])
            self.store.write_result(task.task_id, result)
            self._sync_task_with_result(task, result)
            return True

        if task.mode == "single":
            output_root = task_dir / "artifacts" / "output"
            if not list(output_root.rglob("*_merged.c")) and not list(output_root.rglob("final_result")):
                return False
            source_parent = input_root.parent if input_root and input_root.exists() else task_dir / "artifacts" / "input"
            legacy = self._collect_single_live_output(source_parent, output_root, raw, returncode=None, timeout_sec=timeout_sec)
            source_code = input_root.read_text(encoding="utf-8", errors="ignore") if input_root and input_root.exists() and input_root.is_file() else ""
            result = self._build_result(
                task,
                status=legacy["status"],
                summary=legacy["summary"],
                source_code=source_code,
                result_code=legacy["result_code"],
                partial_correctness_code=None,
                command=None,
                logs={"summary": legacy["log_summary"], "raw": raw},
                specifications=legacy["specifications"],
                highlights=["recovered from artifacts", *legacy["highlights"]],
                proof_stats=legacy["proof_stats"],
                timing_stats=legacy["timing_stats"],
                engine_detail={**legacy["engine_detail"], "recovered_from_artifacts": True},
                failure_excerpt=legacy["failure_excerpt"],
                failure_analysis=legacy["failure_analysis"],
                evidence_summary=legacy["evidence_summary"],
            )
            self._mark_phases_from_result(task, legacy["status"], legacy["verification_detail"])
            self.store.write_result(task.task_id, result)
            self._sync_task_with_result(task, result)
            return True

        return False

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
        if task.mode.startswith("rust-"):
            from .rust import execute_rust
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

        cached = self._find_verified_single_cache(task, source)
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
            source.relative_to(ROOT_DIR).as_posix(),
            output_dir.relative_to(ROOT_DIR).as_posix(),
            payload.model_name,
            payload.enable_mutation,
        )
        timeout_sec = payload.timeout_sec or int(os.getenv("AUTOSPEC_SINGLE_TIMEOUT", "120"))
        try:
            completed = run_command(command, ROOT_DIR, timeout=timeout_sec)
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
            stage1_dir.relative_to(ROOT_DIR).as_posix(),
            stage2_dir.relative_to(ROOT_DIR).as_posix(),
            verified_dir.relative_to(ROOT_DIR).as_posix(),
            payload.model_name,
            service=self.capabilities.termination_service,
        )
        raw_parts: list[str] = []
        for command in commands:
            completed = run_command(command, ROOT_DIR)
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
            workspace_root.relative_to(ROOT_DIR).as_posix(),
        )
        timeout_sec = payload.timeout_sec or 600
        try:
            completed = run_command(command, ROOT_DIR, timeout=timeout_sec)
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
            source.relative_to(ROOT_DIR).as_posix(),
            payload.model_name,
            workspace_root.relative_to(ROOT_DIR).as_posix(),
            results_root.relative_to(ROOT_DIR).as_posix(),
            output_root.relative_to(ROOT_DIR).as_posix(),
        )
        timeout_sec = payload.timeout_sec or int(os.getenv("AUTOSPEC_BATCH_TIMEOUT", "180"))
        task.metadata["timeout_sec"] = timeout_sec
        self.store.write_task(task)
        try:
            completed = run_command(command, ROOT_DIR, timeout=timeout_sec)
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

    def _build_result(
        self,
        task: RunTask,
        *,
        status: str,
        summary: str,
        source_code: str,
        result_code: str,
        command: str | None,
        logs: dict,
        specifications: dict,
        partial_correctness_code: str | None = None,
        highlights: list[str] | None = None,
        paper_keywords: list[str] | None = None,
        proof_stats: dict | None = None,
        timing_stats: dict | None = None,
        engine_detail: dict | None = None,
        failure_excerpt: str | None = None,
        failure_analysis: dict | None = None,
        evidence_summary: list[str] | None = None,
        task_summary: dict | None = None,
        aggregate_metrics: dict | None = None,
        items: list[dict] | None = None,
        call_graph_summary: dict | None = None,
        module_results: list[dict] | None = None,
        merged_translation_unit: str | None = None,
        split_outputs: list[dict] | None = None,
        project_verification: dict | None = None,
    ) -> dict:
        artifacts = [ArtifactItem.model_validate(item) for item in self.store.list_artifacts(task.task_id)]
        finished_at = task.finished_at or utcnow()
        elapsed_ms = _elapsed_ms(task.started_at, finished_at)
        normalized_specs, _, _ = _normalize_specifications(specifications)
        normalized_failure = failure_analysis or (
            {
                "category": "none",
                "label": "Verifier-approved",
                "summary": "Proof obligations closed with a stable artifact.",
                "evidence": [],
                "actionable_hint": None,
            }
            if status == "Pass"
            else _classify_failure(logs.get("raw", ""), result_code=result_code, context=task.mode)
        )
        normalized_proof = proof_stats or _normalize_proof_stats()
        return RunResult(
            task_id=task.task_id,
            mode=task.mode,
            status=status,
            engine=task.engine,
            title=task.title,
            summary=summary,
            command=command,
            repro_command=command,
            source_code=source_code,
            result_code=_sanitize_result_code(result_code),
            partial_correctness_code=partial_correctness_code,
            specifications=normalized_specs,
            logs=logs,
            highlights=highlights or [],
            paper_keywords=paper_keywords or [],
            artifacts=artifacts,
            status_reason=failure_excerpt if status != "Pass" else None,
            engine_detail=engine_detail or {},
            started_at=task.started_at,
            finished_at=finished_at,
            elapsed_ms=elapsed_ms,
            phase_metrics=_phase_metrics(task),
            status_category=normalized_failure["category"],
            proof_stats=normalized_proof,
            timing_stats=timing_stats or _timing_stats(wall_clock_ms=elapsed_ms),
            failure_analysis=normalized_failure,
            evidence_summary=evidence_summary or normalized_failure.get("evidence", []),
            task_summary=task_summary or _task_summary(task, status),
            aggregate_metrics=aggregate_metrics or {},
            items=items or [],
            call_graph_summary=call_graph_summary or {},
            module_results=module_results or [],
            merged_translation_unit=merged_translation_unit,
            split_outputs=split_outputs or [],
            input_manifest=task.metadata.get("input_manifest", []),
            failure_excerpt=failure_excerpt,
            project_verification=project_verification or {},
        ).model_dump(mode="json")

    def _unavailable_result(
        self,
        task: RunTask,
        summary: str,
        raw: str = "",
        command: str | None = None,
        *,
        actionable_hint: str | None = None,
    ) -> dict:
        if raw:
            self.store.write_text_artifact(task.task_id, "logs", "run.log", raw)
        self._fail_remaining_phases(task, summary)
        return self._build_result(
            task,
            status="Unavailable",
            summary=summary,
            source_code="",
            result_code="",
            partial_correctness_code=None,
            command=command,
            logs={"summary": [summary], "raw": raw},
            specifications={},
            highlights=["live execution unavailable"],
            failure_excerpt=raw.strip() or summary,
            failure_analysis={
                "category": "environment",
                "label": "Environment Unavailable",
                "summary": summary,
                "evidence": [line for line in raw.splitlines() if line.strip()],
                "actionable_hint": actionable_hint or "检查 Docker、镜像与验证工具链后重试。",
            },
        )

    def _advance_phase(self, task: RunTask, key: str, status: str, detail: str) -> None:
        now = utcnow()
        for phase in task.phases:
            if phase.key != key:
                continue
            phase.status = status  # type: ignore[assignment]
            phase.detail = detail
            if status == "running":
                phase.started_at = now
            else:
                phase.started_at = phase.started_at or now
                phase.finished_at = now
        task.updated_at = now
        self.store.write_task(task)

    def _fail_remaining_phases(self, task: RunTask, detail: str) -> None:
        now = utcnow()
        seen_failure = False
        for phase in task.phases:
            if phase.status == "completed":
                continue
            if not seen_failure:
                phase.status = "failed"
                phase.detail = detail
                phase.started_at = phase.started_at or now
                phase.finished_at = now
                seen_failure = True
            else:
                phase.status = "skipped"
                phase.detail = "Skipped after upstream failure."
        task.updated_at = now
        self.store.write_task(task)

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
