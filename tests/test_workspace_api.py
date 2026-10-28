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
            task = SimpleNamespace(task_id=f'task-{len(tasks)+1}', status='queued')
            tasks[task.task_id] = task
            return task
    app = FastAPI()
    app.include_router(workspace.create_workspace_router(Manager(), Store()))
    test_client = TestClient(app)
    test_client.snapshots = snapshots
    test_client.tasks = tasks
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
