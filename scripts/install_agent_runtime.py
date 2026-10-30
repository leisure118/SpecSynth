"""Install locked, application-owned Agent CLIs; never use personal global CLIs."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def check_node():
    node=shutil.which('node')
    if not node:raise SystemExit('Node.js >=24.9 is required for the Agent runtimes.')
    version=subprocess.check_output([node,'--version'],text=True).strip().lstrip('v')
    if tuple(map(int,version.split('.')[:2]))<(24,9):raise SystemExit('Node.js >=24.9 is required; found '+version)
    system={'Darwin':'darwin','Linux':'linux','Windows':'win32'}[platform.system()]
    arch={'arm64':'arm64','aarch64':'arm64','x86_64':'x64','AMD64':'x64'}[platform.machine()]
    return system, arch


def check(dest):
    system,arch=check_node()
    modules=dest/'agent-runtime/node_modules'
    for name in ('@openai/codex-sdk','@anthropic-ai/claude-agent-sdk'):
        p=modules/name/'package.json'
        if not p.is_file():raise SystemExit('Missing '+name+'; run the installer without --check.')
        print(name,json.loads(p.read_text())['version'])
    claude=modules/('@anthropic-ai/claude-agent-sdk-'+system+'-'+arch)/('claude.exe' if system=='win32' else 'claude')
    if not claude.is_file():raise SystemExit('Missing platform-native Claude Code binary; npm optional dependencies must be installed.')
    codex=modules/('@openai/codex-'+system+'-'+arch)
    if not codex.is_dir():raise SystemExit('Missing platform-native Codex package; npm optional dependencies must be installed.')
    dsh=dest/'deepseek-runtime/node_modules/@deepseek-ai/dsh'
    if not (dsh/'lib/bin.js').is_file():raise SystemExit('Missing official DeepSeek Harness CLI.')
    print('@deepseek-ai/dsh',json.loads((dsh/'package.json').read_text())['version'])
    print('Agent runtime dependencies ready. API connectivity and Verus readiness are separate checks.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,default=Path(os.environ.get('ACSL_AGENT_RUNTIME_ROOT') or ROOT/'runtime'))
    parser.add_argument('--check',action='store_true',help='Offline dependency preflight; never installs or calls models')
    args=parser.parse_args();dest=args.runtime_root.expanduser().resolve()
    check_node()
    if not args.check:
        if not shutil.which('npm'):raise SystemExit('Install Node.js >=24.9 and npm first.')
        for name in ('agent-runtime','deepseek-runtime'):
            target=dest/name;target.mkdir(parents=True,exist_ok=True)
            for filename in ('package.json','package-lock.json'):shutil.copyfile(ROOT/'configs'/name/filename,target/filename)
            subprocess.run(['npm','ci','--prefix',str(target),'--no-audit','--no-fund'],check=True)
    check(dest)


if __name__=='__main__':main()
