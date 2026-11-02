"""NL2Verus integration using the platform's durable tasks and source snapshots."""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from math import ceil
from pathlib import PurePosixPath

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Literal
from engine.nl2verus import agents
from engine.nl2verus.profiles import all_profiles, public_profile, save_profile
from engine.nl2verus import verifier
from engine.nl2verus.b3_runner import candidate_problem, verify_b3_candidate
from engine.nl2verus.dataset import load_tasks, summarize_task
from engine.nl2verus.platform_provider import provider_status
from engine.nl2verus.workflow import WorkflowRequest, prepare_workflow
from engine.nl2verus.workflow_runs import WorkflowRuns, WorkflowRunRequest, TERMINAL
from acsl.infrastructure.settings import resolve_project_path
from acsl.adapters.storage import utcnow
from acsl.application.rust_execution import execute_rust, generated_filename, validate_generation

router = APIRouter(prefix='/api/v1/rust', tags=['rust'])


@router.get('/status')
def rust_status():
    return {'verifier': verifier.verifier_info(), 'provider': provider_status(), **agents.capabilities()}


class ModelProfileBody(BaseModel):
    id: str = Field(min_length=1,max_length=64)
    name: str = Field(min_length=1,max_length=100)
    model: str = Field(min_length=1,max_length=160,pattern=r'^[A-Za-z0-9][A-Za-z0-9._:/-]*$')
    base_url: str = Field(min_length=1,max_length=500)
    api_key: str = Field(default='',max_length=4000,repr=False)
    protocol: Literal['chat','responses','anthropic']='chat'
    auth_mode: Literal['api_key','none']='api_key'
    is_default: bool = False


@router.get('/models')
def generation_models():
    return {'items':[public_profile(p) for p in all_profiles().values()]}


@router.post('/models')
async def configure_model(request: Request):
    # Keep raw validation inputs (especially API keys) out of HTTP error details.
    if request.headers.get('content-type','').split(';')[0] != 'application/json':
        raise HTTPException(415,'请使用 JSON 提交配置。')
    origin=request.headers.get('origin')
    if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
        raise HTTPException(403,'模型配置仅允许同源页面提交。')
    try:
        raw=await request.body()
        if len(raw)>64000:raise ValueError('too large')
        body=ModelProfileBody.model_validate_json(raw)
        return save_profile(body.model_dump())
    except (ValueError,OSError):
        raise HTTPException(422,'无法保存配置；请检查编号、API 地址和密钥。') from None


class SkillBody(BaseModel):
    id: str = Field(min_length=1,max_length=64,pattern=r'^[a-z0-9][a-z0-9-]*$')
    name: str = Field(min_length=1,max_length=100)
    content: str = Field(min_length=1,max_length=48000)


@router.post('/skills')
def configure_skill(body: SkillBody):
    from engine.nl2verus.profiles import ROOT, LOCK
    import os
    path=ROOT/'runtime/generation-skills.json'
    with LOCK:
        rows=json.loads(path.read_text()) if path.is_file() else {}
        key='uploaded-'+body.id
        if len(rows)>=30 and key not in rows:
            raise HTTPException(422,'最多保存 30 个自定义 Skill。')
        rows[key]={'id':key,'name':body.name,'description':'自定义 Skill · 作为生成指令上下文加载','content':body.content}
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix('.tmp')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(rows,stream,ensure_ascii=False)
        os.replace(temp,path)
    return {k:v for k,v in rows[key].items() if k!='content'}


@router.get('/examples')
def examples(q: str = '', page: int = Query(1, ge=1)):
    rows = [r for r in load_tasks() if q.casefold() in (str(r.get('description', '')) + str(r.get('sample_id', ''))).casefold()]
    return {'items': [summarize_task(r) | {'code': r.get('verified_verus', '')} for r in rows[(page-1)*12:page*12]], 'total': len(rows)}


@router.get('/dataset/stats')
def dataset_stats():
    tasks = load_tasks()
    categories = Counter(str(task.get('category') or 'Uncategorized') for task in tasks)
    return {'total': len(tasks), 'categories': dict(sorted(categories.items())), 'source': 'NL2VBench'}


@router.get('/dataset/tasks')
def dataset_tasks(query: str = Query('', max_length=200), category: str = Query('all', max_length=40),
                  page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50)):
    query, category = query.strip().casefold(), category.strip().casefold()
    items = []
    for task in load_tasks():
        summary = summarize_task(task)
        if category != 'all' and str(summary['category']).casefold() != category:
            continue
        haystack = '\n'.join(str(summary[key]) for key in ('sample_id', 'description', 'function_signature')).casefold()
        if query and query not in haystack:
            continue
        items.append(summary)
    start = (page - 1) * page_size
    return {'items': items[start:start + page_size], 'page': page, 'page_size': page_size,
            'total': len(items), 'pages': ceil(len(items) / page_size)}


@router.get('/dataset/tree')
def dataset_tree():
    from engine.nl2verus.dataset import task_catalog
    return task_catalog(load_tasks())


@router.get('/dataset/tasks/{sample_id}/input')
def dataset_input(sample_id: str):
    for task in load_tasks():
        if task.get('sample_id') == sample_id:
            return summarize_task(task)
    raise HTTPException(404, '数据集任务不存在。')


@router.get('/dataset/tasks/{sample_id}')
def dataset_task(sample_id: str):
    for task in load_tasks():
        if task.get('sample_id') == sample_id:
            return summarize_task(task) | {'verified_verus': task.get('verified_verus') or ''}
    raise HTTPException(404, '数据集任务不存在。')


from acsl.domain.agents import AssistantConfig, compose_description

class PrepareRequest(WorkflowRequest):
    assistant: AssistantConfig | None = None


@router.post('/prepare')
def prepare(request: PrepareRequest):
    try:
        body = request.model_dump(exclude={'assistant'})
        from acsl.application.skills import resolve_assistant
        body['description'] = compose_description(request.description, resolve_assistant(request.assistant))
        return prepare_workflow(WorkflowRequest(**body))
    except (ValueError, OSError):
        raise HTTPException(422, '无法准备提示词，请检查任务与本地知识库。') from None
