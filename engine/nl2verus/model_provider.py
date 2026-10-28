"""Opt-in provider boundary. Configuration and credentials never leave this module.

Status only inspects local configuration. Calls use one request, no redirects,
no SDK retry, and the original experiment's single user message. The approved
destination is deliberately an allowlist, not an arbitrary URL from a browser.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

import httpx
import yaml

from .verifier import MAX_CODE_BYTES, PROJECT_ROOT

SETTINGS_PATH = PROJECT_ROOT.parents[1] / "runtime" / "rust-settings.json"
AUTHORIZED_HOSTS = frozenset({"api.linyinet.asia"})
MAX_CONFIG_BYTES = 512 * 1024
MAX_PROMPT_BYTES = 512 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_TOKENS = 8192
MAX_REQUEST_SECONDS = 120
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}\Z")


class ProviderError(RuntimeError):
    """Only application-owned, non-sensitive messages may cross this boundary."""
    def __init__(self, code: str, safe_message: str, *, usage: Any = None):
        self.code = code
        self.safe_message = safe_message
        self.usage = _usage(usage)
        super().__init__(safe_message)


@dataclass(frozen=True, repr=False)
class ModelProfile:
    id: str
    name: str
    url: str
    key: str
    configured: bool
    output_token_limit: int
    temperature: float
    seed: int
    timeout_seconds: float
    is_thinking: bool = False
    reasoning_effort: str = "low"


@dataclass(frozen=True, repr=False)
class ConfigSnapshot:
    models: Mapping[str, ModelProfile]
    default_model_id: str | None
    embedding: ModelProfile | None


class _NoAliasesLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise yaml.YAMLError("YAML aliases are not supported")
        return super().compose_node(parent, index)


def _read_bounded(path: Path, limit: int) -> str:
    with path.open("rb") as handle:
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise ProviderError("config_invalid", "本地私有配置超过大小限制。")
    return content.decode("utf-8-sig")


def _number(value: Any, default: float, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        return default
    return max(minimum, min(maximum, float(value)))


def _identifier(value: Any, secrets: tuple[str, ...]) -> str | None:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or value.lower().startswith("sk-"):
        return None
    if any(secret and secret in value for secret in secrets):
        return None
    return value


def _endpoint(value: Any, operation: str) -> str:
    """Accept either an approved HTTPS API base or its complete endpoint."""
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("invalid endpoint")
    parsed = urlsplit(value.strip())
    if (parsed.scheme != "https" or parsed.hostname not in AUTHORIZED_HOSTS
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443)):
        raise ValueError("unapproved endpoint")
    path = parsed.path.rstrip("/")
    suffix = "/chat/completions" if operation == "generation" else "/embeddings"
    if path.endswith(("/chat/completions", "/embeddings")):
        if not path.endswith(suffix):
            raise ValueError("wrong endpoint type")
    else:
        path = (path or "/v1") + suffix
    return urlunsplit(("https", parsed.netloc, path, "", ""))


def get_config() -> ConfigSnapshot:
    """Read an immutable per-run snapshot; do not serialize this private object."""
    try:
        configured_path = os.environ.get("NL2VERUS_CONFIG", "").strip()
        settings: dict = {}
        if not configured_path:
            if not SETTINGS_PATH.is_file():
                raise ProviderError("config_missing", "尚未指定本地私有模型配置。")
            settings = json.loads(_read_bounded(SETTINGS_PATH, 16 * 1024))
            if not isinstance(settings, dict):
                raise ValueError("invalid settings")
            configured_path = settings.get("config_path", "")
        if not isinstance(configured_path, str) or not configured_path.strip():
            raise ProviderError("config_missing", "尚未指定本地私有模型配置。")
        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        config = yaml.load(_read_bounded(path, MAX_CONFIG_BYTES), Loader=_NoAliasesLoader)
        if not isinstance(config, dict):
            raise ValueError("invalid mapping")
        raw_models = config.get("models", {})
        raw_embedding = config.get("embedding", {})
        generation = config.get("generation", {})
        if not all(isinstance(value, dict) for value in (raw_models, raw_embedding, generation)):
            raise ValueError("invalid sections")
        if len(raw_models) + len(raw_embedding) > 128:
            raise ValueError("too many profiles")
        all_profiles = [value for value in [*raw_models.values(), *raw_embedding.values()] if isinstance(value, dict)]
        secrets = tuple(value["api_key"] for value in all_profiles if isinstance(value.get("api_key"), str))

        def profile(model_id: Any, raw: Any, operation: str) -> ModelProfile | None:
            if not isinstance(raw, dict):
                return None
            identity = _identifier(model_id, secrets)
            name = _identifier(raw.get("model_name", model_id), secrets)
            if not identity or not name:
                return None
            # Never put an embedding-only profile in the generation selector.
            if operation == "generation" and (name.startswith("text-embedding-") or raw.get("embedding_dim")):
                return None
            key = raw.get("api_key", "")
            key = key.strip() if isinstance(key, str) else ""
            if not key and isinstance(raw.get("api_key_env"), str):
                key = os.environ.get(raw["api_key_env"], "").strip()
            if len(key) > 4096 or any(char in key for char in "\r\n"):
                key = ""
            try:
                url = _endpoint(raw.get("base_url") or raw.get("api_base") or raw.get("url"), operation)
            except (ValueError, TypeError):
                url = ""
            thinking = raw.get("is_thinking") is True
            budget_key = "thinking_max_tokens" if thinking else "chat_max_tokens"
            budget = int(_number(generation.get(budget_key, 2048), 2048, 1, MAX_OUTPUT_TOKENS))
            budget = min(budget, int(_number(generation.get("max_tokens_cap", MAX_OUTPUT_TOKENS), MAX_OUTPUT_TOKENS, 1, MAX_OUTPUT_TOKENS)))
            effort = raw.get("reasoning_effort", "low")
            if effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
                effort = "low"
            timeout = _number(raw.get("timeout", generation.get("timeout", 90)), 90, 5, MAX_REQUEST_SECONDS)
            return ModelProfile(identity, name, url, key, bool(url and key), budget,
                                _number(generation.get("temperature", 0), 0, 0, 2),
                                int(_number(generation.get("seed", 42), 42, 0, 2**31 - 1)),
                                min(timeout, 45) if operation == "embedding" else timeout,
                                thinking, effort)

        models = {key: parsed for key, raw in raw_models.items()
                  if (parsed := profile(key, raw, "generation")) is not None}
        embedding_raw = raw_embedding.get(EMBEDDING_MODEL) or raw_models.get(EMBEDDING_MODEL)
        embedding = profile(EMBEDDING_MODEL, embedding_raw, "embedding")
        if (embedding and (embedding.name != EMBEDDING_MODEL or
                embedding_raw.get("embedding_dim", EMBEDDING_DIMENSIONS) != EMBEDDING_DIMENSIONS)):
            embedding = None
        default = config.get("default_model_id") or generation.get("default_model_id") or settings.get("default_model_id")
        available = [identity for identity, item in models.items() if item.configured]
        if default not in available:
            default = "gpt-5.4-mini" if "gpt-5.4-mini" in available else next(iter(available), None)
        return ConfigSnapshot(MappingProxyType(models), default, embedding)
    except ProviderError:
        raise
    except Exception:
        # YAML errors can contain raw secret-bearing source lines. Never include them.
        raise ProviderError("config_invalid", "无法读取本地私有模型配置，请在本机检查文件格式与权限。") from None


def provider_status(*, snapshot: ConfigSnapshot | None = None) -> dict[str, Any]:
    """Local readiness, not a provider authentication or network health probe."""
    base = {"models": [], "default_model_id": None, "generation_configured": False,
            "embedding_configured": False, "connectivity_verified": False, "model_called": False,
            "output_token_cap": MAX_OUTPUT_TOKENS, "implicit_retries": 0}
    try:
        config = snapshot if snapshot is not None else get_config()
    except ProviderError as error:
        return {**base, "message": error.safe_message, "error_code": error.code}
    models = [{"id": item.id, "name": item.name,
               "label": item.name if item.id == item.name else f"{item.name}（配置：{item.id}）",
               "configured": item.configured, "output_token_limit": item.output_token_limit}
              for item in config.models.values()]
    return {**base, "models": models, "default_model_id": config.default_model_id,
            "generation_configured": any(item.configured for item in config.models.values()),
            "embedding_configured": bool(config.embedding and config.embedding.configured),
            "embedding_model": EMBEDDING_MODEL, "embedding_dimensions": EMBEDDING_DIMENSIONS,
            "message": "已读取本地配置；配置就绪不代表密钥、额度或网络已通过实际调用验证。"}


def _post_json(profile: ModelProfile, payload: dict[str, Any]) -> dict[str, Any]:
    if not profile.configured:
        raise ProviderError("provider_unconfigured", "所选模型配置不完整，或服务地址未获授权。")
    # Revalidate even injected snapshots; credentials never follow redirects/proxies.
    operation = "embedding" if profile.name == EMBEDDING_MODEL else "generation"
    try:
        _endpoint(profile.url, operation)
    except ValueError:
        raise ProviderError("provider_unconfigured", "模型服务地址未获授权。") from None
    started = time.monotonic()
    try:
        with httpx.Client(timeout=httpx.Timeout(profile.timeout_seconds, connect=min(10, profile.timeout_seconds)),
                          follow_redirects=False, trust_env=False) as client:
            with client.stream("POST", profile.url, json=payload,
                               headers={"Authorization": f"Bearer {profile.key}", "Accept-Encoding": "identity"}) as response:
                status = response.status_code
                if not 200 <= status < 300:
                    if status in (401, 403):
                        raise ProviderError("provider_auth", "模型服务拒绝认证，请检查本地凭据与权限。")
                    if status == 429:
                        raise ProviderError("provider_rate_limit", "模型服务额度不足或触发限流；未自动重试。")
                    raise ProviderError("provider_http_error", f"模型服务返回 HTTP {status}；未自动重试。")
                if response.headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
                    raise ProviderError("provider_response_invalid", "模型服务返回不支持的压缩响应。")
                content = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise ProviderError("provider_response_too_large", "模型响应超过大小限制。")
                    if time.monotonic() - started > profile.timeout_seconds:
                        raise ProviderError("provider_timeout", "模型服务调用超时；未自动重试。")
                    content.extend(chunk)
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("response must be object")
        return data
    except ProviderError:
        raise
    except httpx.TimeoutException:
        raise ProviderError("provider_timeout", "模型服务调用超时；未自动重试。") from None
    except httpx.HTTPError:
        raise ProviderError("provider_network", "无法连接模型服务；未自动重试。") from None
    except Exception:
        raise ProviderError("provider_response_invalid", "模型服务未返回有效的结构化响应。") from None


def _usage(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {key: item for key in ("prompt_tokens", "completion_tokens", "total_tokens")
            if type(item := value.get(key)) is int and 0 <= item <= 10**9}


def generate_code(prompt: str, model_id: str, *, snapshot: ConfigSnapshot | None = None) -> dict[str, Any]:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ProviderError("prompt_invalid", "生成提示词为空或超过 512 KiB 限制。")
    config = snapshot if snapshot is not None else get_config()
    profile = config.models.get(model_id)
    if profile is None:
        raise ProviderError("model_unknown", "所选模型不在本地配置中。")
    payload = {"model": profile.name, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": profile.output_token_limit, "temperature": profile.temperature,
               "seed": profile.seed, "n": 1}
    if profile.is_thinking:
        payload["reasoning_effort"] = profile.reasoning_effort
    data = _post_json(profile, payload)
    usage = _usage(data.get("usage"))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ProviderError("model_response_invalid", "模型响应缺少代码候选。", usage=usage)
    choice = choices[0]
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("refusal"):
        raise ProviderError("model_refused", "模型未提供可用代码。", usage=usage)
    finish = choice.get("finish_reason")
    if finish not in ("stop", "length", None):
        raise ProviderError("model_incomplete", "模型响应未正常结束，未将其当作完整代码。", usage=usage)
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(item.get("text", "") for item in content
                          if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str))
    # reasoning_content is intentionally not treated as generated code.
    # Preserve paid partial output and usage. The runner must stop on "length"
    # before verification/repair; an empty truncated body is also useful evidence.
    if finish == "length" and content is None:
        content = ""
    if not isinstance(content, str) or (not content.strip() and finish != "length"):
        raise ProviderError("model_empty", "模型没有返回代码正文；推理文本不作为代码。", usage=usage)
    code = content.strip()
    fenced = re.fullmatch(r"```(?:rust|verus)?\s*\n([\s\S]*?)\n```", code)
    if fenced:
        code = fenced.group(1).strip()
    if (not code and finish != "length") or len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise ProviderError("model_code_invalid", "模型代码为空或超过 256 KiB 限制。", usage=usage)
    private_profiles = [*config.models.values(), *([config.embedding] if config.embedding else [])]
    if any(item.key and item.key in code for item in private_profiles):
        raise ProviderError("model_sensitive_output", "模型响应包含敏感配置内容，已阻止显示。", usage=usage)
    return {"code": code, "model_id": profile.id, "model_name": profile.name,
            "usage": usage, "finish_reason": finish or "unknown",
            "output_token_limit": profile.output_token_limit}


def embedding_identity(snapshot: ConfigSnapshot) -> str:
    profile = snapshot.embedding
    if not profile or not profile.configured:
        raise ProviderError("embedding_unconfigured", "匹配现有索引的查询 embedding 尚未配置；不会降级为关键词检索。")
    return hashlib.sha256((profile.url + "\0" + profile.key + "\0" + profile.name).encode()).hexdigest()


def embed_query(text: str, *, snapshot: ConfigSnapshot | None = None) -> dict[str, Any]:
    config = snapshot if snapshot is not None else get_config()
    embedding_identity(config)
    if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 24 * 1024:
        raise ProviderError("embedding_input_invalid", "查询文本为空或超过 24 KiB 限制；未自动裁剪原任务。")
    data = _post_json(config.embedding, {"model": EMBEDDING_MODEL, "input": [text],
                                      "dimensions": EMBEDDING_DIMENSIONS, "encoding_format": "float"})
    values = data.get("data")
    if (not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict)
            or values[0].get("index") != 0):
        raise ProviderError("embedding_response_invalid", "Embedding 服务返回的向量数量或编号不正确。")
    vector = values[0].get("embedding")
    if (not isinstance(vector, list) or len(vector) != EMBEDDING_DIMENSIONS
            or any(isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) for value in vector)):
        raise ProviderError("embedding_dimension_mismatch", "查询向量无效或不是现有索引所需的 3072 维；未执行检索。")
    if data.get("model") not in (None, EMBEDDING_MODEL):
        raise ProviderError("embedding_model_mismatch", "Embedding 服务报告的模型与现有索引配置不一致。")
    return {"vector": vector, "model": EMBEDDING_MODEL, "usage": _usage(data.get("usage"))}
