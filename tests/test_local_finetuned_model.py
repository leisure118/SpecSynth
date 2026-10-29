import pytest

from pathlib import Path
from types import SimpleNamespace

from apps.api.app.config import get_available_models
from engine.autospec.src.config_manager import ConfigLoader
from engine.llm_clients import qwencore
from engine import spectool_llm


CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "models_config.yaml"


def test_finetuned_model_is_selectable_and_resolves_endpoint(monkeypatch):
    monkeypatch.setenv("QWEN35_4B_API_BASE_URL", "http://model-gateway:8001/v1")
    config = ConfigLoader.get_model_config("qwen35-4b-ft", str(CONFIG_PATH))

    assert "qwen35-4b-ft" in get_available_models()
    assert config.model_name == "qwen35-4b-ft"
    assert config.base_url == "http://model-gateway:8001/v1"
    assert config.api_key == "EMPTY"
    assert config.params["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_mix64_model_has_independent_endpoint(monkeypatch):
    monkeypatch.setenv("QWEN35_9B_MIX64_API_BASE_URL", "http://model-gateway:8003/v1")
    config = ConfigLoader.get_model_config("qwen35-9b-mix64", str(CONFIG_PATH))

    assert "qwen35-9b-mix64" in get_available_models()
    assert config.model_name == "qwen35-9b-mix64"
    assert config.base_url == "http://model-gateway:8003/v1"
    assert config.api_key == "EMPTY"
    assert config.params["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_finetuned_chat_uses_adapter_name_and_disables_thinking(monkeypatch):
    monkeypatch.setenv("QWEN35_4B_API_BASE_URL", "http://model-gateway:8001/v1")
    requests = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            requests.append(("client", kwargs))
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            requests.append(("request", kwargs))
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="loop invariant i >= 0;"))],
                usage=SimpleNamespace(completion_tokens=7),
            )

    monkeypatch.setattr(qwencore, "OpenAI", FakeOpenAI)
    config = ConfigLoader.get_model_config("qwen35-4b-ft", str(CONFIG_PATH))
    client = qwencore.BaseChatClass(config=config, conversation_list=[
        {"role": "system", "content": "Generate ACSL"},
        {"role": "system", "content": ""},
    ])
    response, _ = client.get_respone("Generate an invariant")

    assert response == ["loop invariant i >= 0;"]
    assert requests[1][1]["model"] == "qwen35-4b-ft"
    assert requests[1][1]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert requests[1][1]["max_tokens"] == 1024
    assert requests[1][1]["messages"][0] == {"role": "system", "content": "Generate ACSL"}
    assert requests[1][1]["messages"][1]["role"] == "user"


def test_spectool_generation_uses_finetuned_adapter(monkeypatch):
    monkeypatch.setenv("QWEN35_4B_API_BASE_URL", "http://model-gateway:8001/v1")
    requests = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(
                    content='{"contract":"assigns \\\\nothing;\\nensures \\\\result >= a;","loop_specs":[],"notes":[]}'
                ))],
                usage=SimpleNamespace(total_tokens=42),
            )

    monkeypatch.setattr(spectool_llm, "OpenAI", FakeOpenAI)
    result = spectool_llm.generate_annotations(
        "int max2(int a, int b) { return a >= b ? a : b; }",
        "max2",
        "qwen35-4b-ft",
    )

    assert result["generation_mode"] == "llm"
    assert "ensures" in result["contract"]
    assert requests[0]["model"] == "qwen35-4b-ft"
    assert requests[0]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_termination_normalizes_wrapped_variant(monkeypatch):
    monkeypatch.setenv("QWEN35_4B_API_BASE_URL", "http://model-gateway:8001/v1")
    monkeypatch.setenv("TERMINATION_LLM_MODEL", "qwen35-4b-ft")
    from engine.termination.llmcore import _normalize_loop_variant

    assert _normalize_loop_variant("/*@ loop variant n - i; */") == "loop variant n - i;"
    assert _normalize_loop_variant("n - i") == "loop variant n - i;"


def test_finetuned_model_requires_deployment_endpoint(monkeypatch):
    monkeypatch.delenv("QWEN35_4B_API_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="QWEN35_4B_API_BASE_URL"):
        ConfigLoader.get_model_config("qwen35-4b-ft", str(CONFIG_PATH))
