import os
from pathlib import Path
import pytest
from engine.autospec.src.config_manager import ConfigLoader
from engine.nl2verus.dsh_cli import patch_for
CONFIG=Path(__file__).resolve().parents[1]/'configs/models_config.yaml'
@pytest.fixture(autouse=True)
def isolate_loader(monkeypatch):
 monkeypatch.setattr(ConfigLoader,'_templates',{})
 monkeypatch.setattr(ConfigLoader,'_model_map',{})

def test_bailian_main_model_uses_backend_key_and_explicit_endpoint(monkeypatch,tmp_path):
 monkeypatch.setenv('aliyun_API_KEY','private-test-key')
 monkeypatch.setenv('BAILIAN_DEEPSEEK_BASE_URL','https://test-workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1')
 cfg=ConfigLoader.get_model_config('deepseek-v4.1-flash-1017',str(CONFIG))
 assert cfg.model_name=='deepseek-v4.1-flash-1017' and cfg.api_key=='private-test-key'
 child={'model':'qwen35-4b-mix64','base_url':'http://sub.internal/v1','api_key':'child-key'}
 patch=patch_for({'model':cfg.model_name,'base_url':cfg.base_url,'api_key':cfg.api_key},tmp_path,child)
 providers=next(p for p in patch if p.get('id')=='llm-pi-ai')['config']['providers']
 assert providers['platform-api']['baseURL']==cfg.base_url
 assert providers['platform-subagent']['baseURL']==child['base_url']
 assert providers['platform-subagent']['models'][0]['id']=='qwen35-4b-mix64'
 assert 'private-test-key' not in str(patch) and 'child-key' not in str(patch)

def test_bailian_endpoint_defaults_to_documented_beijing_service(monkeypatch):
 monkeypatch.delenv('BAILIAN_DEEPSEEK_BASE_URL',raising=False)
 monkeypatch.setenv('aliyun_API_KEY','test')
 cfg=ConfigLoader.get_model_config('deepseek-v4.1-flash-1017',str(CONFIG))
 assert cfg.base_url=='https://dashscope.aliyuncs.com/compatible-mode/v1'
 assert cfg.model_name=='deepseek-v4.1-flash-1017'
