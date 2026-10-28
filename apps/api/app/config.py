from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[3]
RUNTIME_DIR = ROOT_DIR / "runtime"
RUNS_DIR = RUNTIME_DIR / "runs"
UPLOADS_DIR = RUNS_DIR / "uploads"
CONFIGS_DIR = ROOT_DIR / "configs"
WEB_DIR = ROOT_DIR / "apps" / "web"
MODELS_CONFIG_PATH = CONFIGS_DIR / "models_config.yaml"
DEMO_CASES_PATH = CONFIGS_DIR / "demo_cases.json"


def resolve_project_path(value: str | Path) -> Path:
    """Resolve a project-relative path while reading old absolute task records."""
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def project_relative_path(value: str | Path) -> str:
    """Return a portable POSIX path for API payloads and persisted metadata."""
    path = Path(value).resolve()
    try:
        return path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return path.as_posix()

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


def ensure_runtime_dirs() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_available_models() -> list[str]:
    if not MODELS_CONFIG_PATH.exists():
        return [DEFAULT_MODEL]
    with MODELS_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    model_map = payload.get("ModelMap", {})
    models = sorted(model_map.keys())
    return models or [DEFAULT_MODEL]


def load_demo_cases_config() -> list[dict[str, Any]]:
    if not DEMO_CASES_PATH.exists():
        return []
    with DEMO_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_allowed_origins() -> list[str]:
    raw_value = os.getenv("ACSL_AGENT_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [item.strip() for item in raw_value.split(",") if item.strip()]
