"""RunManager lifecycle: submit, execute, materialize and overview."""
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

from .analysis import (
    _build_project_call_graph,
    _build_project_verification,
    _classify_failure,
    _normalize_status_and_failure,
    _parse_result_marker,
)
from .collection import RunCollectionMixin
from .live import RunLiveMixin
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
from .recovery import RunRecoveryMixin
from .results import RunResultMixin


class RunManager(RunLiveMixin, RunRecoveryMixin, RunResultMixin, RunCollectionMixin):
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self._run_slots=threading.BoundedSemaphore(max(1,min(8,int(os.getenv('ACSL_AGENT_MAX_WORKERS','2')))))
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
        if payload.assistant:
            from acsl.application.skills import resolve_assistant
            from acsl.domain.agents import AssistantConfig

            payload.assistant = resolve_assistant(AssistantConfig(**payload.assistant)).model_dump()
        task_id = utcnow().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        task_dir = settings.runs_dir / task_id
        case = get_demo_case(payload.demo_case_id) if payload.demo_case_id else None
        engine = "live"
        if case and case.get("execution_mode", "replay") == "replay":
            engine = "replay"
        capabilities = self.refresh_capabilities()
        source_type = "demo" if payload.demo_case_id else "derived" if payload.upstream_task_id else "upload"
        title = case["title"] if case else (f"{APP_NAME} verify-only" if payload.verification_only else f"{APP_NAME} {mode} run")
        phase_defs = [("formal_verifying", "Formal Verifying")] if payload.verification_only and mode == "single" else PHASE_LABELS[mode]
        phases = [PhaseState(key=key, label=label) for key, label in phase_defs]
        actual_model=None if payload.verification_only else payload.model_name
        if payload.assistant and payload.assistant.get('agent') in ('codex','claude-code'):
            from acsl.adapters.agent_runtime import runner_default_model
            actual_model=payload.assistant.get('runner_model') or runner_default_model(payload.assistant['agent']) or payload.assistant['agent']+' 默认模型'
        task = RunTask(
            task_id=task_id,
            mode=mode,
            title=title,
            source_type=source_type,
            status="queued",
            engine=engine,
            model_name=None if mode=="rust-verify" else actual_model,
            demo_case_id=payload.demo_case_id,
            file_id=payload.file_id,
            upstream_task_id=payload.upstream_task_id,
            created_at=utcnow(),
            updated_at=utcnow(),
            task_dir=project_relative_path(task_dir),
            phases=phases,
            capabilities=capabilities.as_dict(),
            metadata={"worker_pid": os.getpid(), "assistant": payload.assistant, "agent_instructions": payload.agent_instructions, "benchmark": payload.benchmark_context, "verification_only": payload.verification_only, "verification_tool": payload.verification_tool},
        )
        self.store.create_task(task)
        if payload.benchmark_context:
            upload=self.store.read_upload(payload.file_id)
            source=resolve_project_path(upload['stored_path']).read_text()
            self.store.write_text_artifact(task.task_id,'benchmark','source.c',source)
            self.store.write_text_artifact(task.task_id,'benchmark','configuration.json',json.dumps(payload.benchmark_context,ensure_ascii=False))
        worker = threading.Thread(target=self._execute_with_slot, args=(task.task_id, payload), daemon=True)
        worker.start()
        return task

    def ensure_materialized(self, task_id: str) -> tuple[RunTask | None, dict | None]:
        task = self.store.read_task(task_id)
        if task is None:
            return None, None
        result = self.store.read_result(task_id)
        if ((task.mode.startswith("rust-") or task.metadata.get("benchmark")) and task.status in {"queued", "running"}
                and task.metadata.get("worker_pid") != os.getpid() and result is None):
            # Never retry a model request after backend restart. Preserve any
            # completed rounds and make the interrupted state explicit.
            task.status = "unavailable"
            task.message = "服务已重启，本次基准重跑中断；已保存输入与工件，请手动重新提交。" if task.metadata.get("benchmark") else "服务已重启，本次 Rust 验证中断；已完成的轮次保留，请手动重新提交。"
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

    def _execute_with_slot(self,task_id,payload):
        with self._run_slots:
            self._execute(task_id,payload)

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
