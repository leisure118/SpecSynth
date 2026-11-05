"""Ten-file, independent test of the compact main-agent token policy."""
import copy,hashlib,json,os,sys,fcntl
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import run_bailian_qwen9b_live25 as runner
from engine.verification.worker_contract import thinking_policy
FILES=['array-cav19_array_doub_access_init_const.c','array-cav19_array_tiling_poly6.c','array-cav19_array_init_pair_sum_const.c','array-cav19_array_tiling_tcpy.c','array-crafted_bAnd2.c','array-crafted_bAnd4.c','array-crafted_bor1.c','array-cav19_array_init_both_ends_multiple_sum.c','array-cav19_array_init_nondet_vars.c','array-crafted_zero_sum_const3.c']
BID='dsh_bailian_qwen9b_live25_small10_patches_20261104_v1'
BASE='dsh_bailian_qwen9b_live25_20261104_token32k_r1'
COMPARISON='dsh_bailian_qwen9b_live25_small10_20261104_v1'

def usage(folder):
    output=inputs=calls=handoffs=0
    for p in folder.glob('round-*/harness-runtime.json'):
        d=json.loads(p.read_text());runtime=d.get('agent_runtime',{})
        for e in runtime.get('events',[]):
            u=e.get('usage') or {};output+=u.get('outputTokens',0) or 0;inputs+=u.get('inputTokens',0) or 0
            if e.get('type')=='status' and e.get('phase')=='step_start':calls+=1
    for p in folder.glob('round-*/subagent-audit.jsonl'):
        handoffs+=sum(json.loads(l).get('type')=='handoff' for l in p.read_text().splitlines())
    return {'main_output_tokens':output,'main_input_tokens_uncached':inputs,'main_calls':calls,'automatic_handoffs':handoffs}

def main():
    lock=(ROOT/'runtime/experiments/live25-small10.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Ten-file test already running')
    baseline=json.loads((runner.DATA/BASE/'index.json').read_text());base_config=json.loads((runner.DATA/BASE/'configuration.json').read_text())
    comparison=json.loads((runner.DATA/COMPARISON/'index.json').read_text())
    folder=runner.DATA/BID;path=folder/'index.json'
    if path.exists():
        saved=json.loads((folder/'configuration.json').read_text())
        if saved.get('thinking_policy')!=thinking_policy():raise ValueError('Thinking policy changed; use a new experiment id rather than mixing results')
        snapshot=json.loads(path.read_text())
    else:
        rows=[]
        for name in FILES:
            previous=next(r for r in comparison['items'] if r['path']==name)
            original=next(r for r in baseline['items'] if r['path']==name);row={k:copy.deepcopy(v) for k,v in original.items() if k in ('id','path','original_filename','original_path','original_sha256')}
            row.update(status='pending',raw_status='pending',round=0,proved=0,total=0,goal_rate=None,tokens=0,elapsed_sec=0,error='',artifacts={'original_source':original['artifacts']['original_source']},baseline={'benchmark_id':COMPARISON,'status':previous['status'],'round':previous.get('round'),'error':previous.get('error'),**usage(runner.DATA/COMPARISON/previous['id'])})
            rows.append(row)
        b=copy.deepcopy(baseline['benchmark']);b.update(id=BID,name=f'LiveFMBench 2025 · {len(FILES)}文件规约补丁复测',experiment_status='running',reported_total=len(FILES),indexed_total=len(FILES),completed_count=0,passed_count=0,original_source_count=len(FILES),run_tag=f'small{len(FILES)}-acsl-patches-v1',configuration_label=runner.LABEL,description=f'{len(FILES)}个定向样例：覆盖历史通过、源码改动、token超限、ACSL语法和证明目标未通过；不代表全集通过率。',notice='最多5次候选，pass@1/pass@5沿用历史定义。主模型输出统计仅取主会话使用记录；原生子模型直接交接仅在有效JSON输出时生效。')
        b.pop('paused_at',None)
        snapshot={'benchmark':b,'items':rows}
        runner.atomic(folder/'configuration.json',{**base_config,'sample_files':FILES,'sample_selection':'targeted, not random','auto_handoff':True,'thinking_policy':thinking_policy(),'receipt_validation':'before-acknowledgement','candidate_protocol':'acsl-patches-v1','sub_max_tokens':4096,'qwen_context_window':16384,'worker_context_reserve_tokens':1024,'repair_feedback_max_chars':5000,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    snapshot['benchmark']['experiment_status']='running';runner.publish(snapshot)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(runner.run_case,snapshot,row,base_config['instructions'],600):row for row in snapshot['items'] if row['status'] in ('pending','running')}
        for future in as_completed(futures):
            row=futures[future]
            try:future.result()
            except Exception as exc:row.update(status='error',error=type(exc).__name__)
            row['token_usage']=usage(folder/row['id']);runner.publish(snapshot)
    snapshot['benchmark']['experiment_status']='completed';runner.publish(snapshot)
    summary={'benchmark_id':BID,'sample_size':len(FILES),'selection':'targeted; not representative of whole dataset','pass_at_1':snapshot['benchmark']['summary']['pass@1'],'pass_at_5':snapshot['benchmark']['summary']['pass@5'],'items':[{k:r.get(k) for k in ('path','status','round','proved','total','elapsed_sec','error','failure_stage','first_candidate_quality','baseline','token_usage')} for r in snapshot['items']]}
    runner.atomic(folder/'small-test-summary.json',summary)
    print(json.dumps({'completed':True,'summary':str(folder/'small-test-summary.json')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
