"""Dependency-injected B3 controller; deliberately not exposed as an HTTP route.

There is no remote generator implementation, configuration loader, or API client.
Callers must explicitly supply generation and verification adapters. Tests use
in-memory fakes; the public workflow only prepares prompts for manual operation.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Protocol

from .b3 import B3_WORKFLOW
from .verifier import MAX_CODE_BYTES, VERUS_VERSION
from .workflow import RepairPromptRequest, WorkflowRequest, prepare_repair_prompt, prepare_workflow


class GeneratorProvider(Protocol):
    def __call__(self, prompt: str, *, phase: str, round: int) -> str: ...


class VerifierProvider(Protocol):
    def __call__(self, code: str) -> Mapping[str, Any]: ...


def candidate_problem(code: object) -> str | None:
    """Conservative preflight, not a semantic or complete trusted-code audit."""
    if not isinstance(code, str) or not code.strip():
        return "empty_candidate"
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return "oversized_candidate"
    # Ignore ordinary comments and strings, but leave whitespace where they were
    # removed so comments between a call name and '(' do not evade the guard.
    source = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|r(#+)"[\s\S]*?"\1|"(?:\\.|[^"\\])*"', " ", code)
    if re.search(r"\b(?:assume|admit|assume_specification|external_body|external_fn_specification)\b", source):
        return "proof_bypass"
    if re.search(r"#\s*\[\s*verifier\s*(?:::|\()\s*external\b", source):
        return "proof_bypass"
    return None


def classify_verification(result: Mapping[str, Any]) -> str:
    if result.get("verus_version") != VERUS_VERSION:
        return "version_mismatch"
    status = result.get("status")
    if status in {"timeout", "tool_error", "no_checks", "version_mismatch"}:
        return str(status)
    if status == "verified" or result.get("verified") is True:
        count = result.get("verified_count")
        if type(count) is int and count == 0:
            return "no_checks"
        if (status == "verified" and result.get("verified") is True
                and type(count) is int and count > 0
                and type(result.get("error_count")) is int and result.get("error_count") == 0
                and type(result.get("exit_code")) is int and result.get("exit_code") == 0):
            return "verified"
        return "tool_error"
    if status in {"failed", "verification_failed"}:
        count, errors, exit_code = result.get("verified_count"), result.get("error_count"), result.get("exit_code")
        if type(count) is int and count == 0 and errors == 0 and exit_code == 0:
            return "no_checks"
        if type(count) is int and count >= 0 and type(errors) is int and errors > 0 and type(exit_code) is int and exit_code != 0:
            return str(status)
        return "tool_error"
    if status == "compile_error":
        exit_code = result.get("exit_code")
        return "compile_error" if type(exit_code) is int and exit_code != 0 else "tool_error"
    return "tool_error"


def verify_b3_candidate(code: str, *, verify: VerifierProvider) -> dict[str, Any]:
    """Shared guard for manually submitted candidates and injected execution.

    This catches obvious bypasses only. Passing this preflight never establishes
    natural-language correctness or the absence of every trusted-code escape.
    """
    problem = candidate_problem(code)
    if problem:
        return {
            "status": "blocked", "verified": False, "guard_reason": problem,
            "exit_code": None, "elapsed_ms": 0, "verified_count": None,
            "error_count": None, "stdout": "", "stderr": "",
            "verus_version": VERUS_VERSION, "verification_run": False,
            "message": "代码被阻止：" + {
                "proof_bypass": "检测到明显的 assume/admit/external_body 等证明绕过标记，请移除后重新提交。",
                "empty_candidate": "代码不能为空。",
                "oversized_candidate": "代码超过 256 KiB 限制。",
            }[problem],
        }
    result = verify(code)
    if not isinstance(result, Mapping):
        result = {"status": "tool_error", "message": "验证器未返回结构化结果。"}
    status = classify_verification(result)
    if status == "version_mismatch":
        status = "tool_error"
        message = "无法确认本次结果来自指定 Verus 版本，不能接受为通过。"
    elif status == "no_checks":
        message = "没有实际验证项，不能接受为通过。"
    elif status == "tool_error" and result.get("verified"):
        message = "验证结果缺少有效摘要或相互矛盾，不能接受为通过。"
    else:
        message = str(result.get("message") or "请查看验证诊断。")
    return {"exit_code": None, "elapsed_ms": 0, "verified_count": None, "verus_version": "",
            "error_count": None, "stdout": "", "stderr": "",
            **result, "status": status, "verified": status == "verified",
            "message": message, "verification_run": True,
            "guard_notice": "仅拦截明显证明绕过标记；工具通过不等于自然语言语义正确。"}


def run_b3(request: WorkflowRequest, *, generate: GeneratorProvider,
           verify: VerifierProvider) -> dict[str, Any]:
    """One initial candidate plus at most three *additional* repairs.

    No retries, multi-candidate sampling, or re-retrieval are hidden in this
    controller. Injected adapters must disclose any transport retry accounting.
    A 'verified' outcome is tool verification, never semantic correctness/SVC.
    """
    # Capture immutable task values before handing control to injected adapters.
    original_description = request.description
    original_signature = request.function_signature
    preparation = prepare_workflow(request)
    outcome: dict[str, Any] = {
        "run_id": preparation["run_id"],
        "mode": "injected",
        "workflow": dict(B3_WORKFLOW),
        "verus_version": VERUS_VERSION,
        "status": "not_run",
        "verified": False,
        "provider_calls": 0,
        "repair_rounds": 0,
        "attempts": [],
        "retrieval": preparation["retrieval"],
    }
    prompt = str(preparation["prompt"])
    for round_number in range(4):
        phase = "generation" if round_number == 0 else "repair"
        outcome["provider_calls"] += 1
        outcome["repair_rounds"] = round_number
        try:
            code = generate(prompt, phase=phase, round=round_number)
        except Exception as error:
            outcome.update(status="generation_error", message=str(error)[:500])
            return outcome
        attempt: dict[str, Any] = {"phase": phase, "round": round_number, "code": code,
                                   "prompt": prompt, "verification": None}
        outcome["attempts"].append(attempt)
        problem = candidate_problem(code)
        if problem:
            attempt["status"] = problem
            outcome.update(status=problem, message="代码未通过安全预检查；没有运行验证或后续修复。")
            return outcome
        try:
            verification = verify(code)
        except TimeoutError:
            attempt["status"] = "timeout"
            outcome.update(status="timeout", message="验证超时，已停止修复链。")
            return outcome
        except Exception as error:
            attempt["status"] = "tool_error"
            outcome.update(status="tool_error", message=str(error)[:500])
            return outcome
        if not isinstance(verification, Mapping):
            attempt["status"] = "tool_error"
            outcome.update(status="tool_error", message="验证器未返回结构化结果。")
            return outcome
        attempt["verification"] = dict(verification)
        status = classify_verification(verification)
        attempt["status"] = status
        outcome["status"] = status
        if status == "verified":
            outcome["verified"] = True
            return outcome
        if status not in {"failed", "verification_failed", "compile_error"}:
            return outcome
        if round_number == 3:
            outcome.update(status="repair_limit", message="已完成最多三次额外修复，未验证通过。")
            return outcome
        diagnostics = "\n".join(str(verification.get(field) or "") for field in ("stderr", "stdout", "message")).strip()
        if not diagnostics:
            outcome.update(status="tool_error", message="缺少可用验证诊断；不继续猜测修复。")
            return outcome
        # Exact original task/interface are carried into every round. No call to
        # prepare_workflow/retrieve_references happens after the initial stage.
        repair = prepare_repair_prompt(RepairPromptRequest(
            description=original_description,
            function_signature=original_signature,
            code=code,
            diagnostics=diagnostics[:32_000],
            round=round_number + 1,
        ))
        prompt = str(repair["prompt"])
    return outcome
