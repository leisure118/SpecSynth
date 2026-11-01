"""Restart recovery and legacy replay-log upgrades."""
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


class RunRecoveryMixin:
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
