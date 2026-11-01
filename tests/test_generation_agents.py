"""Agent contracts: API-only credentials, protocol compatibility and real tools."""
import json
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from engine.nl2verus import agents, profiles, dsh_cli
from apps.api.app import rust

GOOD='use vstd::prelude::*;\nverus! { fn inc(x:u64)->(r:u64) requires x<100, ensures r==x+1, {x+1} }'

@pytest.fixture
def configured(tmp_path,monkeypatch):
    monkeypatch.setattr(dsh_cli,'installed',lambda:True)
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


def test_official_harness_dispatch_never_calls_direct_api(configured,monkeypatch):
    profiles.save_profile(configured)
    seen=[]
    monkeypatch.setattr(agents,'_chat_generate',lambda *a:pytest.fail('must launch official CLI'))
    monkeypatch.setattr(dsh_cli,'generate',lambda prompt,profile:seen.append(profile['model']) or {'code':GOOD})
    class Runner:
        def __init__(self,**kw):self.kw=kw
    runner=agents.make_runner({'agent_id':'deepseek-harness','model_id':'test'},Runner)
    assert runner.kw['generate']('task','test',snapshot=None)['code']==GOOD
    assert seen==['test-model']


def test_official_harness_disabled_without_runtime(configured,monkeypatch):
    profiles.save_profile(configured)
    monkeypatch.setattr(dsh_cli,'installed',lambda:False)
    with pytest.raises(ValueError,match='不可用'):agents.validate_selection('deepseek-harness','test',[])


def test_native_cli_events_require_completion_and_real_tools():
    events=[{'type':'session','sessionId':'real-session'},
            {'type':'status','phase':'step_start'},
            {'type':'tool_call','callId':'1','tool':'bash','input':{'command':'verus output.rs'}},
            {'type':'tool_result','callId':'1','status':'completed','result':'verification results:: 1 verified, 0 errors'},
            {'type':'status','phase':'step_end','usage':{'inputTokens':10,'outputTokens':2,'totalTokens':12}},
            {'type':'status','phase':'turn_end','reason':{'kind':'completed'}},
            {'type':'final','text':GOOD}]
    encode=lambda rows:'\n'.join(json.dumps(e) for e in rows)
    result=dsh_cli.parse_events(encode(events))
    assert result['provider_calls']==1 and result['usage']['total_tokens']==12
    assert result['session_id']=='real-session' and result['agent_events'][0]['tool']=='bash'
    assert result['native_events'][2]==events[2]
    with pytest.raises(agents.ProviderError):dsh_cli.parse_events(encode(events[:-1]))
    with pytest.raises(agents.ProviderError):dsh_cli.parse_events(encode([e for e in events if not e['type'].startswith('tool_')]))
    events[-2]['reason']={'kind':'error'}
    with pytest.raises(agents.ProviderError):dsh_cli.parse_events(encode(events))


def test_cli_patch_switches_model_route_without_credentials(configured):
    p=dsh_cli.patch_for(configured,'/tmp/task')
    route=next(x for x in p if x['id']=='llm-pi-ai')['config']['providers']['platform-api']
    assert route['baseURL']==configured['base_url'] and route['models'][0]['id']==configured['model']
    assert 'secret-api-key' not in json.dumps(p)
    assert next(x for x in p if x['id']=='sandbox-policy')['config']['mode']=='workspace-write'


@pytest.mark.parametrize('compact',[False,True])
@pytest.mark.parametrize('child_stop',[None,'completed','error'])
@pytest.mark.parametrize('output_format',['verus','files'])
def test_official_cli_process_identity_and_private_config(configured,monkeypatch,tmp_path,output_format,child_stop,compact):
    monkeypatch.setenv('XUANJIAN_HARNESS_COMPACT','1' if compact else '0')
    package=tmp_path/'official';(package/'lib').mkdir(parents=True)
    (package/'lib/bin.js').write_text('// pinned upstream entry')
    monkeypatch.setattr(dsh_cli,'PACKAGE',package)
    monkeypatch.setattr(dsh_cli,'installed',lambda:True)
    captured={}
    class Process:
        returncode=0
        def __init__(self,cmd,**kw):
            captured.update(cmd=cmd,**kw)
            config_path=cmd[cmd.index('--patch')+1]
            captured['patch']=json.loads(__import__('pathlib').Path(config_path).read_text())
            self.out=kw['stdout']
            if child_stop:
                __import__('pathlib').Path(kw['cwd'],'subagent-audit.jsonl').write_text(json.dumps({'type':'end','id':'child','stop_reason':child_stop})+'\n')
            __import__('pathlib').Path(kw['cwd'],'output.rs' if output_format=='verus' else 'answer.json').write_text(GOOD if output_format=='verus' else json.dumps({'files':[{'path':'main.c','content':'int main(){return 0;}'}]}))
        def communicate(self,payload,timeout):
            captured['prompt']=payload.decode()
            events=[{'type':'session','sessionId':'official-session'},
                    {'type':'tool_call','callId':'1','tool':'write','input':{'content':configured['api_key']}},
                    {'type':'tool_result','callId':'1','status':'completed'},
                    *([{'type':'tool_call','callId':'2','tool':'subagent'},{'type':'tool_result','callId':'2','status':'completed'}] if child_stop else []),
                    {'type':'status','phase':'turn_end','reason':{'kind':'completed'}},
                    {'type':'final','text':GOOD}]
            self.out.write(('\n'.join(json.dumps(e) for e in events)).encode())
    monkeypatch.setattr(dsh_cli.subprocess,'Popen',Process)
    if child_stop=='error':
        with pytest.raises(agents.ProviderError,match='未正常完成'):
            dsh_cli.generate('task',configured,output_format=output_format,require_subagent=True)
        return
    result=dsh_cli.generate('task',configured,output_format=output_format,require_subagent=bool(child_stop))
    if output_format=='files':
        assert json.loads(result['code'])['files'][0]['path']=='main.c'
        if compact:
            assert 'Do not run an internal proof' in captured['prompt']
            assert result['agent_runtime']['workflow']=='compact-c-v1'
        else:assert 'harness_verify_c.py' in captured['prompt']
    assert captured['cmd'][1]==str(package/'lib/bin.js')
    assert captured['cmd'][-2:]==['--json','-']
    assert captured['env']['DSH_PLATFORM_KEY']==configured['api_key']
    assert configured['api_key'] not in json.dumps(captured['patch'])
    assert configured['api_key'] not in json.dumps(result)
    assert result['agent_runtime']['session_id']=='official-session'
    assert result['agent_runtime']['package']=='@deepseek-ai/dsh'
    assert result['agent_runtime']['events'][1]['input']['content']=='[REDACTED]'


@pytest.mark.parametrize('child_model',['','qwen35-4b-mix64','qwen35-9b-mix64'])
def test_native_child_route_is_fixed_or_inherits_main(configured,child_model):
    child={'model':child_model,'base_url':'https://child.invalid/v1','api_key':'private-child-key'} if child_model else None
    patch=dsh_cli.patch_for(configured,'/tmp/workspace',child)
    main=next(p for p in patch if p.get('id')=='agent-default-model')['config']
    tool=next(p for p in patch if p.get('id')=='tool-subagent')['config']
    providers=next(p for p in patch if p.get('id')=='llm-pi-ai')['config']['providers']
    assert main=={'provider':'platform-api','model':configured['model']}
    assert tool['provider']=='spawn' and tool['maxDepth']==1
    if child:
        assert tool['agentOptions']=={'provider':'platform-subagent','model':child_model}
        assert providers['platform-subagent']['apiKeyEnv']=='DSH_SUBAGENT_KEY'
        assert child['api_key'] not in json.dumps(patch)
    else:
        assert tool['agentOptions']=={} and 'platform-subagent' not in providers
