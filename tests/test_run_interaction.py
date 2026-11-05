import pytest
from acsl.application.run_interaction import enqueue,consume,messages
from acsl.application.terminal import safe_terminal_text

def test_feedback_consumed_once_and_status_persists(tmp_path):
    item=enqueue(tmp_path,'保留循环不变式')
    assert item['status']=='pending'
    rows=consume(tmp_path,1)
    assert rows[0]['id']==item['id'] and rows[0]['round']==1
    assert consume(tmp_path,2)==[]
    assert messages(tmp_path)[0]['status']=='applied'
    with pytest.raises(ValueError):enqueue(tmp_path,' ')
    with pytest.raises(ValueError):enqueue(tmp_path,'x'*4001)

def test_terminal_redacts_env_secrets_and_bearer(monkeypatch):
    monkeypatch.setenv('TEST_API_KEY','secret-value-123')
    result=safe_terminal_text('curl -H "Authorization: Bearer abcdefghijkl" API_KEY=very-secret secret-value-123')
    assert 'secret-value-123' not in result and 'abcdefghijkl' not in result and 'very-secret' not in result

def test_terminal_projection_contains_actual_commands_and_tool_output():
    from engine.c_agent_cli import project_event
    rows=project_event('codex',{'type':'item.completed','item':{'id':'1','type':'command_execution','command':'frama-c -wp main.c','aggregated_output':'7/7 goals','exit_code':0}})
    assert rows[0]['command']=='frama-c -wp main.c'
    assert rows[0]['output']=='7/7 goals'
    assert project_event('codex',{'type':'item.completed','item':{'type':'reasoning','text':'private'}})==[]


def test_progress_exposes_redacted_command_and_output(monkeypatch):
    from types import SimpleNamespace
    from acsl.application.agent_progress import AgentProgress
    monkeypatch.setenv('PRIVATE_TEST_TOKEN','secret-token-example')
    task=SimpleNamespace(metadata={})
    progress=AgentProgress(task,SimpleNamespace(write_task=lambda t:None))
    progress.update({'id':'x','label':'Tool','status':'completed','command':'run --token=secret-token-example','output':'7/7 goals'})
    assert 'secret-token-example' not in str(task.metadata)
    assert progress.state['steps'][0]['output']=='7/7 goals'


def test_interaction_api_rejects_finished_tasks_and_records_pending(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from apps.api.app import main
    task=SimpleNamespace(status='running',metadata={'agent':'deepseek-harness'},task_dir=str(tmp_path))
    monkeypatch.setattr(main.store,'read_task',lambda id:task if id=='known' else None)
    with TestClient(main.app) as client:
        assert client.post('/api/v1/runs/missing/interaction',json={'text':'test'}).status_code==404
        response=client.post('/api/v1/runs/known/interaction',json={'text':'Preserve invariant'})
        assert response.status_code==200 and response.json()['status']=='pending'
        assert len(client.get('/api/v1/runs/known/interaction').json()['items'])==1
        task.status='verified'
        assert client.post('/api/v1/runs/known/interaction',json={'text':'test'}).status_code==409


def test_native_terminal_reads_real_commands_and_keeps_platform_phases_out(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from acsl.application.terminal import native_terminal
    monkeypatch.setenv('PRIVATE_TEST_TOKEN','terminal-secret-123')
    folder=tmp_path/'artifacts/agent/round-0';folder.mkdir(parents=True)
    events=[{'id':'launch-command','command':'node dsh.js --json -','status':'completed','at':'2026-11-05T00:00:00Z'},
            {'id':'tool1','command':'verifast --token=terminal-secret-123 source.c','status':'running'},
            {'id':'tool1','output':'0 errors found (3 statements verified)','status':'completed'},
            {'id':'platform-proof','label':'平台独立验证','status':'completed','detail':'this is not native CLI output'}]
    (folder/'live-progress.jsonl').write_text('\n'.join(map(json.dumps,events))+'\n')
    task=SimpleNamespace(task_dir=str(tmp_path),metadata={'agent':'deepseek-harness'},status='pass')
    report=native_terminal(task)
    assert report['agent']=='deepseek-harness' and len(report['events'])==2
    assert report['events'][0]['command']=='node dsh.js --json -'
    assert report['events'][1]['status']=='completed'
    assert '3 statements verified' in report['events'][1]['output']
    assert 'terminal-secret-123' not in str(report)
    assert 'this is not native CLI output' not in str(report)


def test_native_terminal_rejects_symlinked_round_outside_task(tmp_path):
    from types import SimpleNamespace
    from acsl.application.terminal import native_terminal
    taskdir=tmp_path/'task';root=taskdir/'artifacts/agent';root.mkdir(parents=True)
    outside=tmp_path/'outside';outside.mkdir();(outside/'live-progress.jsonl').write_text('{"id":"secret","command":"not allowed"}\n')
    (root/'round-0').symlink_to(outside,target_is_directory=True)
    assert native_terminal(SimpleNamespace(task_dir=str(taskdir),metadata={},status='pass'))['events']==[]
