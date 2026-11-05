"""Tool-specific Skill snapshots preserve original versions and custom bindings."""
import pytest
from acsl.application import skills
from acsl.domain.agents import AssistantConfig
from acsl.infrastructure.settings import settings

@pytest.mark.parametrize('agent',['codex','claude-code','deepseek-harness'])
def test_verifast_uses_new_skill_and_preserves_original_and_custom(tmp_path,monkeypatch,agent):
    monkeypatch.setattr(settings,'runtime_dir',tmp_path)
    old_refs=skills.ensure_bundled_skills()
    before={ref['id']:skills.read(ref['id']) for ref in old_refs}
    custom=skills.create_skill({'name':'Project requirements','instructions':'Keep task-specific requirements.','agents':[agent],'enabled':True})
    config=AssistantConfig(agent=agent,skill_refs=[*old_refs,{'id':custom['id'],'version':1}])
    resolved=skills.resolve_assistant(config,verification_tool='verifast')
    assert {s.name for s in resolved.skills}=={'spec-verifast','Project requirements'}
    assert 'count_to_limit' in resolved.prompt('C')
    assert 'Keep task-specific requirements.' in resolved.prompt('C')
    assert config.skill_refs[0].id==old_refs[0]['id']
    assert all(skills.read(key)==record for key,record in before.items())
    assert {s.name for s in skills.resolve_assistant(config).skills}=={*skills.ACSL_SKILLS,'Project requirements'}
    catalog=skills.list_skills()
    assert len([s for s in catalog if s['name']=='spec-verifast' and s['version']==1])==1
    assert all('instructions' not in s for s in catalog)


def test_verifast_defaults_and_explicit_custom_only(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'runtime_dir',tmp_path)
    default=skills.resolve_assistant(AssistantConfig(agent='codex'),verification_tool='verifast')
    assert [s.name for s in default.skills]==['spec-verifast']
    custom=AssistantConfig(agent='codex',skills=[{'id':'project','name':'Custom','instructions':'Custom rules','agents':['codex']}])
    assert [s.name for s in skills.resolve_assistant(custom,verification_tool='verifast').skills]==['Custom']
