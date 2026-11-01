"""HTTP interface for the versioned Skill library."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from acsl.application import skills as skill_service
from acsl.domain.agents import AGENTS, AgentId, AssistantConfig

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


class SkillBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    instructions: str | None = Field(default=None, min_length=1, max_length=24000)
    agents: list[AgentId] = Field(default_factory=lambda: list(AGENTS), min_length=1, max_length=4)
    enabled: bool = True
    version: int | None = Field(default=None, ge=1)


def _call(function, *args):
    try:
        return function(*args)
    except skill_service.SkillError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.get("")
def list_skills():
    return {"items": skill_service.list_skills()}


@router.post("", status_code=201)
def create_skill(body: SkillBody):
    return _call(skill_service.create_skill, body.model_dump(exclude={"version"}))


@router.get("/{identifier}")
def get_skill(identifier: str, version: int | None = None):
    return _call(skill_service.get_skill, identifier, version)


@router.put("/{identifier}")
def update_skill(identifier: str, body: SkillBody):
    return _call(skill_service.update_skill, identifier, body.model_dump())


@router.delete("/{identifier}")
def archive_skill(identifier: str):
    _call(skill_service.archive_skill, identifier)
    return {"archived": True}


def ensure_bundled_skills():
    return skill_service.ensure_bundled_skills()


def resolve_assistant(config: AssistantConfig | None):
    return skill_service.resolve_assistant(config)


# Compatibility names for server-side callers that still import the API module.
read = skill_service.read
write = skill_service.write
