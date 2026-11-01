"""Read-only benchmark catalog and re-run submissions."""
from __future__ import annotations

import hashlib
import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from acsl.adapters.storage import utcnow
from acsl.contracts.runs import RunRequest
from acsl.domain.agents import AssistantConfig
from acsl.infrastructure.settings import settings


class BenchmarkError(Exception):
    status_code = 400


class BenchmarkNotFound(BenchmarkError):
    status_code = 404


class BenchmarkConflict(BenchmarkError):
    status_code = 409


class BenchmarkValidation(BenchmarkError):
    status_code = 422


class BenchmarkRunRequest(BaseModel):
    file: str = Field(min_length=1, max_length=240)
    action: Literal["verify", "generate"] = "verify"
    source_variant: Literal["original", "annotated"] = "annotated"
    model_name: str = Field(default="qwen-turbo", max_length=120)
    assistant: AssistantConfig = Field(default_factory=AssistantConfig)
    timeout_sec: int = Field(default=200, ge=10, le=3600)
    max_repair_rounds: int = Field(default=0, ge=0, le=3)
    description: str = Field(default="", max_length=16000)


class BenchmarkCatalog:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir or settings.root_dir / "resources" / "benchmarks")

    def catalog(self) -> dict:
        return {"items": json.loads((self.data_dir / "index.json").read_text())}

    @lru_cache(maxsize=4)
    def snapshot(self, benchmark_id: str) -> dict:
        if benchmark_id not in {item["id"] for item in self.catalog()["items"]}:
            raise BenchmarkNotFound("基准不存在")
        return json.loads((self.data_dir / benchmark_id / "index.json").read_text())

    def detail(self, benchmark_id: str) -> dict:
        data = self.snapshot(benchmark_id)
        return {
            "benchmark": data["benchmark"],
            "items": [{key: value for key, value in row.items() if key != "artifacts"} for row in data["items"]],
        }

    def file_detail(self, benchmark_id: str, file: str) -> dict:
        row = next((item for item in self.snapshot(benchmark_id)["items"] if item["path"] == file), None)
        if row is None:
            raise BenchmarkNotFound("文件不存在")
        result = {key: value for key, value in row.items() if key != "artifacts"}
        for kind in ("source", "log"):
            relative = row["artifacts"].get(kind)
            result[kind] = (self.data_dir / relative).read_text(errors="replace") if relative else None
        original_relative = row["artifacts"].get("original_source")
        result["original_source"] = (
            (self.data_dir / original_relative).read_text(errors="replace") if original_relative else None
        )
        result["annotated_source"] = result["source"]
        if result["source"] is None:
            result["source"] = result["original_source"]
        result["source_kind"] = "annotated" if result["annotated_source"] is not None else "original"
        return result


class BenchmarkRunService:
    def __init__(self, manager, store, catalog: BenchmarkCatalog | None = None) -> None:
        self.manager = manager
        self.store = store
        self.catalog = catalog or BenchmarkCatalog()
        self._lock = threading.RLock()

    def history(self, benchmark_id: str, file: str) -> list[dict]:
        self.catalog.file_detail(benchmark_id, file)  # Validate exact indexed file, not a caller path.
        rows = []
        for task in self.store.list_tasks(limit=100000):
            origin = task.metadata.get("benchmark") or {}
            if origin.get("id") == benchmark_id and origin.get("file") == file:
                task, result = self.manager.ensure_materialized(task.task_id)
                rows.append(
                    {
                        "task_id": task.task_id,
                        "status": task.status,
                        "message": task.message,
                        "created_at": task.created_at.isoformat(),
                        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
                        "model_name": task.model_name,
                        "origin": origin,
                        "result": result,
                    }
                )
        return sorted(rows, key=lambda item: item["created_at"], reverse=True)

    def list_runs(self, benchmark_id: str, file: str) -> list[dict]:
        return self.history(benchmark_id, file)

    def submit_run(self, benchmark_id: str, body: BenchmarkRunRequest) -> dict:
        from acsl.adapters.agent_runtime import require_agent
        from acsl.application.skills import SkillError, resolve_assistant
        from acsl.infrastructure import settings as settings_module

        original = self.catalog.file_detail(benchmark_id, body.file)
        input_source = original["original_source"] if body.source_variant == "original" else original["source"]
        input_kind = (
            "original-source"
            if body.source_variant == "original" or original["annotated_source"] is None
            else "imported-annotated-source"
        )
        if not input_source:
            raise BenchmarkValidation("实验包未提供源码，不能重新验证此案例。")
        if len(input_source.encode()) > 256 * 1024:
            raise BenchmarkValidation("单案例源码不能超过 256 KiB。")
        try:
            assistant = resolve_assistant(body.assistant)
        except SkillError as exc:
            raise BenchmarkValidation(str(exc)) from exc
        if body.action == "generate":
            if original["status"] == "flagged" and input_kind == "imported-annotated-source":
                raise BenchmarkValidation("此历史源码存在违规假设，请先在项目工作台清理规约；本页不自动修改历史输入。")
            if assistant.agent in ("default", "deepseek-harness") and body.model_name not in settings_module.get_available_models():
                raise BenchmarkValidation("请选择已注册模型。")
            if assistant.agent == "deepseek-harness" and "deepseek" not in body.model_name.lower():
                raise BenchmarkValidation("DeepSeek Harness 需要选择 DeepSeek 模型。")
            if assistant.agent != "default":
                try:
                    require_agent(assistant.agent)
                except ValueError as exc:
                    raise BenchmarkValidation(str(exc)) from exc
        context = {
            "id": benchmark_id,
            "file": body.file,
            "action": body.action,
            "source_sha256": hashlib.sha256(input_source.encode()).hexdigest(),
            "source_kind": input_kind,
            "submitted_at": utcnow().isoformat(),
            "configuration": body.model_dump(mode="json") | {"assistant": assistant.model_dump()},
        }
        with self._lock:
            if any(row["status"] in ("queued", "running") for row in self.history(benchmark_id, body.file)):
                raise BenchmarkConflict("此案例已有运行中的任务，请等待完成。")
            upload = self.store.create_upload(body.file, input_source.encode())
            payload = RunRequest(
                file_id=upload["file_id"],
                entry_path=body.file,
                model_name=body.model_name,
                timeout_sec=body.timeout_sec,
                assistant=assistant.model_dump() if body.action == "generate" else None,
                agent_instructions=assistant.prompt("C") if body.action == "generate" else "",
                description=body.description,
                max_repair_rounds=body.max_repair_rounds,
                verification_only=body.action == "verify",
                benchmark_context=context,
            )
            task = self.manager.submit("single", payload)
        return {"task_id": task.task_id, "status": task.status, "benchmark": context}
