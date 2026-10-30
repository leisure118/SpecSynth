"""Portable runtime installation and deployment-owned model routing."""
import json
from pathlib import Path
import pytest
import yaml
from engine.nl2verus import profiles,agent_runtime,claude_cli,dsh_cli,agents

ROOT=Path(__file__).resolve().parents[1]


def test_server_env_profiles_need_no_workstation_credentials(monkeypatch,tmp_path):
    monkeypatch.setattr(profiles,'PROFILES_PATH',tmp_path/'absent.json')
    monkeypatch.setattr(profiles,'legacy_profiles',lambda snapshot=None:{})
    monkeypatch.setenv('NL2VERUS_MODEL_BASE_URL','http://model.internal:8888/v1')
    monkeypatch.setenv('NL2VERUS_MODEL_ID','deepseek-test')
    monkeypatch.setenv('NL2VERUS_MODEL_PROTOCOLS','chat,responses,anthropic')
    monkeypatch.setenv('NL2VERUS_MODEL_API_KEY','PRIVATE-DEPLOYMENT-KEY')
    monkeypatch.setenv('NL2VERUS_MODEL_AUTH_MODE','api_key')
    rows=profiles.all_profiles()
    assert set(rows)=={'deployment-chat','deployment-responses','deployment-anthropic'}
    assert rows['deployment-anthropic']['base_url']=='http://model.internal:8888'
    assert rows['deployment-responses']['base_url'].endswith('/v1')
    assert all(row['model']=='deepseek-test' for row in rows.values())
    public=[profiles.public_profile(p) for p in rows.values()]
    assert 'PRIVATE-DEPLOYMENT-KEY' not in json.dumps(public)
    assert all(row['configured'] and not row['editable'] for row in public)
    assert not profiles.PROFILES_PATH.exists()
    monkeypatch.setenv('NL2VERUS_MODEL_PROTOCOLS','chat')
    assert set(profiles.environment_profiles())=={'deployment-chat'}


def test_runtime_binaries_live_outside_mounted_data(monkeypatch,tmp_path):
    monkeypatch.setenv('ACSL_AGENT_RUNTIME_ROOT',str(tmp_path/'image-dependencies'))
    assert agent_runtime.runtime_directory('agent-runtime')==tmp_path/'image-dependencies/agents'
    assert claude_cli.package_paths()[1].is_relative_to(tmp_path/'image-dependencies')
    for name in ('docker-compose.unified.yml','docker-compose.unified.offline.yml'):
        service=yaml.safe_load((ROOT/name).read_text())['services']['acsl-agent']
        dependency_root=service['environment']['ACSL_AGENT_RUNTIME_ROOT']
        assert dependency_root=='/opt/acsl-agent/agents'
        assert all(not dependency_root.startswith(mount.split(':')[1]+'/') for mount in service['volumes'])
    ignore=(ROOT/'.dockerignore').read_text().splitlines()
    assert 'runtime' in ignore and '.env' in ignore


def test_claude_dispatches_official_cli_not_legacy_text_bridge(monkeypatch,tmp_path):
    profile={'id':'claude-test','model':'deepseek-test','name':'DeepSeek','base_url':'http://models.internal','protocol':'anthropic','api_key':'key'}
    monkeypatch.setattr(profiles,'all_profiles',lambda:{'claude-test':profile})
    monkeypatch.setattr(agents,'_sdk_generate',lambda *a:pytest.fail('legacy tool-disabled adapter must not run'))
    seen=[]
    monkeypatch.setattr(claude_cli,'generate',lambda prompt,p:seen.append(p['model']) or {'code':'verus! {}'})
    class Runner:
        def __init__(self,**kw):self.kw=kw
    run=agents.make_runner({'agent_id':'claude','model_id':'claude-test'},Runner)
    assert run.kw['generate']('TASK','claude-test',snapshot=None)['code']=='verus! {}'
    assert seen==['deepseek-test']


def test_claude_native_tools_and_failure_identity_are_not_inferred():
    events=[{'type':'system','subtype':'init','session_id':'official-session'},
            {'type':'assistant','message':{'id':'request-1','content':[{'type':'tool_use','id':'tool-1','name':'Write','input':{'file_path':'output.rs'}}]}},
            {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'tool-1','content':'created'}]}},
            {'type':'result','subtype':'success','is_error':False,'usage':{'input_tokens':20,'output_tokens':10},'session_id':'official-session'}]
    result=claude_cli.parse_events('\n'.join(json.dumps(e) for e in events))
    assert result['complete'] and result['provider_calls']==1
    assert result['agent_events'][0]['status']=='completed'
    events[-1].update(subtype='error_during_execution',is_error=True,errors=['service unavailable'])
    failure=claude_cli.parse_events('\n'.join(json.dumps(e) for e in events))
    assert not failure['complete'] and failure['session_id']=='official-session'
    assert failure['errors']==['service unavailable']


def test_harness_exhausted_budget_retains_structured_reason():
    raw='\n'.join(json.dumps(e) for e in [
        {'type':'session','sessionId':'budget-session'},
        {'type':'status','phase':'step_start'},
        {'type':'status','phase':'turn_end','reason':{'kind':'max-tokens'}},
        {'type':'final','text':''}])
    result=dsh_cli.parse_events(raw,require_complete=False)
    assert result['reason']['kind']=='max-tokens' and not result['complete']
    assert result['provider_calls']==1 and result['session_id']=='budget-session'
