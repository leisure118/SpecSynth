"""Compatibility shim for the pre-refactor RunManager module.

The implementation is split across :mod:`acsl.application.runs`:
manager (lifecycle), live (execution), recovery, results, collection,
metrics and analysis.
"""
from acsl.application.runs.analysis import (  # noqa: F401
    _build_project_call_graph,
    _build_project_verification,
    _classify_failure,
    _normalize_status_and_failure,
    _parse_result_marker,
)
from acsl.application.runs.manager import RunManager  # noqa: F401
from acsl.application.runs.metrics import (  # noqa: F401
    _build_manifest,
    _collect_pickle_metrics,
    _concat_sources,
    _elapsed_ms,
    _extract_pickle_metrics,
    _extract_timeout_goals,
    _format_datetime,
    _merge_pickle_metrics,
    _metrics_from_run_log,
    _normalize_proof_stats,
    _normalize_specifications,
    _phase_metrics,
    _proof_stats_from_paths,
    _proof_stats_from_text,
    _rank_spec,
    _safe_ratio,
    _sanitize_result_code,
    _status_to_task_status,
    _subprocess_output_text,
    _successful_iteration_log,
    _task_summary,
    _termination_input_ready,
    _timeout_output,
    _timing_stats,
)
