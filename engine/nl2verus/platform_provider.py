"""Use explicit NL2Verus settings, or the platform's existing model configuration."""
import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import model_provider as original


@dataclass(repr=False)
class PlatformConfig:
    models: dict


def get_config():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / '.env', override=False)
    if os.environ.get('NL2VERUS_CONFIG') or original.SETTINGS_PATH.is_file():
        return original.get_config()
    from engine.autospec.src.config_manager import ConfigLoader
    from apps.api.app.config import get_available_models, MODELS_CONFIG_PATH
    models = {}
    for name in get_available_models():
        try:
            model = ConfigLoader.get_model_config(name, str(MODELS_CONFIG_PATH))
            if model.base_url and model.api_key:
                models[name] = model
        except (ValueError, OSError):
            continue
    return PlatformConfig(models)


def provider_status(*, snapshot=None):
    try:
        config = snapshot if snapshot is not None else get_config()
    except Exception:
        return {'generation_configured': False, 'embedding_configured': False, 'models': [],
                'message': '无法读取 Rust 模型配置。'}
    if not isinstance(config, PlatformConfig):
        return original.provider_status(snapshot=config)
    return {'generation_configured': bool(config.models), 'embedding_configured': False,
            'models': [{'id': key, 'name': value.model_name, 'label': value.model_name, 'configured': True}
                       for key, value in config.models.items()],
            'default_model_id': 'qwen-turbo' if 'qwen-turbo' in config.models else next(iter(config.models), None),
            'message': '使用平台现有模型配置；RAG 需要单独配置 NL2VERUS_CONFIG。'}


def generate_code(prompt, model_id, *, snapshot):
    if not isinstance(snapshot, PlatformConfig):
        return original.generate_code(prompt, model_id, snapshot=snapshot)
    from openai import OpenAI
    model = snapshot.models.get(model_id)
    if model is None:
        raise original.ProviderError('model_missing', '请选择已配置的模型。')
    try:
        with OpenAI(api_key=model.api_key, base_url=model.base_url, max_retries=0, timeout=120) as client:
            response = client.chat.completions.create(model=model.model_name,
                messages=[{'role': 'user', 'content': prompt}], temperature=0.1,
                max_tokens=4096, **({'extra_body': model.params['extra_body']} if model.params.get('extra_body') else {}))
        choice = response.choices[0]
        if choice.message.refusal or choice.finish_reason not in ('stop', 'length', None):
            raise ValueError('incomplete or refused response')
        code = (choice.message.content or '').strip()
        match = re.fullmatch(r'```(?:rust|verus)?\s*\n([\s\S]*?)\n```', code)
        if match:
            code = match.group(1).strip()
        if not code and choice.finish_reason != 'length':
            raise ValueError('empty response')
        if len(code.encode()) > original.MAX_CODE_BYTES or any(m.api_key and m.api_key in code for m in snapshot.models.values()):
            raise ValueError('invalid response')
        return {'code': code, 'model_id': model_id, 'model_name': model.model_name,
                'usage': original._usage(response.usage.model_dump() if response.usage else {}),
                'finish_reason': choice.finish_reason, 'output_token_limit': 4096}
    except Exception:
        raise original.ProviderError('provider_error', '模型调用失败；请检查配置、网络和额度，没有自动重试。') from None
