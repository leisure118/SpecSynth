"""Versioned local Skill library. Runs resolve pinned references to immutable snapshots."""
from __future__ import annotations
import re
import threading
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .assistants import AgentId, AGENTS, AssistantConfig, Skill
from .config import RUNTIME_DIR
from .storage import JsonStore, utcnow

SKILLS_DIR = RUNTIME_DIR/'skills'
_LOCK = threading.RLock()
router=APIRouter(prefix='/api/v1/skills',tags=['skills'])

class SkillBody(BaseModel):
    name: str = Field(min_length=1,max_length=80)
    instructions: str = Field(min_length=1,max_length=6000)
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


def public(record):
    return record['versions'][-1] | {'archived':record.get('archived',False)}


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
    return found


@router.put('/{identifier}')
def update_skill(identifier:str,body:SkillBody):
    with _LOCK:
        record=read(identifier)
        if record.get('archived'):raise HTTPException(409,'Skill 已归档。')
        if body.version!=record['versions'][-1]['version']:raise HTTPException(409,'Skill 已更新，请刷新后重试。')
        snapshot=body.model_dump(exclude={'version'})|{'id':identifier,'version':body.version+1,'updated_at':utcnow().isoformat()}
        record['versions'].append(snapshot);write(record)
        return public(record)


@router.delete('/{identifier}')
def archive_skill(identifier:str):
    with _LOCK:
        record=read(identifier);record['archived']=True;write(record)
    return {'archived':True}


def resolve_assistant(config:AssistantConfig|None):
    if config is None:return None
    skills=[s.model_dump() for s in config.skills]
    for ref in config.skill_refs:
        item=get_skill(ref.id,ref.version)
        skills.append(Skill(**{k:item[k] for k in ('id','name','instructions','agents','enabled')}).model_dump() | {'enabled':ref.enabled and item['enabled']})
    # Clear references in the executable snapshot; the project retains pinned bindings.
    return AssistantConfig(agent=config.agent,runner_model=config.runner_model,skills=skills)
