"""Real description-vector retrieval over the unchanged, bundled FAISS snapshot."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from . import b3, model_provider
from .dataset import load_tasks, summarize_task
from .model_provider import ConfigSnapshot, ProviderError
from .workflow import MAX_RETRIEVAL_CONTEXT_BYTES, WorkflowReferenceNotFound, WorkflowRequest, _code_key, _excluded_indices

MAX_INDEX_BYTES = 16 * 1024 * 1024
MAX_CACHE_ENTRIES = 128
CACHE_TTL_SECONDS = 900
_CACHE: OrderedDict[str, tuple[float, tuple[float, ...]]] = OrderedDict()
_CACHE_LOCK = threading.Lock()
_CACHE_SALT = os.urandom(32)


@dataclass(frozen=True, repr=False)
class VectorIndex:
    vectors: Any
    faiss_index: Any
    engine: str

    def rank(self, query: Any) -> list[tuple[int, float]]:
        if self.faiss_index is not None:
            scores, indices = self.faiss_index.search(query.reshape(1, -1), len(self.vectors))
            ranked = [(int(index), float(score)) for index, score in zip(indices[0], scores[0]) if index >= 0]
        else:
            scores = self.vectors @ query
            ranked = [(index, float(score)) for index, score in enumerate(scores)]
        # Match cosine/IP ordering and make equal-score ordering reproducible.
        return sorted(ranked, key=lambda item: (-item[1], item[0]))


def _decode_flat_index(content: bytes, dimensions: int, count: int) -> VectorIndex:
    if len(content) < 45 or content[:4] != b"IxFI":
        raise ProviderError("index_invalid", "知识库不是受支持的标准 FAISS IndexFlatIP 快照。")
    actual_dim, actual_count = struct.unpack_from("<iq", content, 4)
    metric = struct.unpack_from("<i", content, 33)[0]
    floats = struct.unpack_from("<Q", content, 37)[0]
    if ((actual_dim, actual_count, content[32], metric, floats) != (dimensions, count, 1, 0, dimensions * count)
            or len(content) != 45 + 4 * floats):
        raise ProviderError("index_invalid", "知识库索引的维度、条数或字节布局不匹配。")
    vectors = np.frombuffer(content, dtype="<f4", offset=45).reshape(count, dimensions)
    norms = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(vectors).all() or not np.all(np.abs(norms - 1.0) < 1e-4):
        raise ProviderError("index_invalid", "知识库包含无效或未归一化的向量。")
    try:
        import faiss
    except ImportError:
        return VectorIndex(vectors, None, "numpy_indexflatip")
    try:
        index = faiss.deserialize_index(np.frombuffer(content, dtype=np.uint8))
        return VectorIndex(vectors, index, "faiss")
    except Exception:
        raise ProviderError("index_invalid", "FAISS 无法载入已经校验的索引，未重新建库或降级检索。") from None


@lru_cache(maxsize=2)
def _cached_assets(index_path: str, metadata_path: str, manifest_path: str,
                   signatures: tuple) -> tuple[tuple[dict, ...], VectorIndex]:
    del signatures  # Included in the key to detect edits to the local snapshot.
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
        with Path(index_path).open("rb") as handle:
            content = handle.read(MAX_INDEX_BYTES + 1)
        with Path(metadata_path).open("rb") as handle:
            metadata_bytes = handle.read(b3.MAX_KNOWLEDGE_BYTES + 1)
        if len(content) > MAX_INDEX_BYTES or len(metadata_bytes) > b3.MAX_KNOWLEDGE_BYTES:
            raise ValueError("asset too large")
        index_info = manifest["index"]
        if (manifest["count"] != 705 or index_info["count"] != 705 or index_info["dimensions"] != 3072
                or hashlib.sha256(content).hexdigest() != index_info["sha256"]
                or hashlib.sha256(metadata_bytes).hexdigest() != manifest["metadata_sha256"]):
            raise ValueError("snapshot mismatch")
        records = b3.load_knowledge(Path(metadata_path))
        if len(records) != 705 or any(record.get("index_position") != index for index, record in enumerate(records)):
            raise ValueError("metadata order mismatch")
        return records, _decode_flat_index(content, 3072, 705)
    except ProviderError:
        raise
    except Exception:
        raise ProviderError("knowledge_unavailable", "知识库文件缺失、已改动或与索引不匹配；未调用 embedding。") from None


def _load_assets() -> tuple[tuple[dict, ...], VectorIndex]:
    try:
        paths = (b3.INDEX_PATH, b3.METADATA_PATH, b3.KNOWLEDGE_ROOT / "manifest.json")
        if paths[2].stat().st_size > 64 * 1024:
            raise ValueError("manifest too large")
        signatures = tuple((path.stat().st_mtime_ns, path.stat().st_size) for path in paths)
        return _cached_assets(*(str(path) for path in paths), signatures)
    except ProviderError:
        raise
    except Exception:
        raise ProviderError("knowledge_unavailable", "本地向量知识库尚不可用；未调用 embedding。") from None


def vector_retrieval_status() -> dict[str, Any]:
    """Inspect local files only. Configuration readiness is reported separately."""
    try:
        records, index = _load_assets()
        return {"available": True, "count": len(records), "dimensions": 3072,
                "method": "faiss_vector", "engine": index.engine, "embedding_called": False}
    except ProviderError as error:
        return {"available": False, "method": "faiss_vector", "error_code": error.code,
                "message": error.safe_message, "embedding_called": False}


def clear_query_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def _query_vector(description: str, snapshot: ConfigSnapshot) -> tuple[Any, bool, dict]:
    identity = model_provider.embedding_identity(snapshot)
    cache_key = hashlib.sha256(_CACHE_SALT + identity.encode() + b"\0" + description.encode("utf-8")).hexdigest()
    # Single-flight prevents two concurrent jobs paying for the same query twice.
    with _CACHE_LOCK:
        now = time.monotonic()
        cached = _CACHE.get(cache_key)
        if cached and now - cached[0] < CACHE_TTL_SECONDS:
            _CACHE.move_to_end(cache_key)
            return np.array(cached[1], dtype=np.float32), True, {}
        result = model_provider.embed_query(description, snapshot=snapshot)
        vector = np.asarray(result["vector"], dtype=np.float32)
        if vector.shape != (3072,) or not np.isfinite(vector).all():
            raise ProviderError("embedding_dimension_mismatch", "查询向量无效或维度不匹配。")
        norm = float(np.linalg.norm(vector))
        if not np.isfinite(norm) or norm <= 0:
            raise ProviderError("embedding_invalid", "查询 embedding 为无效的零向量；未执行检索。")
        vector = vector / norm
        _CACHE[cache_key] = (time.monotonic(), tuple(float(value) for value in vector))
        _CACHE.move_to_end(cache_key)
        while len(_CACHE) > MAX_CACHE_ENTRIES:
            _CACHE.popitem(last=False)
        return vector, False, result.get("usage", {})


def retrieve_vector_references(request: WorkflowRequest, *, snapshot: ConfigSnapshot | None = None) -> dict[str, Any]:
    result = {"enabled": request.rag_enabled, "method": "faiss_vector", "items": [],
              "excluded_count": 0, "corpus": "b3", "embedding_connected": False,
              "embedding_calls": 0, "cache_hit": False,
              "notice": "参考检索未启用；未调用 embedding。"}
    if not request.rag_enabled:
        return result
    records, index = _load_assets()
    dataset = load_tasks()
    if request.sample_id is not None and not any(item.get("sample_id") == request.sample_id for item in dataset):
        raise WorkflowReferenceNotFound("未找到当前数据集任务")
    excluded = _excluded_indices(records, request, dataset)
    config = snapshot if snapshot is not None else model_provider.get_config()
    query, cache_hit, usage = _query_vector(request.description, config)
    items = []
    seen_codes: set[str] = set()
    for position, score in index.rank(query):
        if position in excluded:
            continue
        record = records[position]
        code_key = _code_key(record)
        if not code_key or code_key in seen_codes:
            continue
        item = {**summarize_task(record), "id": record["sample_id"], "code": record["verified_verus"],
                "score": round(score, 6)}
        for field in ("source", "source_file", "source_snapshot_file", "source_url", "source_version",
                      "source_file_sha256", "license", "license_file"):
            item[field] = record.get(field, "Unspecified" if field == "license" else "")
        if len(json.dumps([*items, item], ensure_ascii=False, indent=2).encode()) > MAX_RETRIEVAL_CONTEXT_BYTES:
            continue
        items.append(item)
        seen_codes.add(code_key)
        if len(items) >= request.top_k:
            break
    return {**result, "items": items, "excluded_count": len(excluded), "engine": index.engine,
            "embedding_connected": True, "embedding_model": model_provider.EMBEDDING_MODEL,
            "dimensions": 3072, "embedding_calls": 0 if cache_hit else 1,
            "cache_hit": cache_hit, "embedding_usage": usage,
            "notice": "已使用真实查询向量与原有索引进行归一化内积检索；分数不是正确率。"
                      "已排除当前任务及可识别的文本/参考代码重复项，不保证消除所有语义近重复。"
                      "参考代码来自外部项目，未在本轮重新验证；修复不再次检索。"
                      + ("本次复用内存中的查询向量，未新增 embedding 请求。" if cache_hit else "本次调用 1 次查询 embedding。")}
