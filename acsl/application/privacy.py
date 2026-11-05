"""Public API projection: Skill bodies and prompt snapshots stay server-side."""
import json
import re
from functools import lru_cache
from pathlib import Path

from acsl.infrastructure.settings import settings

PRIVATE_KEYS = {
    "instructions",
    "agent_instructions",
    "worker_instructions",
    "prompt",
    "effective_prompt",
    "system_prompt",
    "skill_snapshot",
    "native_events",
    "agent_events",
}
PRIVATE_ARTIFACT_MARKERS = (
    "skill.md",
    ".platform-worker-task",
    ".platform-worker-final",
    "skill-snapshot",
    "skill_snapshot",
    "prompt",
    "harness-events",
    "cli-events",
    "cli-raw",
)
NOTICE = "Skill 正文和执行提示词仅保存在后端。"


@lru_cache(maxsize=2)
def _fragments(signature):
    fragments = set()
    for filename, _ in signature:
        try:
            path = Path(filename)
            data = {"instructions": path.read_text()} if path.suffix.lower() == ".md" else json.loads(path.read_text())
            if path.name == "project.json":
                data = {"skills": data.get("assistant", {}).get("skills", [])}
        except (OSError, ValueError):
            continue

        def collect(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ("instructions", "content") and isinstance(item, str) and len(item) >= 24:
                        fragments.add(item)
                        fragments.update(
                            part
                            for part in item.split("\n\n")
                            if len(part) >= 80 and (re.search(r"[一-鿿]", part) or part.startswith("#"))
                        )
                    else:
                        collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(data)
    return tuple(fragments)


def protected_fragments():
    from acsl.application.skills import skills_dir

    root = settings.root_dir
    runtime = settings.runtime_dir
    paths = (
        list(skills_dir().glob("*.json"))
        + list((runtime / "projects").glob("*/project.json"))
        + list((root / "skills").glob("**/SKILL.md"))
        + list((root / "resources/skills").glob("**/SKILL.md"))
    )
    if (runtime / "generation-skills.json").exists():
        paths.append(runtime / "generation-skills.json")
    return _fragments(tuple(sorted((str(path), path.stat().st_mtime_ns) for path in paths)))


def private_artifact(path):
    value = str(path).lower().replace("\\", "/")
    if "/skills/" in value:
        return True
    if Path(value).suffix in (".c", ".h", ".rs", ".i"):
        return False
    return any(marker in value for marker in PRIVATE_ARTIFACT_MARKERS)


def public_payload(value, fragments=None):
    if fragments is None:
        fragments = protected_fragments()
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key.lower() in PRIVATE_KEYS or ("prompt" in key.lower() and isinstance(item, (str, list, dict))):
                continue
            if key in ("events", "input", "arguments") and (
                "agent_runtime" in value or "tool" in value or "type" in value or "command" in value
            ):
                continue
            if key == "skills" and isinstance(item, list):
                result[key] = [
                    {
                        k: public_payload(v, fragments)
                        for k, v in skill.items()
                        if k in ("id", "name", "version", "agents", "enabled", "description")
                    }
                    if isinstance(skill, dict)
                    else skill
                    for skill in item
                ]
            else:
                result[key] = public_payload(item, fragments)
        if value.get("events_kind") or value.get("package") in ("@deepseek-ai/dsh", "@anthropic-ai/claude-agent-sdk"):
            result.pop("events", None)
        if isinstance(result.get("items"), list):
            result["items"] = [
                item
                for item in result["items"]
                if not isinstance(item, dict) or not private_artifact(item.get("relative_path", ""))
            ]
        if "content" in result and "name" in result and str(result.get("id", "")).startswith(("uploaded-", "local-")):
            result.pop("content", None)
        return result
    if isinstance(value, list):
        return [public_payload(item, fragments) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                return json.dumps(public_payload(json.loads(value), fragments), ensure_ascii=False, indent=2)
            except (ValueError, TypeError):
                pass
        if any(marker in value for marker in ("# spec-split —", "# spec-orchestrate —", "# spec-bottomup —")):
            return NOTICE
        if any(fragment in value for fragment in fragments):
            return NOTICE
        return value
    return value
