"""Portable, read-only snapshots of imported benchmark experiments."""
import json
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from .config import ROOT_DIR

DATA_DIR = ROOT_DIR / 'resources' / 'benchmarks'
router = APIRouter(prefix='/api/v1/benchmarks', tags=['benchmarks'])

@lru_cache(maxsize=4)
def snapshot(benchmark_id):
    if benchmark_id not in {x['id'] for x in catalog()['items']}:
        raise HTTPException(404, '基准不存在')
    return json.loads((DATA_DIR / benchmark_id / 'index.json').read_text())

@router.get('')
def catalog():
    return {'items': json.loads((DATA_DIR / 'index.json').read_text())}

@router.get('/{benchmark_id}')
def detail(benchmark_id: str):
    data = snapshot(benchmark_id)
    return {'benchmark':data['benchmark'], 'items':[{k:v for k,v in r.items() if k!='artifacts'} for r in data['items']]}

@router.get('/{benchmark_id}/file')
def file_detail(benchmark_id: str, file: str):
    row = next((r for r in snapshot(benchmark_id)['items'] if r['path']==file),None)
    if row is None:
        raise HTTPException(404,'文件不存在')
    result = {k:v for k,v in row.items() if k!='artifacts'}
    for kind in ('source','log'):
        relative = row['artifacts'].get(kind)
        result[kind] = (DATA_DIR / relative).read_text(errors='replace') if relative else None
    original_relative=row['artifacts'].get('original_source')
    result['original_source']=(DATA_DIR/original_relative).read_text(errors='replace') if original_relative else None
    result['annotated_source']=result['source']
    if result['source'] is None:
        result['source']=result['original_source']
    result['source_kind']='annotated' if result['annotated_source'] is not None else 'original'
    return result

# New runs are stored separately from the immutable imported experiment bundle.
import hashlib
import threading
from typing import Literal
from pydantic import BaseModel, Field
from .assistants import AssistantConfig
from .schemas import RunRequest
from .storage import utcnow

_RUN_LOCK = threading.RLock()

class BenchmarkRunRequest(BaseModel):
    file: str = Field(min_length=1, max_length=240)
    action: Literal['verify', 'generate'] = 'verify'
    source_variant: Literal['original', 'annotated'] = 'annotated'
    model_name: str = Field(default='qwen-turbo', max_length=120)
    assistant: AssistantConfig = Field(default_factory=AssistantConfig)
    timeout_sec: int = Field(default=200, ge=10, le=3600)
    max_repair_rounds: int = Field(default=0, ge=0, le=3)
    description: str = Field(default='', max_length=16000)


def create_benchmark_runs_router(manager, store):
    runs_router = APIRouter(prefix='/api/v1/benchmarks', tags=['benchmark-runs'])

    def history(benchmark_id, file):
        file_detail(benchmark_id, file)  # Validate exact indexed file, not a caller path.
        rows=[]
        for task in store.list_tasks(limit=100000):
            origin=task.metadata.get('benchmark') or {}
            if origin.get('id')==benchmark_id and origin.get('file')==file:
                task,result=manager.ensure_materialized(task.task_id)
                rows.append({'task_id':task.task_id,'status':task.status,'message':task.message,
                             'created_at':task.created_at.isoformat(),'finished_at':task.finished_at.isoformat() if task.finished_at else None,
                             'model_name':task.model_name,'origin':origin,
                             'result':result})
        return sorted(rows,key=lambda x:x['created_at'],reverse=True)

    @runs_router.get('/{benchmark_id}/runs')
    def list_runs(benchmark_id: str, file: str):
        return {'items':history(benchmark_id,file)}

    @runs_router.post('/{benchmark_id}/runs', status_code=201)
    def submit_run(benchmark_id: str, body: BenchmarkRunRequest):
        from .config import get_available_models
        from .skill_library import resolve_assistant
        from .agent_runners import require_agent
        original=file_detail(benchmark_id,body.file)
        input_source=original['original_source'] if body.source_variant=='original' else original['source']
        input_kind='original-source' if body.source_variant=='original' or original['annotated_source'] is None else 'imported-annotated-source'
        if not input_source:
            raise HTTPException(422,'实验包未提供源码，不能重新验证此案例。')
        if len(input_source.encode())>256*1024:
            raise HTTPException(422,'单案例源码不能超过 256 KiB。')
        assistant=resolve_assistant(body.assistant)
        if body.action=='generate':
            if original['status']=='flagged' and input_kind=='imported-annotated-source':
                raise HTTPException(422,'此历史源码存在违规假设，请先在项目工作台清理规约；本页不自动修改历史输入。')
            if assistant.agent in ('default','deepseek-harness') and body.model_name not in get_available_models():
                raise HTTPException(422,'请选择已注册模型。')
            if assistant.agent=='deepseek-harness' and 'deepseek' not in body.model_name.lower():
                raise HTTPException(422,'DeepSeek Harness 需要选择 DeepSeek 模型。')
            if assistant.agent!='default':
                try: require_agent(assistant.agent)
                except ValueError as exc: raise HTTPException(422,str(exc)) from None
        context={'id':benchmark_id,'file':body.file,'action':body.action,
                 'source_sha256':hashlib.sha256(input_source.encode()).hexdigest(),
                 'source_kind':input_kind,'submitted_at':utcnow().isoformat(),
                 'configuration':body.model_dump(mode='json') | {'assistant':assistant.model_dump()}}
        with _RUN_LOCK:
            if any(r['status'] in ('queued','running') for r in history(benchmark_id,body.file)):
                raise HTTPException(409,'此案例已有运行中的任务，请等待完成。')
            upload=store.create_upload(body.file,input_source.encode())
            payload=RunRequest(file_id=upload['file_id'],entry_path=body.file,
                model_name=body.model_name,timeout_sec=body.timeout_sec,
                assistant=assistant.model_dump() if body.action=='generate' else None,
                agent_instructions=assistant.prompt('C') if body.action=='generate' else '',
                description=body.description,max_repair_rounds=body.max_repair_rounds,
                verification_only=body.action=='verify',benchmark_context=context)
            task=manager.submit('single',payload)
        return {'task_id':task.task_id,'status':task.status,'benchmark':context}

    return runs_router
