"""Local project workspace; verification delegates to the existing RunManager."""
from __future__ import annotations

import re
import threading
import uuid
from pathlib import PurePosixPath
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .config import RUNTIME_DIR, get_available_models, resolve_project_path
from .demo_cases import get_demo_case
from .assistants import AssistantConfig, compose_description
from .schemas import RunRequest
from .storage import JsonStore, utcnow
from .project_import import GithubImport

PROJECTS_DIR = RUNTIME_DIR / 'projects'
_LOCK = threading.RLock()


class SourceFile(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(max_length=2_000_000)

    @model_validator(mode='after')
    def safe_path(self):
        path = PurePosixPath(self.path)
        if (path.is_absolute() or '\\' in self.path or ':' in self.path
                or any(p in ('', '.', '..') for p in self.path.split('/'))
                or path.suffix not in ('.c', '.h', '.rs') or any(ord(c) < 32 for c in self.path)):
            raise ValueError('Use a relative .c, .h or .rs path without traversal.')
        return self


class ProjectBody(BaseModel):
    language: Literal["C", "Rust"] = "C"
    name: str = Field(min_length=1, max_length=120)
    files: list[SourceFile] = Field(min_length=1, max_length=200)

    @model_validator(mode='after')
    def validate_files(self):
        self.name = self.name.strip()
        if not self.name or len({f.path for f in self.files}) != len(self.files):
            raise ValueError('Project name and unique file paths are required.')
        allowed = ('.rs',) if self.language == 'Rust' else ('.c', '.h')
        if any(PurePosixPath(f.path).suffix not in allowed for f in self.files):
            raise ValueError('文件扩展名必须与项目语言一致。')
        if not any(f.path.endswith('.rs' if self.language == 'Rust' else '.c') for f in self.files):
            raise ValueError('项目至少需要一个对应语言的源文件。')
        if sum(len(f.content.encode('utf-8')) for f in self.files) > 10_000_000:
            raise ValueError('Project source exceeds 10 MB.')
        return self


class ProjectSave(ProjectBody):
    revision: int = Field(ge=1)


class ProjectRename(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    revision:int=Field(ge=1)

class ProjectRun(BaseModel):
    revision: int = Field(ge=1)
    mode: Literal['single', 'termination', 'inter-modular', 'rust-verify', 'rust-generate'] = 'single'
    entry_path: str
    description: str = Field(default='', max_length=16000)
    function_signature: str = Field(default='', max_length=4000)
    rag_enabled: bool = False
    max_repair_rounds: int = Field(default=3, ge=0, le=3)
    model_name: str = 'qwen-turbo'
    timeout_sec: int = Field(default=120, ge=10, le=3600)
    execution: Literal['live', 'replay'] = 'live'
    assistant: AssistantConfig | None = None


class ExampleImport(BaseModel):
    demo_case_id: str
    mode: Literal['single', 'termination', 'inter-modular'] | None = None


def _example_files(case):
    files = []
    for item in case.get('source_manifest', []):
        if PurePosixPath(item['relative_path']).suffix in ('.c', '.h'):
            files.append({'path': item['relative_path'].replace('\\', '/'),
                          'content': resolve_project_path(item['path']).read_text(encoding='utf-8-sig')})
    if not files:
        files = [{'path': PurePosixPath(case.get('source_file') or 'main.c').name,
                  'content': case['source_code']}]
    return files


def _read(project_id: str):
    if not re.fullmatch(r'[a-f0-9]{32}', project_id):
        raise HTTPException(404, 'Project not found.')
    path = PROJECTS_DIR / project_id / 'project.json'
    if not path.is_file():
        raise HTTPException(404, 'Project not found.')
    return JsonStore._read_json(path)


def _write(project):
    directory = PROJECTS_DIR / project['id']
    directory.mkdir(parents=True, exist_ok=True)
    JsonStore._write_json(directory / 'project.json', project)


def _summary(project):
    return {k: v for k, v in project.items() if k != 'files'} | {'file_count': len(project['files'])}


def create_workspace_router(manager, store):
    router = APIRouter(prefix='/api/v1/projects', tags=['workspace'])

    def with_status(project):
        project = dict(project)
        project['runs'] = [dict(run, status=(task.status if (task := store.read_task(run['task_id'])) else 'unknown')) for run in project['runs']]
        return project

    @router.get('')
    def list_projects():
        items = []
        for path in PROJECTS_DIR.glob('*/project.json'):
            try:
                record=JsonStore._read_json(path)
                if not record.get('archived'):items.append(_summary(record))
            except (OSError, ValueError, KeyError):
                continue
        return {'items': sorted(items, key=lambda x: x['updated_at'], reverse=True)}

    @router.post('', status_code=201)
    def create_project(body: ProjectBody):
        now = utcnow().isoformat()
        project = body.model_dump() | {'id': uuid.uuid4().hex,
                                      'revision': 1, 'created_at': now, 'updated_at': now, 'runs': []}
        with _LOCK:
            _write(project)
        return project

    @router.post('/from-github', status_code=201)
    def import_github(body:GithubImport):
        from .project_import import import_sources
        data, origin=import_sources(body)
        try:
            project=create_project(ProjectBody(**data))
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from None
        project['origin']=origin
        _write(project)
        return project

    @router.post('/from-demo', status_code=201)
    def import_example(body: ExampleImport):
        try:
            case = get_demo_case(body.demo_case_id)
        except KeyError:
            raise HTTPException(404, '案例不存在。') from None
        mode = body.mode or case['modes'][0]
        if mode not in case['modes']:
            raise HTTPException(422, '该案例不支持此验证模式。')
        files = _example_files(case)
        validated = ProjectBody(name=case['title'], language='C', files=files)
        with _LOCK:
            # Opening an unchanged example again reuses its project/history.
            # Edited projects remain intact; a fresh example gets a new project.
            for path in sorted(PROJECTS_DIR.glob('*/project.json')):
                try:
                    project = JsonStore._read_json(path)
                except (OSError, ValueError, KeyError):
                    continue
                if (not project.get('archived') and (project.get('example') or {}).get('id') == case['id']
                        and project.get('files') == files):
                    return with_status(project)
            project = create_project(validated)
            project['example'] = {'id': case['id'], 'title': case['title'],
                                  'mode': mode, 'modes': case['modes'],
                                  'execution_mode': case['execution_mode'],
                                  'showcase': 'x509' if case['id'] == 'x509_inter_modular_replay' else None}
            _write(project)
            return project

    @router.get('/{project_id}')
    def get_project(project_id: str):
        return with_status(_read(project_id))

    @router.put('/{project_id}')
    def save_project(project_id: str, body: ProjectSave):
        with _LOCK:
            project = _read(project_id)
            if body.revision != project['revision']:
                raise HTTPException(409, 'Project changed in another window. Reload before saving.')
            if body.language != project.get('language', 'C'):
                raise HTTPException(422, '项目创建后不能更换语言。')
            project.update(name=body.name, files=[f.model_dump() for f in body.files],
                           revision=project['revision'] + 1, updated_at=utcnow().isoformat())
            _write(project)
        return project

    @router.patch('/{project_id}')
    def rename_project(project_id:str, body:ProjectRename):
        with _LOCK:
            project=_read(project_id)
            if body.revision!=project['revision']:raise HTTPException(409,'项目已更新，请刷新后重试。')
            if not body.name.strip():raise HTTPException(422,'请输入项目名称。')
            project.update(name=body.name.strip(),revision=project['revision']+1,updated_at=utcnow().isoformat())
            _write(project)
        return project

    @router.post('/{project_id}/duplicate',status_code=201)
    def duplicate_project(project_id:str):
        with _LOCK:
            project=_read(project_id)
            cloned=create_project(ProjectBody(name=(project['name']+' 副本')[:120],language=project.get('language','C'),files=project['files']))
            for field in ('assistant','example','origin'):
                if field in project:cloned[field]=project[field]
            _write(cloned)
        return cloned

    @router.delete('/{project_id}')
    def archive_project(project_id:str):
        with _LOCK:
            project=_read(project_id)
            if any((task:=store.read_task(r['task_id'])) and task.status in ('queued','running') for r in project['runs']):
                raise HTTPException(409,'项目仍有运行任务，请等待结束后归档。')
            project['archived']=True;_write(project)
        return {'archived':True}

    @router.get('/{project_id}/export')
    def export_project(project_id:str):
        import io,json,zipfile
        from fastapi.responses import Response
        from .skill_library import resolve_assistant
        project=_read(project_id)
        config=resolve_assistant(AssistantConfig(**project['assistant'])) if project.get('assistant') else None
        snapshot={k:project[k] for k in ('name','language','files')}
        if config:snapshot['assistant']=config.model_dump()
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as bundle:
            for f in project['files']:bundle.writestr('source/'+f['path'],f['content'])
            bundle.writestr('project.json',json.dumps(snapshot,ensure_ascii=False,indent=2))
        return Response(stream.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="project-'+project_id+'.zip"'})

    @router.put('/{project_id}/assistant')
    def save_assistant(project_id: str, body: AssistantConfig):
        with _LOCK:
            project = _read(project_id)
            from .skill_library import resolve_assistant
            resolve_assistant(body)
            project['assistant'] = body.model_dump()
            _write(project)
        return project['assistant']

    @router.post('/{project_id}/agent-prompt')
    def preview_agent_prompt(project_id:str,body:ProjectRun):
        from .agent_execution import initial_prompt
        from .skill_library import resolve_assistant
        project=_read(project_id)
        if body.revision!=project['revision']:raise HTTPException(409,'源码已更新，请保存并重试。')
        if not any(f['path']==body.entry_path for f in project['files']):raise HTTPException(422,'请选择项目中的文件。')
        config=resolve_assistant(body.assistant or AssistantConfig(**project.get('assistant',{})))
        if config.agent=='default':raise HTTPException(422,'此接口用于外部 Agent 提示词预览。')
        if sum(len(f['content'].encode()) for f in project['files'])>512*1024:raise HTTPException(422,'Agent 输入源码不能超过 512 KiB。')
        return {'prompt':initial_prompt(project['files'],body.mode,body.description,body.function_signature,config.prompt(project.get('language','C'))),'provider_calls':0}

    @router.post('/{project_id}/runs', status_code=201)
    def run_project(project_id: str, body: ProjectRun):
        with _LOCK:
            project = _read(project_id)
            if project.get('archived'):raise HTTPException(409,'项目已归档，请复制后运行。')
            if body.revision != project['revision']:
                raise HTTPException(409, 'Save the current source revision before verification.')
            rust = project.get('language') == 'Rust'
            if rust != body.mode.startswith('rust-'):
                raise HTTPException(422, '验证模式与项目语言不匹配。')
            entry = next((f for f in project['files'] if f['path'] == body.entry_path), None)
            if not entry or not entry['path'].endswith('.rs' if rust else '.c'):
                raise HTTPException(422, '请选择与项目语言匹配的源文件。')
            replay_case = None
            if body.execution == 'replay':
                example_id = (project.get('example') or {}).get('id')
                try:
                    replay_case = get_demo_case(example_id)
                except KeyError:
                    raise HTTPException(422, '当前项目没有可回放的案例。') from None
                if (rust or replay_case['execution_mode'] != 'replay'
                        or body.mode not in replay_case['modes']
                        or project['files'] != _example_files(replay_case)):
                    raise HTTPException(422, '仅支持回放未修改的原始案例；修改源码后请执行真实验证。')
                if body.mode != 'inter-modular' and body.entry_path != _example_files(replay_case)[0]['path']:
                    raise HTTPException(422, '请选择案例的原始源文件进行回放。')
            for prior in reversed(project['runs']):
                if prior['mode'] == body.mode and (body.mode == 'inter-modular' or prior['entry_path'] == body.entry_path):
                    existing = store.read_task(prior['task_id'])
                    if existing and existing.status in ('queued', 'running'):
                        raise HTTPException(409, 'This file already has an active verification in this mode.')
            from .skill_library import resolve_assistant
            assistant_config = body.assistant or (AssistantConfig(**project['assistant']) if project.get('assistant') else None)
            assistant = resolve_assistant(assistant_config)
            if not rust and (assistant is None or assistant.agent in ('default','deepseek-harness')) and body.model_name not in get_available_models():
                raise HTTPException(422, 'Unknown model.')
            if body.mode=='rust-generate' and not body.description.strip():
                raise HTTPException(422,'请输入自然语言任务。')
            if assistant and assistant.agent=='deepseek-harness' and not replay_case and body.mode!='rust-verify' and ('deepseek' not in body.model_name.lower() or body.model_name not in get_available_models()):
                raise HTTPException(422,'DeepSeek Harness 需要选择 DeepSeek 模型。')
            if assistant and assistant.agent != 'default' and not replay_case and body.mode != 'rust-verify':
                from .agent_runners import require_agent
                try:
                    require_agent(assistant.agent)
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
                if body.rag_enabled:
                    raise HTTPException(422, '外部 Agent 暂不使用内置 RAG，请关闭 RAG。')
            instructions = assistant.prompt(project.get('language', 'C')) if assistant and not replay_case else ''
            workflow = None
            if body.mode == 'rust-generate' and (not assistant or assistant.agent == 'default'):
                from engine.nl2verus.workflow_runs import WorkflowRunRequest
                from .rust import validate_generation
                try:
                    workflow = WorkflowRunRequest(request_id=uuid.uuid4().hex,
                        description=compose_description(body.description, assistant), function_signature=body.function_signature,
                        model_id=body.model_name, rag_enabled=body.rag_enabled,
                        repair_enabled=body.max_repair_rounds > 0,
                        max_repair_rounds=max(1, body.max_repair_rounds),
                        timeout_seconds=min(60, body.timeout_sec)).model_dump()
                    validate_generation(workflow)
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
            # Snapshot every submitted source; subsequent editor saves cannot change a running task.
            if body.mode == 'inter-modular' or rust or (assistant and assistant.agent!='default' and not replay_case):
                upload = store.create_bundle_upload([
                    {'relative_path': f['path'], 'payload': f['content'].encode('utf-8')}
                    for f in project['files']])
            else:
                upload = store.create_upload(PurePosixPath(entry['path']).name, entry['content'].encode('utf-8'))
            task = manager.submit(body.mode, RunRequest(file_id=upload['file_id'],
                demo_case_id=replay_case['id'] if replay_case else None,
                model_name=body.model_name, timeout_sec=body.timeout_sec,
                entry_path=body.entry_path, rust_workflow=workflow, agent_instructions=instructions,
                assistant=assistant.model_dump() if assistant else None, description=body.description,
                function_signature=body.function_signature, max_repair_rounds=body.max_repair_rounds))
            project['runs'].append({'task_id': task.task_id, 'revision': project['revision'],
                                    'entry_path': body.entry_path, 'mode': body.mode,
                                    'execution': body.execution,
                                    'assistant': assistant.model_dump() if assistant else None,
                                    'skill_refs': [r.model_dump() for r in assistant_config.skill_refs] if assistant_config else [],
                                    'created_at': utcnow().isoformat()})
            project['updated_at'] = utcnow().isoformat()
            _write(project)
        return {'task_id': task.task_id, 'status': task.status, 'revision': project['revision']}

    @router.post('/{project_id}/batch-runs',status_code=201)
    def batch_runs(project_id:str,body:ProjectRun):
        if body.mode not in ('single','rust-verify'):
            raise HTTPException(422,'批量验证支持 C 逐文件验证和直接 Verus 验证。')
        project=_read(project_id)
        entries=[f['path'] for f in project['files'] if f['path'].endswith('.rs' if project.get('language')=='Rust' else '.c')]
        if len(entries)>20:raise HTTPException(422,'单次批量验证最多 20 个文件。')
        items=[];errors=[]
        for entry in entries:
            try:items.append(run_project(project_id,body.model_copy(update={'entry_path':entry}))|{'entry_path':entry})
            except HTTPException as exc:errors.append({'entry_path':entry,'message':exc.detail})
        return {'items':items,'errors':errors}

    return router
