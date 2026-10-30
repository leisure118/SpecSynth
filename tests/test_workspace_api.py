"""Project persistence and immutable submission contract, isolated from user records."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app import workspace


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, 'PROJECTS_DIR', tmp_path / 'projects')
    monkeypatch.setattr(workspace, 'get_available_models', lambda: ['test-model'])
    snapshots = []
    submissions = []
    tasks = {}
    class Store:
        def read_task(self, task_id):
            return tasks.get(task_id)
        def create_upload(self, filename, payload):
            snapshots.append((filename, payload))
            return {'file_id': 'snapshot'}
        def create_bundle_upload(self, files):
            snapshots.extend((f['relative_path'], f['payload']) for f in files)
            return {'file_id': 'snapshot'}
    class Manager:
        def submit(self, mode, payload):
            assert payload.file_id == 'snapshot'
            submissions.append((mode,payload))
            task = SimpleNamespace(task_id=f'task-{len(tasks)+1}', status='queued')
            tasks[task.task_id] = task
            return task
    app = FastAPI()
    app.include_router(workspace.create_workspace_router(Manager(), Store()))
    test_client = TestClient(app)
    test_client.snapshots = snapshots
    test_client.tasks = tasks
    test_client.submissions = submissions
    return test_client


def project(client):
    response = client.post('/api/v1/projects', json={'name':'Example', 'files':[
        {'path':'src/main.c','content':'int main(void) { return 0; }'},
        {'path':'include/main.h','content':'int main(void);'}]})
    assert response.status_code == 201
    return response.json()


def test_create_save_and_revision_conflict(client):
    p = project(client)
    assert client.get('/api/v1/projects').json()['items'][0]['file_count'] == 2
    assert client.get('/api/v1/projects/'+p['id']).json()['files'] == p['files']
    body = {'name':'Renamed','files':p['files'],'revision':1}
    assert client.put('/api/v1/projects/'+p['id'],json=body).json()['revision'] == 2
    assert client.put('/api/v1/projects/'+p['id'],json=body).status_code == 409
    assert client.get('/api/v1/projects/'+p['id']).json()['name'] == 'Renamed'


@pytest.mark.parametrize('path', ['../escape.c','/tmp/escape.c','src/../../escape.c','src\\escape.c','C:/escape.c','src//main.c','script.py'])
def test_invalid_paths_are_rejected(client, path):
    assert client.post('/api/v1/projects',json={'name':'Bad','files':[{'path':path,'content':''}]}).status_code == 422


def test_run_uses_snapshot_and_records_revision(client):
    p=project(client)
    response=client.post('/api/v1/projects/'+p['id']+'/runs',json={
        'revision':1,'mode':'inter-modular','entry_path':'src/main.c','model_name':'test-model'})
    assert response.status_code == 201
    assert client.snapshots == [(f['path'],f['content'].encode()) for f in p['files']]
    p['files'][0]['content']='changed'
    assert client.put('/api/v1/projects/'+p['id'],json={'name':p['name'],'revision':1,'files':p['files']}).status_code == 200
    assert client.snapshots[0][1] == b'int main(void) { return 0; }'
    saved=client.get('/api/v1/projects/'+p['id']).json()
    assert saved['runs'][0]['revision']==1
    assert saved['runs'][0]['task_id']=='task-1'


def test_invalid_submission_does_not_run(client):
    p=project(client)
    base={'revision':1,'mode':'single','entry_path':'src/main.c','model_name':'test-model'}
    for changes,status in [({'revision':2},409),({'entry_path':'missing.c'},422),({'entry_path':'include/main.h'},422),({'model_name':'unknown'},422)]:
        assert client.post('/api/v1/projects/'+p['id']+'/runs',json=base|changes).status_code==status
    assert client.snapshots == []


def test_each_file_has_independent_verification_and_duplicate_guard(client):
    p=project(client)
    p['files'].append({'path':'other/main.c','content':'int other(void) { return 1; }'})
    saved=client.put('/api/v1/projects/'+p['id'],json={'name':p['name'],'revision':1,'files':p['files']}).json()
    endpoint='/api/v1/projects/'+p['id']+'/runs'
    payload={'revision':saved['revision'],'mode':'single','entry_path':'src/main.c','model_name':'test-model'}
    first=client.post(endpoint,json=payload)
    assert first.status_code==201
    assert client.post(endpoint,json=payload).status_code==409
    second=client.post(endpoint,json=payload|{'entry_path':'other/main.c'})
    assert second.status_code==201
    assert first.json()['task_id']!=second.json()['task_id']
    assert client.snapshots[0][1]!=client.snapshots[1][1]
    client.tasks[first.json()['task_id']].status='pass'
    data=client.get('/api/v1/projects/'+p['id']).json()
    assert [(r['entry_path'],r['status']) for r in data['runs']]==[('src/main.c','pass'),('other/main.c','queued')]
    assert client.post(endpoint,json=payload).status_code==201


def test_project_runs_remain_distinct_from_file_runs(client):
    p=project(client)
    base={'revision':1,'entry_path':'src/main.c','model_name':'test-model'}
    endpoint='/api/v1/projects/'+p['id']+'/runs'
    assert client.post(endpoint,json=base|{'mode':'single'}).status_code==201
    assert client.post(endpoint,json=base|{'mode':'inter-modular'}).status_code==201
    assert client.post(endpoint,json=base|{'mode':'inter-modular'}).status_code==409


def example(monkeypatch, execution='replay'):
    case={'id':'example','title':'Example demo','modes':['single','termination'],
          'execution_mode':execution,'source_file':'sample.c','source_code':'int f(void) { return 1; }','source_manifest':[]}
    def lookup(key):
        if key!=case['id']:raise KeyError(key)
        return case
    monkeypatch.setattr(workspace,'get_demo_case',lookup)
    return case


def test_example_import_reuses_original_and_preserves_edited_project(client,monkeypatch):
    case=example(monkeypatch)
    response=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example','mode':'single'})
    assert response.status_code==201
    p=response.json()
    assert p['files']==[{'path':'sample.c','content':case['source_code']}]
    assert p['example']['execution_mode']=='replay' and p['runs']==[]
    assert client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()['id']==p['id']
    edited=[{'path':'sample.c','content':'int f(void) { return 2; }'}]
    client.put('/api/v1/projects/'+p['id'],json={'name':p['name'],'revision':1,'files':edited})
    new=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()
    assert new['id']!=p['id'] and new['files'][0]['content']==case['source_code']
    assert client.get('/api/v1/projects/'+p['id']).json()['files']==edited
    assert client.post('/api/v1/projects/from-demo',json={'demo_case_id':'missing'}).status_code==404
    assert client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example','mode':'inter-modular'}).status_code==422


def test_project_replay_requires_matching_original_source_and_records_history(client,monkeypatch):
    example(monkeypatch)
    p=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()
    endpoint='/api/v1/projects/'+p['id']+'/runs'
    body={'revision':1,'entry_path':'sample.c','mode':'single','model_name':'test-model','execution':'replay'}
    assert client.post(endpoint,json=body).status_code==201
    assert client.submissions[0][1].demo_case_id=='example'
    assert client.get('/api/v1/projects/'+p['id']).json()['runs'][0]['execution']=='replay'
    client.tasks['task-1'].status='pass'
    files=[{'path':'sample.c','content':'int changed(void){return 42;}'}]
    client.put('/api/v1/projects/'+p['id'],json={'name':p['name'],'files':files,'revision':1})
    assert client.post(endpoint,json=body|{'revision':2}).status_code==422
    assert client.post(endpoint,json=body|{'revision':2,'execution':'live'}).status_code==201
    assert client.submissions[-1][1].demo_case_id is None


def test_replay_cannot_be_requested_for_normal_or_live_example_projects(client,monkeypatch):
    p=project(client)
    example(monkeypatch,execution='live')
    body={'revision':1,'entry_path':'src/main.c','model_name':'test-model','execution':'replay'}
    assert client.post('/api/v1/projects/'+p['id']+'/runs',json=body).status_code==422
    p=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()
    assert client.post('/api/v1/projects/'+p['id']+'/runs',json=body|{'entry_path':'sample.c'}).status_code==422


def test_assistant_persistence_binding_and_run_snapshot(client):
    p = project(client)
    config = {'agent':'default', 'runner_model':'', 'workflow':'standard', 'sub_model':'', 'skill_refs':[], 'skills':[
        {'id':'bounds','name':'Bounds','instructions':'Check each array index.', 'agents':['default'], 'enabled':True},
        {'id':'other','name':'Other','instructions':'Do not include this.', 'agents':['codex'], 'enabled':True},
        {'id':'off','name':'Off','instructions':'Disabled instruction.', 'agents':['default'], 'enabled':False}]}
    url = '/api/v1/projects/'+p['id']
    assert client.put(url+'/assistant', json=config).status_code == 200
    stored = client.get(url).json()
    assert stored['assistant'] == config
    assert stored['revision'] == p['revision']
    assert client.post(url+'/runs', json={'revision':1,'entry_path':'src/main.c','model_name':'test-model'}).status_code == 201
    payload = client.submissions[-1][1]
    assert 'Check each array index.' in payload.agent_instructions
    assert 'Do not include this.' not in payload.agent_instructions
    assert 'Disabled instruction.' not in payload.agent_instructions
    assert payload.assistant == config
    assert client.get(url).json()['runs'][-1]['assistant'] == config
    assert client.put(url+'/assistant', json={'agent':'shell'}).status_code == 422
    config['skills'].append(config['skills'][0])
    assert client.put(url+'/assistant', json=config).status_code == 422


def test_external_agent_configuration_does_not_silently_run_default(client,monkeypatch):
    from apps.api.app import agent_runners
    def unavailable(agent):
        raise ValueError("Agent is unavailable")
    monkeypatch.setattr(agent_runners,"require_agent",unavailable)
    p = project(client)
    url = '/api/v1/projects/'+p['id']
    for agent in ['codex', 'claude-code', 'deepseek-harness']:
        assert client.put(url+'/assistant', json={'agent':agent,'skills':[]}).status_code == 200
        response = client.post(url+'/runs', json={'revision':1,'entry_path':'src/main.c','model_name':'test-model'})
        assert response.status_code == 422
        assert not client.submissions


def test_project_actions_preserve_history_and_export_sources(client):
    import io,json,zipfile
    p=project(client);url='/api/v1/projects/'+p['id']
    assert client.patch(url,json={'name':'Renamed','revision':1}).status_code==200
    assert client.patch(url,json={'name':'Old','revision':1}).status_code==409
    clone=client.post(url+'/duplicate').json()
    assert clone['id']!=p['id'] and clone['revision']==1 and not clone['runs']
    assert clone['files']==p['files']
    response=client.get(url+'/export')
    assert response.status_code==200 and response.headers['content-type']=='application/zip'
    with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
        assert bundle.read('source/src/main.c').decode()==p['files'][0]['content']
        assert json.loads(bundle.read('project.json'))['name']=='Renamed'
    assert client.delete(url).status_code==200
    assert p['id'] not in [p['id'] for p in client.get('/api/v1/projects').json()['items']]
    assert client.get(url).json()['archived']


def test_batch_snapshots_and_busy_files(client):
    p=project(client);url='/api/v1/projects/'+p['id']
    files=p['files']+[{'path':'src/second.c','content':'int second(void){return 1;}'}]
    assert client.put(url,json={'name':p['name'],'revision':1,'files':files}).status_code==200
    body={'revision':2,'entry_path':'src/main.c','mode':'single','model_name':'test-model'}
    result=client.post(url+'/batch-runs',json=body)
    assert result.status_code==201,result.text
    assert len(result.json()['items'])==2 and not result.json()['errors']
    assert {p.entry_path for _,p in client.submissions}=={'src/main.c','src/second.c'}
    repeated=client.post(url+'/batch-runs',json=body).json()
    assert not repeated['items'] and len(repeated['errors'])==2
    assert client.delete(url).status_code==409


def test_archived_examples_are_not_reused_by_home_entry(client,monkeypatch):
    example(monkeypatch)
    first=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()
    assert client.delete('/api/v1/projects/'+first['id']).status_code==200
    second=client.post('/api/v1/projects/from-demo',json={'demo_case_id':'example'}).json()
    assert first['id']!=second['id'] and not second.get('archived')


def test_external_prompt_preview_matches_initial_execution_prompt(client,monkeypatch):
    from apps.api.app import agent_execution
    from apps.api.app.assistants import AssistantConfig
    monkeypatch.setattr(agent_execution,'generate',lambda *a,**k:pytest.fail('offline preview must not call agent'))
    p=project(client)
    config={'agent':'codex','skills':[]}
    response=client.post('/api/v1/projects/'+p['id']+'/agent-prompt',json={'revision':1,'entry_path':'src/main.c','description':'Keep semantics','assistant':config})
    assert response.status_code==200,response.text
    assert response.json()['provider_calls']==0
    expected=agent_execution.initial_prompt(p['files'],'single','Keep semantics','',AssistantConfig(**config).prompt('C'))
    assert response.json()['prompt']==expected
