"""C/ACSL candidates from official Codex and Claude CLIs using platform API auth."""
from pathlib import Path
import json,os,shlex,signal,subprocess,threading,time,tempfile
from datetime import datetime,timezone
from engine.cli_runtime import ROOT,command
from engine.nl2verus.model_provider import ProviderError


def project_event(agent,event):
    """Return only native tool lifecycle events, without generated reasoning."""
    rows=[]
    if agent=='codex' and event.get('type') in ('item.started','item.completed'):
        item=event.get('item',{});kind=item.get('type')
        if kind in ('command_execution','file_change','mcp_tool_call'):
            proof_failed=bool(item.get('error'))
            if kind=='mcp_tool_call':
                for block in (item.get('result') or {}).get('content',[]):
                    try:proof_failed=proof_failed or json.loads(block.get('text','')).get('verified') is False
                    except (ValueError,AttributeError):pass
            status='running' if event['type']=='item.started' else 'failed' if proof_failed or item.get('status')=='failed' or item.get('exit_code',0) not in (None,0) else 'completed'
            rows.append({'id':item.get('id','tool'),'label':('源码分析与函数分层' if item.get('tool')=='prepare_project' else 'Frama-C MCP 验证') if kind=='mcp_tool_call' else '执行工作区命令' if kind=='command_execution' else 'CLI 写入候选规约','status':status})
    if agent=='claude-code' and event.get('type') in ('assistant','user'):
        for block in event.get('message',{}).get('content',[]):
            if block.get('type')=='tool_use':rows.append({'id':block['id'],'label':'Frama-C MCP 验证' if block.get('name','').startswith('mcp__frama') else 'Claude '+block.get('name','工具执行'),'status':'running'})
            if block.get('type')=='tool_result':
                failed=bool(block.get('is_error'));content=block.get('content',[])
                texts=[content] if isinstance(content,str) else [c.get('text','') for c in content if isinstance(c,dict)]
                for text in texts:
                    try:failed=failed or json.loads(text).get('verified') is False
                    except (ValueError,AttributeError):pass
                rows.append({'id':block['tool_use_id'],'label':'Claude 工具执行','status':'failed' if failed else 'completed'})
    return rows


def generate(agent,prompt,profile,directory,timeout=200,*,subagent_candidate=None):
    profile=dict(profile)
    if agent=='claude-code':profile['base_url']=profile['base_url'].rstrip('/').removesuffix('/v1')
    directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    workspace=directory/'workspace';workspace.mkdir(exist_ok=True)
    private=tempfile.TemporaryDirectory(prefix='c-agent-cli-')
    home=Path(private.name)/'home';home.mkdir(exist_ok=True)
    python=ROOT/'.venv/bin/python'
    if not python.is_file():python=Path(__import__('sys').executable)
    sources=json.JSONDecoder().raw_decode(prompt.split('Original source:\n',1)[1])[0]
    for item in sources:
        path=Path(item['path'])
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid source path')
        target=workspace/'input'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item['content'])
    manifest=directory/'source-manifest.json'
    if manifest.exists():manifest.chmod(0o600)
    manifest.write_text(json.dumps(sources,ensure_ascii=False));manifest.chmod(0o400)
    mcp_args=[str(ROOT/'scripts/c_verifier_mcp.py'),str(workspace),str(manifest)]
    verify=shlex.join([str(python),str(ROOT/'scripts/harness_verify_c.py'),str(workspace/'answer.json')])
    task=(prompt+'\nYou are the official '+agent+' CLI, using the platform model API. Original files are in input/. Use your real file tools to create answer.json with a files array of {path,content}, preserving each original path and ALL original C tokens and ACSL assertions. Only add valid ACSL contracts and loop annotations. Do not add admit/assume/axioms or false preconditions. Use the registered Frama-C MCP tool verify_candidate to run actual verification. Do not try to access Docker from shell tools. Write all loop clauses in ONE block /*@ loop invariant ...; loop assigns ...; loop variant ...; */ immediately before each loop, not separate //@ annotation blocks. Inspect actual Frama-C diagnostics and repair annotations if needed. Keep final candidates in answer.json. Do not install packages or access network from tools. If the verifier reports status unavailable, stop and report the environment error; never attempt to repair Docker or its configuration from shell tools. Finish once the actual verifier passes; do not reread unrelated files. The platform independently checks the output.')
    if 'Skill: spec-split' in prompt:
        task += ('\nFor the attached three Skills, first call the MCP prepare_project tool to execute spec-split. Read the resulting stub/inline slices in output/. Apply spec-orchestrate bottom-up, with spec-bottomup annotation generation using the provided API sub-agent candidate when present, otherwise this CLI and its selected model. Do not attempt to spawn an unavailable subagent or switch models. Use MCP verify_candidate for actual proof diagnostics. For these small projects, avoid shell-based tool discovery and use the provided native file and MCP tools directly. Preserve original requirements and report actual failures.')
    if subagent_candidate is not None:
        task+='\nThe platform has already delegated specification generation to the selected API sub-agent. Its validated candidate follows. Use this candidate as your starting point; inspect and repair its annotations rather than regenerate from scratch. Do not spawn another subagent. Preserve original requirements, use native tools to write answer.json, and execute the independent verification tool.\nSub-agent candidate:\n'+json.dumps({'files':subagent_candidate},ensure_ascii=False)
    env={k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR','SYSTEMROOT','ACSL_AGENT_RUNTIME_ROOT','XUANJIAN_PROOF_CPUS','XUANJIAN_PROOF_CONCURRENCY')}
    env.update(HOME=str(home),CODEX_HOME=str(home),PYTHONPATH=str(ROOT),NL2VERUS_AGENT_KEY=profile['api_key'])
    from engine.docker_runtime import configure_docker
    mcp_env=configure_docker(workspace,env)
    try:
        probe=subprocess.run(['docker','compose','version'],env=env,cwd=ROOT,capture_output=True,timeout=10)
        if probe.returncode:raise ProviderError('agent_tools','Docker Compose 不可用；已在调用模型前停止，请检查验证器运行环境。')
    except (OSError,subprocess.TimeoutExpired):
        raise ProviderError('agent_tools','无法启动 Docker Compose；已在调用模型前停止。') from None
    if agent=='codex':
        args=command('codex')+['exec','--json','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral','--sandbox','workspace-write','--model',profile['model'],
          '-c','model_provider="platform"','-c','model_providers.platform.name="Platform API"','-c','model_providers.platform.base_url='+json.dumps(profile['base_url']),
          '-c','model_providers.platform.wire_api="responses"','-c','model_providers.platform.env_key="NL2VERUS_AGENT_KEY"','-c','model_providers.platform.requires_openai_auth=false',
          '-c','model_providers.platform.supports_websockets=false','-c','model_providers.platform.request_max_retries=0','-c','model_providers.platform.stream_max_retries=0',
          '-c','mcp_servers.frama.command='+json.dumps(str(python)),'-c','mcp_servers.frama.args='+json.dumps(mcp_args),'-c','mcp_servers.frama.enabled_tools=["prepare_project","verify_candidate"]','-c','mcp_servers.frama.tools.prepare_project.approval_mode="approve"','-c','mcp_servers.frama.tools.verify_candidate.approval_mode="approve"','-c','mcp_servers.frama.required=true','-c','mcp_servers.frama.tool_timeout_sec=120','-c','approval_policy="never"','-c','features.apps=false','-c','features.browser_use=false','-c','web_search="disabled"','-']
        for key,value in mcp_env.items():args[-1:-1]=['-c','mcp_servers.frama.env.'+key+'='+json.dumps(value)]
        stdin=task
    else:
        args=['node',str(ROOT/'scripts/claude_bridge.mjs')]
        stdin=json.dumps({'prompt':task,'profile':profile,'workingDirectory':str(workspace),'homeDirectory':str(home),'verifierCommand':verify,'taskLanguage':'C','mcpConfig':{'frama':{'command':str(python),'args':mcp_args}},'runtimeEnvironment':mcp_env})
    rawfile=Path(private.name)/'events.jsonl';errfile=Path(private.name)/'stderr.log';progress=directory/'live-progress.jsonl';stop=threading.Event();events=[]
    def redact(text):
        for value in (profile.get('api_key'),profile.get('base_url')):
            if value:text=text.replace(value,'[PRIVATE]')
        return text
    offset=0
    def consume():
        nonlocal offset
        if not rawfile.exists():return
        with rawfile.open() as stream:
            stream.seek(offset)
            while True:
                line=stream.readline()
                if not line or not line.endswith('\n'):break
                offset=stream.tell()
                try:event=json.loads(line)
                except ValueError:continue
                if event.get('item',{}).get('type')=='reasoning':continue
                events.append(event)
                with progress.open('a') as output:
                    for row in project_event(agent,event):
                        row['at']=datetime.now(timezone.utc).isoformat()
                        output.write(json.dumps(row,ensure_ascii=False)+'\n')
    def pump():
        while not stop.wait(.15):consume()
    thread=threading.Thread(target=pump,daemon=True);thread.start();started=time.monotonic();timed_out=False
    try:
        with rawfile.open('wb') as out,errfile.open('wb') as err:
            proc=subprocess.Popen(args,cwd=workspace,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True)
            try:proc.communicate(stdin.encode(),timeout=max(1,timeout))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate();timed_out=True
        time.sleep(.2)
    finally:
        stop.set();thread.join();consume()
        safe=redact('\n'.join(json.dumps(e,ensure_ascii=False) for e in events))
        (directory/'cli-events.jsonl').write_text(safe)
        diagnostics=redact(errfile.read_text(errors='replace')) if errfile.exists() else ''
        private.cleanup()
    completed=any(e.get('type')=='turn.completed' for e in events) if agent=='codex' else any(e.get('type')=='result' and e.get('subtype')=='success' and not e.get('is_error') for e in events)
    tools=[row for event in events for row in project_event(agent,event)]
    child_tool_ids={b.get('id') for e in events if e.get('type')=='assistant' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_use' and b.get('name')=='mcp__frama__verify_candidate'}
    mcp_executed=any(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='mcp_tool_call' and e['item'].get('server')=='frama' and e['item'].get('tool')=='verify_candidate' and e['item'].get('status')=='completed' and not e['item'].get('error') for e in events) if agent=='codex' else any(b.get('type')=='tool_result' and b.get('tool_use_id') in child_tool_ids and not b.get('is_error') for e in events if e.get('type')=='user' for b in e.get('message',{}).get('content',[]))
    metadata={'native_verifier_executed':mcp_executed,'agent':agent,'model':profile['model'],'protocol':'responses' if agent=='codex' else 'anthropic','completed':completed,'exit_code':proc.returncode,'tool_events':tools,'elapsed_sec':round(time.monotonic()-started,2)}
    child_runtime=directory/'subagent-runtime.json'
    if child_runtime.is_file():metadata['subagent']=json.loads(child_runtime.read_text())
    elif subagent_candidate is not None:metadata['subagent']={'transport':'existing-candidate','status':'reused'}
    (directory/'cli-runtime.json').write_text(json.dumps(metadata,ensure_ascii=False))
    if timed_out:raise ProviderError('agent_timeout',agent+' 超过任务时间限制；工具时间线和运行元数据已保留。')
    if proc.returncode or not completed:
        errors=[e.get('message') or e.get('error') or e.get('errors') for e in events if e.get('type') in ('error','bridge_error','result')]
        (directory/'cli-diagnostics.json').write_text(redact(json.dumps({'errors':errors,'stderr':diagnostics[-4000:]},ensure_ascii=False)))
        raise ProviderError('agent_failed',agent+' 官方 CLI 未正常完成；请查看 cli-diagnostics.json。')
    if not mcp_executed:raise ProviderError('agent_tools',agent+' 未成功调用平台验证工具；未将普通生成结果当作完整验证流程。')
    target=workspace/'answer.json'
    if not tools or target.is_symlink() or not target.is_file() or target.stat().st_size>2*1024*1024:raise ProviderError('agent_output',agent+' 未通过实际工具创建有效候选。')
    return json.loads(target.read_text())
