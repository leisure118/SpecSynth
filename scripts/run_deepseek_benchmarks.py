"""Resumable real DSH + DeepSeek + spec-skill benchmark experiment.

Each case uses original sources, pinned skills, at most five outer repair rounds,
and independent platform Frama-C verification. No imported outcomes are reused.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import fcntl
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.nl2verus.harness_session import case_session
DATA=ROOT/'resources/benchmarks'
LABEL='DeepSeek Harness + deepseek-v4-flash + spec-skill'
BASES=('live25','live24','opus46_autobench')
_PUBLISH_LOCK=threading.RLock()

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)

def metrics(items):
    done=[r for r in items if r['status'] not in ('pending','running')]
    def passed(r,k):
        return r['status']=='passed' and 1<=r['round']<=k and r.get('total',0)>0 and r.get('proved')==r['total']
    return {f'pass@{k}':{'passed':sum(passed(r,k) for r in done),
        'total':len(items),'rate':round(100*sum(passed(r,k) for r in done)/len(items),1) if done and len(done)==len(items) else None} for k in (1,5)}

def publish(snapshot):
    with _PUBLISH_LOCK:_publish(snapshot)

def _publish(snapshot):
    b=snapshot['benchmark'];items=snapshot['items']
    b.update(summary=metrics(items),completed_count=sum(r['status'] not in ('pending','running') for r in items),
        passed_count=sum(r['status']=='passed' for r in items),updated_at=datetime.now(timezone.utc).isoformat())
    atomic(DATA/b['id']/'index.json',snapshot)
    with (DATA/'.catalog.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        catalog=json.loads((DATA/'index.json').read_text())
        atomic(DATA/'index.json',[r for r in catalog if r['id']!=b['id']]+[b])

def initialize():
    snapshots=[]
    for base in BASES:
        old=json.loads((DATA/base/'index.json').read_text());meta=old['benchmark']
        bid='dsh_deepseek_'+('autobench' if base=='opus46_autobench' else base)
        target=DATA/bid/'index.json'
        if target.exists():
            snapshots.append(json.loads(target.read_text()));continue
        items=[]
        for row in old['items']:
            original=row['artifacts'].get('original_source')
            if not original or not (DATA/original).is_file():raise ValueError('Missing original source: '+row['path'])
            items.append({k:row[k] for k in ('id','path','original_filename','original_path') if k in row} |
                {'original_sha256':hashlib.sha256((DATA/original).read_bytes()).hexdigest(),
                 'status':'pending','raw_status':'pending','round':0,'proved':0,'total':0,'goal_rate':None,'tokens':0,'elapsed_sec':0,'error':'','artifacts':{'original_source':original}})
        b={'id':bid,'dataset_id':meta.get('dataset_id',base),'name':meta['name'],'language':'C / ACSL',
           'model':'deepseek-v4-flash-0731','agent':'deepseek-harness','skill':'spec-bottomup','skill_family':'spec-skill',
           'configuration_label':LABEL,'date':datetime.now(timezone.utc).date().isoformat(),'experiment_status':'running',
           'reported_total':len(items),'indexed_total':len(items),'original_source_count':len(items),'flagged_count':0,
           'description':'官方 DeepSeek Harness 与 spec-skill 生成规约，平台独立执行 Frama-C WP。',
           'notice':'pass@k表示在k轮外层Harness生成与修复内通过，每轮包含多次原生模型和工具调用。实时实验；未完成前不显示最终通过率。最多5轮，原始源码、Skill快照、候选与证明日志独立保存；0/0不计通过。'}
        snapshots.append({'benchmark':b,'items':items});publish(snapshots[-1])
    return snapshots

def recover_candidate(attempt_dir, original, entry):
    """Recover only structurally valid, semantics-preserving draft; never a Pass."""
    from apps.api.app.agent_execution import validate_candidates
    path=attempt_dir/'workspace'/'answer.json'
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1024*1024:return None
    try:
        files=json.loads(path.read_text())['files']
        return validate_candidates(original,files,False,entry,'single')
    except (ValueError,KeyError,TypeError,OSError):return None


@case_session()
def run_case(snapshot,row,instructions,timeout):
    from apps.api.app.agent_runners import generate
    from apps.api.app.agent_execution import initial_prompt,validate_candidates,verify_candidates
    bid=snapshot['benchmark']['id'];folder=DATA/bid/row['id'];folder.mkdir(parents=True,exist_ok=True)
    original_bytes=(DATA/row['artifacts']['original_source']).read_bytes()
    if hashlib.sha256(original_bytes).hexdigest()!=row['original_sha256']:raise ValueError('Original source changed after experiment initialization')
    original=original_bytes.decode()
    files=[{'path':row['path'],'content':original}]
    atomic(folder/'input.json',{'files':files,'sha256':row['original_sha256']})
    row.update(status='running',error='',workflow='compact-c-v1' if os.getenv('XUANJIAN_HARNESS_COMPACT')=='1' else 'standard');publish(snapshot)
    started=time.monotonic();historical_elapsed=0;candidate=files;diagnostic='';check={};attempts=[]
    for number in range(1,6):
        prompt=initial_prompt(files,'single','Prove the original benchmark assertions without changing program semantics.','',instructions)
        if attempts:prompt+='\nPrevious candidate:\n'+json.dumps(candidate,ensure_ascii=False)+'\nVerifier diagnostics:\n'+diagnostic[-16000:]
        attempt_dir=folder/f'round-{number}';attempt_dir.mkdir(exist_ok=True)
        previous=attempt_dir/'verification.json'
        if previous.exists():
            request=attempt_dir/'request.json'
            if request.exists():historical_elapsed+=max(0,previous.stat().st_mtime-request.stat().st_mtime)
            check=json.loads(previous.read_text())
            saved=attempt_dir/'candidate.json'
            if saved.exists():candidate=json.loads(saved.read_text())['files']
            else:
                recovered=recover_candidate(attempt_dir,files,row['path'])
                if recovered:
                    candidate=recovered
                    atomic(saved,{'files':candidate,'origin':'interrupted-harness-draft','verified':False})
            attempts.append({'round':number,'verification':check})
            diagnostic='\n'.join(str(check.get(k,'')) for k in ('message','stdout','stderr'))
            if check.get('verified') or check.get('status')=='unavailable':break
            continue
        workflow='compact-c-v1' if os.getenv('XUANJIAN_HARNESS_COMPACT')=='1' else 'standard'
        atomic(attempt_dir/'request.json',{'prompt':prompt,'round':number,'model':'deepseek-v4-flash-0731','workflow':workflow})
        row['round']=number
        row['artifacts']['log']=(attempt_dir/'live-progress.jsonl').relative_to(DATA).as_posix()
        publish(snapshot)
        try:
            produced=generate('deepseek-harness',prompt,attempt_dir,timeout,'deepseek-v4-flash-0731')
            candidate=validate_candidates(files,produced,False,row['path'],'single')
            atomic(attempt_dir/'candidate.json',{'files':candidate})
            with (attempt_dir/'live-progress.jsonl').open('a') as feedback:
                feedback.write(json.dumps({'id':'platform-proof','label':'平台独立 Frama-C 证明','status':'running','at':datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+'\n')
            check=verify_candidates(candidate,row['path'],'single',attempt_dir/'proof',90)
            with (attempt_dir/'live-progress.jsonl').open('a') as feedback:
                feedback.write(json.dumps({'id':'platform-proof','label':'平台独立 Frama-C 证明','status':'completed' if check.get('verified') else 'failed','detail':check.get('message'),'at':datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+'\n')
        except Exception as exc:
            # Runner errors are already redacted; do not include provider transport details.
            from apps.api.app.agent_runners import AgentCallError
            check={'status':('timeout' if getattr(exc,'code','')=='agent_timeout' else 'unavailable') if isinstance(exc,AgentCallError) else 'blocked','verified':False,
                   'message':str(exc) if isinstance(exc,(AgentCallError,ValueError,TimeoutError)) else type(exc).__name__}
        if not (attempt_dir/'candidate.json').exists():
            recovered=recover_candidate(attempt_dir,files,row['path'])
            if recovered:
                candidate=recovered
                atomic(attempt_dir/'candidate.json',{'files':candidate,'origin':'interrupted-harness-draft','verified':False})
                check['recovered_candidate']=True
        atomic(attempt_dir/'verification.json',check)
        attempts.append({'round':number,'verification':check})
        diagnostic='\n'.join(str(check.get(k,'')) for k in ('message','stdout','stderr'))
        if check.get('verified') or check.get('status')=='unavailable':break
    proved=int(check.get('verified_count') or 0);total=proved+int(check.get('error_count') or 0)
    usage=0
    for i in range(1,len(attempts)+1):
        runtime=folder/f'round-{i}'/'harness-runtime.json'
        if runtime.exists():usage+=int(json.loads(runtime.read_text()).get('usage',{}).get('total_tokens',0) or 0)
    row.update(tokens=usage,status='passed' if check.get('verified') and total>0 and proved==total else 'error' if check.get('status')=='unavailable' else 'failed',
        raw_status=check.get('status','failed'),round=len(attempts),proved=proved,total=total,goal_rate=round(100*proved/total,1) if total else None,
        elapsed_sec=round(historical_elapsed+time.monotonic()-started,2),error='' if check.get('verified') else check.get('message','验证失败'))
    has_candidate=any((folder/f'round-{i}'/'candidate.json').exists() for i in range(1,6))
    if has_candidate:(folder/'candidate.acsl.c').write_text(candidate[0]['content'])
    (folder/'proof.wp.txt').write_text(diagnostic)
    atomic(folder/'attempts.json',attempts)
    row['artifacts']['log']=(folder/'proof.wp.txt').relative_to(DATA).as_posix()
    if has_candidate:row['artifacts']['source']=(folder/'candidate.acsl.c').relative_to(DATA).as_posix()
    publish(snapshot)
    print(json.dumps({'dataset':bid,'file':row['path'],'status':row['status'],'round':row['round'],'proved':proved,'total':total},ensure_ascii=False),flush=True)
    return row['status']

def pending_jobs(snapshots):
    queues=[[(s,r) for r in s['items'] if r['status'] in ('pending','running')] for s in snapshots]
    return ((queue[i]) for i in range(max(map(len,queues),default=0)) for queue in queues if i<len(queue))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--limit',type=int,default=0);p.add_argument('--timeout',type=int,default=600);p.add_argument('--workers',type=int,choices=range(1,13),default=3);args=p.parse_args()
    from apps.api.app.agent_runners import agent_environment,require_agent
    lock_path=ROOT/'runtime/deepseek-benchmark.lock';lock_path.parent.mkdir(parents=True,exist_ok=True)
    lock=lock_path.open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('A DeepSeek batch is already running')
    agent_environment();require_agent('deepseek-harness')
    from apps.api.app.skill_library import resolve_assistant
    from apps.api.app.assistants import AssistantConfig
    assistant=resolve_assistant(AssistantConfig(agent='deepseek-harness'))
    instructions=assistant.prompt('C')
    snapshots=initialize()
    for snapshot in snapshots:
        config=DATA/snapshot['benchmark']['id']/'configuration.json'
        if config.exists():
            saved=json.loads(config.read_text())
            if saved['instructions']!=instructions or saved['round_timeout_sec']!=args.timeout:raise ValueError('Resume requires the original pinned Skill and timeout configuration')
        else:atomic(config,{'agent':'deepseek-harness','model':'deepseek-v4-flash-0731','instructions':instructions,'max_rounds':5,'round_timeout_sec':args.timeout,'metric_definition':'pass@k: platform proof succeeds within k outer Harness repair rounds; each Harness round can contain multiple native model/tool steps','verifier':'Frama-C WP + RTE, Alt-Ergo,Z3','sub_model':'same as main model','runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'skill_sha256':hashlib.sha256(instructions.encode()).hexdigest()})
    for snapshot in snapshots:
        snapshot['benchmark']['experiment_status']='running'
        for row in snapshot['items']:
            if row['status']=='running':row['status']='pending'
        publish(snapshot)
    if args.workers>1 and not args.limit:
        # Interleave files from all datasets; no dataset can monopolize the pool.
        jobs=iter(pending_jobs(snapshots))
        stopped=False;errors=0
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending={}
            def fill():
                while not stopped and len(pending)<args.workers:
                    job=next(jobs,None)
                    if job is None:break
                    s,row=job;pending[pool.submit(run_case,s,row,instructions,args.timeout)]=job
            fill()
            while pending:
                completed,_=wait(pending,return_when=FIRST_COMPLETED)
                for future in completed:
                    pending.pop(future)
                    try:status=future.result()
                    except Exception:
                        stopped=True;status='error'
                        print('Worker stopped unexpectedly; preserved checkpoints.',flush=True)
                    errors=errors+1 if status=='error' else 0
                    if errors>=3:stopped=True
                fill()
        for s in snapshots:
            s['benchmark']['experiment_status']='completed' if all(r['status'] not in ('pending','running') for r in s['items']) else 'blocked'
            publish(s)
        return
    count=0;errors=0
    # Round-robin datasets so all three have early observable results.
    for index in range(max(len(s['items']) for s in snapshots)):
        for snapshot in snapshots:
            if index>=len(snapshot['items']):continue
            row=snapshot['items'][index]
            if row['status'] not in ('pending','running'):continue
            status=run_case(snapshot,row,instructions,args.timeout);count+=1;errors=errors+1 if status=='error' else 0
            if errors>=3:
                for s in snapshots:s['benchmark']['experiment_status']='blocked';publish(s)
                raise RuntimeError('Three consecutive service failures; experiment stopped without counting pending cases as failures.')
            if args.limit and count>=args.limit:return
    for snapshot in snapshots:snapshot['benchmark']['experiment_status']='completed';publish(snapshot)

if __name__=='__main__':main()
