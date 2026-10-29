"""Explicit, bounded NL2Verus agent adapters. No browser-provided commands."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile

from . import platform_provider as provider
from .model_provider import ProviderError, MAX_CODE_BYTES

SKILLS = {
    'verus-contracts': {'id': 'verus-contracts', 'name': 'Verus 规约与实现',
        'description': '明确输入条件、后置条件与整数边界，生成完整实现。',
        'content': 'Translate the natural language faithfully into complete Verus. Specify requires and ensures; preserve the requested interface and executable behavior. Distinguish mathematical int/nat and machine integers; prove overflow safety. Never weaken the intended contract just to obtain verification.'},
    'verus-proof': {'id': 'verus-proof', 'name': '循环与证明辅助',
        'description': '检查循环不变量、终止性与辅助引理。',
        'content': 'For each loop, establish initialization, preservation and exit sufficiency of invariants, with bounds and a decreases measure where needed. Add small proof lemmas for sequence properties when necessary. Do not use assume, admit, external_body or trusted proof bypasses.'},
}


def skills():
    rows = dict(SKILLS)
    # An application-owned extension directory; filenames are never supplied by HTTP.
    root = Path(__file__).resolve().parents[2] / 'skills' / 'verus'
    for path in sorted(root.glob('*/SKILL.md')):
        if path.is_symlink() or path.parent.is_symlink() or not re.fullmatch(r'[a-z0-9-]{1,64}', path.parent.name):
            continue
        if path.stat().st_size > 48_000:
            continue
        text = path.read_text(encoding='utf-8')
        key = 'local-' + path.parent.name
        rows[key] = {'id': key, 'name': 'NL → Verus Baseline' if path.parent.name=='verus-baseline' else path.parent.name,
                     'description': '默认英文 Skill · 完整实现、规约、循环证明与诊断修复' if path.parent.name=='verus-baseline' else '项目扩展 Skill', 'content': text}
    extra = Path(__file__).resolve().parents[2] / 'runtime' / 'generation-skills.json'
    if extra.is_file():
        rows.update(json.loads(extra.read_text()))
    return rows


# Display presets are not authenticated profiles. Availability is checked separately.
# Model IDs checked against official catalogs; gateways may expose different IDs.
MODEL_PRESETS = {
    'responses': [('GPT-6.1 Sol','gpt-6.1-sol','https://api.openai.com/v1'),
                  ('GPT-6 Astra','gpt-6-astra','https://api.openai.com/v1'),
                  ('GPT-6 Luna','gpt-6-luna','https://api.openai.com/v1')],
    'anthropic': [('Claude Sonnet 5.5','claude-sonnet-5-5','https://api.anthropic.com'),
                  ('Claude Opus 5.5','claude-opus-5-5','https://api.anthropic.com'),
                  ('Claude Haiku 5.5','claude-haiku-5-5','https://api.anthropic.com'),
                  ('DeepSeek Flash','deepseek-flash','https://api.deepseek.com/anthropic'),
                  ('DeepSeek V4 Pro','deepseek-v4-pro','https://api.deepseek.com/anthropic')],
    'chat': [('DeepSeek Flash','deepseek-flash','https://api.deepseek.com'),
             ('DeepSeek V4 Pro','deepseek-v4-pro','https://api.deepseek.com')],
}


def model_presets(protocol, configured):
    existing={p['model'] for p in configured}
    entries=[{'id':'preset:'+protocol+':'+model,'name':name,'model':model,
              'base_url':url,'protocol':protocol,'configured':False,'preset':True}
             for name,model,url in MODEL_PRESETS[protocol] if model not in existing]
    entries.append({'id':'preset:'+protocol+':custom','name':'自定义 / 自训练模型',
                    'model':'','base_url':'','protocol':protocol,'configured':False,'preset':True})
    return entries


def capabilities():
    from .profiles import all_profiles, public_profile, ROOT
    profiles = list(all_profiles().values())
    runtime = ROOT / 'runtime' / 'agent-runtime' / 'node_modules'
    specs = [('direct','模型直连','chat','原 NL2Verus 单次生成，按设置验证与修复'),
             ('deepseek-harness','DeepSeek Harness · 内置','chat','平台内置 Harness · 由模型调用 Verus 工具；支持兼容工具调用的模型'),
             ('codex','Codex','responses','平台独立运行时 · 需要 Responses API'),
             ('claude','Claude Code','anthropic','平台独立 SDK · 需要 Anthropic Messages API')]
    rows=[]
    for key,name,protocol,message in specs:
        installed = key in ('direct','deepseek-harness') or (runtime / ('@openai/codex-sdk' if key=='codex' else '@anthropic-ai/claude-agent-sdk')).is_dir()
        models=[public_profile(p) for p in profiles if p['protocol']==protocol]
        models+=model_presets(protocol,models)
        rows.append({'id':key,'name':name,'available':installed,'message':message if installed else '平台 Agent SDK 尚未安装','models':models,'protocol':protocol})
    codex=next(a for a in rows if a['id']=='codex')
    preferred=next((m for m in codex['models'] if m['configured'] and m.get('is_default')),None)
    return {'agents':rows,'skills':[{k:v for k,v in row.items() if k!='content'} for row in skills().values()],
            'defaults':{'agent_id':'codex' if preferred and codex['available'] else 'direct',
                        'model_id':preferred['id'] if preferred else None,
                        'skill_ids':['local-verus-baseline'],
                        'execution':'api' if preferred and codex['available'] else 'reference'}}


def validate_selection(agent, model, skill_ids):
    selected=next((a for a in capabilities()['agents'] if a['id']==agent),None)
    if not selected or not selected['available']:
        raise ValueError('所选平台 Agent 不可用。')
    if model not in {m['id'] for m in selected['models'] if m['configured']}:
        raise ValueError('请选择与 Agent 接口协议兼容的已配置模型。')
    if len(skill_ids)>8 or len(set(skill_ids))!=len(skill_ids) or any(s not in skills() for s in skill_ids):
        raise ValueError('请选择已安装的 Skill。')


def snapshot_skills(ids):
    registry = skills()
    return [dict(registry[key], sha256=hashlib.sha256(registry[key]['content'].encode()).hexdigest()) for key in ids]


def augment(prompt, selected):
    context = '\n\n'.join(f"### Skill: {s['name']}\n{s['content']}" for s in selected)
    return (f'Selected application skills (applied as instruction context):\n{context}\n\n' if context else '') + prompt


def _clean_code(code, secrets=()):
    match=re.fullmatch(r'\s*```(?:rust|verus)?\s*\n([\s\S]*?)\n```\s*',code)
    code=(match.group(1) if match else code).strip()
    if not code or len(code.encode())>MAX_CODE_BYTES or any(key and key in code for key in secrets):
        raise ProviderError('agent_output','Agent 未返回可用代码，或输出包含敏感配置，已阻止显示。')
    return code


def _sdk_generate(agent,prompt,profile,timeout=240):
    from .profiles import ROOT
    node=shutil.which('node')
    if not node:
        raise ProviderError('agent_missing','平台 Node.js 运行时不可用。')
    with tempfile.TemporaryDirectory(prefix='nl2verus-agent-') as folder:
        data={'agent':agent,'prompt':prompt,'profile':profile,'workingDirectory':folder}
        env={k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR','SYSTEMROOT','HTTPS_PROXY','HTTP_PROXY','NO_PROXY')}
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            proc=subprocess.Popen([node,str(ROOT/'scripts/agent_bridge.mjs')],cwd=folder,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err,start_new_session=True)
            try:
                proc.communicate(json.dumps(data).encode(),timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate()
                raise ProviderError('agent_timeout','Agent API 调用超时，已停止；没有自动重试。') from None
            if proc.returncode:
                raise ProviderError('agent_failed','Agent API 执行失败，请检查接口协议、模型权限和 API Key；没有自动重试。')
            if out.tell()>2_000_000:
                raise ProviderError('agent_output','Agent 输出超过限制。')
            out.seek(0)
            try: result=json.load(out);code=result['code']
            except (ValueError,KeyError,TypeError):
                raise ProviderError('agent_output','Agent 未返回完整结果。') from None
    return {'code':_clean_code(code,[profile['api_key']]),'model_name':profile['model'],'usage':result.get('usage',{}),'finish_reason':'stop'}


def _chat_generate(prompt,profile,harness=False):
    from openai import OpenAI, omit
    from .b3_runner import verify_b3_candidate
    from .verifier import verify_code
    messages=[{'role':'user','content':prompt}]
    events=[]; usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}
    tools=[{'type':'function','function':{'name':'verify_verus','description':'Check a complete Verus candidate and return verifier diagnostics.','parameters':{'type':'object','properties':{'code':{'type':'string'}},'required':['code'],'additionalProperties':False}}}]
    try:
        with OpenAI(api_key=profile.get('api_key') or 'not-required',base_url=profile['base_url'],timeout=120,max_retries=0,
                    **({'default_headers':{'Authorization':omit}} if profile.get('auth_mode')=='none' else {})) as client:
            for turn in range(5 if harness else 1):
                response=client.chat.completions.create(model=profile['model'],messages=messages,max_tokens=8192,**({'tools':tools,'tool_choice':'auto' if turn<4 else 'none'} if harness else {}))
                if response.usage:
                    for key in usage: usage[key]+=getattr(response.usage,key,0) or 0
                choice=response.choices[0];msg=choice.message
                if msg.tool_calls:
                    if choice.finish_reason!='tool_calls':raise ValueError('incomplete tool call')
                    if turn>=4: raise ValueError('tool budget')
                    messages.append(msg.model_dump(exclude_none=True))
                    for call in msg.tool_calls[:3]:
                        if call.function.name!='verify_verus': raise ValueError('unknown tool')
                        code=_clean_code(json.loads(call.function.arguments)['code'],[profile['api_key']])
                        check=verify_b3_candidate(code,verify=lambda c:verify_code(c,30))
                        events.append({'tool':'verify_verus','status':check['status'],'verified':check.get('verified',False)})
                        messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(check,ensure_ascii=False)[:24000]})
                    if len(msg.tool_calls)>3: raise ValueError('tool budget')
                    continue
                if msg.refusal or choice.finish_reason!='stop': raise ValueError('incomplete response')
                return {'code':_clean_code(msg.content or '',[profile['api_key']]),'model_name':profile['model'],'usage':usage,'finish_reason':'stop','agent_events':events,'provider_calls':turn+1}
    except ProviderError: raise
    except Exception:
        raise ProviderError('agent_api','模型 API 调用失败；请检查协议、工具调用支持、网络与额度，没有自动重试。') from None
    raise ProviderError('agent_budget','Harness 已达工具调用上限，没有获得完整代码。')


def make_runner(payload,runner_class):
    from .profiles import all_profiles, public_profile
    agent=payload.get('agent_id','direct');selected=payload.get('skill_snapshot',[])
    if agent=='direct' and not selected and not payload.get('managed_profile') and not payload.get('model_profile'):
        return runner_class()
    profile=all_profiles()[payload['model_id']]
    if payload.get('model_profile') and public_profile(profile)!=payload['model_profile']:
        raise ValueError('运行前模型配置已变更，请重新提交任务。')
    def generate(prompt,model_id,*,snapshot):
        prompt=augment(prompt,selected)
        if agent!='direct' or not profile.get('legacy'):
            prompt+='\nReturn complete Verus Rust source only. Preserve the task semantics; no assume/admit/external_body.'
        result=(provider.generate_code(prompt,model_id,snapshot=snapshot) if agent=='direct' and profile.get('legacy') else _sdk_generate(agent,prompt,profile) if agent in ('codex','claude') else _chat_generate(prompt,profile,agent=='deepseek-harness'))
        result['effective_prompt']=prompt
        return result
    def status(*,snapshot):
        base=provider.provider_status(snapshot=snapshot)
        return dict(base,generation_configured=True,default_model_id=payload['model_id'],models=[{'id':payload['model_id'],'configured':True}])
    def config():
        try:return provider.get_config()
        except Exception:return provider.PlatformConfig({})
    return runner_class(config=config,status=status,generate=generate)
