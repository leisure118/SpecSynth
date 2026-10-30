"""Unified launcher: python3 scripts/run_agent_cli.py deepseek|codex|claude [args]."""
from pathlib import Path
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.cli_runtime import command
if len(sys.argv)<2:raise SystemExit('Usage: run_agent_cli.py deepseek|codex|claude [args]')
args=command(sys.argv[1])
if not args:raise SystemExit('CLI is not installed in runtime/cli. Run scripts/install_agent_runtime.py.')
os.execvp(args[0],args+sys.argv[2:])
