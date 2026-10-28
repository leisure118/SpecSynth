"""Local project workspace; verification delegates to the existing RunManager."""
from __future__ import annotations

import re
import threading
import uuid
from pathlib import PurePosixPath
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .config import RUNTIME_DIR, get_available_models
from .schemas import RunRequest
from .storage import JsonStore, utcnow

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
                or path.suffix not in ('.c', '.h') or any(ord(c) < 32 for c in self.path)):
            raise ValueError('Use a relative .c or .h path without traversal.')
        return self


class ProjectBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    files: list[SourceFile] = Field(min_length=1, max_length=200)

    @model_validator(mode='after')
    def validate_files(self):
        self.name = self.name.strip()
        if not self.name or len({f.path for f in self.files}) != len(self.files):
            raise ValueError('Project name and unique file paths are required.')
        if not any(f.path.endswith('.c') for f in self.files):
            raise ValueError('A project needs at least one C source file.')
        if sum(len(f.content.encode('utf-8')) for f in self.files) > 10_000_000:
            raise ValueError('Project source exceeds 10 MB.')
        return self


class ProjectSave(ProjectBody):
    revision: int = Field(ge=1)


class ProjectRun(BaseModel):
    revision: int = Field(ge=1)
    mode: Literal['single', 'termination', 'inter-modular'] = 'single'
    entry_path: str
    model_name: str = 'qwen-turbo'
    timeout_sec: int = Field(default=120, ge=10, le=3600)


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
                items.append(_summary(JsonStore._read_json(path)))
            except (OSError, ValueError, KeyError):
                continue
        return {'items': sorted(items, key=lambda x: x['updated_at'], reverse=True)}

    @router.post('', status_code=201)
    def create_project(body: ProjectBody):
        now = utcnow().isoformat()
        project = body.model_dump() | {'id': uuid.uuid4().hex, 'language': 'C',
                                      'revision': 1, 'created_at': now, 'updated_at': now, 'runs': []}
        with _LOCK:
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
            project.update(name=body.name, files=[f.model_dump() for f in body.files],
                           revision=project['revision'] + 1, updated_at=utcnow().isoformat())
            _write(project)
        return project

    @router.post('/{project_id}/runs', status_code=201)
    def run_project(project_id: str, body: ProjectRun):
        with _LOCK:
            project = _read(project_id)
            if body.revision != project['revision']:
                raise HTTPException(409, 'Save the current source revision before verification.')
            if body.model_name not in get_available_models():
                raise HTTPException(422, 'Unknown model.')
            entry = next((f for f in project['files'] if f['path'] == body.entry_path), None)
            if not entry or not entry['path'].endswith('.c'):
                raise HTTPException(422, 'Select a C source file as the entry.')
            for prior in reversed(project['runs']):
                if prior['mode'] == body.mode and (body.mode == 'inter-modular' or prior['entry_path'] == body.entry_path):
                    existing = store.read_task(prior['task_id'])
                    if existing and existing.status in ('queued', 'running'):
                        raise HTTPException(409, 'This file already has an active verification in this mode.')
            # Snapshot every submitted source; subsequent editor saves cannot change a running task.
            if body.mode == 'inter-modular':
                upload = store.create_bundle_upload([
                    {'relative_path': f['path'], 'payload': f['content'].encode('utf-8')}
                    for f in project['files']])
            else:
                upload = store.create_upload(PurePosixPath(entry['path']).name, entry['content'].encode('utf-8'))
            task = manager.submit(body.mode, RunRequest(file_id=upload['file_id'],
                model_name=body.model_name, timeout_sec=body.timeout_sec))
            project['runs'].append({'task_id': task.task_id, 'revision': project['revision'],
                                    'entry_path': body.entry_path, 'mode': body.mode,
                                    'created_at': utcnow().isoformat()})
            project['updated_at'] = utcnow().isoformat()
            _write(project)
        return {'task_id': task.task_id, 'status': task.status, 'revision': project['revision']}

    return router
