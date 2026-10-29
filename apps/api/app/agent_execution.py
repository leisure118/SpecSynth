"""Agent candidate -> real verifier -> bounded feedback loop."""
from __future__ import annotations
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import time
import uuid
from .agent_runners import generate, run_process, AgentCallError
from .config import ROOT_DIR, resolve_project_path
from .storage import utcnow


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


def verify_candidates(files, entry, mode, directory, timeout):
    if mode.startswith('rust-'):
        from engine.nl2verus.verifier import verify_code
        from engine.nl2verus.b3_runner import verify_b3_candidate
        source = next(f['content'] for f in files if f['path']==entry)
        return verify_b3_candidate(source,verify=lambda code:verify_code(code,timeout,files=files,entry_path=entry))
    for f in files:
        target=directory/f['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(f['content'])
    paths = [f['path'] for f in files if f['path'].endswith('.c')] if mode=='inter-modular' else [entry]
    container_root='/app/'+directory.relative_to(ROOT_DIR).as_posix()
    args=['frama-c','-wp','-wp-rte','-wp-prover','Alt-Ergo,Z3','-wp-print','-wp-timeout',str(max(1,min(15,timeout))),
          '-cpp-extra-args=-I'+container_root]
    if mode=='termination':
        args += ['-wp-no-definitions-terminate','-wp-no-declarations-terminate','-wp-variant-with-terminates']
    args += [container_root+'/'+path for path in paths]
    name='xuanjian-proof-'+uuid.uuid4().hex[:12]
    cmd=['docker','compose','run','--rm','-T','--name',name,'autospec','bash','-lc',
         'export PATH=/root/.opam/default/bin:$PATH; '+shlex.join(args)]
    try:
        code,out,err=run_process(cmd,cwd=ROOT_DIR,timeout=timeout)
    except TimeoutError:
        # Killing the CLI alone does not terminate its Docker container.
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
        return {'status':'timeout','verified':False,'message':'Frama-C 验证超时，容器已回收。','verified_count':0,'error_count':0}
    match=re.search(r'Proved goals:\s*(\d+)\s*/\s*(\d+)',out+'\n'+err)
    proved,total=map(int,match.groups()) if match else (0,0)
    passed=code==0 and total>0 and proved==total
    return {'status':'verified' if passed else 'failed' if match else 'compile_error','verified':passed,
            'verified_count':proved,'error_count':max(0,total-proved),'stdout':out,'stderr':err,
            'message':f'Frama-C 证明目标 {proved}/{total}' if match else 'Frama-C 未产生有效证明结果。'}


def base_prompt(files, mode, description, signature, instructions):
    rust=mode.startswith('rust-')
    return ('Return ONLY JSON with a files array of {path, content}. Return every input file using its original path. '
        'Do not use tools or access any files outside the supplied source. Preserve all original requirements and specifications. '
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
    detail=manager.refresh_capabilities().mode_detail(mode)
    return None if detail['ready'] else detail['summary']


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
    problem=verifier_preflight(manager,rust,task.mode)
    if problem:return manager._unavailable_result(task,problem)
    if sum(len(f['content'].encode()) for f in files)>512*1024:
        raise ValueError('单次 Agent 输入源码不能超过 512 KiB，请拆分项目。')
    directory=resolve_project_path(task.task_dir)/'agent';directory.mkdir(parents=True,exist_ok=True)
    task.input_file=upload['stored_path'];task.metadata.update(input_manifest=upload.get('manifest',[]),agent=agent)
    store.write_text_artifact(task.task_id,'input','sources.json',json.dumps(files,ensure_ascii=False))
    deadline=time.monotonic()+(payload.timeout_sec or 120)
    attempts=[];candidate=files;diagnostic='';check={'status':'failed','verified':False,'message':'尚未验证'}
    prompt_base=base_prompt(files,task.mode,payload.description,payload.function_signature,payload.agent_instructions)
    for round_number in range(payload.max_repair_rounds+1):
        remaining=int(deadline-time.monotonic())
        if remaining<1:
            check={'status':'timeout','verified':False,'message':'任务总超时，已停止修复。'};break
        prompt=prompt_base+'\nOriginal source:\n'+json.dumps(files,ensure_ascii=False)
        if attempts:
            prompt+='\nPrevious candidate:\n'+json.dumps(candidate,ensure_ascii=False)+'\nVerifier diagnostics:\n'+diagnostic[-16000:]
        task.message=f'{agent} 第 {round_number+1} 轮：生成与验证'
        task.updated_at=utcnow();store.write_task(task)
        manager._advance_phase(task,'generation' if rust else 'generate_specifications','running',task.message)
        attempt={'id':str(round_number),'round':round_number,'prompt':prompt,'model_name':payload.assistant.get('runner_model') or agent}
        try:
            produced=generate(agent,prompt,directory/f'round-{round_number}',remaining,
                              payload.model_name if agent=='deepseek-harness' else payload.assistant.get('runner_model',''))
            candidate=validate_candidates(files,produced,rust,entry,task.mode)
            attempt['code']=next(f['content'] for f in candidate if f['path']==entry)
            left=int(deadline-time.monotonic())
            if left<1:raise TimeoutError('生成完成时任务已超时，未执行验证。')
            manager._advance_phase(task,'verus' if rust else 'formal_verifying','running','正在执行实际验证器')
            check=verify_candidates(candidate,entry,task.mode,directory/f'proof-{round_number}',left)
        except AgentCallError as exc:
            check={'status':'unavailable','verified':False,'message':str(exc)}
        except TimeoutError as exc:
            check={'status':'timeout','verified':False,'message':str(exc)}
        except (ValueError,OSError) as exc:
            check={'status':'blocked','verified':False,'message':str(exc)}
        attempt.update(verification=check,status=check['status']);attempts.append(attempt)
        diagnostic='\n'.join(str(check.get(k,'')) for k in ('message','stdout','stderr'))
        store.write_text_artifact(task.task_id,'agent',f'round-{round_number}.json',json.dumps(attempt,ensure_ascii=False))
        task.metadata['agent_attempts']=attempts;store.write_task(task)
        if check.get('verified') or check['status'] in ('timeout','unavailable'):break
    status='Pass' if check.get('verified') else 'Unavailable' if check['status']=='unavailable' else 'Timeout' if check['status']=='timeout' else 'Invalid' if check['status'] in ('blocked','compile_error') else 'Fail'
    code=next(f['content'] for f in candidate if f['path']==entry)
    proved=int(check.get('verified_count') or 0);errors=int(check.get('error_count') or 0);total=proved+errors
    for phase in task.phases:phase.status='completed' if status=='Pass' else 'failed'
    store.write_text_artifact(task.task_id,'output',PurePosixPath(entry).name,code)
    store.write_text_artifact(task.task_id,'output','sources.json',json.dumps(candidate,ensure_ascii=False))
    store.write_text_artifact(task.task_id,'logs','agent.log',diagnostic)
    result=manager._build_result(task,status=status,summary=check['message'],source_code=source,result_code=code,command=None,
        logs={'raw':diagnostic,'summary':[check['message']]},specifications={},
        engine_detail={'agent':agent,'attempts':attempts,'verification':check,'verifier':'Verus' if rust else 'Frama-C'},
        proof_stats={'scope':'proof-goals','unit':'goals','proved_goals':proved,'total_goals':total,'open_goals':errors,'pass_rate':proved/total if total else 0},
        highlights=[agent,'验证器实际执行','任务输入快照'])
    if rust:result['result_code']=code
    return result


def execute_verification_only(manager, task, payload):
    """Verify the submitted annotated source without any provider invocation."""
    upload=manager.store.read_upload(payload.file_id)
    if not upload or upload.get('kind')=='bundle' or task.mode!='single':
        raise ValueError('直接验证需要单个 C 源文件快照。')
    source=resolve_project_path(upload['stored_path']).read_text()
    entry=payload.entry_path
    comments='\n'.join(''.join(m) for m in re.findall(r'/\*@([\s\S]*?)\*/|//@([^\n]*)',source))
    if re.search(r'\b(?:admit|assume|axiom|axiomatic)\b',comments):
        check={'status':'blocked','verified':False,'message':'源码包含 admit/assume/axiom 等假设，直接验证已阻止，不能计为通过。'}
    else:
        problem=verifier_preflight(manager,False,'single')
        if problem:
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
        highlights=['基准单案例重跑','输入快照','未调用模型'])
