"""HTTP routes for the project workspace.

All persistence, validation and submission rules live in
:class:`acsl.application.projects.ProjectService`; this module only maps
requests to that service and domain errors to HTTP responses.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from acsl.adapters.github_import import GithubImport
from acsl.application.projects import (
    ExampleImport,
    GenerationConfig,
    ProjectBody,
    ProjectError,
    ProjectRename,
    ProjectRun,
    ProjectSave,
    ProjectService,
)
from acsl.domain.agents import AssistantConfig
from acsl.infrastructure.settings import get_available_models, settings

PROJECTS_DIR = settings.runtime_dir / "projects"


def _project_error(exc: ProjectError) -> HTTPException:
    return HTTPException(exc.status_code, str(exc))


def create_workspace_router(manager, store, projects_dir=None):
    service = ProjectService(
        manager,
        store,
        projects_dir=projects_dir or PROJECTS_DIR,
        models=get_available_models,
    )
    router = APIRouter(prefix="/api/v1/projects", tags=["workspace"])

    def call(function, *args):
        try:
            return function(*args)
        except ProjectError as exc:
            raise _project_error(exc) from exc

    @router.get("")
    def list_projects():
        return {"items": service.list_projects()}

    @router.post("", status_code=201)
    def create_project(body: ProjectBody):
        return call(service.create_project, body)

    @router.post("/from-github", status_code=201)
    def import_github(body: GithubImport):
        return call(service.import_github, body)

    @router.post("/from-demo", status_code=201)
    def import_example(body: ExampleImport):
        return call(service.import_example, body)

    @router.get("/{project_id}")
    def get_project(project_id: str):
        return call(service.get_project, project_id)

    @router.get("/{project_id}/versions/{revision}")
    def source_version(project_id: str, revision: int):
        return call(service.source_version,project_id,revision)

    @router.put("/{project_id}/generation-config")
    def save_generation_config(project_id: str, body: GenerationConfig):
        return call(service.save_generation_config, project_id, body)

    @router.put("/{project_id}")
    def save_project(project_id: str, body: ProjectSave):
        return call(service.save_project, project_id, body)

    @router.patch("/{project_id}")
    def rename_project(project_id: str, body: ProjectRename):
        return call(service.rename_project, project_id, body)

    @router.post("/{project_id}/duplicate", status_code=201)
    def duplicate_project(project_id: str):
        return call(service.duplicate_project, project_id)

    @router.delete("/{project_id}")
    def archive_project(project_id: str):
        call(service.archive_project, project_id)
        return {"archived": True}

    @router.get("/{project_id}/export")
    def export_project(project_id: str):
        payload, filename = call(service.export_project, project_id)
        return Response(
            payload,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.put("/{project_id}/assistant")
    def save_assistant(project_id: str, body: AssistantConfig):
        return call(service.save_assistant, project_id, body)

    @router.post("/{project_id}/agent-prompt")
    def preview_agent_prompt(project_id: str, body: ProjectRun):
        return call(service.preview_agent_prompt, project_id, body)

    @router.post("/{project_id}/runs", status_code=201)
    def run_project(project_id: str, body: ProjectRun):
        return call(service.run_project, project_id, body)

    @router.post("/{project_id}/batch-runs", status_code=201)
    def batch_runs(project_id: str, body: ProjectRun):
        return call(service.batch_runs, project_id, body)

    return router
