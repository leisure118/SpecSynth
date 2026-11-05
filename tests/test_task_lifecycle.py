from datetime import datetime,timezone
import time
import pytest
from acsl.infrastructure.task_control import TaskControl,TaskCancelled,task_scope,current,checkpoint
from acsl.contracts.runs import RunTask,RunRequest
from acsl.application.runs.manager import RunManager

class Store:
    def __init__(self,task):self.task=task;self.result=None
    def read_task(self,_):return self.task.model_copy(deep=True)
    def write_task(self,task):self.task=task.model_copy(deep=True)
    def list_artifacts(self,_):return []
    def write_result(self,_,result):self.result=result
    def read_result(self,_):return self.result

def manager(tmp_path,monkeypatch):
    monkeypatch.setattr('acsl.application.runs.manager.detect_live_capabilities',lambda:{})
    now=datetime.now(timezone.utc)
    task=RunTask(task_id='test',mode='single',title='test',source_type='upload',status='queued',engine='live',created_at=now,updated_at=now,task_dir=str(tmp_path),metadata={'worker_pid':__import__('os').getpid()})
    store=Store(task);return RunManager(store),store


def test_total_budget_and_cancel_are_separate(tmp_path,monkeypatch):
    clock=[10.0];monkeypatch.setattr('acsl.infrastructure.task_control.time.monotonic',lambda:clock[0])
    with task_scope(tmp_path,20) as control:
        clock[0]=15;assert control.remaining(100)==15
        control.set_timeout(30);assert control.remaining()==25
        clock[0]=41
        with pytest.raises(TimeoutError):checkpoint()
        (tmp_path/'cancel.requested').touch()
        with pytest.raises(TaskCancelled):checkpoint()
    assert current() is None


def test_queued_cancellation_never_executes_generation(tmp_path,monkeypatch):
    m,store=manager(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'_run_live',lambda *args:pytest.fail('Must not start work after queued cancellation'))
    m.cancel('test');m.cancel('test')
    m._execute('test',RunRequest(file_id='input'))
    assert store.task.status=='cancelled' and store.result['status']=='Cancelled'
    assert store.task.finished_at is not None


def test_cancellation_during_call_preserves_artifact_and_never_reports_pass(tmp_path,monkeypatch):
    m,store=manager(tmp_path,monkeypatch)
    def run(task,payload):
        m.cancel(task.task_id)
        return m._build_result(task,status='Pass',summary='ok',source_code='int f();',result_code='candidate',command=None,logs={},specifications={},engine_detail={'verifier':'VeriFast','verification':{'verified':True,'status':'verified','verified_statements':3}})
    monkeypatch.setattr(m,'_run_live',run)
    m._execute('test',RunRequest(file_id='input'))
    assert store.result['result_code']=='candidate'
    assert store.result['status']=='Cancelled' and store.task.status=='cancelled'
    assert store.result['verification']['verified'] is False
    assert store.result['verification']['outcome']=='cancelled'


def test_rust_nested_job_inherits_cancellation_and_keeps_returned_candidate(tmp_path):
    from engine.nl2verus.workflow_runs import WorkflowRuns,WorkflowRunRequest,TERMINAL
    from engine.nl2verus.verifier import VERUS_VERSION
    caps={'generation_configured':True,'embedding_configured':False,'default_model_id':'fake','models':[{'id':'fake','configured':True}]}
    code='use vstd::prelude::*; verus! { fn f() {} }'
    def generate(*args,**kwargs):
        assert current() is not None
        (tmp_path/'cancel.requested').touch()
        return {'code':code,'finish_reason':'stop'}
    with task_scope(tmp_path,30):
        runner=WorkflowRuns(config=lambda:None,status=lambda **kwargs:caps,generate=generate,
            verify=lambda *args:pytest.fail('Cancelled job must not invoke Verus'),verifier_status=lambda:{'available':True,'version':VERUS_VERSION})
        try:
            row=runner.submit(WorkflowRunRequest(request_id='nested',description='prove',function_signature='fn f()',rag_enabled=False))
            for _ in range(100):
                row=runner.get(row['id'])
                if row['status'] in TERMINAL:break
                time.sleep(.01)
            assert row['status']=='cancelled'
            assert row['attempts'][0]['code']==code
        finally:runner.close()


def test_task_overrun_preserves_returned_code_but_is_timeout(tmp_path,monkeypatch):
    m,store=manager(tmp_path,monkeypatch)
    clock=[100.0];monkeypatch.setattr('acsl.infrastructure.task_control.time.monotonic',lambda:clock[0])
    def run(task,payload):
        clock[0]=111.0
        return m._build_result(task,status='Pass',summary='ok',source_code='',result_code='returned-candidate',command=None,logs={},specifications={})
    monkeypatch.setattr(m,'_run_live',run)
    m._execute('test',RunRequest(file_id='input',timeout_sec=10))
    assert store.task.status=='timeout' and store.result['status']=='Timeout'
    assert store.result['result_code']=='returned-candidate'


def test_restarted_c_task_never_reissues_generation(tmp_path,monkeypatch):
    m,store=manager(tmp_path,monkeypatch)
    store.task.metadata['worker_pid']=-1
    monkeypatch.setattr(m,'_run_live',lambda *args:pytest.fail('Recovery must not call models'))
    task,result=m.ensure_materialized('test')
    assert task.status=='unavailable' and result['status']=='Unavailable'
    assert '重启' in result['summary']
