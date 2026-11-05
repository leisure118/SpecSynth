"""Agent candidate -> real verifier -> bounded feedback loop."""
from __future__ import annotations
import json
from pathlib import Path, PurePosixPath
import re
import time
from engine.nl2verus.harness_session import case_session
from acsl.adapters.agent_runtime import generate, AgentCallError
from acsl.application.agent_progress import AgentProgress
from acsl.application.time_budget import c_budget
from acsl.infrastructure.proof_limits import proof_slot
from acsl.adapters.storage import utcnow
from acsl.infrastructure.settings import resolve_project_path


from engine.verification.repair_feedback import compact_feedback

def c_tokens(code):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|[^\s]',code)
    return [t for t in tokens if not t.startswith(('/*','//'))]


def validate_candidates(original, candidates, rust, entry, mode):
    if not isinstance(candidates,list) or len(candidates)!=len(original):
        raise ValueError('Agent 必须返回完整原始文件集合。')
    source = {f['path']:f['content'] for f in original}
    seen = set()
    from engine.nl2verus.b3_runner import candidate_problem
    for f in candidates:
        path, code = f.get('path'), f.get('content')
        if path not in source or path in seen or not isinstance(code,str) or len(code.encode())>256*1024:
            raise ValueError('Agent 返回了非法、重复或过大的文件。')
        seen.add(path)
        if rust:
            problem = candidate_problem(code)
            if problem:
                raise ValueError('候选未通过证明完整性检查：'+problem)
        else:
            if c_tokens(source[path]) != c_tokens(code):
                raise ValueError('C Agent 只能添加规约，不能修改原始程序语义。')
            # Preserve original ACSL obligations as exact tokens, rather than replacing them.
            for contract in re.findall(r'/\*@([\s\S]*?)\*/|//@([^\n]*)',source[path]):
                original_contract = re.sub(r'\s+','', ''.join(contract))
                candidate_contracts=''.join(''.join(c) for c in re.findall(r'/\*@([\s\S]*?)\*/|//@([^\n]*)',code))
                if original_contract not in re.sub(r'\s+','',candidate_contracts):
                    raise ValueError('Agent 不得删除或弱化已有 ACSL 规约。')
            for marker in ('admit','assume','axiom','axiomatic','lemma'):
                pattern=r'\b'+marker+r'\b'
                if len(re.findall(pattern,code))>len(re.findall(pattern,source[path])):
                    raise ValueError('候选包含新增的证明绕过语句或未验证逻辑声明。')
    if not rust and mode=='termination':
        code=next(f['content'] for f in candidates if f['path']==entry)
        if (re.search(r'\b(?:for|while)\s*\(',code) and 'loop variant' not in code) or not re.search(r'\bterminates\s+\\?true\s*;',code):
            raise ValueError('终止性候选必须提供 terminates true 和 loop variant。')
    return candidates


def verify_candidates(files, entry, mode, directory, timeout, function=None, verification_tool="framac"):
    if verification_tool == "verifast":
        from engine.verification.verifast_runtime import verify
        with proof_slot(timeout) as remaining:
            return verify(files,entry,min(600,max(1,int(remaining))))
    if mode.startswith('rust-'):
        from engine.nl2verus.verifier import verify_code
        from engine.nl2verus.b3_runner import verify_b3_candidate
        source = next(f['content'] for f in files if f['path']==entry)
        return verify_b3_candidate(source,verify=lambda code:verify_code(code,timeout,files=files,entry_path=entry))
    # Shared C verification never depends on the AutoSpec image. The runtime
    # selector prefers host Frama-C, then a dedicated verifier container.
    from engine.verification.framac_runtime import run_candidate
    with proof_slot(timeout) as remaining:
        return run_candidate(files, entry, mode, remaining, directory, function=function)


def base_prompt(files, mode, description, signature, instructions, verification_tool="framac"):
    if verification_tool == "verifast":
        return ('Return ONLY JSON with a files array of {path, content}. Return every input file using its original path. '
            'Platform verification tool: VeriFast. Only add VeriFast separation-logic ghost annotations, preserving every original C token and assertion. '
            'Use requires and ensures after the function signature and before its body; result is written result (not \\result). '
            'Use &*& for separation/conjunction, //@ invariant between the while/for header and its body. '
            'Do not use ACSL loop invariant/assigns clauses. Add contracts for every function because enforce_annotations is on. '
            'Never use assume/admit, false preconditions, unproved lemmas or change code. Respect stated input conditions. '
            'Verify the original requested behavior; proof claims are never accepted as evidence. '
            +'\nTask: '+description+'\nSignature: '+signature+'\nUnchanged reference Skills (adapt syntax to VeriFast; do not execute ACSL/Frama-C steps):\n'+instructions)
    rust=mode.startswith('rust-')
    return ('Return ONLY JSON with a files array of {path, content}. Return every input file using its original path. '
        'Only access the task workspace and verifier toolchain. Preserve all original requirements and specifications. '
        'Never use assume, admit, external_body, or axioms to bypass proofs. '
        + ('Generate Verus Rust code satisfying the task.' if rust else 'Only ADD ACSL specifications; keep every original C token unchanged. Include meaningful function contracts and loop invariants.')
        + (' Include terminates true and a decreasing loop variant for each loop.' if mode=='termination' else '')
        + '\nTask: '+description+'\nSignature: '+signature+'\n'+instructions)


def initial_prompt(files,mode,description,signature,instructions):
    return base_prompt(files,mode,description,signature,instructions)+'\nOriginal source:\n'+json.dumps(files,ensure_ascii=False)


def verifier_preflight(manager,rust,mode):
    if rust:
        from engine.nl2verus.verifier import verifier_info
        info=verifier_info()
        return None if info['available'] else info['message']
    from engine.verification.framac_runtime import preflight
    ready,message=preflight()
    return None if ready else message


@case_session()
def execute_agent(manager,task,payload):
    store=manager.store;upload=store.read_upload(payload.file_id)
    if not upload:
        raise ValueError('缺少源码快照。')
    if upload.get('kind')=='bundle':
        files=[{'path':r['relative_path'],'content':resolve_project_path(r['stored_path']).read_text()} for r in upload['manifest']]
    else:
        files=[{'path':payload.entry_path,'content':resolve_project_path(upload['stored_path']).read_text()}]
    entry=payload.entry_path;rust=task.mode.startswith('rust-');agent=payload.assistant['agent']
    source=next(f['content'] for f in files if f['path']==entry)
    from acsl.application.source_routing import classify_sources,routing_instructions
    route=classify_sources(files,entry,task.mode)
    task.metadata['source_classification']=route
    store.write_task(task)
    verifast=payload.verification_tool=='verifast'
    if verifast:
        from engine.verification.verifast_runtime import capabilities
        info=capabilities();problem=None if info['ready'] else info['message']
        route={'id':'verifast-c','label':'C / VeriFast 规约生成与验证'}
        task.metadata['source_classification']=route
    else:problem=verifier_preflight(manager,rust,task.mode)
    if problem:return manager._unavailable_result(task,problem)
    if sum(len(f['content'].encode()) for f in files)>512*1024:
        raise ValueError('单次 Agent 输入源码不能超过 512 KiB，请拆分项目。')
    directory=resolve_project_path(task.task_dir)/'artifacts'/'agent';directory.mkdir(parents=True,exist_ok=True)
    task.input_file=upload['stored_path'];task.metadata.update(input_manifest=upload.get('manifest',[]),agent=agent)
    store.write_text_artifact(task.task_id,'input','sources.json',json.dumps(files,ensure_ascii=False))
    progress=AgentProgress(task,store) if agent in ('deepseek-harness','codex','claude-code') else None
    if progress:progress.update({'id':'source-routing','label':'识别源文件与选择工作流','status':'completed','detail':route['label']+' · '+entry})
    budget=c_budget(files,payload.timeout_sec,getattr(payload,'adaptive_timeout',True)) if not rust else {'requested_sec':payload.timeout_sec or 200,'effective_sec':payload.timeout_sec or 200,'adaptive':False,'reasons':[]}
    task.metadata['time_budget']=budget;store.write_task(task)
    deadline=time.monotonic()+budget['effective_sec']
    proof_reserve=min(60,max(15,int(budget['effective_sec']*.15))) if not rust else 0
    attempts=[];candidate=files;diagnostic='';check={'status':'failed','verified':False,'message':'尚未验证'}
    prompt_base=base_prompt(files,task.mode,payload.description,payload.function_signature,payload.agent_instructions,verification_tool=payload.verification_tool)
    if not verifast:prompt_base+=routing_instructions(route)
    if payload.manual_context:
        task.metadata['manual_context']=payload.manual_context
        prompt_base+='\nContinue from the manually edited source below, not a fresh implementation. Preserve the human annotations and original assertions; fill missing proof annotations and repair failed goals where permitted. Do not remove requirements or introduce assumptions. Previous diagnostics refer to the earlier source version: relocate their goals against the current source instead of assuming old line numbers still match. Previous verifier diagnostics:\n'+str(payload.manual_context.get('diagnostics',''))[-16000:]

    for round_number in range(payload.max_repair_rounds+1):
        remaining=int(deadline-time.monotonic())
        if remaining<1:
            check={'status':'timeout','verified':False,'message':'任务总超时，已停止修复。'};break
        prompt=prompt_base+'\nOriginal source:\n'+json.dumps(files,ensure_ascii=False)
        if attempts:
            prompt+='\nPrevious candidate:\n'+json.dumps(candidate,ensure_ascii=False)+'\nVerifier diagnostics:\n'+compact_feedback(check)
        from acsl.application.run_interaction import consume
        feedback=consume(resolve_project_path(task.task_dir),round_number)
        if feedback:
            prompt_base+='\nAdditional user instructions (preserve original source, assertions and proof checks):\n'+'\n'.join(row['text'] for row in feedback)
            prompt+='\nAdditional user instructions:\n'+'\n'.join(row['text'] for row in feedback)
        operation='首次生成与验证' if round_number==0 else f'修复现有规约 {round_number}/{payload.max_repair_rounds}'
        task.message=f'{agent}：{operation}（总预算 {budget["effective_sec"]} 秒）'
        task.updated_at=utcnow();store.write_task(task)
        manager._advance_phase(task,'generation' if rust else 'generate_specifications','running',task.message)
        attempt={'id':str(round_number),'round':round_number,'prompt':prompt,'model_name':payload.model_name}
        try:
            from contextlib import nullcontext
            with (progress.watch(directory/f'round-{round_number}',round_number,reuse=agent=='deepseek-harness' and round_number>0) if progress else nullcontext()):
                produced=generate(agent,prompt,directory/f'round-{round_number}',max(1,remaining-proof_reserve),
                                  payload.model_name, **({'sub_model':payload.assistant['sub_model']} if agent in ('codex','claude-code','deepseek-harness') and payload.assistant.get('sub_model') else {}), **({'verification_tool':'verifast'} if verifast else {}))
            runtime_file=directory/f'round-{round_number}'/'harness-runtime.json'
            if not runtime_file.is_file():runtime_file=directory/f'round-{round_number}'/'cli-runtime.json'
            if runtime_file.is_file():attempt['agent_runtime']=json.loads(runtime_file.read_text())
            candidate=validate_candidates(files,produced,rust,entry,task.mode)
            attempt['code']=next(f['content'] for f in candidate if f['path']==entry)
            if progress:progress.update({'id':'candidate','label':'平台检查源码与原始断言','status':'completed'})
            left=int(deadline-time.monotonic())
            if left<1:raise TimeoutError('生成完成时任务已超时，未执行验证。')
            manager._advance_phase(task,'verus' if rust else 'formal_verifying','running','正在执行实际验证器')
            if progress:progress.update({'id':'platform-proof','label':'平台独立 VeriFast 验证' if verifast else '平台独立 Frama-C 验证','status':'running'})
            check=verify_candidates(candidate,entry,task.mode,directory/f'proof-{round_number}',left,**({'verification_tool':'verifast'} if verifast else {}))
        except AgentCallError as exc:
            failure_code=getattr(exc,'code','agent_failed')
            failure_status='timeout' if failure_code=='agent_timeout' else 'blocked' if failure_code in ('agent_delegation','agent_output','agent_tools','output_limit') else 'unavailable'
            check={'status':failure_status,'verified':False,'message':str(exc),'code':failure_code}
            runtime_file=directory/f'round-{round_number}'/'harness-runtime.json'
            if not runtime_file.is_file():runtime_file=directory/f'round-{round_number}'/'cli-runtime.json'
            if runtime_file.is_file():attempt['agent_runtime']=json.loads(runtime_file.read_text())
        except TimeoutError as exc:
            check={'status':'timeout','verified':False,'message':str(exc)}
        except (ValueError,OSError) as exc:
            check={'status':'blocked','verified':False,'message':str(exc)}
        if progress and any(step['id']==f'{round_number}:platform-proof' for step in progress.state['steps']):
            progress.update({'id':'platform-proof','label':'平台独立 VeriFast 验证' if verifast else '平台独立 Frama-C 验证','status':'completed' if check.get('verified') else 'failed','detail':check['message']})
        from engine.verification.spec_patches import repairable_patch_receipt
        attempt['patch_repairable']=check.get('code')=='agent_output' and repairable_patch_receipt(directory/f'round-{round_number}')
        attempt.update(verification=check,status=check['status']);attempts.append(attempt)
        diagnostic='\n'.join(str(check.get(k,'')) for k in ('message','stdout','stderr'))
        store.write_text_artifact(task.task_id,'agent',f'round-{round_number}.json',json.dumps(attempt,ensure_ascii=False))
        task.metadata['agent_attempts']=attempts;store.write_task(task)
        if check.get('verified') or check['status'] in ('timeout','unavailable') or ('code' not in attempt and not attempt['patch_repairable']):break
    status='Pass' if check.get('verified') else 'Unavailable' if check['status']=='unavailable' else 'Timeout' if check['status']=='timeout' else 'Invalid' if check['status'] in ('blocked','compile_error') else 'Fail'
    if progress:progress.finish(bool(check.get('verified')))
    code=next(f['content'] for f in candidate if f['path']==entry)
    proved=int(check.get('verified')) if verifast else int(check.get('verified_count') or 0);errors=int(not check.get('verified')) if verifast else int(check.get('error_count') or 0);total=proved+errors
    for phase in task.phases:phase.status='completed' if status=='Pass' else 'failed'
    store.write_text_artifact(task.task_id,'output',PurePosixPath(entry).name,code)
    store.write_text_artifact(task.task_id,'output','sources.json',json.dumps(candidate,ensure_ascii=False))
    store.write_text_artifact(task.task_id,'logs','agent.log',diagnostic)
    result=manager._build_result(task,status=status,summary=check['message'],source_code=source,result_code=code,command=check.get('command_text') if verifast else None,
        logs={'raw':diagnostic,'summary':[check['message']]},specifications={},
        engine_detail={'agent':agent,'attempts':attempts,'verification':check,'verifier':'VeriFast' if verifast else 'Verus' if rust else 'Frama-C','verification_tool':payload.verification_tool},
        proof_stats={'scope':'compilation-unit' if verifast else 'proof-goals','unit':'units' if verifast else 'goals','proved_goals':proved,'total_goals':total,'open_goals':errors,'pass_rate':proved/total if total else 0},
        highlights=[agent,'验证器实际执行','任务输入快照'])
    if rust or verifast:result['result_code']=code
    return result


def direct_verification_problem(source):
    comments='\n'.join(''.join(m) for m in re.findall(r'/\*@([\s\S]*?)\*/|//@([^\n]*)',source))
    if re.search(r'\b(?:admit|assume|axiom|axiomatic)\b',comments):
        return '带规约代码含 admit/assume/axiom 等未证明假设，无法作为独立证明输入。请切换到原始源码重新生成规约，或在项目中修正前置条件；系统不会自动删除这些假设。'
    return None


def execute_verification_only(manager, task, payload):
    """Verify the submitted annotated source without any provider invocation."""
    upload=manager.store.read_upload(payload.file_id)
    if not upload or upload.get('kind')=='bundle' or task.mode!='single':
        raise ValueError('直接验证需要单个 C 源文件快照。')
    source=resolve_project_path(upload['stored_path']).read_text()
    entry=payload.entry_path
    problem=direct_verification_problem(source)
    if problem:
        check={'status':'blocked','verified':False,'message':problem}
    else:
        from engine.verification.framac_runtime import preflight
        ready,problem=preflight()
        if not ready:
            check={'status':'unavailable','verified':False,'message':problem}
        else:
            manager._advance_phase(task,'formal_verifying','running','正在直接验证基准源码，不调用模型')
            files=[{'path':entry,'content':source}]
            directory=resolve_project_path(task.task_dir)/'benchmark-proof'
            check=verify_candidates(files,entry,'single',directory,payload.timeout_sec or 120)
    status='Pass' if check.get('verified') else 'Unavailable' if check['status']=='unavailable' else 'Timeout' if check['status']=='timeout' else 'Invalid' if check['status'] in ('blocked','compile_error') else 'Fail'
    proved=int(check.get('verified_count') or 0);errors=int(check.get('error_count') or 0);total=proved+errors
    diagnostic='\n'.join(str(check.get(k,'')) for k in ('message','stdout','stderr'))
    for phase in task.phases:
        phase.status='completed' if status=='Pass' else 'failed'
        phase.detail='直接验证已有规约；未调用模型。'
    task.model_name=None
    return manager._build_result(task,status=status,summary=check['message'],source_code=source,result_code=source,command=None,
        logs={'raw':diagnostic,'summary':[check['message']]},specifications={},
        engine_detail={'verification':check,'verifier':'Frama-C','provider_calls':0,'verification_only':True},
        proof_stats={'scope':'proof-goals','unit':'goals','proved_goals':proved,'total_goals':total,'open_goals':errors,'pass_rate':proved/total if total else 0},
        highlights=['直接验证已有规约','输入快照','未调用模型'])
