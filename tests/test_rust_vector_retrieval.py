import json
import socket
import struct
from types import MappingProxyType

import numpy as np
import pytest

from engine.nl2verus import model_provider as provider, vector_retrieval as retrieval
from engine.nl2verus.workflow import WorkflowRequest, WorkflowReferenceNotFound


@pytest.fixture(autouse=True)
def isolated_no_network(monkeypatch):
    retrieval.clear_query_cache()
    def forbidden(*args, **kwargs):
        raise AssertionError("Vector tests must not call the network")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(provider, "_post_json", forbidden)
    yield
    retrieval.clear_query_cache()


@pytest.fixture
def snapshot():
    profile = provider.ModelProfile("text-embedding-3-large", "text-embedding-3-large",
                                    "https://api.linyinet.asia/v1/embeddings", "fixture-key", True,
                                    2048, 0, 42, 30)
    return provider.ConfigSnapshot(MappingProxyType({}), None, profile)


def record(identifier, description, code):
    return {"sample_id": identifier, "description": description, "verified_verus": code,
            "function_signature": "fn reference()", "category": "Simple", "source": "vest",
            "source_file": "rag_verus/code/tasks/vest_task_files/verified/reference.rs",
            "source_url": "https://github.com/secure-foundations/vest", "source_version": "recorded-version",
            "license": "MIT", "license_file": "licenses/vest-LICENSE"}


@pytest.fixture
def corpus(monkeypatch):
    records = tuple([record("alias", "Different wording", "TARGET CODE"),
                     record("same-text", "  SUM all values.\n", "SECOND TARGET CODE"),
                     record("one", "Count values", "REFERENCE ONE"),
                     record("duplicate", "Alternative count description", "REFERENCE ONE\r\n"),
                     record("two", "Sort values", "REFERENCE TWO"),
                     record("three", "Search values", "REFERENCE THREE")])
    class Index:
        engine = "mock_indexflatip"
        def rank(self, query):
            assert query.shape == (3072,) and np.isclose(np.linalg.norm(query), 1)
            return [(i, 1 - i * 0.1) for i in range(len(records))]
    monkeypatch.setattr(retrieval, "_load_assets", lambda: (records, Index()))
    monkeypatch.setattr(retrieval, "load_tasks", lambda: (record("target", "Sum all values.", "TARGET CODE"),))
    calls = []
    def embed(text, *, snapshot):
        calls.append(text)
        return {"vector": [2.0] + [0.0] * 3071, "usage": {"prompt_tokens": 6, "total_tokens": 6}}
    monkeypatch.setattr(provider, "embed_query", embed)
    return records, calls


def test_vector_excludes_answer_aliases_deduplicates_code_and_preserves_sources(corpus, snapshot):
    request = WorkflowRequest(description="Sum all values.", function_signature="fn must_not_embed()", sample_id="target", rag_enabled=True)
    result = retrieval.retrieve_vector_references(request, snapshot=snapshot)
    assert corpus[1] == ["Sum all values."]
    assert result["method"] == "faiss_vector" and result["embedding_calls"] == 1
    assert result["excluded_count"] == 2
    assert [item["sample_id"] for item in result["items"]] == ["one", "two", "three"]
    assert result["items"][0]["code"] == "REFERENCE ONE"
    assert result["items"][0]["source_url"].endswith("/vest")
    assert result["items"][0]["license"] == "MIT" and result["items"][0]["score"] == 0.8


def test_custom_input_alias_exclusion_and_top_k(corpus, snapshot):
    result = retrieval.retrieve_vector_references(WorkflowRequest(description="SUM all values.", rag_enabled=True, top_k=1), snapshot=snapshot)
    assert result["excluded_count"] == 2 and len(result["items"]) == 1
    assert result["items"][0]["sample_id"] == "one"


def test_disabled_rag_never_loads_config_index_or_embedding(monkeypatch):
    monkeypatch.setattr(retrieval, "_load_assets", lambda: pytest.fail("must not load assets"))
    monkeypatch.setattr(provider, "get_config", lambda: pytest.fail("must not load config"))
    result = retrieval.retrieve_vector_references(WorkflowRequest(description="Task"))
    assert not result["enabled"] and result["embedding_calls"] == 0


def test_unknown_task_fails_before_embedding(corpus, snapshot):
    with pytest.raises(WorkflowReferenceNotFound):
        retrieval.retrieve_vector_references(WorkflowRequest(description="Task", sample_id="missing", rag_enabled=True), snapshot=snapshot)
    assert corpus[1] == []


def test_cache_reuses_query_and_is_bounded_without_text(corpus, snapshot, monkeypatch):
    request = WorkflowRequest(description="private task one", rag_enabled=True)
    first = retrieval.retrieve_vector_references(request, snapshot=snapshot)
    second = retrieval.retrieve_vector_references(request, snapshot=snapshot)
    assert first["embedding_calls"] == 1 and second["embedding_calls"] == 0 and second["cache_hit"]
    assert len(corpus[1]) == 1 and "private task" not in repr(retrieval._CACHE)
    monkeypatch.setattr(retrieval, "MAX_CACHE_ENTRIES", 2)
    for text in ("private task two", "private task three"):
        retrieval.retrieve_vector_references(WorkflowRequest(description=text, rag_enabled=True), snapshot=snapshot)
    assert len(retrieval._CACHE) == 2
    third = retrieval.retrieve_vector_references(request, snapshot=snapshot)
    assert third["embedding_calls"] == 1


def test_expired_cache_requests_new_vector(corpus, snapshot, monkeypatch):
    request = WorkflowRequest(description="TTL task", rag_enabled=True)
    retrieval.retrieve_vector_references(request, snapshot=snapshot)
    monkeypatch.setattr(retrieval, "CACHE_TTL_SECONDS", -1)
    assert not retrieval.retrieve_vector_references(request, snapshot=snapshot)["cache_hit"]
    assert len(corpus[1]) == 2


def test_embedding_failure_never_silently_downgrades(corpus, snapshot, monkeypatch):
    def failure(*args, **kwargs):
        raise provider.ProviderError("provider_rate_limit", "Embedding unavailable")
    monkeypatch.setattr(provider, "embed_query", failure)
    with pytest.raises(provider.ProviderError) as caught:
        retrieval.retrieve_vector_references(WorkflowRequest(description="Task", rag_enabled=True), snapshot=snapshot)
    assert caught.value.code == "provider_rate_limit" and not retrieval._CACHE


def test_zero_vector_rejected(corpus, snapshot, monkeypatch):
    monkeypatch.setattr(provider, "embed_query", lambda *args, **kwargs: {"vector": [0.0] * 3072})
    with pytest.raises(provider.ProviderError) as caught:
        retrieval.retrieve_vector_references(WorkflowRequest(description="Task", rag_enabled=True), snapshot=snapshot)
    assert caught.value.code == "embedding_invalid"


def test_reference_context_budget_not_truncated(corpus, snapshot, monkeypatch):
    monkeypatch.setattr(retrieval, "MAX_RETRIEVAL_CONTEXT_BYTES", 1)
    result = retrieval.retrieve_vector_references(WorkflowRequest(description="Task", rag_enabled=True), snapshot=snapshot)
    assert result["items"] == []


def make_index(vectors):
    vectors = np.array(vectors, dtype="<f4")
    count, dimensions = vectors.shape
    header = bytearray(45)
    header[:4] = b"IxFI"
    struct.pack_into("<iq", header, 4, dimensions, count)
    header[32] = 1
    struct.pack_into("<iQ", header, 33, 0, count * dimensions)
    return bytes(header) + vectors.tobytes()


def test_safe_index_decoder_and_real_cosine_order():
    content = make_index([[1, 0], [0, 1], [-1, 0]])
    index = retrieval._decode_flat_index(content, 2, 3)
    assert index.rank(np.array([1, 0], dtype=np.float32)) == [(0, 1.0), (1, 0.0), (2, -1.0)]


@pytest.mark.parametrize("content", [b"raw-untrusted-file", make_index([[2, 0]]), make_index([[float("nan"), 0]]), make_index([[1, 0]])[:-1]])
def test_invalid_index_fails_without_rebuilding(content):
    with pytest.raises(provider.ProviderError):
        retrieval._decode_flat_index(content, 2, 1)


def test_bundled_snapshot_validates_without_any_api():
    status = retrieval.vector_retrieval_status()
    assert status["available"] and status["count"] == 705 and status["dimensions"] == 3072
    assert status["method"] == "faiss_vector" and not status["embedding_called"]
