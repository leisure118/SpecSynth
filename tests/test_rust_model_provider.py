"""All transport is mocked. These tests must never spend provider credit."""
import dataclasses
import json
import socket

import httpx
import pytest
import yaml

from engine.nl2verus import model_provider as provider


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("External network is forbidden in provider tests")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture
def private_config(tmp_path, monkeypatch):
    # Synthetic credentials only; no test reads the user's private configuration.
    data = {"models": {
        "gpt-5.4-mini": {"model_name": "gpt-5.4-mini", "api_key": "fixture-private-key",
                         "base_url": "https://api.linyinet.asia/v1/chat/completions"},
        "deepseek-v4-flash": {"model_name": "gpt-5.4-mini", "api_key": "fixture-private-key",
                              "base_url": "https://api.linyinet.asia/v1"},
        "thinking": {"model_name": "thinking", "api_key": "fixture-private-key",
                     "base_url": "https://api.linyinet.asia/v1", "is_thinking": True},
    }, "embedding": {provider.EMBEDDING_MODEL: {
        "model_name": provider.EMBEDDING_MODEL, "api_key": "fixture-embedding-key",
        "base_url": "https://api.linyinet.asia/v1/embeddings", "embedding_dim": 3072}},
        "generation": {"chat_max_tokens": 2048, "thinking_max_tokens": 128000,
                       "max_tokens_cap": 128000, "temperature": 0, "seed": 42}}
    path = tmp_path / "private.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("NL2VERUS_CONFIG", str(path))
    return data, path


def rewrite(private_config):
    data, path = private_config
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def mock_transport(monkeypatch, handler):
    client_class = httpx.Client
    options = []
    def client(**kwargs):
        options.append(kwargs)
        return client_class(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr(provider.httpx, "Client", client)
    return options


def completion(code="verus! { fn main() {} }", **updates):
    return {"choices": [{"message": {"content": code}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}, **updates}


def test_status_safe_local_alias_and_budget(private_config, monkeypatch):
    monkeypatch.setattr(provider, "_post_json", lambda *args: pytest.fail("status must not send requests"))
    status = provider.provider_status()
    assert status["generation_configured"] and status["embedding_configured"]
    assert not status["connectivity_verified"] and not status["model_called"]
    assert status["default_model_id"] == "gpt-5.4-mini"
    alias = next(model for model in status["models"] if model["id"] == "deepseek-v4-flash")
    assert alias["name"] == "gpt-5.4-mini" and "配置：deepseek-v4-flash" in alias["label"]
    assert status["models"][0]["output_token_limit"] == 2048
    assert status["models"][2]["output_token_limit"] == 8192
    safe = json.dumps(status)
    for prohibited in ("fixture-private-key", "fixture-embedding-key", "api.linyinet.asia", str(private_config[1])):
        assert prohibited not in safe


def test_config_snapshot_frozen_and_does_not_reread(private_config, monkeypatch):
    snapshot = provider.get_config()
    assert "fixture-private-key" not in repr(snapshot)
    assert "fixture-private-key" not in repr(snapshot.models["gpt-5.4-mini"])
    with pytest.raises(TypeError):
        snapshot.models["new"] = None
    with pytest.raises(dataclasses.FrozenInstanceError):
        snapshot.models["gpt-5.4-mini"].key = "new"
    private_config[1].write_text("invalid: [", encoding="utf-8")
    assert provider.provider_status(snapshot=snapshot)["generation_configured"]
    calls = []
    monkeypatch.setattr(provider, "_post_json", lambda profile, payload: calls.append(payload) or completion())
    assert provider.generate_code("EXACT\nPROMPT", "gpt-5.4-mini", snapshot=snapshot)["code"]
    assert calls[0]["messages"] == [{"role": "user", "content": "EXACT\nPROMPT"}]


def test_env_precedes_settings_and_settings_fallback(private_config, monkeypatch, tmp_path):
    settings = tmp_path / "local-settings.json"
    settings.write_text(json.dumps({"config_path": str(private_config[1])}), encoding="utf-8")
    monkeypatch.setattr(provider, "SETTINGS_PATH", settings)
    monkeypatch.delenv("NL2VERUS_CONFIG")
    assert provider.provider_status()["generation_configured"]
    monkeypatch.setenv("NL2VERUS_CONFIG", str(tmp_path / "missing"))
    result = provider.provider_status()
    assert not result["generation_configured"] and result["error_code"] == "config_invalid"
    assert str(tmp_path) not in result["message"]


@pytest.mark.parametrize("bad", ["https://unapproved.example/v1", "http://api.linyinet.asia/v1",
                                   "https://user:password@api.linyinet.asia/v1",
                                   "https://api.linyinet.asia/v1?key=private", "https://api.linyinet.asia:444/v1"])
def test_unapproved_endpoints_not_configured(private_config, bad):
    private_config[0]["models"]["gpt-5.4-mini"]["base_url"] = bad
    rewrite(private_config)
    status = provider.provider_status()
    assert status["models"][0]["configured"] is False
    assert bad not in json.dumps(status)


@pytest.mark.parametrize("text", ["models: [fixture-private-key", "a: &anchor {x: 1}\nmodels: *anchor", "[]"])
def test_config_errors_do_not_echo_source(private_config, text):
    private_config[1].write_text(text, encoding="utf-8")
    result = provider.provider_status()
    assert result["error_code"] == "config_invalid"
    assert "fixture-private-key" not in json.dumps(result)


def test_no_models_invented_and_credential_as_model_name_hidden(private_config):
    private_config[0]["models"] = {"fixture-private-key": {"model_name": "fixture-private-key", "api_key": "fixture-private-key"}}
    rewrite(private_config)
    assert provider.provider_status()["models"] == []
    with pytest.raises(provider.ProviderError, match="不在本地配置"):
        provider.generate_code("prompt", "imaginary-model")


def test_original_payload_alias_and_full_or_base_url(private_config, monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=completion("```rust\nfn main() {}\n```"))
    options = mock_transport(monkeypatch, handler)
    result = provider.generate_code("Original prompt\n", "deepseek-v4-flash")
    body = json.loads(requests[0].content)
    assert body == {"model": "gpt-5.4-mini", "messages": [{"role": "user", "content": "Original prompt\n"}],
                    "max_tokens": 2048, "temperature": 0, "seed": 42, "n": 1}
    assert str(requests[0].url).endswith("/v1/chat/completions")
    assert result["code"] == "fn main() {}" and result["model_id"] == "deepseek-v4-flash"
    assert options[0]["follow_redirects"] is False and options[0]["trust_env"] is False


@pytest.mark.parametrize("status,expected", [(302, "provider_http_error"), (401, "provider_auth"),
                                             (429, "provider_rate_limit"), (500, "provider_http_error")])
def test_http_error_safe_without_retry(private_config, monkeypatch, status, expected):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(status, text="fixture-private-key raw-provider-error", headers={"location": "https://other.example"})
    mock_transport(monkeypatch, handler)
    with pytest.raises(provider.ProviderError) as caught:
        provider.generate_code("prompt", "gpt-5.4-mini")
    assert caught.value.code == expected and len(requests) == 1
    assert "fixture-private-key" not in str(caught.value)


def test_network_timeout_and_response_bound(private_config, monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("fixture-private-key", request=request)
    mock_transport(monkeypatch, handler)
    with pytest.raises(provider.ProviderError) as caught:
        provider.generate_code("prompt", "gpt-5.4-mini")
    assert caught.value.code == "provider_timeout" and "fixture-private-key" not in str(caught.value)


def test_bounded_response_stream(private_config, monkeypatch):
    monkeypatch.setattr(provider, "MAX_RESPONSE_BYTES", 32)
    mock_transport(monkeypatch, lambda request: httpx.Response(200, content=b"x" * 100))
    with pytest.raises(provider.ProviderError) as caught:
        provider.generate_code("prompt", "gpt-5.4-mini")
    assert caught.value.code == "provider_response_too_large"


@pytest.mark.parametrize("data,expected", [
    ({}, "model_response_invalid"),
    ({"choices": [{"message": {"reasoning_content": "fn main() {}"}, "finish_reason": "stop"}]}, "model_empty"),
    (completion("fixture-private-key"), "model_sensitive_output"),
    ({"choices": [{"message": {"content": "", "refusal": "private error"}, "finish_reason": "stop"}]}, "model_refused"),
])
def test_response_rejection_without_reasoning_fallback(private_config, monkeypatch, data, expected):
    monkeypatch.setattr(provider, "_post_json", lambda *args: data)
    with pytest.raises(provider.ProviderError) as caught:
        provider.generate_code("prompt", "gpt-5.4-mini")
    assert caught.value.code == expected


def test_usage_only_safe_integers_and_thinking_budget(private_config, monkeypatch):
    calls = []
    def post(profile, payload):
        calls.append(payload)
        return completion(usage={"prompt_tokens": 10, "completion_tokens": "private", "total_tokens": True,
                                 "provider_secret": "fixture-private-key"})
    monkeypatch.setattr(provider, "_post_json", post)
    result = provider.generate_code("prompt", "thinking")
    assert result["usage"] == {"prompt_tokens": 10}
    assert calls[0]["max_tokens"] == 8192 and calls[0]["reasoning_effort"] == "low"


@pytest.mark.parametrize("content", ["fn partial(", "", None])
def test_length_preserves_paid_partial_code_and_usage(private_config, monkeypatch, content):
    data = {"choices": [{"message": {"content": content, "reasoning_content": "not candidate code"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 2048, "total_tokens": 2098}}
    calls = []
    monkeypatch.setattr(provider, "_post_json", lambda *args: calls.append(args) or data)
    result = provider.generate_code("prompt", "gpt-5.4-mini")
    assert result["code"] == (content or "") and result["finish_reason"] == "length"
    assert result["usage"] == data["usage"] and len(calls) == 1


def test_refusal_retains_safe_usage_without_raw_response(private_config, monkeypatch):
    data = {"choices": [{"message": {"refusal": "fixture-private-key"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 80, "unsafe": "fixture-private-key"}}
    monkeypatch.setattr(provider, "_post_json", lambda *args: data)
    with pytest.raises(provider.ProviderError) as caught:
        provider.generate_code("prompt", "gpt-5.4-mini")
    assert caught.value.usage == {"total_tokens": 80}
    assert "fixture-private-key" not in str(caught.value)


def test_default_selects_only_configured_model(private_config):
    private_config[0]["models"]["gpt-5.4-mini"]["api_key"] = ""
    private_config[0]["default_model_id"] = "gpt-5.4-mini"
    rewrite(private_config)
    status = provider.provider_status()
    assert status["default_model_id"] == "deepseek-v4-flash"
    for model in private_config[0]["models"].values():
        model["api_key"] = ""
    rewrite(private_config)
    assert provider.provider_status()["default_model_id"] is None


def test_embedding_exact_query_and_dimension(private_config, monkeypatch):
    calls = []
    def post(profile, payload):
        calls.append(payload)
        return {"data": [{"index": 0, "embedding": [1.0] + [0.0] * 3071}], "model": provider.EMBEDDING_MODEL,
                "usage": {"prompt_tokens": 5, "total_tokens": 5}}
    monkeypatch.setattr(provider, "_post_json", post)
    result = provider.embed_query("Exact NL\n")
    assert len(result["vector"]) == 3072
    assert calls == [{"model": provider.EMBEDDING_MODEL, "input": ["Exact NL\n"], "dimensions": 3072, "encoding_format": "float"}]


@pytest.mark.parametrize("vector", [[1.0], [float("nan")] * 3072, [True] * 3072])
def test_embedding_bad_vector_rejected(private_config, monkeypatch, vector):
    monkeypatch.setattr(provider, "_post_json", lambda *args: {"data": [{"index": 0, "embedding": vector}]})
    with pytest.raises(provider.ProviderError) as caught:
        provider.embed_query("query")
    assert caught.value.code == "embedding_dimension_mismatch"


def test_wrong_embedding_model_not_configured(private_config):
    private_config[0]["embedding"][provider.EMBEDDING_MODEL]["model_name"] = "text-embedding-ada-002"
    rewrite(private_config)
    assert not provider.provider_status()["embedding_configured"]
