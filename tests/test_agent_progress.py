import json
from types import SimpleNamespace
from apps.api.app.agent_progress import AgentProgress


class Store:
    def __init__(self):self.snapshots=[]
    def write_task(self,task):self.snapshots.append(json.loads(json.dumps(task.metadata)))


def test_live_steps_are_visible_before_process_returns_and_failure_preserves_completed(tmp_path):
    store=Store();task=SimpleNamespace(metadata={});progress=AgentProgress(task,store)
    with progress.watch(tmp_path,0) as monitor:
        p=tmp_path/'live-progress.jsonl'
        p.write_text(json.dumps({'id':'child','label':'子 Agent 生成规约','status':'running'})+'\n')
        monitor.read()
        assert store.snapshots[-1]['agent_progress']['current']=='子 Agent 生成规约'
        with p.open('a') as f:f.write(json.dumps({'id':'child','status':'completed'})+'\n'+json.dumps({'id':'verify','label':'Frama-C 验证','status':'running'})+'\n')
        monitor.read()
        assert progress.state['steps'][1]['status']=='completed'
    progress.finish(False)
    assert next(s for s in progress.state['steps'] if s['id']=='0:child')['status']=='completed'
    assert next(s for s in progress.state['steps'] if s['id']=='0:verify')['status']=='failed'


def test_partial_event_waits_for_complete_line_and_rounds_keep_separate_ids(tmp_path):
    store=Store();progress=AgentProgress(SimpleNamespace(metadata={}),store)
    with progress.watch(tmp_path,0) as monitor:
        p=tmp_path/'live-progress.jsonl';p.write_text('{"id":"tool","status":"running"')
        monitor.read();assert len(progress.state['steps'])==1
        with p.open('a') as f:f.write('}\n')
        monitor.read();assert progress.state['steps'][-1]['id']=='0:tool'
    progress.state['round']=1
    progress.update({'id':'tool','status':'completed'})
    assert progress.state['steps'][-1]['id']=='1:tool'


def test_repair_progress_reuses_session_without_second_startup(tmp_path):
    progress=AgentProgress(SimpleNamespace(metadata={}),Store())
    with progress.watch(tmp_path,1,reuse=True) as monitor:
        p=tmp_path/'live-progress.jsonl'
        p.write_text(json.dumps({'id':'write','label':'写入修复后的规约','status':'completed'})+'\n')
        monitor.read()
    assert progress.state['steps'][0]['label']=='复用原会话修复规约'
    assert all(step['label']!='启动官方 CLI' for step in progress.state['steps'])
