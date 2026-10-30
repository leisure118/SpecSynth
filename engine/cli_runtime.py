"""One project-owned location for all Agent CLI runtimes and SDKs."""
from pathlib import Path
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
from engine.nl2verus.agent_runtime import runtime_root
CLI_ROOT = runtime_root()
SDK_ROOT = CLI_ROOT / 'agents'
DEEPSEEK_ROOT = CLI_ROOT / 'deepseek'


def command(agent):
    if agent not in ('deepseek','deepseek-harness','codex','claude','claude-code'):return None
    if agent in ('deepseek', 'deepseek-harness'):
        entry=DEEPSEEK_ROOT/'node_modules/@deepseek-ai/dsh/lib/bin.js'
        return [shutil.which('node') or 'node',str(entry)] if entry.is_file() else None
    name='claude' if agent in ('claude','claude-code') else 'codex'
    configured=os.getenv('XUANJIAN_'+name.upper()+'_EXECUTABLE')
    if configured:
        found=shutil.which(configured)
        return [found] if found else None
    custom=CLI_ROOT/name/name
    if custom.is_file():return [str(custom)]
    if name=='claude':
        import platform
        system={'Darwin':'darwin','Linux':'linux','Windows':'win32'}[platform.system()]
        arch={'arm64':'arm64','aarch64':'arm64','x86_64':'x64','AMD64':'x64'}[platform.machine()]
        binary=SDK_ROOT/f'node_modules/@anthropic-ai/claude-agent-sdk-{system}-{arch}'/('claude.exe' if system=='win32' else 'claude')
        if binary.is_file():return [str(binary)]
        entry=SDK_ROOT/'node_modules/@anthropic-ai/claude-agent-sdk/cli.js'
        return [shutil.which('node') or 'node',str(entry)] if entry.is_file() else None
    platform={'darwin':'darwin','linux':'linux','win32':'win32'}.get(sys.platform,sys.platform)
    import platform as machine
    arch={'arm64':'arm64','aarch64':'arm64','x86_64':'x64','AMD64':'x64'}.get(machine.machine(),machine.machine())
    package=SDK_ROOT/f'node_modules/@openai/codex-{platform}-{arch}'
    candidates=list(package.glob('vendor/*/bin/codex*'))
    return [str(candidates[0])] if candidates else None
