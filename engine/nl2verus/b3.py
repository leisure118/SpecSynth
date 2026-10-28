"""Bundled B3 knowledge assets and explicit offline capability information.

The FAISS file is portable research data, not an active retrieval provider.
Query embeddings are deliberately not configured or requested by this module.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Protocol, Sequence

from .verifier import PROJECT_ROOT, VERUS_VERSION


KNOWLEDGE_ROOT = PROJECT_ROOT / "data" / "knowledge" / "b3"
METADATA_PATH = KNOWLEDGE_ROOT / "metadata.json"
INDEX_PATH = KNOWLEDGE_ROOT / "index.faiss"
MAX_KNOWLEDGE_BYTES = 16 * 1024 * 1024
B3_WORKFLOW = {
    "id": "b3",
    "label": "单次生成与三轮修复",
    "initial_candidates": 1,
    "max_repair_rounds": 3,
}
RETRIEVAL_NOTICE = (
    "独立参考库；当前使用本地关键词检索降级，尚未接入查询 embedding，"
    "未运行原实验的向量 RAG。FAISS 索引仅随项目打包。"
)


class EmbeddingProvider(Protocol):
    """Future opt-in boundary; no implementation or caller is enabled here."""

    def embed(self, text: str) -> Sequence[float]: ...


def load_knowledge(path: Path | None = None) -> tuple[dict[str, Any], ...]:
    metadata_path = path if path is not None else METADATA_PATH
    if metadata_path.stat().st_size > MAX_KNOWLEDGE_BYTES:
        raise ValueError("知识库文件超过 16 MiB 限制")
    data = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    records = data.get("items") if isinstance(data, dict) else data
    if not isinstance(records, list) or len(records) > 10_000:
        raise ValueError("知识库必须为不超过 10000 条记录的列表")
    result = []
    seen_ids: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("知识库包含无效记录")
        sample_id = item.get("sample_id") or item.get("id")
        description = item.get("description")
        code = item.get("verified_verus", item.get("code"))
        if not all(isinstance(value, str) and value.strip() for value in (sample_id, description, code)):
            raise ValueError("参考记录缺少编号、描述或代码")
        if sample_id in seen_ids:
            raise ValueError("知识库编号重复")
        seen_ids.add(sample_id)
        result.append({
            **item,
            "id": sample_id,
            "sample_id": sample_id,
            "description": description,
            "function_signature": str(item.get("function_signature") or ""),
            "verified_verus": code,
            "source": str(item.get("source") or "unknown"),
            "source_file": str(item.get("source_file") or ""),
            # Do not invent a license for records without attribution.
            "license": item.get("license") or "Unspecified",
        })
    return tuple(result)


def workflow_status() -> dict[str, object]:
    try:
        records = load_knowledge()
        counts = Counter(item["source"] for item in records)
        knowledge = {
            "available": True,
            "count": len(records),
            "source_count": len(counts),
            "sources": [{"id": source, "name": source, "count": count} for source, count in sorted(counts.items())],
            "notice": RETRIEVAL_NOTICE + "参考代码来自外部项目，未在本轮重新验证。",
        }
    except (OSError, ValueError) as error:
        knowledge = {"available": False, "count": 0, "source_count": 0, "sources": [],
                     "notice": f"本地知识库尚不可用：{type(error).__name__}"}
    return {
        "mode": "offline",
        "model_connected": False,
        "embedding_connected": False,
        "model_called": False,
        "verus_version": VERUS_VERSION,
        "workflow": dict(B3_WORKFLOW),
        "knowledge": {**knowledge, "index_available": INDEX_PATH.is_file(),
                      "method": "local_keyword", "vector_retrieval_enabled": False},
    }
