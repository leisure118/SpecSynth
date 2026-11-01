"""Versioned Skill library and pinned assistant resolution.

This module contains no HTTP concerns. The API router maps :class:`SkillError`
instances to HTTP responses.
"""
from __future__ import annotations

import re
import threading
import uuid
from pathlib import Path

from acsl.adapters.storage import JsonStore, utcnow
from acsl.domain.agents import AGENTS, AssistantConfig, Skill, SkillReference
from acsl.infrastructure.settings import settings

_LOCK = threading.RLock()
BUNDLED_SKILLS = ("spec-split", "spec-orchestrate", "spec-bottomup")


class SkillError(Exception):
    status_code = 400


class SkillNotFound(SkillError):
    status_code = 404


class SkillConflict(SkillError):
    status_code = 409


def skills_dir() -> Path:
    return settings.runtime_dir / "skills"


def read(identifier: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", identifier):
        raise SkillNotFound("Skill 不存在。")
    path = skills_dir() / (identifier + ".json")
    if not path.is_file():
        raise SkillNotFound("Skill 不存在。")
    return JsonStore._read_json(path)


def write(record: dict) -> None:
    directory = skills_dir()
    directory.mkdir(parents=True, exist_ok=True)
    JsonStore._write_json(directory / (record["id"] + ".json"), record)


def public(record: dict) -> dict:
    return record["versions"][-1] | {"archived": record.get("archived", False)}


def ensure_bundled_skills() -> list[dict]:
    """Import portable user-provided skills once; never overwrite edited versions."""
    refs = []
    with _LOCK:
        for name in BUNDLED_SKILLS:
            identifier = uuid.uuid5(uuid.NAMESPACE_URL, "xuanjian:skills:" + name).hex
            path = settings.root_dir / "resources" / "skills" / name / "SKILL.md"
            if not path.is_file():
                continue
            if not (skills_dir() / (identifier + ".json")).is_file():
                snapshot = {
                    "id": identifier,
                    "name": name,
                    "instructions": path.read_text(),
                    "agents": ["deepseek-harness"],
                    "enabled": True,
                    "version": 1,
                    "updated_at": utcnow().isoformat(),
                }
                write({"id": identifier, "versions": [snapshot], "archived": False})
            refs.append({"id": identifier, "version": 1, "enabled": True})
    return refs


def list_skills() -> list[dict]:
    with _LOCK:
        items = []
        for path in sorted(skills_dir().glob("*.json")):
            record = JsonStore._read_json(path)
            if not record.get("archived"):
                items.append(public(record))
        return items


def create_skill(body: dict) -> dict:
    with _LOCK:
        identifier = uuid.uuid4().hex
        snapshot = {**body, "id": identifier, "version": 1, "updated_at": utcnow().isoformat()}
        snapshot.pop("version", None)
        snapshot["version"] = 1
        record = {"id": identifier, "versions": [snapshot], "archived": False}
        write(record)
        return public(record)


def get_skill(identifier: str, version: int | None = None) -> dict:
    record = read(identifier)
    if version is None:
        return public(record)
    found = next((item for item in record["versions"] if item["version"] == version), None)
    if not found:
        raise SkillNotFound("Skill 版本不存在。")
    return found


def update_skill(identifier: str, body: dict) -> dict:
    with _LOCK:
        record = read(identifier)
        if record.get("archived"):
            raise SkillConflict("Skill 已归档。")
        if body.get("version") != record["versions"][-1]["version"]:
            raise SkillConflict("Skill 已更新，请刷新后重试。")
        snapshot = {**body, "id": identifier, "version": body["version"] + 1, "updated_at": utcnow().isoformat()}
        snapshot.pop("version", None)
        snapshot["version"] = body["version"] + 1
        record["versions"].append(snapshot)
        write(record)
        return public(record)


def archive_skill(identifier: str) -> None:
    with _LOCK:
        record = read(identifier)
        record["archived"] = True
        write(record)


def resolve_assistant(config: AssistantConfig | None) -> AssistantConfig | None:
    if config is None:
        return None
    if config.agent == "deepseek-harness" and not config.skills and not config.skill_refs:
        config = config.model_copy(
            update={"skill_refs": [SkillReference(**ref) for ref in ensure_bundled_skills()]}
        )
    skills = [skill.model_dump() for skill in config.skills]
    for ref in config.skill_refs:
        item = get_skill(ref.id, ref.version)
        skills.append(
            Skill(**{key: item[key] for key in ("id", "name", "instructions", "agents", "enabled")}).model_dump()
            | {"enabled": ref.enabled and item["enabled"]}
        )
    # Clear references in the executable snapshot; the project retains pinned bindings.
    return AssistantConfig(
        agent=config.agent,
        runner_model=config.runner_model,
        workflow=config.workflow,
        sub_model=config.sub_model,
        skills=skills,
    )
