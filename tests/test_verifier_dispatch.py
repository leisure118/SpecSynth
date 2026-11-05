from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from acsl.contracts.runs import RunResult,RunRequest
from apps.api.app import verification


def test_shared_verification_endpoint_dispatches_only_selected_adapter(monkeypatch):
    calls=[]
    def vf(files,entry,timeout):
        calls.append(('verifast',files,entry))
        return {'verified':True,'message':'verified','diagnostics':[]}
    def fc(files,entry,mode,timeout,directory):
        calls.append(('framac',files,entry))
        return {'verified':False,'message':'failed','diagnostics':[]}
    monkeypatch.setattr(verification.verifast_runtime,'verify',vf)
    monkeypatch.setattr(verification.framac_runtime,'run_candidate',fc)
    app=FastAPI();app.include_router(verification.router);client=TestClient(app)
    body={'files':[{'path':'a.c','content':'int f(void){return 0;}'}],'entry':'a.c'}
    for tool in ('verifast','framac'):
        r=client.post('/api/v1/verification/verify',json={**body,'verification_tool':tool})
        assert r.status_code==200
        assert r.json()['verification_tool']==tool
        assert calls[-1][0]==tool
    assert len(calls)==2
    assert client.post('/api/v1/verification/verify',json={**body,'verification_tool':'unknown'}).status_code==422


def test_verifast_result_fits_shared_schema_and_preserves_diagnostics(tmp_path,monkeypatch):
    from acsl.application.verifier_execution import execute_verifast
    from acsl.infrastructure.settings import settings
    source=tmp_path/'a.c';source.write_text('int f(void){return 0;}')
    artifacts=[]
    store=SimpleNamespace(read_upload=lambda _: {'stored_path':str(source)},
                          write_text_artifact=lambda *args:artifacts.append(args))
    task=SimpleNamespace(task_id='test',mode='single',phases=[],model_name=None)
    def build(task,**body):
        return RunResult(task_id=task.task_id,mode='single',engine='live',title='test',**body).model_dump()
    manager=SimpleNamespace(store=store,_advance_phase=lambda *args:None,_build_result=build)
    check={'verified':False,'status':'failed','message':'bad contract','display_log':'a.c:3 error',
           'command_text':'verifast a.c','diagnostics':[{'path':'a.c','line':3,'message':'bad contract'}]}
    monkeypatch.setattr(verification.verifast_runtime,'verify',lambda *args:check)
    result=execute_verifast(manager,task,RunRequest(file_id='input',entry_path='a.c',verification_tool='verifast'))
    assert result['engine']=='VeriFast'
    assert result['engine_detail']['verification']['diagnostics'][0]['line']==3
    assert result['proof_stats']['scope']=='compilation-unit'
    assert result['engine_detail']['provider_calls']==0
    assert len(artifacts)==2
