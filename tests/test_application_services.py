"""Direct tests for framework-free application services."""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from acsl.application.projects import (
    ProjectBody,
    ProjectConflict,
    ProjectNotFound,
    ProjectRename,
    ProjectSave,
    ProjectService,
)
from acsl.infrastructure.settings import Settings


class FakeStore:
    def __init__(self) -> None:
        self.tasks = {}
        self.uploads = []

    def read_task(self, task_id):
        return self.tasks.get(task_id)

    def create_upload(self, filename, payload):
        self.uploads.append((filename, payload))
        return {"file_id": "upload", "stored_path": "upload"}

    def create_bundle_upload(self, files, root_dir=None):
        self.uploads.append((root_dir, files))
        return {"file_id": "bundle", "stored_path": "bundle"}


class FakeManager:
    def __init__(self) -> None:
        self.submissions = []

    def submit(self, mode, payload):
        self.submissions.append((mode, payload))
        return SimpleNamespace(task_id=f"task-{len(self.submissions)}", status="queued")


@pytest.fixture
def service(tmp_path):
    return ProjectService(
        FakeManager(),
        FakeStore(),
        projects_dir=tmp_path / "projects",
        models=lambda: ["test-model"],
    )


def make_project(service):
    return service.create_project(
        ProjectBody(
            name="Example",
            files=[
                {"path": "src/main.c", "content": "int main(void) { return 0; }"},
                {"path": "include/main.h", "content": "int main(void);"},
            ],
        )
    )


def test_project_service_persists_revisions_and_detects_conflicts(service):
    project = make_project(service)
    assert [row["file_count"] for row in service.list_projects()] == [2]

    saved = service.save_project(
        project["id"],
        ProjectSave(name="Renamed", files=project["files"], revision=1),
    )
    assert saved["revision"] == 2
    with pytest.raises(ProjectConflict):
        service.save_project(project["id"], ProjectSave(name="Again", files=project["files"], revision=1))

    renamed = service.rename_project(project["id"], ProjectRename(name="Final", revision=2))
    assert renamed["revision"] == 3
    assert service.get_project(project["id"])["name"] == "Final"


def test_project_service_duplicate_export_and_archive(service):
    project = make_project(service)
    cloned = service.duplicate_project(project["id"])
    assert cloned["id"] != project["id"]
    assert cloned["name"].endswith("副本")

    payload, filename = service.export_project(project["id"])
    assert filename == f"project-{project['id']}.zip"
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        assert "source/src/main.c" in bundle.namelist()
        snapshot = json.loads(bundle.read("project.json"))
        assert snapshot["name"] == "Example"

    service.archive_project(project["id"])
    assert not any(row["id"] == project["id"] for row in service.list_projects())
    with pytest.raises(ProjectNotFound):
        service.get_project("../escape")


def test_project_service_rejects_active_archive(service):
    project = make_project(service)
    project["runs"].append({"task_id": "running", "mode": "single", "entry_path": "src/main.c"})
    service._write(project)
    service.store.tasks["running"] = SimpleNamespace(status="running")
    with pytest.raises(ProjectConflict):
        service.archive_project(project["id"])


def test_settings_are_redirectable_without_touching_global_state(tmp_path):
    configured = Settings(tmp_path)
    assert configured.root_dir == tmp_path.resolve()
    assert configured.runs_dir == tmp_path.resolve() / "runtime" / "runs"
    assert configured.uploads_dir == configured.runs_dir / "uploads"
    assert configured.resolve("configs/demo_cases.json") == configured.configs_dir / "demo_cases.json"
    assert configured.relative(configured.runs_dir / "task") == "runtime/runs/task"
    assert configured.relative(Path("/outside/file")) == "/outside/file"
