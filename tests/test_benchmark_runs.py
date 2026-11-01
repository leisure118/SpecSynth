import hashlib
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.app import benchmarks
from apps.api.app.storage import utcnow

@pytest.fixture
def runner():
    tasks={};submissions=[];uploads=[]
    class Store:
        def list_tasks(self,limit=20): return list(tasks.values())
        def create_upload(self,name,payload):
            uploads.append((name,payload));return {'file_id':'snapshot'}
    class Manager:
        def ensure_materialized(self,id):return tasks[id],None
        def submit(self,mode,payload):
            submissions.append(payload)
            task=SimpleNamespace(task_id=str(len(tasks)),status='queued',message='',created_at=utcnow(),finished_at=None,model_name=None,metadata={'benchmark':payload.benchmark_context})
            tasks[task.task_id]=task;return task
    app=FastAPI();app.include_router(benchmarks.create_benchmark_runs_router(Manager(),Store()))
    return TestClient(app),submissions,uploads,tasks

def test_submission_freezes_source_and_configuration_and_blocks_duplicates(runner):
    client,submissions,uploads,tasks=runner
    body={'file':'103.c','action':'verify','timeout_sec':60}
    r=client.post('/api/v1/benchmarks/autobench_v2/runs',json=body)
    assert r.status_code==201,r.text
    p=submissions[0]
    assert p.verification_only and p.assistant is None
    assert p.benchmark_context['source_sha256']==hashlib.sha256(uploads[0][1]).hexdigest()
    assert p.benchmark_context['configuration']['timeout_sec']==60
    assert client.post('/api/v1/benchmarks/autobench_v2/runs',json=body).status_code==409
    history=client.get('/api/v1/benchmarks/autobench_v2/runs',params={'file':'103.c'}).json()['items']
    assert len(history)==1 and history[0]['origin']['source_kind']=='imported-annotated-source'
    assert not client.get('/api/v1/benchmarks/autobench_v2/runs',params={'file':'104.c'}).json()['items']
    tasks['0'].status='pass'
    assert client.post('/api/v1/benchmarks/autobench_v2/runs',json=body).status_code==201

def test_missing_source_and_bad_path_never_submit(runner):
    client,submissions,_,_=runner
    assert client.post('/api/v1/benchmarks/autobench_v2/runs',json={'file':'223.c'}).status_code==422
    assert client.post('/api/v1/benchmarks/live25/runs',json={'file':'../../.env'}).status_code==404
    assert not submissions

def test_generation_resolves_pinned_skills_and_uses_registered_model(runner,monkeypatch):
    from acsl.infrastructure import settings as settings_module
    from acsl.adapters import agent_runtime as agent_runners
    client,submissions,_,_=runner
    monkeypatch.setattr(settings_module,'get_available_models',lambda:['deepseek-test'])
    monkeypatch.setattr(agent_runners,'require_agent',lambda agent:None)
    r=client.post('/api/v1/benchmarks/autobench_v2/runs',json={'file':'103.c','action':'generate','model_name':'deepseek-test','assistant':{'agent':'deepseek-harness','skills':[{'id':'bounds','name':'bounds','instructions':'Preserve bounds','agents':['deepseek-harness']}]}})
    assert r.status_code==201,r.text
    p=submissions[0]
    assert not p.verification_only
    assert 'Preserve bounds' in p.agent_instructions
    assert p.benchmark_context['configuration']['assistant']['skills'][0]['instructions']=='Preserve bounds'

def test_invalid_settings_rejected_before_execution(runner):
    client,submissions,_,_=runner
    for body in [{'file':'103.c','action':'replay'}, {'file':'103.c','timeout_sec':0}, {'file':'103.c','max_repair_rounds':100}]:
        assert client.post('/api/v1/benchmarks/autobench_v2/runs',json=body).status_code==422
    assert not submissions

def test_direct_verification_rejects_assumptions_without_running_tool(tmp_path,monkeypatch):
    from acsl.application import agent_execution
    source=tmp_path/'source.c';source.write_text('int main(){\n//@ admit 0;\nreturn 0;\n}')
    monkeypatch.setattr(agent_execution,'resolve_project_path',lambda _:source)
    def unexpected(*a,**kw):raise AssertionError('Blocked source must never reach verifier')
    monkeypatch.setattr(agent_execution,'verify_candidates',unexpected)
    manager=SimpleNamespace(store=SimpleNamespace(read_upload=lambda _:{'stored_path':'source'}),_build_result=lambda task,**kw:kw)
    task=SimpleNamespace(mode='single',phases=[],model_name='unused')
    r=agent_execution.execute_verification_only(manager,task,SimpleNamespace(file_id='source',entry_path='source.c',timeout_sec=60))
    assert r['status']=='Invalid'
    assert r['engine_detail']['provider_calls']==0
    assert r['proof_stats']['total_goals']==0


def test_original_input_for_rerun_is_saved_separately_from_annotations(runner):
    client,submissions,uploads,_=runner
    r=client.post('/api/v1/benchmarks/autobench_v2/runs',json={'file':'103.c','source_variant':'original'})
    assert r.status_code==201
    assert submissions[0].benchmark_context['source_kind']=='original-source'
    original=benchmarks.file_detail('autobench_v2','103.c')['original_source']
    assert uploads[0][1].decode()==original
