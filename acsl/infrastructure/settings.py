"""Deployment settings and filesystem layout shared by every layer.

The API, application services and adapters all read paths from one mutable
``settings`` object so tests can redirect runtime data without monkeypatching a
different copy of each constant in every module.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

DEFAULT_MODEL = "qwen-turbo"
APP_NAME = "ACSL AGENT"

PHASE_LABELS = {
    "rust-verify": [("verus", "Verus 验证")],
    "rust-generate": [("generation", "生成与反馈修复"), ("verus", "Verus 验证")],
    "single": [
        ("static_analysis", "Static Analysis"),
        ("generate_specifications", "Generate Specifications"),
        ("formal_verifying", "Formal Verifying"),
        ("iterative_repair", "Iterative Repair"),
    ],
    "termination": [
        ("static_analysis", "Static Analysis"),
        ("generate_specifications", "Generate Specifications"),
        ("formal_verifying", "Formal Verifying"),
        ("iterative_repair", "Iterative Repair"),
        ("termination", "Termination"),
    ],
    "inter-modular": [
        ("static_analysis", "Static Analysis"),
        ("extended_call_graph", "Extended Call Graph"),
        ("generate_specifications", "Generate Specifications"),
        ("formal_verifying", "Formal Verifying"),
    ],
    "batch": [
        ("static_analysis", "Static Analysis"),
        ("generate_specifications", "Generate Specifications"),
        ("formal_verifying", "Formal Verifying"),
    ],
}


class Settings:
    """Mutable filesystem settings; one instance is shared process-wide."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir).resolve() if root_dir else Path(__file__).resolve().parents[2]
        self.runtime_dir = self.root_dir / "runtime"
        self.runs_dir = self.runtime_dir / "runs"
        self.uploads_dir = self.runs_dir / "uploads"
        self.configs_dir = self.root_dir / "configs"
        self.web_dir = self.root_dir / "apps" / "web"
        self.models_config_path = self.configs_dir / "models_config.yaml"
        self.demo_cases_path = self.configs_dir / "demo_cases.json"

    def resolve(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root_dir / path

    def relative(self, value: str | Path) -> str:
        path = Path(value).resolve()
        try:
            return path.relative_to(self.root_dir).as_posix()
        except ValueError:
            return path.as_posix()


settings = Settings()
# Load private server settings before constructing task runners.
load_dotenv(settings.root_dir / ".env", override=False)


def resolve_project_path(value: str | Path) -> Path:
    """Resolve a project-relative path while reading old absolute task records."""
    return settings.resolve(value)


def project_relative_path(value: str | Path) -> str:
    """Return a portable POSIX path for API payloads and persisted metadata."""
    return settings.relative(value)


def ensure_runtime_dirs() -> None:
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.configs_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_available_models() -> list[str]:
    path = settings.models_config_path
    if not path.exists():
        return [DEFAULT_MODEL]
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    model_map = payload.get("ModelMap", {})
    models = sorted(model_map.keys())
    return models or [DEFAULT_MODEL]


def load_demo_cases_config() -> list[dict[str, Any]]:
    path = settings.demo_cases_path
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_allowed_origins() -> list[str]:
    raw_value = os.getenv("ACSL_AGENT_ALLOWED_ORIGINS", "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


# Snapshot aliases for interface/bootstrap code. Application and adapter code
# should read ``settings`` directly so runtime paths stay redirectable in tests.
ROOT_DIR = settings.root_dir
RUNTIME_DIR = settings.runtime_dir
RUNS_DIR = settings.runs_dir
UPLOADS_DIR = settings.uploads_dir
CONFIGS_DIR = settings.configs_dir
WEB_DIR = settings.web_dir
MODELS_CONFIG_PATH = settings.models_config_path
DEMO_CASES_PATH = settings.demo_cases_path
