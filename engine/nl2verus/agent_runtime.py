"""Resolve application-owned runtimes on workstations and deployment images."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def runtime_root():
    return Path(os.environ.get('ACSL_AGENT_RUNTIME_ROOT') or ROOT / 'runtime').expanduser().resolve()


def runtime_directory(name):
    if name not in ('agent-runtime', 'deepseek-runtime'):
        raise ValueError('Unknown application runtime')
    return runtime_root() / name
