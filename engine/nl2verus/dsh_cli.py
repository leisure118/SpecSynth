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


def output_limits(profile):
    """Independent budgets: main orchestration vs a 32K-context deployed worker."""
    def limit(name,default,maximum):
        value=int(os.getenv(name,str(default)))
        if not 1024<=value<=maximum:raise ValueError(name+' 超出支持的输出预算范围。')
        return value
    main=limit('XUANJIAN_HARNESS_MAIN_MAX_TOKENS',32768 if profile['model']=='deepseek-v4.1-flash-1017' else 8192,65536)
    child=limit('XUANJIAN_HARNESS_SUB_MAX_TOKENS',8192,16384)
    return main,child


def patch_for(profile, workspace, sub_profile=None):
    main_limit,child_limit=output_limits(profile)
    route = {'api': 'openai-completions', 'baseURL': profile['base_url'],
             'apiKeyEnv': 'DSH_PLATFORM_KEY', 'defaultMaxTokens': main_limit,
             'retryPolicy': {'mode': 'normal', 'maxRetries': 0},
             'compat': {'thinkingFormat': 'deepseek'},
             'models': [{'id': profile['model'], 'contextWindow': 1048576, 'maxTokens': main_limit}]}
    providers={'platform-api':route}
    if sub_profile:
        providers['platform-subagent']={**route,'defaultMaxTokens':child_limit,'baseURL':sub_profile['base_url'],'apiKeyEnv':'DSH_SUBAGENT_KEY','compat':{},'models':[{'id':sub_profile['model'],'contextWindow':int(os.getenv('XUANJIAN_QWEN_CONTEXT_WINDOW','16384' if sub_profile['model']=='qwen35-9b-mix64' else '32768')),'maxTokens':child_limit}]}
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
    verifast=output_format=='verifast-files'
    files_format=output_format in ('files','verifast-files')
    task_root=ROOT/'runtime/harness-tasks' if files_format else None
    if task_root is not None:task_root.mkdir(parents=True,exist_ok=True)
    from .harness_session import workspace_directory, current_session
    with workspace_directory(task_root) as folder:
        base = Path(folder)
        workspace = base / 'workspace'; workspace.mkdir(exist_ok=True)
        home = base / 'home'; home.mkdir(exist_ok=True)
        compact=output_format=='files' and os.environ.get('XUANJIAN_HARNESS_COMPACT')=='1'
        effective_child=(sub_profile or profile) if (compact or verifast) else sub_profile
        config = base / 'provider.patch.yml'
        session=current_session() if files_format else None
        patch=patch_for(profile, workspace, effective_child)
        if session is not None:
            patch += [{'id':'headless-runner','disabled':True},{'insert':[{'id':'platform-persistent-harness','name':str(ROOT/'engine/cli_plugins/persistent_harness.mjs')}]}]
        if verifast:
            from engine.verification.worker_contract import thinking_policy
            policy=thinking_policy()
            for item in patch:
                if item.get('id')=='llm-pi-ai':
                    for role,key in [('main','platform-api'),('worker','platform-subagent')]:
                        provider=item['config']['providers'].get(key)
                        if not provider:continue
                        model=provider['models'][0]['id']
                        provider.update(reasoning='low' if policy[role]=='on' else 'off',compat={'thinkingFormat':'qwen' if model=='deepseek-v4.1-flash-1017' else 'qwen-chat-template','supportsReasoningEffort':False,'supportsDeveloperRole':False})
                        for spec in provider['models']:
                            spec['reasoningEfforts']={'off':None,'low':'low'}
                            if role=='worker':spec.update(maxTokens=min(spec['maxTokens'],4096),contextWindow=max(2048,spec['contextWindow']-1024))
                        if role=='worker':provider['defaultMaxTokens']=min(provider['defaultMaxTokens'],4096)
                if item.get('id')=='tool-subagent':item['config']['agentOptions']['reasoningEffort']='low' if policy['worker']=='on' else 'off'
        config.write_text(json.dumps(patch), encoding='utf-8')
        config.chmod(0o600)
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'TMPDIR', 'SYSTEMROOT', 'HTTPS_PROXY', 'HTTP_PROXY', 'NO_PROXY', 'SHELL', 'XUANJIAN_PROOF_CPUS', 'XUANJIAN_PROOF_CONCURRENCY')}
        user_home = Path.home()
        env.update(HOME=str(home), DSH_HOME=str(base / 'dsh-home'),
                   DSH_PLATFORM_KEY=profile.get('api_key') or 'not-required',
                   RUSTUP_HOME=os.environ.get('RUSTUP_HOME', str(user_home / '.rustup')),
                   CARGO_HOME=os.environ.get('CARGO_HOME', str(user_home / '.cargo')))
        env['DSH_VERIFICATION_TOOL']='verifast' if verifast else 'framac'
        env['DSH_PACKAGE_JSON']=str(PACKAGE/'package.json')
        env['DSH_SUBAGENT_AUDIT']=str(workspace/'subagent-audit.jsonl')
        env['DSH_REQUIRE_SUBAGENT']='1' if require_subagent else '0'
        if compact:
            env['DSH_COMPACT_C']='1'
            env['DSH_AUTO_HANDOFF']='1' if os.getenv('XUANJIAN_HARNESS_AUTO_HANDOFF','1')=='1' else '0'
        if artifact_dir is not None:
            Path(artifact_dir).mkdir(parents=True,exist_ok=True)
            env['DSH_PROGRESS_FILE']=str(Path(artifact_dir).resolve()/'live-progress.jsonl')
        if effective_child:env['DSH_SUBAGENT_KEY']=effective_child.get('api_key') or 'not-required'
        verifier_command = [str(verus_path()), str(workspace / 'output.rs'), '--crate-type', 'lib', '--crate-name', 'submission']
        task = (prompt + '\n\nYou are running inside the official DeepSeek Harness. Use your real file tools to create output.rs in the current workspace. '
                'Use the bash tool to execute this verifier command (arguments are shell quoted):\n' +
                ' '.join(shlex.quote(x) for x in verifier_command) +
                '\nRead actual diagnostics and fix output.rs as needed. Do not access files outside this task workspace except the verifier/toolchain. '
                'Do not install packages or access the network from tools. Never use assume/admit/external_body. '
                'Finish within 6 model steps if possible. Keep the final complete Verus source in output.rs. '
                'The platform independently validates this file; your own success claims do not determine Pass. Return the complete source only.')
        spec_patches=False
        filename = 'output.rs'
        if files_format:
            filename = 'answer.json'
            python = ROOT / '.venv/bin/python'
            verification_command = shlex.join([str(python if python.is_file() else Path(sys.executable)), str(ROOT / 'scripts/harness_verify_c.py'), str(workspace / 'answer.json')]+(['--tool','verifast'] if verifast else []))
            input_dir=workspace/'input';input_dir.mkdir(exist_ok=True)
            try:
                sources=json.JSONDecoder().raw_decode(prompt.split('Original source:\n',1)[1])[0]
                for source in sources:
                    path=Path(source['path'])
                    if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid source path')
                    target=input_dir/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source['content'])
            except (IndexError,ValueError,KeyError,TypeError):
                sources=[]
            env['PYTHONPATH']=str(ROOT)
            from engine.verification.environment import verifier_environment
            verifier_environment(workspace,env,'verifast' if verifast else 'framac')
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
                    'For a root function with no callers (such as main), a reusable function contract is optional: record its actual verification status in summary.json; do not repeatedly call save-contract if it has only loop annotations. '
                    'Use synchronous bash calls for these small tools; do not start background jobs or poll. '
                    'Merge annotations back into the original project paths for answer.json, preserving original tokens and assertions. '
                    'Finish only after running the platform final verification command given above. Do not stop after writing a plan.')
        if sub_profile:
            task += ('\nThe configured Qwen subagent is a text-only specification worker: its tool schemas are deliberately empty because this deployed endpoint does not support automatic tool calls. '
                     'Do not ask it to read files, run commands, call send_message, or invoke any tool. Include the complete source and the generation rules from spec-bottomup in its task. '
                     'Ask it to return annotations or complete annotated source as plain text/JSON. The official runtime delivers its final answer to you automatically. '
                     'You, the main DeepSeek agent, must execute spec-split, tool-based injection, Frama-C verification, contract collection and repairs using that answer. '
                     'If the child fails, report the failure; never fabricate its output or replace its generation with your own.')
        if verifast:
            task=(prompt+'\nYou are the official DeepSeek Harness. Use native file tools to write answer.json with all files as {path,content}. '
                  'Generate only VeriFast separation-logic annotations: requires/ensures after each function signature, and invariant after each loop header. '
                  'Preserve original C code and assertions. No ACSL loop/assigns/\\result syntax, no Frama-C/spectool commands. '
                  'Do not introduce assume/admit, false preconditions or unproved lemmas. '
                  'Use bash only for the exact platform VeriFast verification command: '+verification_command+
                  '\nRead actual diagnostics and repair annotations only. Never claim proof success without tool evidence. '
                  'Do not access files outside the workspace except the verifier toolchain, install packages or use network tools. '
                  'Keep final full-files JSON in answer.json. The platform independently verifies it.')
            if require_subagent:
                task+='\nUse the native subagent tool for annotation generation, including the complete source and VeriFast rules in its task. The child returns text JSON only, cannot use tools, and must not claim verification. Use its candidate and run the verification command yourself. If the child fails, report failure instead of fabricating its answer.'
        # Multi-function input needs the dependency workflow, rather than the single-case compact path.
        if 'Platform source classification: acsl-bottom-up.' in prompt:
            compact=False
        if compact:
            from .c_compact import task_prompt
            task=task_prompt(prompt,auto_handoff=env.get('DSH_AUTO_HANDOFF')=='1')
        repair=bool(session is not None and session.rounds and 'Previous candidate:\n' in prompt)
        if repair:
            require_subagent=False
            env['DSH_REQUIRE_SUBAGENT']='0'
            env['DSH_REPAIR_MODE']='1'
            task=('REPAIR ONLY: continue this same case and existing annotations under the original Skill and proof policy. '
                  'Do not restart specification generation, repeat planning/splitting, or launch another subagent. '
                  'Use the existing candidate below as the baseline. Modify only annotations needed for the failed proof goals; '
                  'retain all unrelated annotations and preserve original C tokens and assertions. '
                  'Write the complete repaired files JSON to answer.json using the native write tool. '
                  'Do not run an internal proof; the platform verifies the repaired candidate independently.\n'
                  'Previous candidate:\n'+prompt.split('Previous candidate:\n',1)[1])
        if files_format and sources and os.getenv('XUANJIAN_HARNESS_SPEC_PATCHES','1')=='1':
            from engine.verification.spec_patches import patch_contract
            from engine.verification.worker_contract import thinking_policy
            policy=thinking_policy()
            spec_patches=True
            env.update(DSH_SPEC_PATCHES='1',DSH_AUTO_HANDOFF='1',DSH_PATCH_PYTHON=str(ROOT/'.venv/bin/python'))
            for entry_patch in patch:
                if entry_patch.get('id')=='llm-pi-ai':
                    worker=entry_patch['config']['providers'].get('platform-subagent')
                    if worker:
                        worker['defaultMaxTokens']=min(worker['defaultMaxTokens'],4096)
                        worker_format='qwen' if worker['models'][0]['id']=='deepseek-v4.1-flash-1017' else 'qwen-chat-template'
                        worker.update(reasoning='low' if policy['worker']=='on' else 'off',compat={'thinkingFormat':worker_format,'supportsReasoningEffort':False,'supportsDeveloperRole':False})
                        for worker_model in worker['models']:
                            # Native token estimation omits some gateway/template overhead.
                            # Reserve context space rather than trimming pinned Skills or source.
                            worker_model.update(maxTokens=min(worker_model['maxTokens'],4096),contextWindow=max(2048,worker_model['contextWindow']-1024),reasoningEfforts={'off':None,'low':'low'})
                    main=entry_patch['config']['providers']['platform-api']
                    if profile['model']=='deepseek-v4.1-flash-1017':
                        main.update(reasoning='low' if policy['main']=='on' else 'off',compat={'thinkingFormat':'qwen','supportsReasoningEffort':False,'supportsDeveloperRole':False})
                        for model in main['models']:model['reasoningEfforts']={'off':None,'low':'low'}
            for child_patch in patch:
                if child_patch.get('id')=='tool-subagent':child_patch['config']['agentOptions']['reasoningEffort']='low' if policy['worker']=='on' else 'off'
            patch += [{'insert':[{'id':'platform-spec-patch-tools','name':str(ROOT/'engine/cli_plugins/spec_patch_tools.mjs')}]}]
            config.write_text(json.dumps(patch),encoding='utf-8')
            context=patch_contract(sources,verification_tool='verifast' if verifast else 'framac')
            (workspace/'.platform-originals.json').write_text(json.dumps(sources,ensure_ascii=False),encoding='utf-8')
            pinned=prompt.split('Original source:\n',1)[0].replace('Return ONLY JSON with a files array of {path, content}. Return every input file using its original path.', 'Return only ACSL annotations and original insertion line numbers.')
            from engine.verification.worker_contract import worker_prompt
            (workspace/'.platform-worker-task.txt').write_text(worker_prompt(pinned,sources,verification_tool='verifast' if verifast else 'framac'),encoding='utf-8')
            (workspace/'.platform-worker-task.txt').chmod(0o600)
            if repair:
                from engine.verification.spec_patches import recover_patch_candidate
                prior=recover_patch_candidate(workspace)
                diagnostics=prompt.split('Verifier diagnostics:\n',1)[-1][-6000:]
                map_file=workspace/'patch-line-map.json'
                mapping=json.loads(map_file.read_text()) if map_file.is_file() else []
                reported={int(n) for n in re.findall(r'(?:"line"\s*:\s*|line\s+)(\d+)',diagnostics)}
                relevant_map=[r for r in mapping if r['generated_line'] in reported][:16]
                task=('REPAIR ANNOTATION PATCHES ONLY. Do not restart specification generation or launch another child. '
                      'Use submit_spec_patches with the complete revised patch set, retaining unrelated valid patches. '
                      'Do not call write/read/bash or output complete source. The platform merges patches into immutable originals and verifies independently. '
                      'For unproved goals, use the exact proof obligations and line mapping below; do not invent assumptions.\n'+context+
                      '\nPrevious generated patches:\n'+json.dumps(prior,ensure_ascii=False)+'\nVerifier diagnostics:\n'+diagnostics+'\nLine map (generated line -> original line / patch index):\n'+json.dumps(relevant_map,ensure_ascii=False))
            else:
                task=('Call delegate_spec with {} exactly once. The platform injects all original source and unchanged pinned Skill instructions into the native worker. '
                      'Do not analyze or rewrite source, repeat Skills, create plans, poll or write files. End your turn and wait for the runtime delivery. '
                      'The platform saves the worker annotation patches automatically. After successful delivery, finish with a brief acknowledgement. '
                      'If its JSON formatting is invalid, use inspect_worker_result and submit_spec_patches to normalize only the existing worker annotations with original line numbers. Do not regenerate or rewrite source. If the child fails or supplied no usable annotations, report failure.')
            # A fresh per-round receipt is required; old output must never masquerade as a new repair.
            receipt=workspace/'candidate-patches.json'
            if receipt.exists():receipt.unlink()
        cmd = [node, str(entry), '--profile', 'headless', '--patch', str(config), '--json', '-']
        def redact(value):
            for sensitive, replacement in [((sub_profile or {}).get('api_key'), '[REDACTED]'), ((sub_profile or {}).get('base_url'), '[SUBAGENT_ENDPOINT]'), (profile.get('api_key'), '[REDACTED]'), (profile['base_url'], '[MODEL_ENDPOINT]'), (str(base), '[TASK]')]:
                if sensitive: value = value.replace(sensitive, replacement)
            value = re.sub(r'https?://[^\s<>"\\]+', '[URL]', value)
            return value
        timed_out = False
        # Keep the existing file in a persistent session: upstream write tools track it.
        previous_output=(workspace/filename).stat().st_mtime_ns if (workspace/filename).is_file() else None
        if session is None:(workspace/filename).unlink(missing_ok=True)
        (workspace/'subagent-audit.jsonl').write_text('')
        if session is not None:
            identity=(profile['model'],profile['base_url'],profile.get('api_key'),json.dumps(effective_child,sort_keys=True),json.dumps(policy,sort_keys=True) if spec_patches else '')
            diagnostics=[]
            try:
                raw=session.request(cmd,workspace,env,task,timeout,identity)
            except TimeoutError as exc:
                raw=getattr(exc,'raw','');timed_out=True
            except RuntimeError as exc:
                raw=getattr(exc,'raw','')
                stderr_file=workspace/'.platform-cli-stderr.log'
                if stderr_file.exists():diagnostics=[redact(stderr_file.read_text(errors='replace')[-3500:])]
            oversized=False
            exit_code=-9 if timed_out else session.proc.poll() if session.proc is not None and session.proc.poll() is not None else 0
        else:
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
            exit_code=proc.returncode
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
                   'auto_child_handoff':env.get('DSH_AUTO_HANDOFF')=='1','candidate_protocol':('verifast-patches-v1' if verifast else 'acsl-patches-v1') if spec_patches else 'full-files',
                   'verification_tool':'verifast' if verifast else 'framac' if files_format else 'verus','thinking_policy':policy if (spec_patches or verifast) else 'provider-default',
                   'worker_context_reserve_tokens':1024 if spec_patches else 0,
                   'output_budget':{'main_max_tokens':output_limits(profile)[0],'sub_max_tokens':min(output_limits(profile)[1],4096) if spec_patches else output_limits(profile)[1]},
                   'exit_code': exit_code, 'operation': 'repair' if repair else 'generate', 'process_reused': bool(session and session.rounds>1), 'session_transport': 'persistent-jsonl' if session else 'one-shot', 'terminal_reason': reason, 'diagnostics': diagnostics,
                   'events_kind': 'upstream-json-projection-without-thinking', 'events': native_events}
        def fail(code, message):
            error = ProviderError(code, message, usage=result['usage'])
            error.agent_runtime = runtime
            error.agent_events = result['agent_events']
            error.provider_calls = result['provider_calls']
            raise error
        audit_file=workspace/'subagent-audit.jsonl'
        child_events=[json.loads(line) for line in audit_file.read_text().splitlines()] if audit_file.exists() else []
        runtime.update(subagent_events=child_events,subagent_model=(sub_profile or profile)['model'],subagent_inherits_main=not bool(sub_profile),workflow='compact-c-v1' if compact else 'standard')
        patch_problem=None
        if spec_patches and complete and not timed_out:
            try:
                from engine.verification.spec_patches import parse_patch_json,merge_spec_patches,patch_line_map,candidate_quality
                receipt=workspace/'candidate-patches.json'
                if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size>262144:
                    worker_final=workspace/'.platform-worker-final.txt'
                    if not repair and worker_final.is_file() and not worker_final.is_symlink() and worker_final.stat().st_size<=1048576:
                        from engine.verification.worker_contract import missing_receipt_message
                        raise ValueError(missing_receipt_message(worker_final.read_text(),sources,verification_tool='verifast' if verifast else 'framac'))
                    raise ValueError('未提交新的规约补丁；不会使用上一轮候选冒充本轮输出。')
                patches=parse_patch_json(receipt.read_text())
                quality=candidate_quality(sources,patches,verification_tool='verifast' if verifast else 'framac')
                if not quality['annotation_nonempty'] and (verifast or quality.get('uncovered_loops_estimate')):raise ValueError('未生成实际规约：不能用空 patches 代替缺少不变量的循环规约。')
                runtime['candidate_quality']=quality
                (workspace/'candidate-quality.json').write_text(json.dumps(quality,ensure_ascii=False))
                merged=merge_spec_patches(sources,patches,verification_tool='verifast' if verifast else 'framac')
                from acsl.application.agent_execution import validate_candidates
                validate_candidates(sources,merged,False,sources[0]['path'],'single')
                (workspace/'answer.json').write_text(json.dumps({'files':merged},ensure_ascii=False))
                (workspace/'patch-line-map.json').write_text(json.dumps(patch_line_map(sources,patches,verification_tool='verifast' if verifast else 'framac'),ensure_ascii=False))
                runtime['patch_count']=len(patches['patches'])
                runtime['candidate_origin']='platform-merged-immutable-source'
            except (ValueError,KeyError,TypeError,OSError) as exc:
                patch_problem=str(exc)
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
            fail('output_limit', f'主 Agent 单次输出达到 {output_limits(profile)[0]} tokens 上限，尚未完成候选；不是网络或账户余额错误。')
        if exit_code or not complete:
            detail = str((reason.get('error') or {}).get('message') or '')[:1500]
            error_code = str((reason.get('error') or {}).get('code') or 'CLI_EXIT')[:100]
            if not detail and diagnostics: detail = diagnostics[-1]
            fail('agent_failed', '官方 DeepSeek Harness 执行失败（' + error_code + '）' + ('：' + detail if detail else '；请展开 CLI 诊断。'))
        if not result['agent_events']:
            fail('agent_tools', '官方 Harness 未执行工具，未将普通文本当作 Agent 工作结果。')
        if require_subagent and (not any(e.get('type')=='end' and e.get('stop_reason')=='completed' for e in child_events) or not any(e.get('tool') in ('subagent','delegate_spec') and e.get('status')=='completed' for e in result['agent_events'])):
            fail('agent_delegation','所选子 Agent 未执行或未正常完成；主模型自行生成的候选不能替代子模型流程。请查看子 Agent 事件。')
        if patch_problem:fail('agent_output',patch_problem)
        target = workspace / filename
        if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_CODE_BYTES:
            fail('agent_output', f'主模型未完成候选交接：未写入有效的 {filename} 文件；验证器尚未执行。')
        if session is not None and previous_output is not None and target.stat().st_mtime_ns==previous_output:
            fail('agent_output','修复轮未更新候选文件，未使用上一轮文件冒充本轮输出。')
        code = _clean_code(target.read_text(), [profile.get('api_key')]) if output_format=='verus' else target.read_text()
        return dict(result, code=code, model_name=profile['model'], finish_reason='stop', agent_runtime=runtime)
