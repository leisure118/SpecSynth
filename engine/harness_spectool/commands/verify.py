"""Skill verification command using the platform's container toolchain."""
from pathlib import Path
import tempfile
from ..registry import command
from ..io import emit_json


@command(name='verify', help='Verify a C candidate using platform Frama-C/WP.')
def configure(parser):
    parser.add_argument('-f','--file',required=True)
    parser.add_argument('--timeout',type=int,default=8)
    parser.add_argument('--save-stdout')


def run(args):
    from engine.verification.framac_runtime import run_candidate
    source=Path(args.file).read_text()
    root=Path.cwd()/'.platform-proofs';root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        result=run_candidate([{'path':'candidate.c','content':source}], 'candidate.c','single',Path(folder),max(10,min(120,args.timeout*4)))
    if args.save_stdout:
        path=Path(args.save_stdout);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(result.get('stdout','')+'\n'+result.get('stderr',''))
    emit_json({'result':'Pass' if result['verified'] else 'Fail', 'proved':result.get('verified_count',0),
               'total':result.get('verified_count',0)+result.get('error_count',0), 'stdout_file':args.save_stdout,
               'diagnostics':result})
