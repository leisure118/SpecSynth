"""Official DeepSeek Harness process adapter; the upstream CLI owns the agent loop."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import shlex
import signal
import subprocess
import tempfile
import sys
import re

from .model_provider import MAX_CODE_BYTES, ProviderError

ROOT = Path(__file__).resolve().parents[2]
from .agent_runtime import runtime_directory
PACKAGE = runtime_directory('deepseek-runtime') / 'node_modules/@deepseek-ai/dsh'
UPSTREAM = 'https://github.com/deepseek-ai/deepseek-harness'
VERSION = '0.2.1-rc.5'


def installed():
    try:
        return (PACKAGE / 'lib/bin.js').is_file() and json.loads((PACKAGE / 'package.json').read_text())['version'] == VERSION
    except (OSError, ValueError, KeyError):
        return False


def patch_for(profile, workspace, sub_profile=None):
    route = {'api': 'openai-completions', 'baseURL': profile['base_url'],
             'apiKeyEnv': 'DSH_PLATFORM_KEY', 'defaultMaxTokens': 8192,
             'retryPolicy': {'mode': 'normal', 'maxRetries': 0},
             'compat': {'thinkingFormat': 'deepseek'},
             'models': [{'id': profile['model'], 'contextWindow': 1048576, 'maxTokens': 8192}]}
    providers={'platform-api':route}
    if sub_profile:
        providers['platform-subagent']={**route,'baseURL':sub_profile['base_url'],'apiKeyEnv':'DSH_SUBAGENT_KEY','compat':{},'models':[{'id':sub_profile['model'],'contextWindow':32768,'maxTokens':8192}]}
    return [
        {'id': 'agent-default-model', 'config': {'provider': 'platform-api', 'model': profile['model']}},
        {'id': 'llm-pi-ai', 'config': {'providers': providers}},
        {'id': 'sandbox-policy', 'config': {'mode': 'workspace-write', 'workspaceRoot': str(workspace)}},
        {'id': 'approval', 'config': {'policy': 'never'}},
        {'id': 'permission', 'config': {'defaultPreset': 'workspace-write', 'presets': {
            'workspace-write': {'sandbox': 'workspace-write', 'approval': 'never'}}}},
        {'insert':[{'id':'platform-subagent-audit','name':str(ROOT/'engine/cli_plugins/subagent_audit.mjs')}]},
        {'id':'tool-subagent','config':{'provider':'spawn','toolName':'subagent','maxDepth':1,'agentOptions':{'provider':'platform-subagent','model':sub_profile['model']} if sub_profile else {}}},
        {'id':'tool-subagent-fork','disabled':True},
        {'id':'subagent','config':{'maxActiveSubagents':1}},
        {'id': 'session-telemetry-otel', 'disabled': True},
    ]


def _redact_event(value, redact):
    if isinstance(value, str): return redact(value)
    if isinstance(value, list): return [_redact_event(item, redact) for item in value]
    if isinstance(value, dict): return {redact(str(key)): _redact_event(item, redact) for key, item in value.items()}
    return value


def parse_events(text, redact=lambda s: s, *, require_complete=True):
    """Keep upstream machine events, not generated interpretations of tool use."""
    trace, tools, calls, final, session = [], {}, 0, None, None
    terminal = None
    usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            if not require_complete: continue
            raise ProviderError('agent_output', '官方 Harness 返回了无法解析的事件。') from None
        kind = event.get('type')
        if kind == 'status' and event.get('phase') == 'turn_start': terminal = None
        if kind == 'status' and event.get('phase') == 'turn_end': terminal = event.get('reason')
        if kind == 'session': session = event.get('sessionId')
        if kind == 'tool_call':
            tools[event['callId']] = {'tool': event.get('tool'), 'status': 'called', 'call_id': event['callId']}
        if kind == 'tool_result' and event.get('callId') in tools:
            tools[event['callId']].update(status=event.get('status'), result=redact(str(event.get('result', '')))[:16000])
        if kind == 'status' and event.get('phase') == 'step_start': calls += 1
        if kind == 'status' and event.get('phase') == 'step_end':
            data = event.get('usage') or {}
            for source, target in [('inputTokens', 'prompt_tokens'), ('outputTokens', 'completion_tokens'), ('totalTokens', 'total_tokens')]:
                usage[target] += data.get(source, 0) or 0
        if kind == 'final': final = event
        # Deliberately exclude private reasoning. This is the CLI's bounded event
        # projection, not a claim to export the complete durable session log.
        if kind in ('session', 'status', 'tool_call', 'tool_result', 'final', 'error'):
            trace.append(_redact_event(event, redact))
    reason = (final or {}).get('reason') or terminal or {}
    complete = bool(final) and reason.get('kind') == 'completed'
    if require_complete and not complete:
        raise ProviderError('agent_failed', '官方 Harness 未正常完成任务，未使用直连 API 兜底。')
    if require_complete and not tools:
        raise ProviderError('agent_tools', '官方 Harness 没有执行工具，未将普通文本当作 Agent 工作结果。')
    return {'agent_events': list(tools.values()), 'native_events': trace, 'session_id': session,
            'provider_calls': calls, 'usage': usage, 'final_text': (final or {}).get('text', ''),
            'complete': complete, 'reason': _redact_event(reason, redact)}


def generate(prompt, profile, timeout=240, *, output_format="verus", artifact_dir=None, sub_profile=None, require_subagent=False):
    from .agents import _clean_code
    from .verifier import verus_path
    node = shutil.which('node')
    if not node or not installed():
        raise ProviderError('agent_missing', '官方 DeepSeek Harness CLI 未安装，请运行安装脚本。')
    entry = PACKAGE / 'lib/bin.js'
    task_root=ROOT/'runtime/harness-tasks' if output_format=='files' else None
    if task_root is not None:task_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='nl2verus-dsh-',dir=task_root) as folder:
        base = Path(folder)
        workspace = base / 'workspace'; workspace.mkdir()
        home = base / 'home'; home.mkdir()
        config = base / 'provider.patch.yml'
        config.write_text(json.dumps(patch_for(profile, workspace, sub_profile)), encoding='utf-8')
        config.chmod(0o600)
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'TMPDIR', 'SYSTEMROOT', 'HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY', 'SHELL')}
        user_home = Path.home()
        env.update(HOME=str(home), DSH_HOME=str(base / 'dsh-home'),
                   DSH_PLATFORM_KEY=profile.get('api_key') or 'not-required',
                   RUSTUP_HOME=os.environ.get('RUSTUP_HOME', str(user_home / '.rustup')),
                   CARGO_HOME=os.environ.get('CARGO_HOME', str(user_home / '.cargo')))
        env['DSH_SUBAGENT_AUDIT']=str(workspace/'subagent-audit.jsonl')
        if sub_profile:env['DSH_SUBAGENT_KEY']=sub_profile.get('api_key') or 'not-required'
        verifier_command = [str(verus_path()), str(workspace / 'output.rs'), '--crate-type', 'lib', '--crate-name', 'submission']
        task = (prompt + '\n\nYou are running inside the official DeepSeek Harness. Use your real file tools to create output.rs in the current workspace. '
                'Use the bash tool to execute this verifier command (arguments are shell quoted):\n' +
                ' '.join(shlex.quote(x) for x in verifier_command) +
                '\nRead actual diagnostics and fix output.rs as needed. Do not access files outside this task workspace except the verifier/toolchain. '
                'Do not install packages or access the network from tools. Never use assume/admit/external_body. '
                'Finish within 6 model steps if possible. Keep the final complete Verus source in output.rs. '
                'The platform independently validates this file; your own success claims do not determine Pass. Return the complete source only.')
        filename = 'output.rs'
        if output_format == 'files':
            filename = 'answer.json'
            python = ROOT / '.venv/bin/python'
            verification_command = shlex.join([str(python if python.is_file() else Path(sys.executable)), str(ROOT / 'scripts/harness_verify_c.py'), str(workspace / 'answer.json')])
            input_dir=workspace/'input';input_dir.mkdir()
            try:
                sources=json.JSONDecoder().raw_decode(prompt.split('Original source:\n',1)[1])[0]
                for source in sources:
                    path=Path(source['path'])
                    if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid source path')
                    target=input_dir/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source['content'])
            except (IndexError,ValueError,KeyError,TypeError):
                sources=[]
            env['PYTHONPATH']=str(ROOT)
            # Give the isolated CLI only plugin discovery and the daemon socket,
            # never the developer's Docker registry credentials or contexts.
            docker_config=workspace/'.docker';docker_config.mkdir()
            plugin_dirs=[user_home/'.docker/cli-plugins',Path('/Applications/Docker.app/Contents/Resources/cli-plugins')]
            (docker_config/'config.json').write_text(json.dumps({'cliPluginsExtraDirs':[str(p) for p in plugin_dirs if p.is_dir()]}))
            env['DOCKER_CONFIG']=str(docker_config)
            docker_socket=user_home/'.docker/run/docker.sock'
            if os.environ.get('DOCKER_HOST'):env['DOCKER_HOST']=os.environ['DOCKER_HOST']
            elif docker_socket.exists():env['DOCKER_HOST']='unix://'+str(docker_socket)
            tool_command=shlex.join([str(python if python.is_file() else Path(sys.executable)), '-m', 'engine.harness_spectool'])
            task = (prompt + '\n\nYou are inside the official DeepSeek Harness CLI. Use real file tools to write the candidate C/header files in this workspace, preserving their relative paths. '
                    'Write answer.json with the candidate files, then use bash to run the platform Frama-C verification tool: ' + verification_command + '\nInspect the actual diagnostics and update the candidate as needed. '
                    'Only add ACSL annotations; preserve all original C tokens and assertions. Never add admit or axioms. '
                    'Do not install packages or access the network from tools. Do not read files outside this workspace except the verifier/toolchain. '
                    'Finally use a file tool to write answer.json containing ONLY a JSON object with a files array of {path, content}, including every original input file. '
                    'The platform independently checks original source preservation and executes Frama-C; your success claims are not proof. '
                    '\nSkill execution environment: input/ is the only original source directory; output/ is the intermediate output directory. '
                    'The spectool commands shown in Skills are available using this exact prefix instead of PYTHONPATH=spectool python3 -m spectool.cli: ' + tool_command +
                    '\nWhen the three spec Skills are attached: execute spec-split first (list-layers, init-contracts and stub/inline slices), '
                    'then spec-orchestrate in bottom-up layer order, applying spec-bottomup to each function. '
                    'You MUST use the native subagent tool to delegate spec-bottomup work. Its model is fixed by the platform; do not try to change the main model or use fork. '
                    'Pass the worker the input slice, inline reference, complete spec-bottomup instructions and exact verification command. '
                    'When only waiting for a child, end your turn so the runtime can deliver its completion; do not poll. '
                    'Never claim a subagent was launched without native tool evidence. Never reuse an unproved callee contract. '
                    'Platform proof policy overrides permissive admit/fallback examples: no new admit, assume, axiom or unproved fallback contracts. '
                    'Store contracts.json, per-function .acsl.c/.wp.txt and summary.json under output/. '
                    'Merge annotations back into the original project paths for answer.json, preserving original tokens and assertions. '
                    'Finish only after running the platform final verification command given above. Do not stop after writing a plan.')
        if sub_profile:
            task += ('\nThe configured Qwen subagent is a text-only specification worker: its tool schemas are deliberately empty because this deployed endpoint does not support automatic tool calls. '
                     'Do not ask it to read files, run commands, call send_message, or invoke any tool. Include the complete source and the generation rules from spec-bottomup in its task. '
                     'Ask it to return annotations or complete annotated source as plain text/JSON. The official runtime delivers its final answer to you automatically. '
                     'You, the main DeepSeek agent, must execute spec-split, tool-based injection, Frama-C verification, contract collection and repairs using that answer. '
                     'If the child fails, report the failure; never fabricate its output or replace its generation with your own.')
        cmd = [node, str(entry), '--profile', 'headless', '--patch', str(config), '--json', '-']
        def redact(value):
            for sensitive, replacement in [((sub_profile or {}).get('api_key'), '[REDACTED]'), ((sub_profile or {}).get('base_url'), '[SUBAGENT_ENDPOINT]'), (profile.get('api_key'), '[REDACTED]'), (profile['base_url'], '[MODEL_ENDPOINT]'), (str(base), '[TASK]')]:
                if sensitive: value = value.replace(sensitive, replacement)
            value = re.sub(r'https?://[^\s<>"\\]+', '[URL]', value)
            return value
        timed_out = False
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc = subprocess.Popen(cmd, cwd=workspace, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err, start_new_session=True)
            try:
                proc.communicate(task.encode(), timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.communicate()
                timed_out = True
            oversized = out.tell() > 2_000_000
            out.seek(0); raw = out.read(2_000_000).decode('utf-8', errors='replace')
            err.seek(0)
            # Never publish reasoning from stderr; only bounded CLI diagnostics.
            diagnostics = [redact(line)[:2000] for line in err.read(1_000_000).decode('utf-8', errors='replace').splitlines()
                           if line.startswith('dsh:') and not line.startswith('dsh: reasoning:')][-5:]
        result = parse_events(raw, redact, require_complete=False)
        native_events = result.pop('native_events')
        session_id = result.pop('session_id')
        result.pop('final_text')
        complete = result.pop('complete')
        reason = result.pop('reason')
        runtime = {'name': 'DeepSeek Harness', 'package': '@deepseek-ai/dsh', 'version': VERSION,
                   'upstream': UPSTREAM, 'entrypoint_sha256': hashlib.sha256(entry.read_bytes()).hexdigest(),
                   'command': ['node', '@deepseek-ai/dsh/lib/bin.js', '--profile', 'headless', '--patch', '[PRIVATE_CONFIG]', '--json', '-'],
                   'session_id': session_id, 'sandbox': 'workspace-write', 'approval_policy': 'never',
                   'exit_code': proc.returncode, 'terminal_reason': reason, 'diagnostics': diagnostics,
                   'events_kind': 'upstream-json-projection-without-thinking', 'events': native_events}
        def fail(code, message):
            error = ProviderError(code, message, usage=result['usage'])
            error.agent_runtime = runtime
            error.agent_events = result['agent_events']
            error.provider_calls = result['provider_calls']
            raise error
        audit_file=workspace/'subagent-audit.jsonl'
        child_events=[json.loads(line) for line in audit_file.read_text().splitlines()] if audit_file.exists() else []
        runtime.update(subagent_events=child_events,subagent_model=(sub_profile or profile)['model'],subagent_inherits_main=not bool(sub_profile))
        if artifact_dir is not None:
            evidence=Path(artifact_dir);evidence.mkdir(parents=True,exist_ok=True)
            (evidence/'harness-events.jsonl').write_text('\n'.join(json.dumps(e,ensure_ascii=False) for e in native_events))
            if audit_file.exists():(evidence/'subagent-audit.jsonl').write_text(redact(audit_file.read_text()))
            archive=evidence/'workspace';archive.mkdir(parents=True,exist_ok=True)
            budget=16*1024*1024
            for source in workspace.rglob('*'):
                if '.docker' in source.parts or '.platform-proofs' in source.parts or source.is_symlink() or not source.is_file() or source.suffix not in ('.c','.h','.json','.txt','.md'):continue
                size=source.stat().st_size
                if size>budget:continue
                budget-=size
                destination=archive/source.relative_to(workspace);destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_text(redact(source.read_text(errors='replace')))
        if timed_out:
            fail('agent_timeout', '官方 DeepSeek Harness 超过运行时限，已停止；已保留工具与错误记录。')
        if oversized:
            fail('agent_output', '官方 Harness 事件输出超过限制，已保留部分事件。')
        if reason.get('kind') == 'max-tokens':
            fail('output_limit', '官方 DeepSeek Harness 输出预算已耗尽，尚未完成生成；这不是网络连接失败。')
        if proc.returncode or not complete:
            detail = str((reason.get('error') or {}).get('message') or '')[:1500]
            error_code = str((reason.get('error') or {}).get('code') or 'CLI_EXIT')[:100]
            if not detail and diagnostics: detail = diagnostics[-1]
            fail('agent_failed', '官方 DeepSeek Harness 执行失败（' + error_code + '）' + ('：' + detail if detail else '；请展开 CLI 诊断。'))
        if not result['agent_events']:
            fail('agent_tools', '官方 Harness 未执行工具，未将普通文本当作 Agent 工作结果。')
        if require_subagent and (not any(e.get('type')=='end' and e.get('stop_reason')=='completed' for e in child_events) or not any(e.get('tool')=='subagent' and e.get('status')=='completed' for e in result['agent_events'])):
            fail('agent_delegation','原生 Sub-agent 未正常完成任务，未回退为主模型自行处理。')
        target = workspace / filename
        if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_CODE_BYTES:
            fail('agent_output', '官方 Harness 未创建有效的 output.rs 文件。')
        code = _clean_code(target.read_text(), [profile.get('api_key')]) if output_format=='verus' else target.read_text()
        return dict(result, code=code, model_name=profile['model'], finish_reason='stop', agent_runtime=runtime)
