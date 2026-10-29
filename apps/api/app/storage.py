from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import RUNS_DIR, UPLOADS_DIR, ensure_runtime_dirs, project_relative_path, resolve_project_path
from .schemas import RunTask


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JsonStore:
    def __init__(self) -> None:
        ensure_runtime_dirs()

    def create_upload(self, filename: str, payload: bytes) -> dict[str, Any]:
        file_id = uuid.uuid4().hex[:12]
        target_dir = UPLOADS_DIR / file_id
        target_dir.mkdir(parents=True, exist_ok=False)
        target_path = target_dir / filename
        target_path.write_bytes(payload)
        meta = {
            "file_id": file_id,
            "filename": filename,
            "stored_path": project_relative_path(target_path),
            "size": len(payload),
            "created_at": utcnow().isoformat(),
        }
        self._write_json(target_dir / "meta.json", meta)
        return meta

    def create_bundle_upload(self, files: list[dict[str, Any]], root_dir: str | None = None) -> dict[str, Any]:
        file_id = uuid.uuid4().hex[:12]
        target_dir = UPLOADS_DIR / file_id
        target_dir.mkdir(parents=True, exist_ok=False)
        manifest: list[dict[str, Any]] = []
        total_size = 0
        display_name = root_dir or f"{file_id}_bundle"

        for item in files:
            relative_path = str(item["relative_path"]).replace("\\", "/").lstrip("/")
            target_path = target_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = item["payload"]
            target_path.write_bytes(payload)
            total_size += len(payload)
            manifest.append(
                {
                    "relative_path": relative_path,
                    "stored_path": project_relative_path(target_path),
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )

        meta = {
            "file_id": file_id,
            "filename": display_name,
            "stored_path": project_relative_path(target_dir),
            "size": total_size,
            "kind": "bundle",
            "entry_count": len(manifest),
            "root_dir": root_dir,
            "manifest": manifest,
            "created_at": utcnow().isoformat(),
        }
        self._write_json(target_dir / "meta.json", meta)
        return meta

    def read_upload(self, file_id: str) -> dict[str, Any] | None:
        meta_path = UPLOADS_DIR / file_id / "meta.json"
        if not meta_path.exists():
            return None
        return self._read_json(meta_path)

    def create_task(self, task: RunTask) -> RunTask:
        task_dir = resolve_project_path(task.task_dir)
        task_dir.mkdir(parents=True, exist_ok=False)
        (task_dir / "artifacts").mkdir(exist_ok=True)
        (task_dir / "logs").mkdir(exist_ok=True)
        self.write_task(task)
        return task

    def write_task(self, task: RunTask) -> None:
        self._write_json(resolve_project_path(task.task_dir) / "task.json", task.model_dump(mode="json"))

    def read_task(self, task_id: str) -> RunTask | None:
        task_path = RUNS_DIR / task_id / "task.json"
        if not task_path.exists():
            return None
        return RunTask.model_validate(self._read_json(task_path))

    def write_result(self, task_id: str, result: dict[str, Any]) -> None:
        self._write_json(RUNS_DIR / task_id / "result.json", result)
        task=self.read_task(task_id)
        if task and task.metadata.get('benchmark'):
            self.write_text_artifact(task_id,'benchmark','proof.json',json.dumps(result,ensure_ascii=False))
            candidate=result.get('result_code')
            if candidate:
                self.write_text_artifact(task_id,'benchmark','candidate.c',candidate)


    def read_result(self, task_id: str) -> dict[str, Any] | None:
        result_path = RUNS_DIR / task_id / "result.json"
        if not result_path.exists():
            return None
        return self._read_json(result_path)

    def list_tasks(self, limit: int = 20) -> list[RunTask]:
        items: list[RunTask] = []
        for task_path in sorted(RUNS_DIR.glob("*/task.json"), reverse=True):
            try:
                items.append(RunTask.model_validate(self._read_json(task_path)))
            except Exception:
                continue
            if len(items) >= limit:
                break
        return items

    def copy_artifact(self, task_id: str, source: Path, category: str, filename: str | None = None) -> Path:
        task_dir = RUNS_DIR / task_id / "artifacts" / category
        task_dir.mkdir(parents=True, exist_ok=True)
        target_name = filename or source.name
        target_path = task_dir / target_name
        shutil.copy2(source, target_path)
        return target_path

    def write_text_artifact(self, task_id: str, category: str, filename: str, content: str) -> Path:
        task_dir = RUNS_DIR / task_id / "artifacts" / category
        task_dir.mkdir(parents=True, exist_ok=True)
        target_path = task_dir / filename
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def write_bytes_artifact(self, task_id: str, category: str, filename: str, content: bytes) -> Path:
        task_dir = RUNS_DIR / task_id / "artifacts" / category
        task_dir.mkdir(parents=True, exist_ok=True)
        target_path = task_dir / filename
        target_path.write_bytes(content)
        return target_path

    def list_artifacts(self, task_id: str) -> list[dict[str, Any]]:
        artifacts_dir = RUNS_DIR / task_id / "artifacts"
        if not artifacts_dir.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(artifacts_dir.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(RUNS_DIR / task_id)
            category = relative_path.parts[1] if len(relative_path.parts) > 1 else path.parent.name
            items.append(
                {
                    "name": path.name,
                    "path": project_relative_path(path),
                    "relative_path": str(relative_path).replace("\\", "/"),
                    "category": category,
                    "size": path.stat().st_size,
                }
            )
        return items

    def read_artifact_text(self, task_id: str, relative_path: str) -> dict[str, Any] | None:
        base_dir = RUNS_DIR / task_id
        target = (base_dir / relative_path).resolve()
        if base_dir.resolve() not in target.parents and target != base_dir.resolve():
            return None
        if not target.exists() or not target.is_file():
            return None
        try:
            content = target.read_text(encoding="utf-8")
            return {
                "path": project_relative_path(target),
                "relative_path": str(target.relative_to(base_dir)).replace("\\", "/"),
                "content": content,
                "encoding": "utf-8",
            }
        except UnicodeDecodeError:
            return None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        tmp_path = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        last_error: PermissionError | None = None
        for _ in range(20):
            try:
                tmp_path.replace(path)
                return
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.05)
        if last_error is not None:
            raise last_error

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        last_error: PermissionError | None = None
        for _ in range(20):
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.05)
        if last_error is not None:
            raise last_error
        return json.loads(path.read_text(encoding="utf-8"))
