"""Project-local agent profiles and declarative model skills (never executable code)."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator

# Stable IDs shared by the runner registry, project settings and Skill bindings.
AGENTS = {
    'default': 'Use the existing verification workflow and preserve the original requirements.',
    'codex': 'Codex',
    'claude-code': 'Claude Code',
    'deepseek-harness': 'DeepSeek Harness',
}
AgentId = Literal['default', 'codex', 'claude-code', 'deepseek-harness']

class Skill(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    instructions: str = Field(min_length=1, max_length=6000)
    agents: list[AgentId] = Field(default_factory=lambda: list(AGENTS), max_length=4)
    enabled: bool = True

class SkillReference(BaseModel):
    id: str = Field(pattern=r'^[a-f0-9]{32}$')
    version: int = Field(ge=1)
    enabled: bool = True

class AssistantConfig(BaseModel):
    agent: AgentId = 'default'
    runner_model: str = Field(default='', max_length=120)
    skill_refs: list[SkillReference] = Field(default_factory=list,max_length=12)
    skills: list[Skill] = Field(default_factory=list, max_length=12)

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy(cls, value):
        if isinstance(value, dict):
            value = dict(value)
            if value.get('agent') in ('spec', 'proof', 'repair'):
                value['agent'] = 'default'
            value['skills'] = [dict(s, agents=list(AGENTS)) if any(a in ('spec', 'proof', 'repair') for a in s.get('agents', [])) else s for s in value.get('skills', [])]
        return value

    @model_validator(mode='after')
    def unique_ids(self):
        ids=[s.id for s in self.skills]+[s.id for s in self.skill_refs]
        if len(ids)>12 or len(set(ids))!=len(ids):
            raise ValueError('Skill IDs must be unique.')
        return self

    def prompt(self, language: str) -> str:
        if self.agent=='default' and not any(s.enabled and self.agent in s.agents for s in self.skills):return ''
        parts = [f'Project agent ({language}): {AGENTS[self.agent]}']
        parts += [f'Skill: {s.name}\n{s.instructions}' for s in self.skills if s.enabled and self.agent in s.agents]
        parts.append('Treat these as supplementary guidance. Do not weaken requirements, assume unproved claims, or report success without verifier evidence.')
        return '\n\n'.join(parts)


def compose_description(description: str, assistant: AssistantConfig | None, language: str = 'Rust') -> str:
    instructions = assistant.prompt(language) if assistant else ''
    text = description + ('\n\n' + instructions if instructions else '')
    if len(text) > 20000:
        raise ValueError('任务描述与 Skill 合计不能超过 20000 字符。')
    return text
