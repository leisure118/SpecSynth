"""Task-scoped text-only specification worker for Codex/Claude orchestration."""
import json
from datetime import datetime,timezone
from pathlib import Path
import time
import httpx
from engine.nl2verus.model_provider import ProviderError


def generate_specifications(prompt,profile,directory,timeout,verification_tool='framac'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();progress=directory/'live-progress.jsonl'
    def event(status,detail=''):
        with progress.open('a') as f:f.write(json.dumps({'id':'subagent-api','label':'子 Agent API 生成规约','status':status,'detail':detail,'at':datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+'\n')
    event('running',profile['model'])
    from engine.verification.spec_patches import parse_patch_json,merge_spec_patches,candidate_quality
    from engine.verification.worker_contract import worker_prompt,thinking_policy
    original=json.JSONDecoder().raw_decode(prompt.split('Original source:\n',1)[1])[0]
    policy=thinking_policy()
    verifast=verification_tool=='verifast'
    task=worker_prompt(prompt.split('Original source:\n',1)[0],original,verification_tool=verification_tool)
    metadata={'model':profile['model'],'transport':'platform-api-worker','candidate_protocol':'verifast-patches-v1' if verifast else 'acsl-patches-v1','max_output_tokens':4096,'thinking_policy':policy,'status':'running'}
    try:
        with httpx.Client(timeout=max(1,timeout),follow_redirects=False,trust_env=False) as client:
            with client.stream('POST',profile['base_url'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+(profile.get('api_key') or 'EMPTY')},json={
                'model':profile['model'],'messages':[{'role':'system','content':('You are a text-only VeriFast C annotation author. Return ONLY JSON {"patches":[{"path":"original path","before_line":2,"before_column":1,"annotation":"//@ requires true;"}]}. Preserve original C tokens and assertions. Add VeriFast contracts and loop invariants only. Never add assume/admit or false preconditions. Do not use tools or claim verification.' if verifast else 'You are a text-only ACSL specification sub-agent. Return only JSON annotation patches: {"patches":[{"path":"original path","before_line":8,"annotation":"/*@ ... */"}]}. Preserve original C tokens and assertions. Never use admit, assume or axioms. Use the supplied Skill instructions. Do not use tools or write plans.')},{'role':'user','content':task}],
                'stream':False,'max_tokens':4096,'temperature':0.2,'chat_template_kwargs':{'enable_thinking':policy['worker']=='on'}}) as response:
                if response.status_code!=200:raise ProviderError('subagent_api',f'子模型 API 返回 HTTP {response.status_code}；未改用主模型伪造子模型结果。')
                chunks=[];size=0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>2*1024*1024:raise ProviderError('agent_output','子模型输出超过大小限制。')
                    if time.monotonic()-started>timeout:raise ProviderError('agent_timeout','子模型 API 超过时间预算。')
                    chunks.append(chunk)
                data=json.loads(b''.join(chunks))
        choice=data['choices'][0]
        if choice.get('finish_reason')=='length':raise ProviderError('output_limit','子模型 API 输出达到 token 上限，候选不完整。')
        text=choice['message']['content'].strip()
        if text.startswith('```'):text='\n'.join(text.splitlines()[1:-1])
        if verifast:
            from acsl.application.agent_execution import validate_candidates
            output=json.loads(text)
            merged=merge_spec_patches(original,output,verification_tool='verifast') if 'patches' in output else output.get('files')
            candidates=validate_candidates(original,merged,False,original[0]['path'],'single')
        else:
            output=parse_patch_json(text)
            quality=candidate_quality(original,output)
            if not quality['annotation_nonempty'] and quality['uncovered_loops_estimate']:raise ProviderError('agent_output','子模型未生成实际循环规约；不能提交空补丁。')
            metadata['candidate_quality']=quality
            merged=merge_spec_patches(original,output)
            (directory/'subagent-patches.json').write_text(json.dumps(output,ensure_ascii=False))
            from acsl.application.agent_execution import validate_candidates
            candidates=validate_candidates(original,merged,False,original[0]['path'],'single')
            metadata.update(status='completed',usage=data.get('usage',{}),elapsed_sec=round(time.monotonic()-started,2))
        (directory/'subagent-candidate.json').write_text(json.dumps({'files':candidates},ensure_ascii=False))
        event('completed',profile['model'])
        return candidates
    except ProviderError:
        metadata['status']='failed';event('failed','子模型未完成候选生成');raise
    except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError):
        metadata['status']='failed';event('failed','子模型请求或候选格式不正确')
        raise ProviderError('subagent_api','子模型 API 调用或候选校验失败；请检查子模型连接与输出格式。') from None
    finally:
        metadata['elapsed_sec']=round(time.monotonic()-started,2)
        (directory/'subagent-runtime.json').write_text(json.dumps(metadata,ensure_ascii=False))
