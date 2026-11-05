"""Read-only server toolchain checks. No model calls and no credentials printed."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['local','server'],default='server')
    parser.add_argument('--tools',nargs='+',choices=['agents','framac','verifast','verus'],default=['agents','framac','verifast','verus'])
    args=parser.parse_args();checks=[]
    from acsl.infrastructure.runtime_profile import apply_runtime_profile
    apply_runtime_profile(args.profile)
    for tool in args.tools:
        try:
            if tool=='agents':
                p=subprocess.run([sys.executable,str(ROOT/'scripts/install_agent_runtime.py'),'--check'],cwd=ROOT,capture_output=True,text=True,timeout=30)
                ready=p.returncode==0;message='CLI dependencies ready' if ready else 'CLI dependencies missing; run install_agent_runtime.py on this server'
            elif tool=='framac':
                from engine.verification.framac_runtime import runtime_info
                info=runtime_info(force=True);ready=info['ready'];message=info['message']
            elif tool=='verifast':
                from engine.verification.verifast_runtime import capabilities
                info=capabilities();ready=info['ready'];message=info['message']
            else:
                from engine.nl2verus.verifier import verifier_info
                info=verifier_info();ready=info.get('available',False);message='Verus ready' if ready else 'Verus unavailable'
            checks.append({'tool':tool,'ready':bool(ready),'message':message})
        except Exception:
            checks.append({'tool':tool,'ready':False,'message':'Tool check failed; inspect server installation and permissions'})
    print(json.dumps({'checks':checks,'model_calls':0},ensure_ascii=False,indent=2))
    return 0 if all(c['ready'] for c in checks) else 1
if __name__=='__main__':raise SystemExit(main())
