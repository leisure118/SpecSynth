"""Call-graph, project-level verification and failure classification."""
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
