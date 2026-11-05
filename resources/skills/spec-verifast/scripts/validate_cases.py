"""Exercise real project patch validation and native VeriFast; no model calls."""
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from engine.verification.spec_patches import merge_spec_patches
from engine.verification.spec_edit import source_tokens
from engine.verification.verifast_runtime import verify,capabilities

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    info=capabilities()
    if not info['ready']:raise SystemExit(info['message'])
    cases=Path(__file__).resolve().parents[1]/'cases';results=[]
    def run(name,files,patches,expected):
        try:
            merged=merge_spec_patches(files,patches,'verifast')
            assert all(source_tokens(a['content'])==source_tokens(b['content']) for a,b in zip(files,merged))
            outcome=verify(merged,files[0]['path'],30)
            stage='verified' if outcome['verified'] else 'verifier-rejected'
            detail={'message':outcome['message'],'verified_statements':outcome.get('verified_statements'),'evidence_id':outcome.get('id')}
        except ValueError as exc:stage='patch-rejected';detail={'message':str(exc)}
        row={'case':name,'expected':expected,'actual':stage,'ok':stage==expected,**detail};results.append(row)
    loaded={}
    for p in sorted(cases.glob('*.c')):
        files=[{'path':p.name,'content':p.read_text()}];patches=json.loads(p.with_suffix('.patches.json').read_text());loaded[p.stem]=(files,patches)
        run(p.stem,files,patches,'verified')
    files,patches=loaded['count-loop']
    bad=copy.deepcopy(patches);bad['patches'][0]['annotation']='/* requires true; ensures true; */';run('ordinary-comment',files,bad,'patch-rejected')
    bad=copy.deepcopy(patches);bad['patches'][1]['annotation']='//@ loop invariant count <= limit;';run('acsl-mixed',files,bad,'patch-rejected')
    bad=copy.deepcopy(patches);bad['patches'][0]['before_line']=1;run('wrong-contract-location',files,bad,'verifier-rejected')
    bad=copy.deepcopy(patches);bad['patches'][1]['annotation']='//@ invariant 0 <= count;';run('insufficient-invariant',files,bad,'verifier-rejected')
    files,patches=loaded['swap-pointers'];bad=copy.deepcopy(patches);bad['patches'][0]['annotation']='//@ requires a != 0 &*& b != 0;\n//@ ensures true;';run('missing-heap-permission',files,bad,'verifier-rejected')
    report={'runtime':info,'model_calls':0,'cases':results,'passed':sum(r['ok'] for r in results),'total':len(results)}
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for row in results:print(row['case'],row['actual'],'OK' if row['ok'] else 'UNEXPECTED',row['message'])
    print(f"{report['passed']}/{report['total']} expected outcomes; no model calls")
    if report['passed']!=report['total']:raise SystemExit(1)
if __name__=='__main__':main()
