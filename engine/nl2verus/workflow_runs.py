"""Bounded process-local jobs with explicit provider calls and no hidden retries."""
from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import threading
from typing import Callable
from uuid import uuid4

from pydantic import Field

from .b3_runner import verify_b3_candidate
from .dataset import load_tasks
from .verifier import VERUS_VERSION, verifier_info, verify_code
from .workflow import (RepairPromptRequest, WorkflowRequest, preparation_from_retrieval,
                       prepare_repair_prompt, retrieve_references)

TERMINAL = frozenset({"completed", "failed", "cancelled"})


class WorkflowRunRequest(WorkflowRequest):
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    model_id: str | None = Field(default=None, min_length=1, max_length=200)
    repair_enabled: bool = Field(default=True, strict=True)
    max_repair_rounds: int = Field(default=3, ge=1, le=3, strict=True)
    timeout_seconds: int = Field(default=30, ge=1, le=60, strict=True)


class RunRequestError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _config():
    from .platform_provider import get_config
    return get_config()


def _status(*, snapshot):
    from .platform_provider import provider_status
    return provider_status(snapshot=snapshot)


def _generate(prompt, model_id, *, snapshot):
    from .platform_provider import generate_code
    return generate_code(prompt, model_id, snapshot=snapshot)


def _retrieve(request, *, snapshot):
    from .vector_retrieval import retrieve_vector_references
    return retrieve_vector_references(request, snapshot=snapshot)


def _validate_task(request):
    if request.sample_id and not any(row.get("sample_id") == request.sample_id for row in load_tasks()):
        raise RunRequestError(422, "原始数据集任务不存在；没有发出模型请求。")


def _safe_error(error: Exception, phase: str) -> str:
    # Only the provider's explicitly sanitized error contract may cross HTTP.
    try:
        from .model_provider import ProviderError
        if isinstance(error, ProviderError):
            return error.safe_message
    except ImportError:
        pass
    if isinstance(error, TimeoutError):
        return "请求超时，已停止；没有自动重试。"
    return ("生成或向量检索调用失败，请检查配置、服务状态与额度；没有自动重试。"
            if phase in {"preparing", "generating", "repairing"}
            else "本机验证器不可用或发生异常，已停止；没有继续生成或修复。")


def _safe_usage(error: Exception) -> dict:
    from .model_provider import ProviderError
    usage = error.usage if isinstance(error, ProviderError) else {}
    return {key: value for key, value in usage.items()
            if key in {"prompt_tokens", "completion_tokens", "total_tokens"}
            and type(value) is int and 0 <= value <= 1_000_000_000}


class WorkflowRuns:
    """One active job; 20 full records and finite idempotency tombstones.

    The private config snapshot lives only in the worker, never in the public
    record. Cancellation cannot undo an in-flight paid call; its output is saved.
    """
    def __init__(self, *, config: Callable = _config, status: Callable = _status,
                 generate: Callable = _generate, retrieve: Callable = _retrieve,
                 verify: Callable = verify_code, verifier_status: Callable = verifier_info,
                 validate_task: Callable = _validate_task, max_runs: int = 20,
                 max_request_ids: int = 256):
        if max_runs < 1 or max_request_ids < 1:
            raise ValueError("运行记录容量必须为正数")
        self._config, self._status, self._generate, self._retrieve = config, status, generate, retrieve
        self._verify, self._verifier_status, self._validate_task = verify, verifier_status, validate_task
        self._max_runs, self._max_ids = max_runs, max_request_ids
        self._runs: OrderedDict[str, dict] = OrderedDict()
        self._requests: dict[str, tuple[str, str]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="workflow-run")
        self._active: str | None = None
        self._closed = False

    def submit(self, request: WorkflowRunRequest) -> dict:
        payload = request.model_dump()
        fingerprint = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        with self._lock:
            previous = self._requests.get(request.request_id)
            if previous:
                if previous[0] != fingerprint:
                    raise RunRequestError(409, "此 request_id 已用于其他输入，请勿复用。")
                return self.get(previous[1])
            if self._closed:
                raise RunRequestError(503, "运行器已停止。")
            if self._active:
                raise RunRequestError(409, "已有自动任务正在运行，请等待完成或取消。")
            if len(self._requests) >= self._max_ids:
                raise RunRequestError(503, "安全去重记录已满，请保存结果后重启后端。")
            try:
                config = self._config()
                capabilities = self._status(snapshot=config)
            except Exception:
                raise RunRequestError(503, "无法读取模型配置；没有发出模型请求。") from None
            if not capabilities.get("generation_configured"):
                raise RunRequestError(503, "尚未配置生成模型；没有发出模型请求。")
            model_id = request.model_id or capabilities.get("default_model_id")
            model_ids = {item.get("id") for item in capabilities.get("models", [])
                         if isinstance(item, dict) and item.get("configured", True)}
            if not model_id or model_id not in model_ids:
                raise RunRequestError(422, "请选择已配置的生成模型。")
            if request.rag_enabled and not capabilities.get("embedding_configured"):
                raise RunRequestError(503, "向量检索需要配置查询 embedding；可关闭 RAG 后生成。")
            self._validate_task(request)
            while len(self._runs) >= self._max_runs:
                self._runs.popitem(last=False)
            run_id, now = str(uuid4()), _now()
            run = {"id": run_id, "run_id": run_id, "request_id": request.request_id,
                   "status": "queued", "phase": "preparing", "outcome": None, "revision": 0,
                   "mode": "automatic", "request": payload, "model_id": model_id,
                   "created_at": now, "updated_at": now, "finished_at": None,
                   "verus_version": VERUS_VERSION, "preparation": None, "prompt": "",
                   "retrieval": None, "attempts": [], "stages": [], "provider_calls": 0,
                   "repair_rounds": 0, "verified": False, "cancel_requested": False,
                   "message": "任务已接收；单次生成，失败后按设置追加修复。"}
            self._runs[run_id] = run
            self._requests[request.request_id] = (fingerprint, run_id)
            self._active = run_id
            snapshot = deepcopy(run)
            try:
                self._executor.submit(self._execute, run_id, request.model_copy(deep=True), model_id, config)
            except Exception:
                self._finish(run_id, "tool_error", "无法启动后台任务；没有发出模型请求。")
                self._active = None
                return self.get(run_id)
            return snapshot

    def get(self, run_id: str) -> dict:
        with self._lock:
            if run_id not in self._runs:
                if any(old_id == run_id for _, old_id in self._requests.values()):
                    raise RunRequestError(410, "运行记录已从内存移除；不会重复执行已接收的请求。")
                raise RunRequestError(404, "当前进程未找到运行记录；不会自动重发。")
            return deepcopy(self._runs[run_id])

    def get_request(self, request_id: str) -> dict:
        with self._lock:
            previous = self._requests.get(request_id)
            if previous is None:
                raise RunRequestError(404, "当前进程未找到该请求；不会自动重发。")
            return self.get(previous[1])

    def cancel(self, run_id: str) -> dict:
        with self._lock:
            self.get(run_id)
            run = self._runs[run_id]
            if run["status"] not in TERMINAL:
                run.update(cancel_requested=True, updated_at=_now(),
                           revision=run["revision"] + 1,
                           message="已请求停止后续步骤；已发出的模型请求可能仍计费，返回结果会保留。")
            return deepcopy(run)

    def _update(self, run_id: str, **values) -> None:
        with self._lock:
            run = self._runs[run_id]
            run.update(**deepcopy(values), updated_at=_now(), revision=run["revision"] + 1)

    def _stage(self, run_id: str, phase: str, message: str, round_number: int = 0) -> None:
        with self._lock:
            run = self._runs[run_id]
            now = _now()
            stages = run.setdefault('stages', [])
            if stages and not stages[-1].get('finished_at'):
                stages[-1].update(finished_at=now, status='completed')
            stages.append({'phase': phase, 'round': round_number, 'started_at': now,
                           'finished_at': None, 'status': 'running', 'message': message})
            run.update(phase=phase, message=message, updated_at=now, revision=run['revision'] + 1)

    def _finish(self, run_id: str, outcome: str, message: str, *, verified: bool = False) -> None:
        with self._lock:
            run = self._runs[run_id]
            cancelled = run["cancel_requested"]
            if run.get('stages') and not run['stages'][-1].get('finished_at'):
                run['stages'][-1].update(finished_at=_now(), status='completed' if verified else 'failed', outcome=outcome)
            run.update(status="cancelled" if cancelled else ("completed" if outcome in {
                "verified", "repair_limit", "verification_failed"} else "failed"),
                phase="done", outcome="cancelled" if cancelled else outcome,
                verified=verified, message=("后续步骤已停止，已返回的代码与检查记录已保留。" if cancelled else message),
                updated_at=_now(), finished_at=_now(), revision=run["revision"] + 1)

    def _cancelled(self, run_id: str) -> bool:
        with self._lock:
            return self._runs[run_id]["cancel_requested"]

    def _attempt_update(self, run_id: str, index: int, **values) -> None:
        with self._lock:
            self._runs[run_id]["attempts"][index].update(**deepcopy(values))
            self._runs[run_id]["updated_at"] = _now()
            self._runs[run_id]["revision"] += 1

    def _execute(self, run_id: str, request: WorkflowRunRequest, model_id: str, config) -> None:
        try:
            self._update(run_id, status="running")
            self._stage(run_id, "preparing", "准备任务、Skill 与提示词")
            self._execute_steps(run_id, request, model_id, config)
        except Exception as error:
            phase = self.get(run_id)["phase"]
            self._finish(run_id, "provider_error" if phase in {"preparing", "generating", "repairing"} else "tool_error",
                         _safe_error(error, phase))
        finally:
            with self._lock:
                self._active = None

    def _execute_steps(self, run_id: str, request: WorkflowRunRequest, model_id: str, config) -> None:
        original = WorkflowRequest(**request.model_dump(include=set(WorkflowRequest.model_fields)))
        try:
            runtime = self._verifier_status()
        except Exception:
            runtime = {}
        if not runtime.get("available") or runtime.get("version") != VERUS_VERSION:
            self._finish(run_id, "tool_error", "指定版本 Verus 尚未就绪；没有发出模型请求。")
            return
        if self._cancelled(run_id):
            self._finish(run_id, "cancelled", "已取消。")
            return
        retrieval = (self._retrieve(original.model_copy(deep=True), snapshot=config) if original.rag_enabled
                     else retrieve_references(original, ()))
        preparation = preparation_from_retrieval(original, retrieval)
        preparation.update(run_id=run_id, mode="automatic")
        prompt = str(preparation["prompt"])
        self._update(run_id, preparation=preparation, prompt=prompt, retrieval=retrieval)
        limit = request.max_repair_rounds if request.repair_enabled else 0
        for round_number in range(limit + 1):
            with self._lock:
                run = self._runs[run_id]
                if run["cancel_requested"]:
                    self._finish(run_id, "cancelled", "已取消。")
                    return
                attempt = {"id": f"{run_id}:{round_number}", "phase": "generation" if round_number == 0 else "repair",
                           "round": round_number, "status": "generating", "code": "", "prompt": prompt,
                           "model_id": model_id, "model_name": "", "usage": {}, "finish_reason": None,
                           "verification": None, "error": None, "created_at": _now(), "finished_at": None}
                run["attempts"].append(attempt)
                run.update(phase="generating" if round_number == 0 else "repairing",
                           provider_calls=run["provider_calls"] + 1, repair_rounds=round_number,
                           updated_at=_now(), revision=run["revision"] + 1)
            self._stage(run_id, 'generating' if round_number == 0 else 'repairing',
                        '正在调用模型生成 Verus' if round_number == 0 else f'根据验证诊断修复 · 第 {round_number} 轮', round_number)
            try:
                generated = self._generate(prompt, model_id, snapshot=config)
                if not isinstance(generated, dict) or not isinstance(generated.get("code"), str):
                    raise ValueError("Invalid provider result")
            except Exception as error:
                message = _safe_error(error, "generating")
                self._attempt_update(run_id, round_number, status="provider_error", error=message,
                                     usage=_safe_usage(error), finished_at=_now())
                self._finish(run_id, "provider_error", message)
                return
            with self._lock:
                self._runs[run_id]['provider_calls'] += max(0,generated.get('provider_calls',1)-1)
            code = generated["code"]
            self._attempt_update(run_id, round_number, agent_events=generated.get('agent_events',[]),
                                 effective_prompt=generated.get('effective_prompt',prompt),
                                 agent_provider_calls=generated.get('provider_calls',1))
            self._attempt_update(run_id, round_number, code=code, status="generated",
                                 model_name=generated.get("model_name", model_id), usage=generated.get("usage") or {},
                                 finish_reason=generated.get("finish_reason"), output_token_limit=generated.get("output_token_limit"))
            with self._lock:
                if self._cancelled(run_id):
                    self._attempt_update(run_id, round_number, status="cancelled", finished_at=_now())
                    self._finish(run_id, "cancelled", "已取消。")
                    return
                if generated.get("finish_reason") == "length":
                    self._attempt_update(run_id, round_number, status="output_limit", finished_at=_now())
                    self._finish(run_id, "output_limit", "模型输出被长度上限截断，已保留；未运行验证或继续修复。")
                    return
                self._stage(run_id, "verifying", "正在运行 Verus 验证" + (f" · 修复 {round_number} 后" if round_number else " · 首次候选"), round_number)
                self._attempt_update(run_id, round_number, status="verifying")
            try:
                verification = verify_b3_candidate(code, verify=lambda value: self._verify(value, request.timeout_seconds))
            except Exception as error:
                message = _safe_error(error, "verifying")
                self._attempt_update(run_id, round_number, status="tool_error", error=message, finished_at=_now())
                self._finish(run_id, "tool_error", message)
                return
            status = verification["status"]
            with self._lock:
                self._runs[run_id]['stages'][-1]['outcome'] = status
            self._attempt_update(run_id, round_number, verification=verification, status=status, finished_at=_now())
            if status == "verified":
                self._finish(run_id, "verified", "Verus 验证通过；这不等于完整自然语言语义审核。", verified=True)
                return
            if self._cancelled(run_id) or status not in {"failed", "verification_failed", "compile_error"}:
                self._finish(run_id, status, "本次检查未通过，已停止后续模型调用。")
                return
            if round_number == limit:
                self._finish(run_id, "repair_limit" if limit else "verification_failed",
                             "已达到追加修复上限，尚未验证通过。" if limit else "验证未通过；未启用追加修复。")
                return
            diagnostics = "\n".join(str(verification.get(key) or "") for key in ("stderr", "stdout", "message")).strip()
            if not diagnostics:
                self._finish(run_id, "tool_error", "没有可用验证诊断，已停止修复。")
                return
            repair = prepare_repair_prompt(RepairPromptRequest(description=original.description,
                function_signature=original.function_signature, code=code, diagnostics=diagnostics[:32_000], round=round_number + 1))
            prompt = str(repair["prompt"])

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if self._active:
                self._runs[self._active]["cancel_requested"] = True
                self._runs[self._active]["updated_at"] = _now()
                self._runs[self._active]["revision"] += 1
        self._executor.shutdown(wait=True, cancel_futures=False)
