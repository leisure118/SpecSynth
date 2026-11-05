"""Project workspace use cases: persistence, snapshots, submission and export."""
from __future__ import annotations

import io
import hashlib
import json
import re
import shutil
import threading
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, Literal

from pydantic import BaseModel, Field, model_validator

from acsl.adapters.github_import import GithubImport, GithubImportError, import_sources
from acsl.adapters.storage import JsonStore, utcnow
from acsl.application.demo_cases import get_demo_case
from acsl.application.privacy import public_payload
from acsl.application.skills import SkillError, resolve_assistant
from acsl.contracts.runs import RunRequest
from acsl.domain.agents import AssistantConfig, compose_description
from acsl.infrastructure.settings import get_available_models, resolve_project_path, settings


class ProjectError(Exception):
    status_code = 400


class ProjectNotFound(ProjectError):
    status_code = 404


class ProjectConflict(ProjectError):
    status_code = 409


class ProjectValidation(ProjectError):
    status_code = 422


class SourceFile(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(max_length=2_000_000)

    @model_validator(mode="after")
    def safe_path(self):
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or "\\" in self.path
            or ":" in self.path
            or any(part in ("", ".", "..") for part in self.path.split("/"))
            or path.suffix not in (".c", ".h", ".rs")
            or any(ord(char) < 32 for char in self.path)
        ):
            raise ValueError("Use a relative .c, .h or .rs path without traversal.")
        return self


class ProjectBody(BaseModel):
    language: Literal["C", "Rust"] = "C"
    name: str = Field(min_length=1, max_length=120)
    files: list[SourceFile] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_files(self):
        self.name = self.name.strip()
        if not self.name or len({item.path for item in self.files}) != len(self.files):
            raise ValueError("Project name and unique file paths are required.")
        allowed = (".rs",) if self.language == "Rust" else (".c", ".h")
        if any(PurePosixPath(item.path).suffix not in allowed for item in self.files):
            raise ValueError("文件扩展名必须与项目语言一致。")
        if not any(item.path.endswith(".rs" if self.language == "Rust" else ".c") for item in self.files):
            raise ValueError("项目至少需要一个对应语言的源文件。")
        if sum(len(item.content.encode("utf-8")) for item in self.files) > 10_000_000:
            raise ValueError("Project source exceeds 10 MB.")
        return self


class ProjectSave(ProjectBody):
    revision: int = Field(ge=1)
    parent_task_id: str | None = Field(default=None,max_length=100)


class VerificationToolConfig(BaseModel):
    verification_tool: Literal["framac", "verifast"]


class ProjectRename(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=1)


class ProjectRun(BaseModel):
    verification_tool: Literal["framac", "verifast"] = "framac"
    resume_task_id: str | None = Field(default=None,max_length=100)
    revision: int = Field(ge=1)
    mode: Literal["single", "termination", "inter-modular", "rust-verify", "rust-generate"] = "single"
    entry_path: str
    description: str = Field(default="", max_length=16000)
    function_signature: str = Field(default="", max_length=4000)
    rag_enabled: bool = False
    max_repair_rounds: int = Field(default=3, ge=0, le=3)
    agent_id: Literal["direct", "codex", "claude", "deepseek-harness"] = "direct"
    skill_ids: list[str] = Field(default_factory=list, max_length=8)
    sample_id: str | None = Field(default=None, max_length=200)
    source_name: str = Field(default="", max_length=240)
    model_name: str = "qwen-turbo"
    timeout_sec: int = Field(default=200, ge=10, le=3600)
    adaptive_timeout: bool = True
    execution: Literal["live", "replay"] = "live"
    verification_only: bool = False
    assistant: AssistantConfig | None = None


class GenerationConfig(BaseModel):
    agent_id: Literal["direct", "codex", "claude", "deepseek-harness"]
    model_id: str = Field(min_length=1, max_length=200)
    skill_ids: list[str] = Field(default_factory=list, max_length=8)


class ExampleImport(BaseModel):
    demo_case_id: str
    mode: Literal["single", "termination", "inter-modular"] | None = None


class ProjectService:
    """Application service shared by the HTTP router and tests."""

    def __init__(
        self,
        manager,
        store: JsonStore,
        *,
        projects_dir: Path | None = None,
        models: Callable[[], list[str]] = get_available_models,
    ) -> None:
        self.manager = manager
        self.store = store
        self.projects_dir = Path(projects_dir or settings.runtime_dir / "projects")
        self.models = models
        self._lock = threading.RLock()

    @staticmethod
    def _resolve_assistant(config, verification_tool="framac"):
        try:
            return resolve_assistant(config, verification_tool=verification_tool)
        except SkillError as exc:
            raise ProjectValidation(str(exc)) from exc

    @staticmethod
    def _hydrate_private_skills(config, previous):
        if config is None:
            return None
        saved = {item["id"]: item.get("instructions", "") for item in (previous or {}).get("skills", [])}
        for skill in config.skills:
            if not skill.instructions:
                skill.instructions = saved.get(skill.id, "")
                if not skill.instructions:
                    raise ProjectValidation("此 Skill 缺少后端绑定的正文。")
        return config

    def _read(self, project_id: str) -> dict:
        if not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise ProjectNotFound("Project not found.")
        path = self.projects_dir / project_id / "project.json"
        if not path.is_file():
            raise ProjectNotFound("Project not found.")
        return JsonStore._read_json(path)

    def _write(self, project: dict) -> None:
        directory = self.projects_dir / project["id"]
        directory.mkdir(parents=True, exist_ok=True)
        JsonStore._write_json(directory / "project.json", project)

    @staticmethod
    def _example_files(case: dict) -> list[dict]:
        files = []
        for item in case.get("source_manifest", []):
            if PurePosixPath(item["relative_path"]).suffix in (".c", ".h"):
                files.append(
                    {
                        "path": item["relative_path"].replace("\\", "/"),
                        "content": resolve_project_path(item["path"]).read_text(encoding="utf-8-sig"),
                    }
                )
        if not files:
            files = [
                {
                    "path": PurePosixPath(case.get("source_file") or "main.c").name,
                    "content": case["source_code"],
                }
            ]
        return files

    def _summary(self, project: dict) -> dict:
        return {key: value for key, value in project.items() if key != "files"} | {
            "file_count": len(project["files"])
        }

    def _with_status(self, project: dict) -> dict:
        project = dict(project)
        project["runs"] = [
            dict(run, status=(task.status if (task := self.store.read_task(run["task_id"])) else "unknown"))
            for run in project["runs"]
        ]
        return project

    def list_projects(self) -> list[dict]:
        items = []
        for path in self.projects_dir.glob("*/project.json"):
            try:
                record = JsonStore._read_json(path)
                if not record.get("archived"):
                    items.append(self._summary(record))
            except (OSError, ValueError, KeyError):
                continue
        return sorted(items, key=lambda item: item["updated_at"], reverse=True)

    def create_project(self, body: ProjectBody) -> dict:
        now = utcnow().isoformat()
        project = body.model_dump() | {
            "id": uuid.uuid4().hex,
            "revision": 1,
            "created_at": now,
            "updated_at": now,
            "runs": [],
        }
        with self._lock:
            self._write(project)
        return project

    def import_github(self, body: GithubImport) -> dict:
        try:
            data, origin = import_sources(body)
            project = self.create_project(ProjectBody(**data))
        except (GithubImportError, ValueError) as exc:
            raise ProjectValidation(str(exc)) from exc
        project["origin"] = origin
        self._write(project)
        return project

    def import_example(self, body: ExampleImport) -> dict:
        try:
            case = get_demo_case(body.demo_case_id)
        except KeyError as exc:
            raise ProjectNotFound("案例不存在。") from exc
        mode = body.mode or case["modes"][0]
        if mode not in case["modes"]:
            raise ProjectValidation("该案例不支持此验证模式。")
        files = self._example_files(case)
        ProjectBody(name=case["title"], language="C", files=files)
        with self._lock:
            # Opening an unchanged example again reuses its project/history.
            # Edited projects remain intact; a fresh example gets a new project.
            for path in sorted(self.projects_dir.glob("*/project.json")):
                try:
                    project = JsonStore._read_json(path)
                except (OSError, ValueError, KeyError):
                    continue
                if (
                    not project.get("archived")
                    and (project.get("example") or {}).get("id") == case["id"]
                    and project.get("files") == files
                ):
                    return self._with_status(project)
            project = self.create_project(ProjectBody(name=case["title"], language="C", files=files))
            project["example"] = {
                "id": case["id"],
                "title": case["title"],
                "mode": mode,
                "modes": case["modes"],
                "execution_mode": case["execution_mode"],
                "showcase": "x509" if case["id"] == "x509_inter_modular_replay" else None,
            }
            self._write(project)
            return project

    def get_project(self, project_id: str) -> dict:
        return self._with_status(self._read(project_id))

    def save_generation_config(self, project_id: str, body: GenerationConfig) -> dict:
        from engine.nl2verus.agents import validate_selection

        with self._lock:
            project = self._read(project_id)
            if project.get("language") != "Rust":
                raise ProjectValidation("此配置用于 Rust / Verus 自然语言生成。")
            try:
                validate_selection(body.agent_id, body.model_id, body.skill_ids)
            except ValueError as exc:
                raise ProjectValidation(str(exc)) from exc
            generation = body.model_dump() | {"updated_at": utcnow().isoformat()}
            project["generation_config"] = generation
            self._write(project)
        return generation

    def save_project(self, project_id: str, body: ProjectSave) -> dict:
        with self._lock:
            project = self._read(project_id)
            if body.revision != project["revision"]:
                raise ProjectConflict("Project changed in another window. Reload before saving.")
            if body.language != project.get("language", "C"):
                raise ProjectValidation("项目创建后不能更换语言。")
            if body.parent_task_id and not any(r['task_id']==body.parent_task_id for r in project['runs']):
                raise ProjectValidation('人工版本关联的 Agent 任务不属于当前项目。')
            saved_files=[item.model_dump() for item in body.files]
            if project.get('language','C')=='C':
                from engine.verification.spec_edit import only_spec_changes
                incoming={f['path']:f['content'] for f in saved_files}
                for old in project['files']:
                    if old['path'] not in incoming or not only_spec_changes(old['content'],incoming[old['path']]):
                        raise ProjectValidation('仅允许修改规约，不能修改或删除原始 C 源码：'+old['path'])
            canonical=lambda rows: sorted((f['path'],f['content']) for f in rows)
            if canonical(saved_files)==canonical(project['files']):
                if body.name!=project['name']:
                    project.update(name=body.name,revision=project['revision']+1,updated_at=utcnow().isoformat())
                    self._write(project)
                return project
            fingerprints=sorted((f['path'],hashlib.sha256(f['content'].encode()).hexdigest()) for f in saved_files)
            previous=next((v for v in project.get('source_versions',[]) if sorted((f['path'],f['sha256']) for f in v['files'])==fingerprints),None)
            if previous:
                project.update(name=body.name,files=saved_files,revision=project['revision']+1,current_human_revision=previous['revision'],updated_at=utcnow().isoformat())
                self._write(project)
                return project
            new_revision=project['revision']+1
            version_dir=self.projects_dir/project_id/'versions'/f'v{new_revision}'
            # Preserve the previous source too; snapshots are never compiled as extra project files.
            version_dir.mkdir(parents=True,exist_ok=False)
            JsonStore._write_json(version_dir/'before.json',{'revision':project['revision'],'files':project['files']})
            saved_files=[item.model_dump() for item in body.files]
            JsonStore._write_json(version_dir/'human.json',{'revision':new_revision,'origin':'human','parent_task_id':body.parent_task_id,'files':saved_files})
            for item in body.files:
                path=PurePosixPath(item.path)
                target=version_dir/'human'/path.parent/(path.stem+f'.human.v{new_revision}'+path.suffix)
                target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item.content,encoding='utf-8')
            project.setdefault('source_versions',[]).append({'revision':new_revision,'origin':'human','parent_task_id':body.parent_task_id,'created_at':utcnow().isoformat(),
                'files':[{'path':f.path,'sha256':hashlib.sha256(f.content.encode()).hexdigest()} for f in body.files]})
            project.update(
                name=body.name,
                files=saved_files,
                revision=project["revision"] + 1,
                current_human_revision=new_revision,
                updated_at=utcnow().isoformat(),
            )
            self._write(project)
        return project

    def deduplicate_source_versions(self, project_id: str) -> dict:
        """Remove exact duplicate human snapshots; retain revision aliases for old links."""
        with self._lock:
            project=self._read(project_id)
            seen={};kept=[];duplicates=[]
            aliases=dict(project.get('source_version_aliases',{}))
            for version in sorted(project.get('source_versions',[]),key=lambda v:v['revision']):
                revision=version['revision']
                if not isinstance(revision,int) or revision<1:raise ProjectValidation('Invalid source revision')
                directory=self.projects_dir/project_id/'versions'/f'v{revision}'
                snapshot=directory/'human.json'
                if not snapshot.is_file():
                    kept.append(version);continue
                data=JsonStore._read_json(snapshot)
                key=tuple(sorted((f['path'],f['content']) for f in data['files']))
                if key not in seen:
                    seen[key]=revision;kept.append(version)
                else:
                    aliases[str(revision)]=seen[key];duplicates.append(directory)
            if not duplicates:return {'deleted':0,'remaining':len(kept)}
            for old,target in list(aliases.items()):
                while str(target) in aliases:target=aliases[str(target)]
                aliases[old]=target
            project['source_versions']=kept
            project['source_version_aliases']=aliases
            current=project.get('current_human_revision',project['revision'])
            project['current_human_revision']=aliases.get(str(current),current)
            self._write(project)
            for directory in duplicates:
                if directory.is_symlink():directory.unlink()
                else:shutil.rmtree(directory)
            return {'deleted':len(duplicates),'remaining':len(kept)}

    def source_version(self, project_id: str, revision: int) -> dict:
        project=self._read(project_id)
        revision=project.get('source_version_aliases',{}).get(str(revision),revision)
        if not any(v['revision']==revision for v in project.get('source_versions',[])):
            raise ProjectNotFound('人工版本不存在。')
        return JsonStore._read_json(self.projects_dir/project_id/'versions'/f'v{revision}'/'human.json')

    def rename_project(self, project_id: str, body: ProjectRename) -> dict:
        with self._lock:
            project = self._read(project_id)
            if body.revision != project["revision"]:
                raise ProjectConflict("项目已更新，请刷新后重试。")
            if not body.name.strip():
                raise ProjectValidation("请输入项目名称。")
            project.update(
                name=body.name.strip(),
                revision=project["revision"] + 1,
                updated_at=utcnow().isoformat(),
            )
            self._write(project)
        return project

    def duplicate_project(self, project_id: str) -> dict:
        with self._lock:
            project = self._read(project_id)
            cloned = self.create_project(
                ProjectBody(
                    name=(project["name"] + " 副本")[:120],
                    language=project.get("language", "C"),
                    files=project["files"],
                )
            )
            for field in ("assistant", "example", "origin"):
                if field in project:
                    cloned[field] = project[field]
            self._write(cloned)
        return cloned

    def archive_project(self, project_id: str) -> None:
        with self._lock:
            project = self._read(project_id)
            if any(
                (task := self.store.read_task(run["task_id"])) and task.status in ("queued", "running")
                for run in project["runs"]
            ):
                raise ProjectConflict("项目仍有运行任务，请等待结束后归档。")
            project["archived"] = True
            self._write(project)

    def export_project(self, project_id: str) -> tuple[bytes, str]:
        project = self._read(project_id)
        config = self._resolve_assistant(AssistantConfig(**project["assistant"])) if project.get("assistant") else None
        snapshot = {key: project[key] for key in ("name", "language", "files")}
        if config:
            snapshot["assistant"] = config.model_dump()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as bundle:
            for item in project["files"]:
                bundle.writestr("source/" + item["path"], public_payload(item["content"]))
            bundle.writestr("project.json", json.dumps(public_payload(snapshot), ensure_ascii=False, indent=2))
        return stream.getvalue(), f"project-{project_id}.zip"

    def save_verification_tool(self, project_id: str, body: VerificationToolConfig) -> dict:
        with self._lock:
            project=self._read(project_id)
            if project.get('language')=='Rust':raise ProjectValidation('Rust 项目使用 Verus。')
            project['verification_tool']=body.verification_tool
            self._write(project)
        return {'verification_tool':body.verification_tool}

    def save_assistant(self, project_id: str, body: AssistantConfig) -> dict:
        with self._lock:
            project = self._read(project_id)
            body = self._hydrate_private_skills(body, project.get("assistant"))
            self._resolve_assistant(body)
            project["assistant"] = body.model_dump()
            self._write(project)
        return project["assistant"]

    def preview_agent_prompt(self, project_id: str, body: ProjectRun) -> dict:
        project = self._read(project_id)
        if body.revision != project["revision"]:
            raise ProjectConflict("源码已更新，请保存并重试。")
        if not any(item["path"] == body.entry_path for item in project["files"]):
            raise ProjectValidation("请选择项目中的文件。")
        config = self._resolve_assistant(
            self._hydrate_private_skills(
                body.assistant or AssistantConfig(**project.get("assistant", {})),
                project.get("assistant"),
            )
        )
        if config.agent == "default":
            raise ProjectValidation("此接口用于外部 Agent 提示词预览。")
        if sum(len(item["content"].encode()) for item in project["files"]) > 512 * 1024:
            raise ProjectValidation("Agent 输入源码不能超过 512 KiB。")
        return {"message": "Skill 正文与执行提示词仅由后端加载。", "provider_calls": 0}

    def _replay_case(self, project: dict, body: ProjectRun):
        example_id = (project.get("example") or {}).get("id")
        try:
            replay_case = get_demo_case(example_id)
        except KeyError as exc:
            raise ProjectValidation("当前项目没有可回放的案例。") from exc
        rust = project.get("language") == "Rust"
        if (
            rust
            or replay_case["execution_mode"] != "replay"
            or body.mode not in replay_case["modes"]
            or project["files"] != self._example_files(replay_case)
        ):
            raise ProjectValidation("仅支持回放未修改的原始案例；修改源码后请执行真实验证。")
        if body.mode != "inter-modular" and body.entry_path != self._example_files(replay_case)[0]["path"]:
            raise ProjectValidation("请选择案例的原始源文件进行回放。")
        return replay_case

    def run_project(self, project_id: str, body: ProjectRun) -> dict:
        with self._lock:
            project = self._read(project_id)
            if project.get("archived"):
                raise ProjectConflict("项目已归档，请复制后运行。")
            if body.revision != project["revision"]:
                raise ProjectConflict("Save the current source revision before verification.")
            rust = project.get("language") == "Rust"
            if rust != body.mode.startswith("rust-"):
                raise ProjectValidation("验证模式与项目语言不匹配。")
            entry = next((item for item in project["files"] if item["path"] == body.entry_path), None)
            if not entry or not entry["path"].endswith(".rs" if rust else ".c"):
                raise ProjectValidation("请选择与项目语言匹配的源文件。")
            if body.verification_tool == "verifast" and (rust or body.mode != "single" or body.execution != "live"):
                raise ProjectValidation("VeriFast 当前支持 C 单文件规约生成与验证。")
            project['verification_tool']=body.verification_tool
            replay_case = None
            if body.execution == "replay":
                replay_case = self._replay_case(project, body)
            for prior in reversed(project["runs"]):
                if prior["mode"] == body.mode and (
                    body.mode == "inter-modular" or prior["entry_path"] == body.entry_path
                ):
                    existing = self.store.read_task(prior["task_id"])
                    if existing and existing.status in ("queued", "running"):
                        raise ProjectConflict("This file already has an active verification in this mode.")
            manual_context=None
            if body.resume_task_id:
                prior=next((r for r in project['runs'] if r['task_id']==body.resume_task_id and r['entry_path']==body.entry_path),None)
                if not prior:raise ProjectValidation('继续验证的任务不属于当前文件。')
                previous=self.store.read_result(body.resume_task_id)
                if not previous:raise ProjectConflict('请等待原任务结束后继续验证。')
                manual_context={'parent_task_id':body.resume_task_id,'input_revision':project['revision'],'input_origin':'human',
                    'diagnostics':str((previous.get('logs') or {}).get('raw') or previous.get('summary',''))[-16000:]}
            if body.verification_tool == "verifast" and body.verification_only:
                if rust or body.mode != "single" or body.execution != "live":
                    raise ProjectValidation("VeriFast 当前支持 C 文件直接验证。")
                from engine.verification.verifast_runtime import validate_files
                try:
                    validate_files(project["files"], body.entry_path)
                except ValueError as exc:
                    raise ProjectValidation(str(exc)) from exc
                upload = self.store.create_bundle_upload([{"relative_path":f["path"],"payload":f["content"].encode()} for f in project["files"]])
                task = self.manager.submit("single", RunRequest(file_id=upload["file_id"], entry_path=body.entry_path,
                    verification_tool="verifast", verification_only=True, timeout_sec=body.timeout_sec, adaptive_timeout=False))
                project["runs"].append({"task_id": task.task_id, "revision": project["revision"],
                    "entry_path": body.entry_path, "mode": "single", "execution": "live", "verification_tool": "verifast",
                    "verification_only": True, "assistant": None, "skill_refs": [], "created_at": utcnow().isoformat()})
                project["updated_at"] = utcnow().isoformat()
                self._write(project)
                return {"task_id": task.task_id, "status": task.status, "revision": project["revision"]}
            if body.verification_only:
                if rust or body.mode != "single":
                    raise ProjectValidation("仅验证仅支持 C 单文件模式。")
                if body.execution == "replay":
                    raise ProjectValidation("仅验证不支持回放。")
                if not re.search(r"/\*@|//@", entry["content"]):
                    raise ProjectValidation("当前文件没有 ACSL 规约，无法直接验证。请先生成或添加规约。")
                upload = self.store.create_upload(PurePosixPath(entry["path"]).name, entry["content"].encode("utf-8"))
                task = self.manager.submit(
                    "single",
                    RunRequest(
                        file_id=upload["file_id"],
                        model_name=body.model_name,
                        timeout_sec=body.timeout_sec,
                        adaptive_timeout=body.adaptive_timeout,
                        entry_path=body.entry_path,
                        verification_only=True,
                        max_repair_rounds=0,
                    ),
                )
                project["runs"].append(
                    {
                        "task_id": task.task_id,
                        "revision": project["revision"],
                        "entry_path": body.entry_path,
                        "mode": "single",
                        "execution": "live",
                        "verification_only": True,
                        "assistant": None,
                        "skill_refs": [],
                        "created_at": utcnow().isoformat(),
                    }
                )
                project["updated_at"] = utcnow().isoformat()
                self._write(project)
                return {"task_id": task.task_id, "status": task.status, "revision": project["revision"]}

            assistant_config = (
                body.assistant
                or (AssistantConfig(**project["assistant"]) if project.get("assistant") else None)
            )
            assistant_config = self._hydrate_private_skills(assistant_config, project.get("assistant"))
            assistant = self._resolve_assistant(assistant_config, verification_tool=body.verification_tool)
            if not rust and (assistant is None or assistant.agent in ("default", "deepseek-harness")) and body.model_name not in self.models():
                raise ProjectValidation("Unknown model.")
            if body.mode == "rust-generate" and not body.description.strip():
                raise ProjectValidation("请输入自然语言任务。")
            if (
                assistant
                and assistant.agent == "deepseek-harness"
                and not replay_case
                and body.mode != "rust-verify"
                and ("deepseek" not in body.model_name.lower() or body.model_name not in self.models())
            ):
                raise ProjectValidation("DeepSeek Harness 需要选择 DeepSeek 模型。")
            if assistant and assistant.agent != "default" and not replay_case and body.mode != "rust-verify":
                from acsl.adapters.agent_runtime import require_agent

                try:
                    require_agent(assistant.agent)
                except ValueError as exc:
                    raise ProjectValidation(str(exc)) from exc
                if body.rag_enabled:
                    raise ProjectValidation("外部 Agent 暂不使用内置 RAG，请关闭 RAG。")
            if body.verification_tool == "verifast" and (not assistant or assistant.agent == "default"):
                raise ProjectValidation("请为 VeriFast 规约生成选择 Codex、Claude Code 或 DeepSeek Harness。")
            instructions = assistant.prompt(project.get("language", "C")) if assistant and not replay_case else ""
            workflow = None
            if body.mode == "rust-generate" and (not assistant or assistant.agent == "default"):
                from engine.nl2verus.workflow_runs import WorkflowRunRequest
                from acsl.application.rust_execution import validate_generation

                try:
                    workflow = WorkflowRunRequest(
                        request_id=uuid.uuid4().hex,
                        description=compose_description(body.description, assistant),
                        function_signature=body.function_signature,
                        sample_id=body.sample_id,
                        model_id=body.model_name,
                        rag_enabled=body.rag_enabled,
                        repair_enabled=body.max_repair_rounds > 0,
                        max_repair_rounds=max(1, body.max_repair_rounds),
                        timeout_seconds=min(60, body.timeout_sec),
                    ).model_dump()
                    from engine.nl2verus import agents
                    from engine.nl2verus.profiles import all_profiles, configured_profiles, public_profile

                    managed = body.model_name in configured_profiles()
                    workflow.update(
                        agent_id=body.agent_id,
                        skill_ids=body.skill_ids,
                        managed_profile=managed,
                        source_name=body.source_name,
                    )
                    validate_generation(workflow)
                    workflow["skill_snapshot"] = agents.snapshot_skills(body.skill_ids)
                    profile = all_profiles().get(body.model_name)
                    if profile:
                        workflow["model_profile"] = public_profile(profile)
                    if body.sample_id:
                        from engine.nl2verus.dataset import load_tasks

                        row = next((item for item in load_tasks() if item.get("sample_id") == body.sample_id), None)
                        if (
                            not row
                            or row.get("description") != body.description
                            or (row.get("function_signature") or "") != body.function_signature
                        ):
                            raise ValueError("数据集任务已修改，请切换为自定义任务后运行。")
                except ValueError as exc:
                    raise ProjectValidation(str(exc)) from exc
            if body.mode == "inter-modular" or rust or (assistant and assistant.agent != "default" and not replay_case):
                upload = self.store.create_bundle_upload(
                    [
                        {"relative_path": item["path"], "payload": item["content"].encode("utf-8")}
                        for item in project["files"]
                    ]
                )
            else:
                upload = self.store.create_upload(PurePosixPath(entry["path"]).name, entry["content"].encode("utf-8"))
            task = self.manager.submit(
                body.mode,
                RunRequest(
                    file_id=upload["file_id"],
                    demo_case_id=replay_case["id"] if replay_case else None,
                    model_name=body.model_name,
                    timeout_sec=body.timeout_sec,
                    adaptive_timeout=body.adaptive_timeout,
                    entry_path=body.entry_path,
                    rust_workflow=workflow,
                    manual_context=manual_context,
                    verification_tool=body.verification_tool,
                    agent_instructions=instructions,
                    assistant=assistant.model_dump() if assistant else None,
                    description=body.description,
                    function_signature=body.function_signature,
                    max_repair_rounds=body.max_repair_rounds,
                ),
            )
            project["runs"].append(
                {
                    "task_id": task.task_id,
                    "revision": project["revision"],
                    "entry_path": body.entry_path,
                    "mode": body.mode,
                    "verification_tool": body.verification_tool,
                    "execution": body.execution,
                    "assistant": assistant.model_dump() if assistant else None,
                    "skill_refs": [ref.model_dump() for ref in assistant_config.skill_refs] if assistant_config else [],
                    "created_at": utcnow().isoformat(),
                }
            )
            project["updated_at"] = utcnow().isoformat()
            self._write(project)
            return {"task_id": task.task_id, "status": task.status, "revision": project["revision"]}

    def batch_runs(self, project_id: str, body: ProjectRun) -> dict:
        if body.mode not in ("single", "rust-verify"):
            raise ProjectValidation("批量验证支持 C 逐文件验证和直接 Verus 验证。")
        project = self._read(project_id)
        suffix = ".rs" if project.get("language") == "Rust" else ".c"
        entries = [item["path"] for item in project["files"] if item["path"].endswith(suffix)]
        if len(entries) > 20:
            raise ProjectValidation("单次批量验证最多 20 个文件。")
        items, errors = [], []
        for entry in entries:
            try:
                items.append(
                    self.run_project(project_id, body.model_copy(update={"entry_path": entry}))
                    | {"entry_path": entry}
                )
            except ProjectError as exc:
                errors.append({"entry_path": entry, "message": str(exc)})
        return {"items": items, "errors": errors}
