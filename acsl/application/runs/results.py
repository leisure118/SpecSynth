"""RunResult construction and phase transitions."""
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


class RunResultMixin:
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
        from engine.verification.report import normalize_verification
        detail = engine_detail or {}
        check = detail.get('verification')
        tool = {'VeriFast':'verifast','Verus':'verus'}.get(detail.get('verifier'), 'framac')
        verification = normalize_verification(check, tool) if isinstance(check,dict) else None
        return RunResult(
            verification=verification,
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
