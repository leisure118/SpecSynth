"""Pure parsing, metric and result-shaping helpers."""
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
