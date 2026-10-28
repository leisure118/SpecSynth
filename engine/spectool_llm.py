from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI, OpenAIError

from engine.autospec.src.config_manager import ConfigLoader
from engine.spectool_core import cextract


ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_CONFIG_PATH = ROOT_DIR / "configs" / "models_config.yaml"


SYSTEM_PROMPT = """You generate ACSL annotations for Frama-C/WP.
Return only valid JSON. Do not include Markdown fences, prose, admit clauses, axioms, or code rewrites.
The JSON schema is:
{
  "contract": "ACSL function contract clauses without /*@ */",
  "loop_specs": [{"line": 0, "acsl": "ACSL loop clauses without /*@ */"}],
  "notes": ["short optional notes"]
}
Use exact original line numbers from the provided loop candidates.
Prefer conservative, provable contracts. Include assigns clauses when obvious.
For loops, include loop invariant clauses and loop assigns/variant clauses when needed.
"""


def generate_annotations(source: str, function_name: str, model_name: str) -> dict[str, Any]:
    match = cextract.extract_one(source, function_name)
    if match is None:
        available = [name for name, _, _, _ in cextract.extract_functions(source)]
        raise ValueError(f"function '{function_name}' not found. Available: {', '.join(available)}")

    function_source, start_line, end_line = match
    loop_candidates = _loop_candidates(source, start_line, end_line)
    template = _heuristic_annotations(function_source, function_name, loop_candidates)
    if template:
        return {
            **template,
            "model_name": model_name,
            "function_name": function_name,
            "function_start_line": start_line,
            "function_end_line": end_line,
            "loop_candidates": loop_candidates,
            "raw_response": "",
            "tokens_usage": 0,
            "generation_mode": "spectool-template",
        }
    prompt = _build_prompt(function_name, function_source, start_line, loop_candidates)

    config = ConfigLoader.get_model_config(model_name, config_file_path=str(MODELS_CONFIG_PATH))
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    try:
        response = client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=config.params.get("temperature", 0.1),
            max_tokens=config.params.get("max_tokens", 1200),
            timeout=config.params.get("timeout", 120),
            **({"extra_body": config.params["extra_body"]} if config.params.get("extra_body") else {}),
        )
    except OpenAIError as exc:
        raise RuntimeError(f"LLM generation failed: {exc}") from exc
    content = response.choices[0].message.content or ""
    payload = _parse_json_object(content)
    normalized = _normalize_payload(payload, loop_candidates)
    normalized.update(
        {
            "model_name": model_name,
            "function_name": function_name,
            "function_start_line": start_line,
            "function_end_line": end_line,
            "loop_candidates": loop_candidates,
            "raw_response": content,
            "tokens_usage": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
            "generation_mode": "llm",
        }
    )
    return normalized


def _heuristic_annotations(
    function_source: str,
    function_name: str,
    loop_candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return deterministic ACSL for simple counter loops.

    This keeps the spectool generate flow usable for small demos even when an
    LLM returns weak or unavailable loop invariants.  The pattern covers code of
    the form ``a = x; y = 0; while (a != 0) { y++; a--; } return y;``.
    """
    if len(loop_candidates) != 1:
        return None
    compact = re.sub(r"\s+", " ", function_source)
    signature = re.search(r"\bint\s+" + re.escape(function_name) + r"\s*\(\s*int\s+(\w+)\s*\)", compact)
    init = re.search(r"\bint\s+(\w+)\s*=\s*(\w+)\s*;\s*int\s+(\w+)\s*=\s*0\s*;", compact)
    loop = re.search(r"while\s*\(\s*(\w+)\s*!=\s*0\s*\)\s*\{\s*(\w+)\s*=\s*\2\s*\+\s*1\s*;\s*(\w+)\s*=\s*\3\s*-\s*1\s*;\s*\}\s*return\s+(\w+)\s*;", compact)
    if not signature or not init or not loop:
        return None
    param = signature.group(1)
    a_var, a_init, y_var = init.group(1), init.group(2), init.group(3)
    if a_init != param:
        return None
    if loop.group(1) != a_var or loop.group(2) != y_var or loop.group(3) != a_var or loop.group(4) != y_var:
        return None
    line = int(loop_candidates[0]["line"])
    contract = "\n".join(
        [
            f"requires {param} >= 0;",
            "assigns \\nothing;",
            f"ensures \\result == {param};",
        ]
    )
    loop_acsl = "\n".join(
        [
            f"loop invariant 0 <= {a_var} <= {param};",
            f"loop invariant {y_var} + {a_var} == {param};",
            f"loop assigns {a_var}, {y_var};",
            f"loop variant {a_var};",
        ]
    )
    return {
        "contract": contract,
        "loop_specs": [{"line": line, "acsl": loop_acsl}],
        "notes": ["Generated by spectool deterministic template for a non-negative countdown loop."],
    }


def _loop_candidates(source: str, start_line: int, end_line: int) -> list[dict[str, Any]]:
    lines = source.splitlines()
    candidates: list[dict[str, Any]] = []
    for line_number in range(start_line, end_line + 1):
        line = lines[line_number - 1] if line_number - 1 < len(lines) else ""
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue
        if re.search(r"\b(for|while)\s*\(", line) or re.search(r"\bdo\b", line):
            candidates.append({"line": line_number, "code": stripped})
    return candidates


def _build_prompt(
    function_name: str,
    function_source: str,
    start_line: int,
    loop_candidates: list[dict[str, Any]],
) -> str:
    numbered = []
    for offset, line in enumerate(function_source.splitlines(), start=start_line):
        numbered.append(f"{offset}: {line}")
    loops = "\n".join(f"- line {item['line']}: {item['code']}" for item in loop_candidates) or "None"
    return "\n".join(
        [
            f"Target function: {function_name}",
            "",
            "Original function with line numbers:",
            "\n".join(numbered),
            "",
            "Loop candidates:",
            loops,
            "",
            "Generate ACSL annotations for this function only.",
            "Return JSON exactly matching the requested schema.",
        ]
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("LLM did not return a JSON object.")
        payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("LLM response must be a JSON object.")
    return payload


def _normalize_payload(payload: dict[str, Any], loop_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    contract = str(payload.get("contract") or "").strip()
    allowed_lines = {int(item["line"]) for item in loop_candidates}
    loop_specs = []
    for item in payload.get("loop_specs") or []:
        if not isinstance(item, dict):
            continue
        try:
            line = int(item.get("line"))
        except (TypeError, ValueError):
            continue
        acsl = str(item.get("acsl") or "").strip()
        if not acsl or line not in allowed_lines:
            continue
        loop_specs.append({"line": line, "acsl": acsl})
    notes = [str(item).strip() for item in payload.get("notes") or [] if str(item).strip()]
    if not contract and not loop_specs:
        raise ValueError("LLM response did not contain any injectable ACSL annotations.")
    return {"contract": contract or None, "loop_specs": loop_specs, "notes": notes[:5]}
