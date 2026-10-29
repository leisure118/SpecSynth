from types import SimpleNamespace
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.app import workspace, config, storage, service, rust
from engine.nl2verus import verifier
from engine.nl2verus.workflow_runs import WorkflowRuns, WorkflowRunRequest

GOOD = 'use vstd::prelude::*;\nverus! { fn inc(x: u64) -> (r: u64) requires x < 100, ensures r == x + 1, { x + 1 } }\n'

@pytest.fixture
def system(tmp_path, monkeypatch):
    runs = tmp_path/'runs'
    runs.mkdir()
    monkeypatch.setattr(workspace, 'PROJECTS_DIR', tmp_path/'projects')
    monkeypatch.setattr(config, 'RUNS_DIR', runs)
    monkeypatch.setattr(storage, 'RUNS_DIR', runs)
    monkeypatch.setattr(storage, 'UPLOADS_DIR', runs/'uploads')
    monkeypatch.setattr(service, 'RUNS_DIR', runs)
    monkeypatch.setattr(workspace, 'get_available_models', lambda: ['test'])
    store=storage.JsonStore()
    manager=service.RunManager(store)
    app=FastAPI();app.include_router(workspace.create_workspace_router(manager,store))
    return TestClient(app),store,manager


def make(client, files=None):
    r=client.post('/api/v1/projects',json={'name':'Rust test','language':'Rust','files':files or [{'path':'src/lib.rs','content':GOOD}]})
    assert r.status_code==201,r.text
    return r.json()


def wait(store, task_id):
    for _ in range(200):
        r=store.read_result(task_id)
        if r:return r
        time.sleep(.01)
    raise AssertionError('task did not finish')


def test_language_and_modes(system):
    client,store,_=system
    p=make(client)
    assert p['language']=='Rust'
    assert client.post('/api/v1/projects',json={'name':'wrong','language':'Rust','files':[{'path':'a.c','content':'x'}]}).status_code==422
    assert client.post('/api/v1/projects',json={'name':'wrong','files':[{'path':'a.rs','content':'x'}]}).status_code==422
    url='/api/v1/projects/'+p['id']
    assert client.put(url,json={'name':p['name'],'files':p['files'],'language':'Rust','revision':1}).status_code==200
    assert client.post(url+'/runs',json={'revision':2,'entry_path':'src/lib.rs','mode':'single','model_name':'test'}).status_code==422
    c=client.post('/api/v1/projects',json={'name':'C','files':[{'path':'a.c','content':'int a;'}]}).json()
    assert client.post('/api/v1/projects/'+c['id']+'/runs',json={'revision':1,'entry_path':'a.c','mode':'rust-verify'}).status_code==422


@pytest.mark.parametrize('outcome,expected,count,errors,exit_code',[('verified','Pass',2,0,0),('failed','Fail',1,1,1),('compile_error','Invalid',None,None,1),('no_checks','Invalid',0,0,0),('timeout','Timeout',None,None,None)])
def test_real_task_contract(system,monkeypatch,outcome,expected,count,errors,exit_code):
    client,store,manager=system
    seen=[]
    def verify(code,timeout,**kwargs):
        seen.append(kwargs)
        return {'status':outcome,'verified':outcome=='verified','verified_count':count,'error_count':errors,'exit_code':exit_code,'verus_version':verifier.VERUS_VERSION,'message':outcome,'stdout':'verifier log','stderr':''}
    monkeypatch.setattr(verifier,'verify_code',verify)
    p=make(client,[{'path':'src/lib.rs','content':GOOD},{'path':'src/helper.rs','content':'pub fn helper() {}'}])
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-verify'})
    assert response.status_code==201,response.text
    task_id=response.json()['task_id'];result=wait(store,task_id)
    assert result['status']==expected
    assert result['source_code']==GOOD and result['result_code']==GOOD
    assert seen[0]['entry_path']=='src/lib.rs' and len(seen[0]['files'])==2
    assert store.list_artifacts(task_id)
    assert manager.ensure_materialized(task_id)[1]['status']==expected
    assert client.get('/api/v1/projects/'+p['id']).json()['runs'][0]['entry_path']=='src/lib.rs'


def test_bypass_in_dependency_blocked(system,monkeypatch):
    client,store,_=system
    monkeypatch.setattr(verifier,'verify_code',lambda *a,**k: pytest.fail('must not run'))
    p=make(client,[{'path':'main.rs','content':GOOD},{'path':'dependency.rs','content':'verus! { proof fn bad() { assume(false); } }'}])
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'main.rs','mode':'rust-verify'})
    assert wait(store,response.json()['task_id'])['status']=='Invalid'


def test_generation_repairs_and_persists(system,monkeypatch):
    client,store,_=system
    calls=[]
    checks=[]
    def generate(prompt,model_id,**kwargs):
        calls.append(prompt);return {'code':GOOD,'model_name':'fake','usage':{'total_tokens':10},'finish_reason':'stop'}
    def verify(code,timeout):
        checks.append(code);ok=len(checks)==2
        return {'status':'verified' if ok else 'failed','verified':ok,'verified_count':1 if ok else 0,'error_count':0 if ok else 1,'exit_code':0 if ok else 1,'verus_version':verifier.VERUS_VERSION,'message':'ok' if ok else 'postcondition failed','stderr':''}
    caps={'generation_configured':True,'embedding_configured':False,'default_model_id':'fake','models':[{'id':'fake','configured':True}]}
    monkeypatch.setattr(rust,'provider_status',lambda:caps)
    monkeypatch.setattr(rust,'WorkflowRuns',lambda:WorkflowRuns(config=lambda:None,status=lambda **k:caps,generate=generate,verify=verify,verifier_status=lambda:{'available':True,'version':verifier.VERUS_VERSION}))
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','model_name':'fake','description':'increment safely','function_signature':'fn inc(x: u64) -> (r: u64)'})
    assert response.status_code==201,response.text
    result=wait(store,response.json()['task_id'])
    assert result['status']=='Pass'
    assert len(result['engine_detail']['attempts'])==2
    assert len(calls)==2 and 'postcondition failed' in calls[1]
    assert any(a['name']=='rounds.json' for a in result['artifacts'])
    assert client.get('/api/v1/projects/'+p['id']).json()['files'][0]['content']==GOOD


def test_unavailable_is_not_failure_or_success(system,monkeypatch):
    client,store,_=system
    def missing(*a,**kw):raise verifier.VerifierUnavailableError('Verus missing')
    monkeypatch.setattr(verifier,'verify_code',missing)
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-verify'})
    result=wait(store,response.json()['task_id'])
    assert result['status']=='Unavailable' and result['proof_stats']['total_goals']==0


def test_external_file_macros_rejected_before_verifier(monkeypatch,tmp_path):
    exe=tmp_path/'verus';exe.touch()
    monkeypatch.setattr(verifier,'verus_path',lambda:exe)
    monkeypatch.setattr(verifier,'verifier_info',lambda:pytest.fail('must reject before launch'))
    for source in ['include_str!("/etc/passwd")','#[path="../outside.rs"] mod hidden;', 'env!("SECRET")']:
        with pytest.raises(ValueError,match='不支持'):
            verifier.verify_code(source)


def test_service_restart_never_replays_generation(system):
    from apps.api.app.schemas import RunTask,PhaseState
    from apps.api.app.storage import utcnow
    client,store,manager=system
    task=RunTask(task_id='interrupted',mode='rust-generate',title='Rust',source_type='upload',status='running',engine='live',created_at=utcnow(),updated_at=utcnow(),task_dir=str(storage.RUNS_DIR/'interrupted'),phases=[PhaseState(key='generation',label='generate',status='running')],metadata={'worker_pid':-1,'rust_workflow':{'attempts':[{'round':0,'code':GOOD}]}})
    store.create_task(task)
    recovered,result=manager.ensure_materialized(task.task_id)
    assert recovered.status=='unavailable' and result['status']=='Unavailable'
    assert result['engine_detail']['attempts'][0]['code']==GOOD
    assert '重启' in result['summary']


def test_api_agent_selection_and_skills_are_persisted(system,monkeypatch,tmp_path):
    import json
    from engine.nl2verus import agents,profiles,platform_provider
    client,store,_=system
    monkeypatch.setattr(profiles,'PROFILES_PATH',tmp_path/'model-profiles.json')
    monkeypatch.setattr(profiles,'legacy_profiles',lambda snapshot=None:{})
    monkeypatch.setattr(platform_provider,'get_config',lambda:platform_provider.PlatformConfig({}))
    profiles.save_profile({'id':'experiment','name':'Experiment','model':'model-under-test','protocol':'chat','base_url':'https://example.com/v1','api_key':'PRIVATE-KEY-DO-NOT-RECORD'})
    seen=[]
    monkeypatch.setattr(agents,'_chat_generate',lambda prompt,profile,harness:seen.append((prompt,harness)) or {'code':GOOD,'finish_reason':'stop','model_name':profile['model'],'agent_events':[{'tool':'verify_verus','status':'verified'}],'provider_calls':2})
    def verify(code,timeout):
        return {'status':'verified','verified':True,'verified_count':1,'error_count':0,'message':'verified','stdout':'1 verified, 0 errors','stderr':'','exit_code':0,'verus_version':verifier.VERUS_VERSION}
    monkeypatch.setattr(rust,'WorkflowRuns',lambda **kwargs:WorkflowRuns(**kwargs,verify=verify,verifier_status=lambda:{'available':True,'version':verifier.VERUS_VERSION}))
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','model_name':'experiment','agent_id':'deepseek-harness','skill_ids':['verus-proof'],'description':'Increment x safely','max_repair_rounds':0})
    assert response.status_code==201,response.text
    task_id=response.json()['task_id'];result=wait(store,task_id)
    assert result['status']=='Pass' and result['result_code']==GOOD
    workflow=result['engine_detail']['workflow']
    assert workflow['selection']['agent_id']=='deepseek-harness'
    assert workflow['selection']['skill_ids']==['verus-proof']
    assert workflow['selection']['skill_snapshot'][0]['sha256']
    assert workflow['provider_calls']==2
    assert 'For each loop' in workflow['attempts'][0]['effective_prompt'] and seen[0][1] is True
    assert 'PRIVATE-KEY-DO-NOT-RECORD' not in json.dumps(result)
    assert 'PRIVATE-KEY-DO-NOT-RECORD' not in store.read_task(task_id).model_dump_json()
    assert client.get('/api/v1/projects/'+p['id']).json()['files'][0]['content']==GOOD


def test_dataset_label_cannot_hide_modified_task(system,monkeypatch):
    from engine.nl2verus.dataset import load_tasks
    client,store,_=system
    caps={'generation_configured':True,'embedding_configured':False,'models':[{'id':'fake','configured':True}]}
    monkeypatch.setattr(rust,'provider_status',lambda:caps)
    p=make(client);row=load_tasks()[0]
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','model_name':'fake','sample_id':row['sample_id'],'description':'Modified task','function_signature':row.get('function_signature','')})
    assert response.status_code==422
    assert not client.get('/api/v1/projects/'+p['id']).json()['runs']

def test_external_agent_failed_proof_repairs_then_persists(system,monkeypatch):
    from apps.api.app import agent_execution, agent_runners
    client,store,_=system
    monkeypatch.setattr(agent_runners,'require_agent',lambda _:None)
    monkeypatch.setattr(agent_execution,'verifier_preflight',lambda *a:None)
    prompts=[]
    def generate(agent,prompt,*args,**kwargs):
        prompts.append(prompt)
        return [{'path':'src/lib.rs','content':GOOD}]
    monkeypatch.setattr(agent_execution,'generate',generate)
    count=[]
    def verify(*args,**kwargs):
        count.append(1)
        ok=len(count)>1
        return {'status':'verified' if ok else 'failed','verified':ok,'message':'proved' if ok else 'boundary obligation failed','verified_count':1 if ok else 0,'error_count':0 if ok else 1}
    monkeypatch.setattr(agent_execution,'verify_candidates',verify)
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','description':'Increment safely','assistant':{'agent':'codex','skills':[]},'max_repair_rounds':1})
    assert response.status_code==201,response.text
    result=wait(store,response.json()['task_id'])
    assert result['status']=='Pass' and len(result['engine_detail']['attempts'])==2
    assert 'boundary obligation failed' in prompts[1]
    assert result['engine_detail']['agent']=='codex'
    assert result['result_code']==GOOD
    assert store.read_task(response.json()['task_id']).metadata['agent']=='codex'


def test_external_agent_cannot_report_pass_without_verifier(system,monkeypatch):
    from apps.api.app import agent_execution,agent_runners
    client,store,_=system
    monkeypatch.setattr(agent_runners,'require_agent',lambda _:None)
    monkeypatch.setattr(agent_execution,'verifier_preflight',lambda *a:None)
    monkeypatch.setattr(agent_execution,'generate',lambda *a,**k:[{'path':'src/lib.rs','content':GOOD}])
    monkeypatch.setattr(agent_execution,'verify_candidates',lambda *a,**k:{'status':'failed','verified':False,'message':'real failure','verified_count':0,'error_count':1})
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','description':'Increment safely','assistant':{'agent':'claude-code'},'max_repair_rounds':0})
    result=wait(store,response.json()['task_id'])
    assert result['status']=='Fail' and result['proof_stats']['proved_goals']==0


def test_unavailable_verifier_never_calls_agent(system,monkeypatch):
    from apps.api.app import agent_execution,agent_runners
    client,store,_=system
    monkeypatch.setattr(agent_runners,'require_agent',lambda _:None)
    monkeypatch.setattr(agent_execution,'verifier_preflight',lambda *a:'Verifier unavailable')
    monkeypatch.setattr(agent_execution,'generate',lambda *a,**k:pytest.fail('must not call model'))
    p=make(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={'revision':1,'entry_path':'src/lib.rs','mode':'rust-generate','description':'Increment safely','assistant':{'agent':'codex'}})
    assert response.status_code==201,response.text
    assert wait(store,response.json()['task_id'])['status']=='Unavailable'
