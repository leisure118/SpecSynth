from __future__ import annotations

import json
from typing import Any

from .config import ROOT_DIR, load_demo_cases_config, project_relative_path, resolve_project_path


_DEMO_CASES_CACHE: list[dict[str, Any]] | None = None
_DEMO_CASES_CACHE_MTIME_NS: int | None = None


def _read_text(relative_path: str | None, *, missing_ok: bool = False) -> str:
    if not relative_path:
        return ""
    path = resolve_project_path(relative_path)
    if missing_ok and not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def _first_available_text(*relative_paths: str | None) -> str:
    for relative_path in relative_paths:
        content = _read_text(relative_path, missing_ok=True)
        if content:
            return content
    return ""


def extract_specifications(code: str) -> dict[str, list[str]]:
    result = {
        "contracts": [],
        "loop_invariants": [],
        "loop_variants": [],
        "assertions": [],
    }
    for raw_line in code.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("requires ", "ensures ", "assigns ", "behavior ", "assumes ")):
            result["contracts"].append(line)
        elif line.startswith("loop invariant "):
            result["loop_invariants"].append(line)
        elif line.startswith("loop variant "):
            result["loop_variants"].append(line)
        elif line.startswith("//@") and "assert" in line:
            result["assertions"].append(line)
    return result


def _demo_cases_config_mtime_ns() -> int | None:
    config_path = ROOT_DIR / "configs" / "demo_cases.json"
    if not config_path.exists():
        return None
    return config_path.stat().st_mtime_ns


def _build_demo_cases() -> list[dict[str, Any]]:
    cases = []
    for item in load_demo_cases_config():
        single_code = _read_text(item.get("single_result_file"), missing_ok=True)
        termination_code = _read_text(item.get("termination_result_file"), missing_ok=True)
        stage2_code = _read_text(item.get("termination_stage2_file"), missing_ok=True)
        inter_modular_code = _read_text(item.get("inter_modular_result_file"), missing_ok=True)
        source_code = _first_available_text(
            item.get("source_file"),
            item.get("single_result_file"),
            item.get("termination_stage2_file"),
            item.get("termination_result_file"),
            item.get("inter_modular_result_file"),
        )
        source_dir = item.get("source_dir")
        source_manifest = []
        if source_dir:
            root = ROOT_DIR / source_dir
            if root.exists():
                source_manifest = [
                    {
                        "relative_path": str(path.relative_to(root)),
                        "path": project_relative_path(path),
                        "size": path.stat().st_size,
                    }
                    for path in sorted(root.rglob("*"))
                    if path.is_file()
                ]
        inter_modular_log = _read_text(item.get("inter_modular_log_file"), missing_ok=True)
        log_payload = {}
        if item.get("single_log_file"):
            raw_log = _read_text(item["single_log_file"], missing_ok=True)
            if raw_log:
                log_payload = json.loads(raw_log)
        cases.append(
            {
                **item,
                "source_code": source_code,
                "single_result_code": single_code,
                "termination_result_code": termination_code,
                "termination_stage2_code": stage2_code,
                "inter_modular_result_code": inter_modular_code,
                "inter_modular_log": inter_modular_log,
                "single_specifications": extract_specifications(single_code),
                "termination_specifications": extract_specifications(termination_code),
                "inter_modular_specifications": extract_specifications(inter_modular_code),
                "single_log_payload": log_payload,
                "inter_modular_call_graph_summary": item.get("inter_modular_call_graph_summary", {}),
                "inter_modular_module_results": item.get("inter_modular_module_results", []),
                "inter_modular_split_outputs": item.get("inter_modular_split_outputs", []),
                "inter_modular_proof_stats": item.get("inter_modular_proof_stats", {}),
                "inter_modular_evidence_summary": item.get("inter_modular_evidence_summary", []),
                "execution_mode": item.get("execution_mode", "replay"),
                "source_manifest": source_manifest,
            }
        )
    return cases


def load_demo_cases() -> list[dict[str, Any]]:
    global _DEMO_CASES_CACHE, _DEMO_CASES_CACHE_MTIME_NS

    current_mtime_ns = _demo_cases_config_mtime_ns()
    if _DEMO_CASES_CACHE is not None and _DEMO_CASES_CACHE_MTIME_NS == current_mtime_ns:
        return _DEMO_CASES_CACHE

    _DEMO_CASES_CACHE = _build_demo_cases()
    _DEMO_CASES_CACHE_MTIME_NS = current_mtime_ns
    return _DEMO_CASES_CACHE


def list_demo_cases() -> list[dict[str, Any]]:
    return [
        {
            "id": case["id"],
            "title": case["title"],
            "description": case["description"],
            "modes": case["modes"],
            "recommended_model": case["recommended_model"],
            "paper_keywords": case["paper_keywords"],
            "highlights": case["highlights"],
            "execution_mode": case["execution_mode"],
            "sample_file": case.get("sample_file"),
            "function_name": case.get("function_name"),
            "upstream_source": case.get("upstream_source"),
            "source_manifest": case["source_manifest"],
        }
        for case in load_demo_cases()
    ]


def get_demo_case(case_id: str) -> dict[str, Any]:
    for case in load_demo_cases():
        if case["id"] == case_id:
            return case
    raise KeyError(case_id)
