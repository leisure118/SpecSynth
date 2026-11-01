import io,json,zipfile
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware
from apps.api.app import skill_library,workspace
from apps.api.app.assistants import AssistantConfig
from apps.api.app.skill_privacy import SkillPrivacyMiddleware,public_payload,private_artifact

SECRET='Private Skill detailed instruction sentinel: never send this server body to a browser.'


@pytest.fixture
def system(tmp_path,monkeypatch):
    monkeypatch.setattr(skill_library,'SKILLS_DIR',tmp_path/'skills')
    monkeypatch.setattr(workspace,'PROJECTS_DIR',tmp_path/'projects')
    app=FastAPI();app.add_middleware(SkillPrivacyMiddleware);app.add_middleware(GZipMiddleware,minimum_size=1)
    app.include_router(skill_library.router)
    app.include_router(workspace.create_workspace_router(SimpleNamespace(),SimpleNamespace(read_task=lambda _:None)))
    @app.get('/api/test-export')
    def example():
        return {'prompt':SECRET,'instructions':SECRET,'metadata':{'assistant':{'skills':[{'id':'x','name':'Test','instructions':SECRET}]}},'content':json.dumps({'prompt':SECRET,'code':'int main(){return 0;}'}),'logs':{'raw':'tool output '+SECRET},'agent_runtime':{'package':'@deepseek-ai/dsh','events':[{'type':'tool_call','input':{'task':SECRET}}]}}
    return TestClient(app)


def test_skill_catalog_versions_updates_and_execution_keep_private_bodies(system):
    row=system.post('/api/v1/skills',json={'name':'Hidden','instructions':SECRET,'agents':['codex']}).json()
    for url in ['/api/v1/skills','/api/v1/skills/'+row['id'],'/api/v1/skills/'+row['id']+'?version=1']:
        response=system.get(url);assert response.status_code==200 and SECRET not in response.text and 'instructions' not in response.text
    changed=system.put('/api/v1/skills/'+row['id'],json={'name':'Renamed','agents':['codex'],'enabled':True,'version':1})
    assert changed.status_code==200 and SECRET not in changed.text
    resolved=skill_library.resolve_assistant(AssistantConfig(agent='codex',skill_refs=[{'id':row['id'],'version':2}]))
    assert SECRET in resolved.prompt('C')
    response=system.get('/api/test-export')
    assert SECRET not in response.text and 'prompt' not in response.json()
    assert 'int main' in response.json()['content']
    assert 'events' not in response.json()['agent_runtime']


def test_project_round_trip_and_zip_never_export_legacy_skill_body(system):
    p=system.post('/api/v1/projects',json={'name':'Private','language':'C','files':[{'path':'main.c','content':'int main(){return 0;}'}]}).json()
    a={'agent':'codex','skills':[{'id':'legacy','name':'Legacy','instructions':SECRET,'agents':['codex']}]}
    response=system.put('/api/v1/projects/'+p['id']+'/assistant',json=a)
    assert response.status_code==200 and SECRET not in response.text
    metadata=response.json();metadata['skills'][0]['name']='Metadata edit'
    response=system.put('/api/v1/projects/'+p['id']+'/assistant',json=metadata)
    assert response.status_code==200 and SECRET not in response.text
    assert workspace._read(p['id'])['assistant']['skills'][0]['instructions']==SECRET
    response=system.get('/api/v1/projects/'+p['id']);assert SECRET not in response.text
    response=system.get('/api/v1/projects/'+p['id']+'/export')
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert SECRET not in archive.read('project.json').decode()
        assert 'main' in archive.read('source/main.c').decode()


def test_private_artifact_paths_and_nested_prompt_json():
    assert private_artifact('artifacts/agent/harness-events.jsonl')
    assert private_artifact('artifacts/skills/spec-bottomup/SKILL.md')
    assert not private_artifact('artifacts/output/main.c')
    result=public_payload({'content':json.dumps({'prompt':'hidden','result_code':'int x;'})})
    assert 'hidden' not in result['content'] and 'int x;' in result['content']


def test_restoring_active_v1_keeps_body_history_and_agent_compatibility(system):
    row=system.post('/api/v1/skills',json={'name':'Original','instructions':SECRET,'agents':['deepseek-harness']}).json()
    system.put('/api/v1/skills/'+row['id'],json={'name':'Original','agents':['deepseek-harness','codex','claude-code'],'version':1})
    record=skill_library.read(row['id']);before=[v['instructions'] for v in record['versions']]
    record.update(active_version=1,agent_compatibility=['deepseek-harness','codex','claude-code']);skill_library.write(record)
    visible=system.get('/api/v1/skills/'+row['id']).json()
    assert visible['version']==1 and 'instructions' not in visible
    assert 'codex' in visible['agents']
    assert system.get('/api/v1/skills/'+row['id']+'?version=2').status_code==200
    resolved=skill_library.resolve_assistant(AssistantConfig(agent='codex',skill_refs=[{'id':row['id'],'version':1}]))
    assert SECRET in resolved.prompt('C')
    assert [v['instructions'] for v in skill_library.read(row['id'])['versions']]==before
    changed=system.put('/api/v1/skills/'+row['id'],json={'name':'Renamed manually','agents':['codex'],'version':1})
    assert changed.json()['version']==3
