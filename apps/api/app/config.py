"""Compatibility shim for the pre-refactor config module.

New code must import from :mod:`acsl.infrastructure.settings`.
"""
from __future__ import annotations

from acsl.infrastructure.settings import (
    APP_NAME,
    DEFAULT_MODEL,
    PHASE_LABELS,
    ensure_runtime_dirs,
    get_allowed_origins,
    get_available_models,
    load_demo_cases_config,
    project_relative_path,
    resolve_project_path,
    settings,
)

ROOT_DIR = settings.root_dir
RUNTIME_DIR = settings.runtime_dir
RUNS_DIR = settings.runs_dir
UPLOADS_DIR = settings.uploads_dir
CONFIGS_DIR = settings.configs_dir
WEB_DIR = settings.web_dir
MODELS_CONFIG_PATH = settings.models_config_path
DEMO_CASES_PATH = settings.demo_cases_path

__all__ = [
    "APP_NAME",
    "DEFAULT_MODEL",
    "PHASE_LABELS",
    "ROOT_DIR",
    "RUNTIME_DIR",
    "RUNS_DIR",
    "UPLOADS_DIR",
    "CONFIGS_DIR",
    "WEB_DIR",
    "MODELS_CONFIG_PATH",
    "DEMO_CASES_PATH",
    "ensure_runtime_dirs",
    "get_allowed_origins",
    "get_available_models",
    "load_demo_cases_config",
    "project_relative_path",
    "resolve_project_path",
    "settings",
]
