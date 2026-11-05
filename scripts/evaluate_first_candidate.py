"""One candidate per fixed case; compare worker thinking without repair or metric inflation."""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def main():
    args=argparse.ArgumentParser();args.add_argument('--worker-thinking',choices=['off','on'],required=True);args.add_argument('--output',required=True);opts=args.parse_args()
    os.environ.update(XUANJIAN_HARNESS_COMPACT='1',XUANJIAN_HARNESS_SPEC_PATCHES='1',XUANJIAN_HARNESS_MAIN_THINKING='off',XUANJIAN_HARNESS_WORKER_THINKING=opts.worker_thinking,XUANJIAN_HARNESS_MAIN_MAX_TOKENS='32768',XUANJIAN_HARNESS_SUB_MAX_TOKENS='4096',XUANJIAN_QWEN_CONTEXT_WINDOW='16384',ACSL_FRAMAC_PROFILE='original',XUANJIAN_PROOF_CPUS='2',XUANJIAN_PROOF_CONCURRENCY='2')
    from acsl.adapters.agent_runtime import generate
    from acsl.application.agent_execution import initial_prompt,validate_candidates,verify_candidates
    from acsl.application.source_routing import classify_sources,routing_instructions
    from engine.nl2verus.harness_session import case_session
    base=ROOT/'resources/benchmarks/dsh_bailian_qwen9b_live25_transport6_20261104_v5';index=json.loads((base/'index.json').read_text());config=json.loads((base/'configuration.json').read_text());out=Path(opts.output).resolve();out.mkdir(parents=True,exist_ok=True)
    result={'worker_thinking':opts.worker_thinking,'main_thinking':'off','candidate_budget_per_case':1,'repairs':0,'selection':'two previously failing cases, not dataset-wide pass rate','items':[]}
    for name in ('array-cav19_array_init_nondet_vars.c','array-crafted_zero_sum_const3.c'):
        row=next(r for r in index['items'] if r['path']==name);files=[{'path':name,'content':(ROOT/'resources/benchmarks'/row['artifacts']['original_source']).read_text()}];folder=out/row['id'];folder.mkdir(exist_ok=True);start=time.monotonic();item={'file':name,'original_sha256':row['original_sha256']}
        prompt=initial_prompt(files,'single','Prove the original benchmark assertions without changing program semantics.','',config['instructions'])+routing_instructions(classify_sources(files,name,'single'))
        try:
            with case_session():candidate=generate('deepseek-harness',prompt,folder,240,'deepseek-v4.1-flash-1017',sub_model='qwen35-9b-mix64')
            validate_candidates(files,candidate,False,name,'single');(folder/'candidate.json').write_text(json.dumps({'files':candidate},ensure_ascii=False))
            proof=verify_candidates(candidate,name,'single',folder/'proof',90);(folder/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
            item.update(status=proof['status'],proved=proof.get('verified_count',0),total=proof.get('verified_count',0)+proof.get('error_count',0),message=proof['message'])
        except Exception as exc:item.update(status='generation_failure',code=getattr(exc,'code',type(exc).__name__),message=str(exc)[:1500])
        rt=folder/'harness-runtime.json'
        if rt.exists():
            evidence=json.loads(rt.read_text());runtime=evidence.get('agent_runtime',{});item.update(quality=runtime.get('candidate_quality'),thinking_policy=runtime.get('thinking_policy'),main_output_tokens=sum((e.get('usage') or {}).get('outputTokens',0) or 0 for e in runtime.get('events',[])))
        item['elapsed_sec']=round(time.monotonic()-start,2);result['items'].append(item);(out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(item,ensure_ascii=False),flush=True)
    result['completed']=True;(out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
