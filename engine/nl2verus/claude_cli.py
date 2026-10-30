"""Run the official bundled Claude Code CLI through its official Agent SDK."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import signal
import subprocess
import tempfile

from .agent_runtime import ROOT, runtime_directory
from .dsh_cli import _redact_event
from .model_provider import MAX_CODE_BYTES, ProviderError


def package_paths():
    modules = runtime_directory('agent-runtime') / 'node_modules'
    system = {'Darwin': 'darwin', 'Linux': 'linux', 'Windows': 'win32'}[platform.system()]
    arch = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}[platform.machine()]
    package = modules / '@anthropic-ai/claude-agent-sdk'
    binary = modules / ('@anthropic-ai/claude-agent-sdk-' + system + '-' + arch) / ('claude.exe' if system == 'win32' else 'claude')
    return package, binary


def installed():
    try:
        package, binary = package_paths()
        return binary.is_file() and (package / 'package.json').is_file()
    except KeyError:
        return False


def parse_events(raw, redact=lambda s: s):
    native, tools, message_ids, diagnostics, result, session = [], {}, set(), [], None, None
    for line in raw.splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        kind = event.get('type')
        if kind == 'bridge_error':
            diagnostics.append(redact(str(event.get('message', '')))[:4000]); continue
        if kind == 'runtime': continue
        event = _redact_event(event, redact)
        native.append(event)
        session = event.get('session_id') or session
        if kind == 'assistant':
            message = event.get('message') or {}
            if message.get('id'): message_ids.add(message['id'])
            for block in message.get('content', []):
                if block.get('type') == 'tool_use':
                    tools[block['id']] = {'tool': block['name'], 'call_id': block['id'], 'status': 'called'}
        if kind == 'user' and isinstance((event.get('message') or {}).get('content'), list):
            for block in event['message']['content']:
                if block.get('type') == 'tool_result' and block.get('tool_use_id') in tools:
                    tools[block['tool_use_id']].update(status='error' if block.get('is_error') else 'completed', result=str(block.get('content', ''))[:16000])
        if kind == 'result': result = event
    data = (result or {}).get('usage') or {}
    return {'events': native, 'agent_events': list(tools.values()), 'provider_calls': len(message_ids),
            'session_id': session, 'diagnostics': diagnostics,
            'complete': bool(result) and result.get('subtype') == 'success' and not result.get('is_error'),
            'terminal_reason': (result or {}).get('subtype'),
            'errors': (result or {}).get('errors', []),
            'usage': {'prompt_tokens': data.get('input_tokens', 0), 'completion_tokens': data.get('output_tokens', 0),
                      'total_tokens': sum(data.get(k, 0) or 0 for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'))}}


def generate(prompt, profile, timeout=300):
    from .agents import _clean_code
    from .verifier import verus_path
    node = shutil.which('node')
    if not node or not installed():
        raise ProviderError('agent_missing', '官方 Claude Code CLI 未安装；请运行项目安装脚本。')
    package, binary = package_paths()
    meta = json.loads((package / 'package.json').read_text())
    with tempfile.TemporaryDirectory(prefix='nl2verus-claude-') as folder:
        base = Path(folder); workspace = base / 'workspace'; workspace.mkdir()
        home = base / 'home'; home.mkdir()
        command = ' '.join(shlex.quote(x) for x in [str(verus_path()), str(workspace/'output.rs'), '--crate-type','lib','--crate-name','submission'])
        task = prompt + '\nUse the Write tool to create output.rs in the current workspace, then use Bash to run exactly this command without cd or additional commands:\n' + command + '\nUse real diagnostics to repair output.rs and run the verifier again. Only task workspace files and this verifier command are permitted. Finish with the complete source saved in output.rs. Never use assume/admit/external_body. The platform independently verifies your output.'
        env = {k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR','SYSTEMROOT','HTTPS_PROXY','HTTP_PROXY','NO_PROXY','ACSL_AGENT_RUNTIME_ROOT')}
        env.update(RUSTUP_HOME=os.environ.get('RUSTUP_HOME',str(Path.home()/'.rustup')),CARGO_HOME=os.environ.get('CARGO_HOME',str(Path.home()/'.cargo')))
        payload = {'prompt':task,'profile':profile,'workingDirectory':str(workspace),'homeDirectory':str(home),'verifierCommand':command}
        timed_out = False
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc = subprocess.Popen([node,str(ROOT/'scripts/claude_bridge.mjs')],cwd=workspace,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True)
            try: proc.communicate(json.dumps(payload).encode(),timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate();timed_out=True
            oversized = out.tell()>2_000_000
            out.seek(0);raw=out.read(2_000_000).decode('utf-8',errors='replace')
        def redact(value):
            for sensitive,replacement in [(profile.get('api_key'),'[REDACTED]'),(profile['base_url'],'[MODEL_ENDPOINT]'),(str(base),'[TASK]')]:
                if sensitive:value=value.replace(sensitive,replacement)
            return re.sub(r'https?://[^\s<>"\\]+','[URL]',value)
        result=parse_events(raw,redact)
        runtime={'name':'Claude Code','package':'@anthropic-ai/claude-agent-sdk','version':meta['claudeCodeVersion'],
                 'sdk_version':meta['version'],'upstream':'https://github.com/anthropics/claude-agent-sdk-typescript',
                 'entrypoint_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
                 'session_id':result['session_id'],'exit_code':proc.returncode,'terminal_reason':result['terminal_reason'],
                 'tool_policy':'workspace file tools and exact Verus command only','turn_limit':24,'timeout_seconds':timeout,
                 'events_kind':'native-sdk-messages-without-thinking','events':result['events'],'diagnostics':result['diagnostics']}
        def fail(code,message):
            error=ProviderError(code,message,usage=result['usage']);error.agent_runtime=runtime
            error.agent_events=result['agent_events'];error.provider_calls=result['provider_calls'];raise error
        if timed_out:fail('agent_timeout','官方 Claude Code CLI 运行超时，已保留事件记录。')
        if oversized:fail('agent_output','官方 Claude Code CLI 事件超过限制。')
        if result['terminal_reason'] == 'error_max_turns':
            fail('output_limit','官方 Claude Code 已达到 24 轮任务上限，尚未正常结束；这不是 API 连接失败。')
        if proc.returncode or not result['complete']:
            details='; '.join(str(s) for s in result['errors']+result['diagnostics'])[:1500]
            fail('agent_failed','官方 Claude Code CLI 未完成任务（'+str(result['terminal_reason'] or 'runtime_error')+'）'+('：'+details if details else '；请展开原生事件查看诊断。'))
        if not result['agent_events']:fail('agent_tools','官方 Claude Code 未执行工具，未将普通文本当作 Agent 工作结果。')
        target=workspace/'output.rs'
        if target.is_symlink() or not target.is_file() or target.stat().st_size>MAX_CODE_BYTES:fail('agent_output','官方 Claude Code 未创建有效的 output.rs。')
        try:code=_clean_code(target.read_text(),[profile.get('api_key')])
        except ProviderError as error:fail(error.code,error.safe_message)
        return {'code':code,'model_name':profile['model'],'usage':result['usage'],'finish_reason':'stop',
                'provider_calls':result['provider_calls'],'agent_events':result['agent_events'],'agent_runtime':runtime}
