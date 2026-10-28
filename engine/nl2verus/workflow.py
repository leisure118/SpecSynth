"""Offline B3 prompt preparation, independent local retrieval, and repair prompts.

Research prompts are bundled here so deployment never depends on the original
NL2V research checkout. This module does not call a model or run the verifier.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .dataset import load_tasks, summarize_task
from .b3 import B3_WORKFLOW, RETRIEVAL_NOTICE, load_knowledge
from .verifier import MAX_CODE_BYTES, VERUS_VERSION
from .experiment_prompts import build_generation_prompt, build_repair_prompt


MAX_RETRIEVAL_CONTEXT_BYTES = 64 * 1024
MAX_DIAGNOSTIC_BYTES = 128 * 1024
STOP_WORDS = frozenset("a an and are as at be by for from given in input inputs is it of on or return returns that the then this to value values where which with function fn pub mut let use verus vstd prelude result u32 i32 u64 i64 usize int nat bool".split())


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=20_000)
    function_signature: str = Field(default="", max_length=4_000)

    @field_validator("description", "function_signature")
    @classmethod
    def validate_input(cls, value: str, info) -> str:
        if info.field_name == "description" and not value.strip():
            raise ValueError("请输入自然语言任务")
        return value


class WorkflowRequest(TaskInput):
    sample_id: str | None = Field(default=None, min_length=1, max_length=200)
    rag_enabled: bool = Field(default=False, strict=True)
    top_k: int = Field(default=3, ge=1, le=3, strict=True)

    @field_validator("sample_id")
    @classmethod
    def trim_sample_id(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("任务编号不能为空白")
        return value.strip() if value is not None else None


class RepairPromptRequest(TaskInput):
    code: str = Field(min_length=1, max_length=MAX_CODE_BYTES)
    diagnostics: str = Field(min_length=1, max_length=64_000)
    round: int = Field(default=1, ge=1, le=3, strict=True)

    @field_validator("code", "diagnostics")
    @classmethod
    def nonempty_bounded_text(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError("代码和验证诊断不能为空白")
        limit = MAX_CODE_BYTES if info.field_name == "code" else MAX_DIAGNOSTIC_BYTES
        if len(value.encode("utf-8")) > limit:
            raise ValueError(f"{info.field_name} 超过 {limit // 1024} KiB 限制")
        return value


class WorkflowReferenceNotFound(ValueError):
    pass


def _normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _code_key(task: dict[str, Any]) -> str:
    return str(task.get("verified_verus") or "").replace("\r\n", "\n").strip()


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    words = {part for token in re.findall(r"[a-z][a-z0-9_]*", normalized) for part in token.split("_") if len(part) > 1 and part not in STOP_WORDS}
    # Chinese bigrams match Chinese corpus text literally; this is not translation
    # or multilingual semantic retrieval.
    for segment in re.findall(r"[\u3400-\u9fff]+", normalized):
        words.update(segment[index:index + 2] for index in range(len(segment) - 1))
    return words


def _excluded_indices(tasks: tuple[dict[str, Any], ...], request: WorkflowRequest,
                      dataset_tasks: tuple[dict[str, Any], ...] = ()) -> set[int]:
    # The evaluation dataset only identifies the target and aliases. Its answers
    # are never retrieved; only indices within the independent B3 corpus survive.
    knowledge_count = len(tasks)
    tasks = tasks + dataset_tasks
    query_description = _normalized_text(request.description)
    descriptions = [_normalized_text(str(task.get("description") or "")) for task in tasks]
    codes = [_code_key(task) for task in tasks]
    excluded = {
        index for index, task in enumerate(tasks)
        if (request.sample_id is not None and task.get("sample_id") == request.sample_id)
        or descriptions[index] == query_description
    }
    # Propagate aliases sharing a target task or its reference implementation.
    # This also handles custom input with no selected sample_id.
    while excluded:
        target_descriptions = {descriptions[index] for index in excluded if descriptions[index]}
        target_codes = {codes[index] for index in excluded if codes[index]}
        expanded = excluded | {index for index in range(len(tasks)) if descriptions[index] in target_descriptions or (codes[index] and codes[index] in target_codes)}
        if expanded == excluded:
            break
        excluded = expanded
    return {index for index in excluded if index < knowledge_count}


def retrieve_references(request: WorkflowRequest, tasks: tuple[dict[str, Any], ...],
                        dataset_tasks: tuple[dict[str, Any], ...] = ()) -> dict[str, object]:
    result: dict[str, object] = {
        "enabled": request.rag_enabled,
        "method": "local_keyword",
        "items": [],
        "excluded_count": 0,
        "corpus": "b3",
        "embedding_connected": False,
        "notice": "参考检索未启用；不会读取参考库或调用 embedding。",
    }
    if not request.rag_enabled:
        return result
    excluded = _excluded_indices(tasks, request, dataset_tasks)
    result["excluded_count"] = len(excluded)
    query_tokens = _tokens(request.description + "\n" + request.function_signature)
    documents = []
    for index, task in enumerate(tasks):
        if index in excluded or not _code_key(task) or not task.get("sample_id"):
            continue
        summary = {**summarize_task(task), "id": task["sample_id"],
                   "source": task.get("source", "unknown"),
                   "source_file": task.get("source_file", ""),
                   "license": task.get("license", "Unspecified")}
        tokens = _tokens(summary["description"] + "\n" + summary["function_signature"])
        if tokens:
            documents.append((summary, str(task["verified_verus"]), tokens))

    frequencies = Counter(token for _, _, tokens in documents for token in tokens)
    total = len(documents)
    def weight(token: str) -> float:
        return math.log(1 + total / (1 + frequencies[token])) + 1

    query_norm = math.sqrt(sum(weight(token) ** 2 for token in query_tokens))
    ranked = []
    for summary, code, tokens in documents:
        shared = query_tokens & tokens
        if not shared or not query_norm:
            continue
        document_norm = math.sqrt(sum(weight(token) ** 2 for token in tokens))
        score = sum(weight(token) ** 2 for token in shared) / (query_norm * document_norm)
        ranked.append(({**summary, "code": code}, score))
    ranked.sort(key=lambda candidate: (-candidate[1], str(candidate[0]["sample_id"])))

    items = []
    seen_codes: set[str] = set()
    for item, score in ranked:
        normalized_code = item["code"].replace("\r\n", "\n").strip()
        if normalized_code in seen_codes:
            continue
        candidate = {**item, "score": round(score, 6)}
        size = len(json.dumps([*items, candidate], ensure_ascii=False, indent=2).encode("utf-8"))
        if size > MAX_RETRIEVAL_CONTEXT_BYTES:
            continue
        items.append(candidate)
        seen_codes.add(normalized_code)
        if len(items) >= request.top_k:
            break
    result["items"] = items
    result["notice"] = (
        RETRIEVAL_NOTICE + "本地关键词检索按词法相似度排序；分数不是正确率或模型置信度。"
        "已排除当前任务及其可识别的文本/参考代码重复项；不保证排除所有语义近似样本。"
        "参考上下文最多 64 KiB，参考实现未在本轮重新验证。"
        + ("未找到符合限制且有共同关键词的其他参考任务。" if not items else "")
    )
    return result


def prepare_workflow(request: WorkflowRequest) -> dict[str, object]:
    tasks = load_tasks() if request.rag_enabled or request.sample_id is not None else ()
    if request.sample_id is not None and not any(task.get("sample_id") == request.sample_id for task in tasks):
        raise WorkflowReferenceNotFound("未找到当前数据集任务")
    knowledge = load_knowledge() if request.rag_enabled else ()
    retrieval = retrieve_references(request, knowledge, tasks)
    return preparation_from_retrieval(request, retrieval)


def preparation_from_retrieval(request: WorkflowRequest, retrieval: dict[str, Any]) -> dict[str, object]:
    """Pure assembly using explicitly chosen references; no model or verifier I/O."""
    # Map only the reference fields consumed by the original pure builder. Scores,
    # provenance and offline/version information remain outside the prompt body.
    references = [{"description": item["description"], "verified_verus": item["code"]}
                  for item in retrieval["items"]]
    prompt = build_generation_prompt(request.description, request.function_signature, references)
    return {
        "run_id": str(uuid4()), "mode": "offline", "model_called": False,
        "code": "", "prompt": prompt, "verus_version": VERUS_VERSION,
        "input": request.model_dump(), "retrieval": retrieval,
        "workflow": dict(B3_WORKFLOW),
        "prompt_template": {"id": "experiment_generation_v1", "source": "原实验生成提示词"},
    }


def prepare_repair_prompt(request: RepairPromptRequest) -> dict[str, object]:
    prompt = build_repair_prompt(request.description, request.function_signature,
                                 request.code, request.diagnostics)
    return {"prompt": prompt, "status": "prompt_ready", "model_called": False,
            "round": request.round, "verus_version": VERUS_VERSION,
            "workflow": dict(B3_WORKFLOW), "retrieval_performed": False,
            "prompt_template": {"id": "experiment_repair_v1", "source": "原实验错误分类修复提示词"}}
