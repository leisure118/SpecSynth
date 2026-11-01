from pathlib import Path
from types import SimpleNamespace
import json
import subprocess
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.app import skill_library, assistants, rust
from acsl.application import skills as skill_service
from acsl.application import agent_execution
from acsl.adapters import agent_runtime as agent_runners
from engine.integration import legacy_adapters

@pytest.fixture
def library(tmp_path,monkeypatch):
    monkeypatch.setattr(skill_service,'skills_dir',lambda: tmp_path/'skills')
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


def test_runner_success_without_proof_is_not_pass():
    from engine.verification import framac_runtime
    check = framac_runtime._check_from_output('Invalid', 'No verification performed', '', 0.01, False, 0, 'host', 'host')
    assert not check['verified'] and check['status']=='compile_error'


def test_github_import_does_not_execute_source_and_skips_symlinks(monkeypatch,tmp_path):
    from acsl.adapters import github_import as project_import
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
    with pytest.raises(ValueError):
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


def test_retired_hierarchy_migrates_to_official_cli():
    config=assistants.AssistantConfig(agent='deepseek-harness',workflow='hierarchical-c')
    assert config.workflow=='standard'


def test_c_harness_launches_official_runtime(monkeypatch,tmp_path):
    from engine.nl2verus import dsh_cli
    from engine.autospec.src.config_manager import ConfigLoader
    files=[{'path':'main.c','content':'int main(){return 0;}'}]
    monkeypatch.setattr(ConfigLoader,'get_model_config',lambda *a:SimpleNamespace(model_name='selected',base_url='https://example.invalid/v1',api_key='private'))
    seen=[]
    def launch(prompt,profile,**kwargs):
        seen.append((profile,kwargs))
        return {'code':json.dumps({'files':files}),'agent_runtime':{'package':'@deepseek-ai/dsh'}}
    monkeypatch.setattr(dsh_cli,'generate',launch)
    assert agent_runners._generate('deepseek-harness','task',tmp_path,12,'model')==files
    assert 11 <= seen[0][1]['timeout'] <= 12
    assert {k:v for k,v in seen[0][1].items() if k!='timeout'}=={'output_format':'files','artifact_dir':tmp_path,'sub_profile':None,'require_subagent':True}
    assert 'private' not in (tmp_path/'harness-runtime.json').read_text()
    def fail(*a,**k):raise RuntimeError('secret provider error')
    monkeypatch.setattr(dsh_cli,'generate',fail)
    with pytest.raises(agent_runners.AgentCallError,match='未回退'):
        agent_runners._generate('deepseek-harness','task',tmp_path,12,'model')


def test_official_c_pipeline_binds_three_versioned_skills(library):
    refs=skill_library.ensure_bundled_skills()
    snapshot=skill_library.resolve_assistant(assistants.AssistantConfig(agent='deepseek-harness'))
    assert [s.name for s in snapshot.skills]==['spec-split','spec-orchestrate','spec-bottomup']
    assert len(refs)==3
    prompt=snapshot.prompt('C')
    assert all(name in prompt for name in ('spec-split','spec-orchestrate','spec-bottomup'))


def test_contract_tool_rejects_forged_proof_claim(monkeypatch,tmp_path):
    from engine.harness_spectool.commands import save_contract
    source=tmp_path/'leaf.acsl.c'
    source.write_text('/* === Target: leaf === */\n/*@ assigns \\nothing; ensures \\result==1; */\nint leaf(void) { return 0; }')
    db=tmp_path/'contracts.json';db.write_text(json.dumps({'leaf':{'contract':None,'status':'pending'}}))
    monkeypatch.setattr('engine.verification.framac_runtime.run_candidate',lambda *a,**k:{'verified':False})
    with pytest.raises(SystemExit):
        save_contract.run(SimpleNamespace(acsl=str(source),db=str(db),func='leaf',proved='999/999'))
    assert json.loads(db.read_text())['leaf']['status']=='pending'


@pytest.mark.parametrize('model',['','qwen35-4b-mix64','qwen35-9b-mix64'])
def test_optional_subagent_configuration(model):
    assert assistants.AssistantConfig(agent='deepseek-harness',sub_model=model).sub_model==model
    assert assistants.AssistantConfig(agent='deepseek-harness').sub_model==''
