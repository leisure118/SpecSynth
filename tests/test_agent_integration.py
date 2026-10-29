from pathlib import Path
from types import SimpleNamespace
import json
import subprocess
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.app import skill_library, assistants, agent_execution, agent_runners, rust
from engine.integration import legacy_adapters

@pytest.fixture
def library(tmp_path,monkeypatch):
    monkeypatch.setattr(skill_library,'SKILLS_DIR',tmp_path/'skills')
    app=FastAPI();app.include_router(skill_library.router)
    return TestClient(app)


def test_pinned_versions_survive_edit_and_archive(library):
    body={'name':'Bounds','instructions':'Version one','agents':['codex'],'enabled':True}
    created=library.post('/api/v1/skills',json=body).json()
    config=assistants.AssistantConfig(agent='codex',skill_refs=[{'id':created['id'],'version':1}])
    assert 'Version one' in skill_library.resolve_assistant(config).prompt('C')
    changed=library.put('/api/v1/skills/'+created['id'],json=body|{'instructions':'Version two','version':1})
    assert changed.status_code==200 and changed.json()['version']==2
    assert library.put('/api/v1/skills/'+created['id'],json=body|{'version':1}).status_code==409
    assert library.delete('/api/v1/skills/'+created['id']).status_code==200
    assert not library.get('/api/v1/skills').json()['items']
    snapshot=skill_library.resolve_assistant(config)
    assert 'Version one' in snapshot.prompt('C') and 'Version two' not in snapshot.prompt('C')
    assert library.get('/api/v1/skills/'+created['id']+'?version=99').status_code==404


def test_compose_forwards_only_name_and_isolates_instructions(monkeypatch,tmp_path):
    seen=[]
    def run(cmd,**kwargs):
        seen.append((cmd,kwargs));return SimpleNamespace(returncode=0)
    monkeypatch.setattr(legacy_adapters.subprocess,'run',run)
    command=['docker','compose','run','--rm','-T','autospec','true']
    legacy_adapters.run_command(command,tmp_path,agent_instructions='first $(do-not-execute)')
    legacy_adapters.run_command(command,tmp_path,agent_instructions='second')
    assert command==['docker','compose','run','--rm','-T','autospec','true']
    assert seen[0][0][3:5]==['-e','XUANJIAN_AGENT_INSTRUCTIONS']
    assert seen[0][1]['env']['XUANJIAN_AGENT_INSTRUCTIONS']=='first $(do-not-execute)'
    assert seen[1][1]['env']['XUANJIAN_AGENT_INSTRUCTIONS']=='second'
    assert 'first $(do-not-execute)' not in ' '.join(seen[0][0])


def test_preview_and_generation_resolve_same_skill_description(library,monkeypatch):
    item=library.post('/api/v1/skills',json={'name':'Bounds','instructions':'Check indices.','agents':['default']}).json()
    config=assistants.AssistantConfig(skill_refs=[{'id':item['id'],'version':1}])
    captured=[]
    monkeypatch.setattr(rust,'prepare_workflow',lambda req:captured.append(req.description) or {'prompt':req.description})
    preview=rust.prepare(rust.PrepareRequest(description='Return max.',assistant=config))
    actual=assistants.compose_description('Return max.',skill_library.resolve_assistant(config))
    assert preview['prompt']==actual and 'Check indices.' in actual


def test_c_candidate_cannot_change_program_or_drop_existing_contract():
    original=[{'path':'a.c','content':'/*@ ensures \\result == x; */ int f(int x){return x;}'}]
    with pytest.raises(ValueError,match='语义'):
        agent_execution.validate_candidates(original,[{'path':'a.c','content':'int f(int x){return 0;}'}],False,'a.c','single')
    with pytest.raises(ValueError,match='规约'):
        agent_execution.validate_candidates(original,[{'path':'a.c','content':'int f(int x){return x;}'}],False,'a.c','single')
    with pytest.raises(ValueError):
        agent_execution.validate_candidates(original,[{'path':'../a.c','content':'int f(int x){return x;}'}],False,'a.c','single')


def test_process_timeout_reaps_child_group(tmp_path):
    with pytest.raises(TimeoutError):
        agent_runners.run_process(['/bin/sh','-c','sleep 20'],cwd=tmp_path,timeout=1)


def test_runner_success_without_proof_is_not_pass(monkeypatch,tmp_path):
    monkeypatch.setattr(agent_execution,'ROOT_DIR',tmp_path)
    monkeypatch.setattr(agent_execution,'run_process',lambda *a,**kw:(0,'No verification performed',''))
    check=agent_execution.verify_candidates([{'path':'main.c','content':'int main(void){return 0;}'}],'main.c','single',tmp_path/'proof',10)
    assert not check['verified'] and check['status']=='compile_error'


def test_github_import_does_not_execute_source_and_skips_symlinks(monkeypatch,tmp_path):
    from apps.api.app import project_import
    monkeypatch.setattr(project_import,'RUNTIME_DIR',tmp_path)
    def clone(args,**kwargs):
        root=Path(args[-1]);(root/'src').mkdir(parents=True)
        (root/'src/main.rs').write_text('fn main() {}')
        (root/'.env').write_text('NOT_IMPORTED=1')
        (root/'src/external.rs').symlink_to(tmp_path/'outside.rs')
        return 0,'',''
    monkeypatch.setattr(project_import,'run_process',clone)
    data,origin=project_import.import_sources(project_import.GithubImport(repository='https://github.com/example/repo',language='Rust'))
    assert data['files']==[{'path':'src/main.rs','content':'fn main() {}'}]
    assert origin['repository']=='example/repo'
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        project_import.import_sources(project_import.GithubImport(repository='https://elsewhere.invalid/repo'))


@pytest.mark.parametrize('agent',['codex','claude-code'])
def test_cli_adapter_reads_structured_candidate_without_shell_execution(monkeypatch,tmp_path,agent):
    files=[{'path':'main.rs','content':'fn main() {}'}]
    seen=[]
    monkeypatch.setattr(agent_runners,'RUNTIME_DIR',tmp_path/'runtime')
    monkeypatch.setattr(agent_runners,'executable',lambda _: '/fake/agent')
    def execute(args,**kwargs):
        seen.append((args,kwargs))
        if agent=='codex':
            Path(args[args.index('--output-last-message')+1]).write_text(json.dumps({'files':files}))
            return 0,'',''
        return 0,json.dumps({'structured_output':{'files':files},'is_error':False}),''
    monkeypatch.setattr(agent_runners,'run_process',execute)
    assert agent_runners.generate(agent,'synthetic prompt',tmp_path/'round',10)==files
    args,kwargs=seen[0]
    assert kwargs['stdin']=='synthetic prompt'
    assert kwargs['cwd']==tmp_path/'round'
    if agent=='codex':assert args[args.index('--sandbox')+1]=='read-only'
    else:assert args[args.index('--tools')+1]==''


def test_agent_proxy_is_scoped_to_child_environment(monkeypatch):
    monkeypatch.setenv('XUANJIAN_AGENT_PROXY','http://127.0.0.1:33210')
    monkeypatch.delenv('HTTPS_PROXY',raising=False)
    env=agent_runners.agent_environment()
    import os
    assert env['HTTPS_PROXY']=='http://127.0.0.1:33210'
    assert 'HTTPS_PROXY' not in os.environ


def test_default_without_skills_preserves_legacy_prompt_and_cache():
    assert assistants.AssistantConfig().prompt('C')==''


def test_legacy_run_api_rejects_unregistered_agent():
    from apps.api.app.schemas import RunRequest
    with pytest.raises(ValueError):RunRequest(file_id='example',assistant={'agent':'arbitrary-shell'})
