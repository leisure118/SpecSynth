import json
from contextlib import nullcontext
from types import SimpleNamespace
import httpx
import pytest
from acsl.adapters import agent_runtime
from engine.verification import subagent_api
from engine.nl2verus.model_provider import ProviderError

FILES=[{'path':'main.c','content':'int main(){return 0;}'}]

@pytest.mark.parametrize('agent',['codex','claude-code'])
def test_selected_child_used_once_and_repair_uses_existing_candidate(monkeypatch,tmp_path,agent):
    from engine import c_agent_cli,cli_model_transport
    from engine.autospec.src.config_manager import ConfigLoader
    monkeypatch.setattr(agent_runtime,'get_available_models',lambda:['main'])
    monkeypatch.setattr(ConfigLoader,'get_model_config',lambda name,*a:SimpleNamespace(model_name=name,base_url='https://example.invalid/v1',api_key='private'))
    monkeypatch.setattr(cli_model_transport,'model_route',lambda profile,**kw:nullcontext(profile))
    workers=[];runs=[]
    monkeypatch.setattr(subagent_api,'generate_specifications',lambda prompt,profile,*a:workers.append(profile['model']) or FILES)
    monkeypatch.setattr(c_agent_cli,'generate',lambda *a,**kw:runs.append(kw['subagent_candidate']) or {'files':FILES})
    agent_runtime._generate(agent,'task',tmp_path,200,'main','qwen35-4b-mix64')
    agent_runtime._generate(agent,'task\nPrevious candidate:\n'+json.dumps(FILES)+'\nVerifier diagnostics:\nfailed',tmp_path,200,'main','qwen35-4b-mix64')
    assert workers==['qwen35-4b-mix64']
    assert runs==[FILES,FILES]

@pytest.mark.parametrize('scenario',['success','length','changed_source','http_error'])
def test_api_worker_validates_candidate_and_redacts_secrets(monkeypatch,tmp_path,scenario):
    client=httpx.Client
    def respond(request):
        assert request.headers['authorization']=='Bearer secret-test-key'
        body=json.loads(request.content)
        assert body['model']=='qwen35-9b-mix64'
        files=FILES if scenario!='changed_source' else [{'path':'main.c','content':'int main(){return 1;}'}]
        return httpx.Response(503 if scenario=='http_error' else 200,json={'choices':[{'finish_reason':'length' if scenario=='length' else 'stop','message':{'content':json.dumps({'files':files})}}]})
    monkeypatch.setattr(subagent_api.httpx,'Client',lambda **kwargs:client(transport=httpx.MockTransport(respond),**kwargs))
    prompt='Original source:\n'+json.dumps(FILES)
    profile={'model':'qwen35-9b-mix64','base_url':'https://example.invalid/v1','api_key':'secret-test-key'}
    if scenario=='success':assert subagent_api.generate_specifications(prompt,profile,tmp_path,10)==FILES
    else:
        with pytest.raises(ProviderError):subagent_api.generate_specifications(prompt,profile,tmp_path,10)
    assert 'secret-test-key' not in ''.join(p.read_text() for p in tmp_path.iterdir())
    assert json.loads((tmp_path/'subagent-runtime.json').read_text())['status']==('completed' if scenario=='success' else 'failed')
