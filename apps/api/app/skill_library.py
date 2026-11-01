"""Versioned local Skill library. Runs resolve pinned references to immutable snapshots."""
from __future__ import annotations
import re
import threading
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .assistants import AgentId, AGENTS, AssistantConfig, Skill, SkillReference
from .config import RUNTIME_DIR, ROOT_DIR
from .storage import JsonStore, utcnow

SKILLS_DIR = RUNTIME_DIR/'skills'
_LOCK = threading.RLock()
router=APIRouter(prefix='/api/v1/skills',tags=['skills'])

class SkillBody(BaseModel):
    name: str = Field(min_length=1,max_length=80)
    instructions: str | None = Field(default=None,min_length=1,max_length=24000)
    agents: list[AgentId] = Field(default_factory=lambda:list(AGENTS),min_length=1,max_length=4)
    enabled: bool = True
    version: int | None = Field(default=None,ge=1)


def read(identifier):
    if not re.fullmatch(r'[a-f0-9]{32}',identifier):raise HTTPException(404,'Skill 不存在。')
    path=SKILLS_DIR/(identifier+'.json')
    if not path.is_file():raise HTTPException(404,'Skill 不存在。')
    return JsonStore._read_json(path)


def write(record):
    SKILLS_DIR.mkdir(parents=True,exist_ok=True)
    JsonStore._write_json(SKILLS_DIR/(record['id']+'.json'),record)


def current(record):
    version=record.get('active_version',record['versions'][-1]['version'])
    return next(v for v in record['versions'] if v['version']==version)

def effective(record,item):
    # Agent compatibility is binding metadata, never a Skill text revision.
    agents=record.get('agent_compatibility')
    if agents and item['instructions']==record['versions'][0]['instructions']:
        return {**item,'agents':agents}
    return item

def public(record):
    return {k:v for k,v in effective(record,current(record)).items() if k!='instructions'} | {'archived':record.get('archived',False)}


def ensure_bundled_skills():
    """Import portable user-provided skills once; never overwrite edited versions."""
    refs=[]
    with _LOCK:
        for name in ('spec-split','spec-orchestrate','spec-bottomup'):
            identifier=uuid.uuid5(uuid.NAMESPACE_URL,'xuanjian:skills:'+name).hex
            path=ROOT_DIR/'resources'/'skills'/name/'SKILL.md'
            if not path.is_file():continue
            if not (SKILLS_DIR/(identifier+'.json')).is_file():
                snapshot={'id':identifier,'name':name,'instructions':path.read_text(),'agents':['deepseek-harness','codex','claude-code'],'enabled':True,'version':1,'updated_at':utcnow().isoformat()}
                write({'id':identifier,'versions':[snapshot],'archived':False})
            record=read(identifier);selected=current(record)
            refs.append({'id':identifier,'version':selected['version'],'enabled':True})
    return refs


@router.get('')
def list_skills():
    with _LOCK:
        items=[]
        for path in sorted(SKILLS_DIR.glob('*.json')):
            record=JsonStore._read_json(path)
            if not record.get('archived'):items.append(public(record))
    return {'items':items}


@router.post('',status_code=201)
def create_skill(body:SkillBody):
    if not body.instructions:raise HTTPException(422,'创建 Skill 需要由后端提供正文。')
    with _LOCK:
        identifier=uuid.uuid4().hex
        snapshot=body.model_dump(exclude={'version'})|{'id':identifier,'version':1,'updated_at':utcnow().isoformat()}
        record={'id':identifier,'versions':[snapshot],'archived':False};write(record)
        return public(record)


@router.get('/{identifier}')
def get_skill(identifier:str,version:int|None=None):
    record=read(identifier)
    if version is None:return public(record)
    found=next((v for v in record['versions'] if v['version']==version),None)
    if not found:raise HTTPException(404,'Skill 版本不存在。')
    return {k:v for k,v in effective(record,found).items() if k!='instructions'}


@router.put('/{identifier}')
def update_skill(identifier:str,body:SkillBody):
    with _LOCK:
        record=read(identifier)
        if record.get('archived'):raise HTTPException(409,'Skill 已归档。')
        if body.version!=current(record)['version']:raise HTTPException(409,'Skill 已更新，请刷新后重试。')
        snapshot=body.model_dump(exclude={'version'})|{'instructions':body.instructions or current(record)['instructions'],'id':identifier,'version':max(v['version'] for v in record['versions'])+1,'updated_at':utcnow().isoformat()}
        record['versions'].append(snapshot);record['active_version']=snapshot['version'];write(record)
        return public(record)


@router.delete('/{identifier}')
def archive_skill(identifier:str):
    with _LOCK:
        record=read(identifier);record['archived']=True;write(record)
    return {'archived':True}


def resolve_assistant(config:AssistantConfig|None):
    if config is None:return None
    if config.agent in ('deepseek-harness','codex','claude-code') and not config.skills and not config.skill_refs:
        config=config.model_copy(update={'skill_refs':[SkillReference(**r) for r in ensure_bundled_skills()]})
    if any(not s.instructions for s in config.skills):raise HTTPException(422,'Skill 正文必须在后端绑定。')
    skills=[s.model_dump() for s in config.skills]
    for ref in config.skill_refs:
        record=read(ref.id)
        item=next((v for v in record['versions'] if v['version']==ref.version),None)
        if item is None:raise HTTPException(404,'Skill 版本不存在。')
        item=effective(record,item)
        skills.append(Skill(**{k:item[k] for k in ('id','name','instructions','agents','enabled')}).model_dump() | {'enabled':ref.enabled and item['enabled']})
    # Clear references in the executable snapshot; the project retains pinned bindings.
    return AssistantConfig(agent=config.agent,runner_model=config.runner_model,workflow=config.workflow,sub_model=config.sub_model,skills=skills)
