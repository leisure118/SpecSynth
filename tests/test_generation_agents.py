"""Agent contracts: API-only credentials, protocol compatibility and real tools."""
import json
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from engine.nl2verus import agents, profiles
from apps.api.app import rust

GOOD='use vstd::prelude::*;\nverus! { fn inc(x:u64)->(r:u64) requires x<100, ensures r==x+1, {x+1} }'

@pytest.fixture
def configured(tmp_path,monkeypatch):
    monkeypatch.setattr(profiles,'PROFILES_PATH',tmp_path/'profiles.json')
    monkeypatch.setattr(profiles,'legacy_profiles',lambda snapshot=None:{})
    monkeypatch.setattr(agents.provider,'provider_status',lambda **k:{'embedding_configured':False})
    return {'id':'test','name':'Test','model':'test-model','base_url':'https://models.example/v1','api_key':'secret-api-key','protocol':'chat'}


def test_model_write_only_and_preserve_key(configured):
    app=FastAPI();app.include_router(rust.router);client=TestClient(app)
    response=client.post('/api/v1/rust/models',json=configured)
    assert response.status_code==200
    assert 'secret-api-key' not in response.text and 'api_key' not in response.json()
    assert 'secret-api-key' not in client.get('/api/v1/rust/models').text
    assert profiles.PROFILES_PATH.stat().st_mode & 0o077 == 0
    missing=dict(configured);missing.pop('model')
    rejected=client.post('/api/v1/rust/models',json=missing)
    assert rejected.status_code==422 and 'secret-api-key' not in rejected.text
    assert client.post('/api/v1/rust/models',json=configured,headers={'Origin':'https://other.example'}).status_code==403
    assert client.post('/api/v1/rust/models',content=json.dumps(configured),headers={'Content-Type':'text/plain'}).status_code==415
    configured['api_key']='';configured['name']='Renamed'
    assert client.post('/api/v1/rust/models',json=configured).status_code==200
    assert profiles.configured_profiles()['test']['api_key']=='secret-api-key'
    configured['base_url']='https://user:password@example.com/v1'
    assert client.post('/api/v1/rust/models',json=configured).status_code==422


def test_protocol_rejected_before_call(configured):
    profiles.save_profile(configured)
    agents.validate_selection('deepseek-harness','test',[])
    with pytest.raises(ValueError):agents.validate_selection('codex','test',[])
    with pytest.raises(ValueError):agents.validate_selection('direct','test',['missing'])
    with pytest.raises(ValueError):agents.validate_selection('direct','test',['verus-proof','verus-proof'])


def test_skills_frozen_and_applied(configured,monkeypatch):
    profiles.save_profile(configured)
    snapshot=agents.snapshot_skills(['verus-contracts'])
    seen=[]
    monkeypatch.setattr(agents,'_chat_generate',lambda prompt,*a:seen.append(prompt) or {'code':GOOD})
    class Runner:
        def __init__(self,**kw):self.kw=kw
    runner=agents.make_runner({'agent_id':'direct','model_id':'test','managed_profile':True,'skill_snapshot':snapshot,'model_profile':profiles.public_profile(configured)},Runner)
    agents.SKILLS['verus-contracts']['content']+=' changed'
    try:
        result=runner.kw['generate']('TASK','test',snapshot=None)
        assert snapshot[0]['content'] in seen[0] and ' changed' not in seen[0]
        assert result['effective_prompt']==seen[0]
    finally:agents.SKILLS['verus-contracts']['content']=agents.SKILLS['verus-contracts']['content'].removesuffix(' changed')
    configured['model']='another-model';profiles.save_profile(configured)
    with pytest.raises(ValueError,match='变更'):
        agents.make_runner({'agent_id':'direct','model_id':'test','managed_profile':True,'model_profile':{'wrong':'snapshot'}},Runner)


def test_harness_actually_calls_verus_tool(configured,monkeypatch):
    import openai
    from engine.nl2verus import verifier,b3_runner
    checks=[]; requests=[]
    monkeypatch.setattr(b3_runner,'verify_b3_candidate',lambda code,verify:verify(code))
    monkeypatch.setattr(verifier,'verify_code',lambda code,timeout:checks.append(code) or {'status':'verified','verified':True,'message':'ok'})
    call=SimpleNamespace(id='tool1',function=SimpleNamespace(name='verify_verus',arguments=json.dumps({'code':GOOD})))
    message=SimpleNamespace(tool_calls=[call],model_dump=lambda **k:{'role':'assistant','tool_calls':[{'id':'tool1','type':'function','function':{'name':'verify_verus','arguments':json.dumps({'code':GOOD})}}]})
    final=SimpleNamespace(tool_calls=None,refusal=None,content='```rust\n'+GOOD+'\n```')
    responses=iter([SimpleNamespace(choices=[SimpleNamespace(message=message,finish_reason='tool_calls')],usage=None),SimpleNamespace(choices=[SimpleNamespace(message=final,finish_reason='stop')],usage=None)])
    class FakeClient:
        def __init__(self,**kwargs):self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def create(self,**kwargs):requests.append(dict(kwargs));return next(responses)
        def __enter__(self):return self
        def __exit__(self,*args):pass
    monkeypatch.setattr(openai,'OpenAI',FakeClient)
    result=agents._chat_generate('task',configured,True)
    assert checks==[GOOD] and result['code']==GOOD and result['provider_calls']==2
    assert result['agent_events']==[{'tool':'verify_verus','status':'verified','verified':True}]
    assert any(m.get('role')=='tool' for m in requests[-1]['messages'])


def test_sensitive_output_blocked():
    with pytest.raises(agents.ProviderError):agents._clean_code('use secret-api-key;',['secret-api-key'])


def test_sdk_is_platform_managed_and_key_only_stdin(configured,monkeypatch):
    captured={}
    class FakeProcess:
        returncode=0
        def __init__(self,cmd,**kw):
            captured.update(cmd=cmd,**kw);self.out=kw['stdout']
        def communicate(self,payload,timeout):
            captured['payload']=json.loads(payload);self.out.write(json.dumps({'code':GOOD}).encode())
    monkeypatch.setattr(agents.subprocess,'Popen',FakeProcess)
    result=agents._sdk_generate('codex','task',configured)
    assert result['code']==GOOD
    assert captured['cmd'][1].endswith('/scripts/agent_bridge.mjs')
    assert 'secret-api-key' not in ' '.join(captured['cmd'])
    assert not any('API_KEY' in k for k in captured['env'])
    assert captured['payload']['profile']['api_key']=='secret-api-key'
    assert captured['cwd'].startswith('/var/') or captured['cwd'].startswith('/tmp/') or captured['cwd'].startswith('/private/')



def test_presets_are_selectable_but_not_configured(configured,monkeypatch):
    caps=agents.capabilities()
    for agent in caps['agents']:
        assert len(agent['models'])>=3
        assert all(not row['configured'] for row in agent['models'])
        assert any(row['name']=='自定义 / 自训练模型' for row in agent['models'])
    preset=next(a for a in caps['agents'] if a['id']=='deepseek-harness')['models'][0]
    with pytest.raises(ValueError,match='已配置'):
        agents.validate_selection('deepseek-harness',preset['id'],[])
    configured.update(id='my-flash',model='deepseek-flash')
    profiles.save_profile(configured)
    models=next(a for a in agents.capabilities()['agents'] if a['id']=='deepseek-harness')['models']
    assert len([m for m in models if m['model']=='deepseek-flash'])==1
    assert next(m for m in models if m['id']=='my-flash')['configured'] is True


def test_no_auth_profile_is_configured_and_edit_switches_real_endpoint(configured,monkeypatch):
    app=FastAPI();app.include_router(rust.router);client=TestClient(app)
    first=dict(configured,id='lab',api_key='',auth_mode='none',protocol='responses',is_default=True,
               model='deepseek-v4-flash-0731',base_url='http://models.internal:8888/v1/chat/completions')
    saved=client.post('/api/v1/rust/models',json=first)
    assert saved.status_code==200,saved.text
    assert saved.json()['configured'] is True and saved.json()['base_url']=='http://models.internal:8888/v1'
    monkeypatch.setattr(agents.shutil,'which',lambda _: '/usr/bin/node')
    # Runtime availability is deployment dependent, so validate routing through the runner directly.
    class Runner:
        def __init__(self,**kw):self.kw=kw
    seen=[]
    monkeypatch.setattr(agents,'_sdk_generate',lambda agent,prompt,p:seen.append((agent,p['model'],p['base_url'],p['auth_mode'])) or {'code':GOOD})
    for model,url in [('deepseek-v4-flash-0731','http://models.internal:8888/v1'),('another-model','http://other.internal:8000/v1')]:
        first.update(model=model,base_url=url)
        assert client.post('/api/v1/rust/models',json=first).status_code==200
        runner=agents.make_runner({'agent_id':'codex','model_id':'lab','managed_profile':True},Runner)
        runner.kw['generate']('TASK','lab',snapshot=None)
    assert seen==[('codex','deepseek-v4-flash-0731','http://models.internal:8888/v1','none'),('codex','another-model','http://other.internal:8000/v1','none')]
    # An explicitly unauthenticated edit clears any previously stored credential.
    profiles.save_profile(configured)
    configured.update(auth_mode='none',api_key='')
    profiles.save_profile(configured)
    assert profiles.configured_profiles()['test']['api_key']==''


def test_multiple_models_keep_distinct_routes_and_single_default(configured,monkeypatch):
    first=dict(configured,id='first',protocol='responses',is_default=True)
    second=dict(configured,id='second',model='second-model',base_url='https://second.example/v1',protocol='responses',is_default=True)
    profiles.save_profile(first);profiles.save_profile(second)
    rows=profiles.configured_profiles()
    assert rows['first']['is_default'] is False and rows['second']['is_default'] is True
    # Capability catalog must expose both profiles to Codex, not only the default.
    models=next(a for a in agents.capabilities()['agents'] if a['id']=='codex')['models']
    assert {m['id'] for m in models if m['configured']}=={'first','second'}
    assert next(m for m in models if m['id']=='second')['base_url']=='https://second.example/v1'

    seen=[]
    class Runner:
        def __init__(self,**kw):self.kw=kw
    monkeypatch.setattr(agents,'_sdk_generate',lambda agent,prompt,p:seen.append((p['id'],p['model'],p['base_url'])) or {'code':GOOD})
    for selected in ('first','second'):
        runner=agents.make_runner({'agent_id':'codex','model_id':selected,'managed_profile':True},Runner)
        runner.kw['generate']('TASK',selected,snapshot=None)
    assert seen==[('first','test-model','https://models.example/v1'),('second','second-model','https://second.example/v1')]
