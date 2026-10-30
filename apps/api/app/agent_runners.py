"""Bounded external Agent calls. Only generated candidates reach the verifier."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import threading
from functools import lru_cache

from .config import ROOT_DIR, RUNTIME_DIR, get_available_models, MODELS_CONFIG_PATH

class AgentCallError(ValueError):
    pass

NAMES = {'default':'默认验证流程','codex':'Codex','claude-code':'Claude Code','deepseek-harness':'DeepSeek Harness CLI'}
SCHEMA = {'type':'object','properties':{'files':{'type':'array','items':{'type':'object','properties':{'path':{'type':'string'},'content':{'type':'string'}},'required':['path','content'],'additionalProperties':False}}},'required':['files'],'additionalProperties':False}


def executable(agent):
    from engine.cli_runtime import command
    args=command(agent)
    return args[0] if args and len(args)==1 else args[-1] if args else None


def runner_default_model(agent):
    if agent!='codex':return ''
    import tomllib
    settings=Path(os.getenv('CODEX_HOME',str(Path.home()/'.codex')))/'config.toml'
    try:return str(tomllib.loads(settings.read_text()).get('model','')) if settings.is_file() else ''
    except (OSError,ValueError):return ''


def runner_models(agent):
    """Advertise local CLI choices without making a paid generation request."""
    if agent == 'claude-code':
        return ['sonnet', 'opus', 'haiku']
    path = Path(os.getenv('CODEX_HOME', str(Path.home()/'.codex'))) / 'models_cache.json'
    try:
        entries = json.loads(path.read_text()).get('models', [])
        names = [m['slug'] for m in entries if m.get('visibility') == 'list' and m.get('slug')]
    except (OSError, ValueError, TypeError):
        names = []
    default = runner_default_model(agent)
    return list(dict.fromkeys(([default] if default else []) + names))


def deepseek_model():
    from engine.autospec.src.config_manager import ConfigLoader
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR/'.env', override=False)
    configured = os.getenv('DEEPSEEK_HARNESS_MODEL')
    for name in ([configured] if configured else list(dict.fromkeys(['deepseek-v4-flash-0731']+get_available_models()))):
        if not name or (not configured and 'deepseek' not in name.lower()):
            continue
        try:
            model = ConfigLoader.get_model_config(name, str(MODELS_CONFIG_PATH))
            if model.api_key and model.base_url:
                return name
        except (ValueError, OSError):
            pass
    return None


def run_process(args, *, cwd, timeout, stdin='', env=None):
    """Drain to temporary files; bound returned logs and terminate the process group."""
    with tempfile.TemporaryFile(mode='w+b') as out, tempfile.TemporaryFile(mode='w+b') as err:
        with subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=out, stderr=err,
                              env=env, start_new_session=True) as proc:
            try:
                proc.communicate(stdin.encode(), timeout=max(1, timeout))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise TimeoutError('Agent 或验证器超过任务时间限制，进程已终止。') from None
            for stream in (out, err):
                if stream.tell() > 4*1024*1024:
                    raise ValueError('运行器输出超过 4 MiB 限制。')
                stream.seek(0)
            return proc.returncode, out.read().decode(errors='replace'), err.read().decode(errors='replace')


@lru_cache(maxsize=8)
def _status(bucket):
    items = [{'id':'default','name':NAMES['default'],'ready':True,'installed':True,'authenticated':None,'message':'使用平台现有模型与验证流程。','model_policy':'platform'}]
    for agent in ('codex','claude-code'):
        path = executable(agent)
        authenticated = False
        if path:
            try:
                command = [path,'login','status'] if agent == 'codex' else [path,'auth','status']
                code, stdout, stderr = run_process(command,cwd=ROOT_DIR,timeout=8)
                authenticated = code == 0 if agent == 'codex' else code == 0 and json.loads(stdout).get('loggedIn') is True
            except (OSError, ValueError, TimeoutError):
                pass
        items.append({'id':agent,'name':NAMES[agent],'installed':bool(path),'authenticated':authenticated,'ready':bool(path and authenticated),
                      'message':'已检测到登录记录；真实连接将在任务执行时验证。' if authenticated else '请先在运行后端的账号下登录。' if path else '未找到可执行程序。',
                      'model_policy':'runner','default_model':runner_default_model(agent),'models':runner_models(agent),'connection_verified':False})
    model = deepseek_model()
    from engine.nl2verus.dsh_cli import installed
    cli_installed = installed() and bool(shutil.which('node'))
    items.append({'id':'deepseek-harness','name':NAMES['deepseek-harness'],'installed':cli_installed,'authenticated':None,'ready':bool(model and cli_installed),
                  'message':'官方 DeepSeek Harness CLI；凭证已配置，候选由 Frama-C 独立验证。' if model and cli_installed else '请运行 python3 scripts/install_agent_runtime.py 安装官方 CLI。' if not cli_installed else '请配置 DeepSeek 模型服务与凭证。',
                  'model_policy':'platform','default_model':model})
    return items


_CONNECTION_LOCK=threading.Lock()

def record_agent_connection(agent,success):
    from .storage import JsonStore,utcnow
    path=RUNTIME_DIR/'agents'/'connections.json'
    with _CONNECTION_LOCK:
        data=JsonStore._read_json(path) if path.is_file() else {}
        data[agent]={'connection_verified':bool(success),'last_checked_at':utcnow().isoformat(),'runtime':'official-dsh' if agent=='deepseek-harness' else agent}
        path.parent.mkdir(parents=True,exist_ok=True)
        JsonStore._write_json(path,data)



def agent_status():
    from .storage import JsonStore
    path=RUNTIME_DIR/'agents'/'connections.json'
    try:connections=JsonStore._read_json(path) if path.is_file() else {}
    except (OSError,ValueError):connections={}
    items=[]
    for raw in _status(int(time.monotonic()//20)):
        entry=dict(raw);last=connections.get(entry['id'])
        if last and (entry['id']!='deepseek-harness' or last.get('runtime')=='official-dsh'):
            entry.update(last)
            if last['connection_verified']:entry['message']='最近一次调用已连通；候选仍须通过验证器检查。'
            else:entry['message']='最近一次调用未成功，请检查代理、登录或模型设置后重试。'
        items.append(entry)
    from .skill_library import ensure_bundled_skills
    from engine.autospec.src.config_manager import ConfigLoader
    sub_models=[]
    for name in ('qwen35-4b-mix64','qwen35-9b-mix64'):
        try:
            config=ConfigLoader.get_model_config(name,str(MODELS_CONFIG_PATH));configured=bool(config.base_url)
        except (ValueError,OSError):configured=False
        sub_models.append({'id':name,'configured':configured,'transport':'ssh' if os.getenv('XUANJIAN_QWEN_SSH_TARGET') else 'direct'})
    for item in items:
        if item['id']=='deepseek-harness':item['sub_models']=sub_models
    return {'items':items,'defaults':{'agent':'deepseek-harness','model':'deepseek-v4-flash-0731','sub_model':'','timeout_sec':200,'skill_refs':ensure_bundled_skills()}}


def require_agent(agent):
    entry = next(x for x in agent_status()['items'] if x['id']==agent)
    if not entry['ready']:
        raise ValueError(entry['message'])


def agent_environment():
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR/'.env',override=False)
    env=dict(os.environ)
    proxy=env.get('XUANJIAN_AGENT_PROXY','').strip()
    if proxy:
        from urllib.parse import urlsplit
        if urlsplit(proxy).scheme not in ('http','https') or not urlsplit(proxy).hostname:
            raise ValueError('XUANJIAN_AGENT_PROXY 需要 HTTP 或 HTTPS 代理地址。')
        env.update(HTTPS_PROXY=proxy,HTTP_PROXY=proxy,https_proxy=proxy,http_proxy=proxy)
    return env


def _generate(agent, prompt, directory: Path, timeout, model='',sub_model=''):
    """Only return a candidate; never treat runner success as verification success."""
    directory.mkdir(parents=True, exist_ok=True)
    if agent == 'deepseek-harness':
        from engine.autospec.src.config_manager import ConfigLoader
        from engine.nl2verus.dsh_cli import generate as run_harness
        model = model or deepseek_model()
        if not model:
            raise ValueError('请选择已配置的模型。')
        config = ConfigLoader.get_model_config(model, str(MODELS_CONFIG_PATH))
        profile = {'model':config.model_name,'base_url':config.base_url,'api_key':config.api_key}
        sub_profile=None
        if sub_model:
            if sub_model not in ('qwen35-4b-mix64','qwen35-9b-mix64'):raise ValueError('不支持的 Sub-agent 模型。')
            child=ConfigLoader.get_model_config(sub_model,str(MODELS_CONFIG_PATH))
            if not child.base_url:raise ValueError('Sub-agent 模型服务地址未配置。')
            sub_profile={'model':child.model_name,'base_url':child.base_url,'api_key':child.api_key}
        try:
            from contextlib import nullcontext
            from engine.cli_model_transport import model_route
            route=model_route(sub_profile,enabled=True) if sub_profile else nullcontext(None)
            started=time.monotonic()
            with route as child_route:
                result = run_harness(prompt, profile, timeout=max(1,timeout-(time.monotonic()-started)), output_format='files', artifact_dir=directory,sub_profile=child_route,require_subagent=True)
        except Exception:
            raise AgentCallError('官方 DeepSeek Harness CLI 执行失败，请检查运行时、网络和模型配置；未回退直连 API。') from None
        (directory/'harness-runtime.json').write_text(json.dumps({k:v for k,v in result.items() if k!='code'},ensure_ascii=False))
        output = result['code']
    else:
        binary = executable(agent)
        if not binary:
            raise AgentCallError('未找到 Agent 可执行程序。')
        if agent == 'codex':
            schema = directory/'response-schema.json'
            schema.write_text(json.dumps(SCHEMA))
            answer = directory/'answer.json'
            model=model or runner_default_model(agent)
            args = [binary,'exec','--ignore-user-config','--disable','shell_tool','--disable','unified_exec','--disable','multi_agent','--disable','plugins','--disable','remote_plugin','--ephemeral','--skip-git-repo-check','--sandbox','read-only',
                    '--output-schema',str(schema),'--output-last-message',str(answer),'--color','never','-']
            if model:
                args[2:2] = ['--model',model]
        else:
            args = [binary,'-p','--output-format','json','--json-schema',json.dumps(SCHEMA),'--tools','',
                    '--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--disable-slash-commands',
                    '--setting-sources','','--no-session-persistence','--permission-mode','dontAsk']
            if model:
                args += ['--model',model]
        code, stdout, stderr = run_process(args,cwd=directory,timeout=timeout,stdin=prompt,env=agent_environment())
        if code:
            # Do not expose raw CLI output: provider errors can contain credentials.
            raise AgentCallError(f'{NAMES[agent]} 执行失败（退出码 {code}），请检查登录状态、模型和网络。')
        if agent == 'codex':
            if not answer.is_file() or answer.stat().st_size > 2*1024*1024:
                raise ValueError('Codex 未返回有效候选。')
            output = answer.read_text()
        else:
            data = json.loads(stdout)
            if data.get('is_error'):
                raise AgentCallError('Claude Code 返回错误，请检查登录、额度和网络。')
            output = data.get('structured_output') or data.get('result')
    if isinstance(output,str):
        output = output.strip()
        if output.startswith('```'):
            output = '\n'.join(output.splitlines()[1:-1])
        output = json.loads(output)
    if not isinstance(output,dict) or not isinstance(output.get('files'),list):
        raise ValueError('Agent 输出必须包含 files 数组。')
    return output['files']


def generate(agent,prompt,directory,timeout,model='',sub_model=''):
    try:
        output=_generate(agent,prompt,directory,timeout,model,sub_model=sub_model) if sub_model else _generate(agent,prompt,directory,timeout,model)
    except Exception:
        record_agent_connection(agent,False)
        raise
    record_agent_connection(agent,True)
    return output
