"""Normalize evidence without changing native verdicts or inventing goal totals."""
import hashlib,re
from functools import wraps
from inspect import signature
from acsl.contracts.verification import VerificationReport

INVALID={'compile_error','blocked','no_checks','invalid','output_limit'}
UNAVAILABLE={'unavailable','tool_error','provider_error','error'}

def count(value):
    return value if type(value) is int and value>=0 else None

def normalize_verification(native,tool,files=()):
    status=str(native.get('status','')).lower()
    verified=native.get('verified') is True
    outcome=('cancelled' if status=='cancelled' else 'timeout' if status=='timeout' else
             'unavailable' if status in UNAVAILABLE else 'invalid' if status in INVALID else
             'verified' if verified else 'failed')
    verified=verified and outcome=='verified'
    if tool=='verifast':
        metric={'unit':'verified-statements','verified':count(native.get('verified_statements')),'total':None,'total_reported':False}
    else:
        proved=count(native.get('verified_count'));errors=count(native.get('error_count'))
        if outcome not in ('verified','failed') and proved==0 and errors==0:proved=errors=None
        metric={'unit':'proof-goals' if tool=='framac' else 'verification-items','verified':proved,
                'total':proved+errors if proved is not None and errors is not None else None,
                'total_reported':proved is not None and errors is not None}
    sources={f['path']:f['content'] for f in files}
    hashes={**native.get('report',{}).get('source_hashes',{}),**native.get('source_hashes',{}),**{p:hashlib.sha256(c.encode()).hexdigest() for p,c in sources.items()}}
    diagnostics=[]
    raw=list(native.get('diagnostics') or native.get('report',{}).get('diagnostics') or [])
    if tool=='verus' and not raw and not verified:
        for m in re.finditer(r'(?:-->\s*)?([^\s:]+\.rs):(\d+):(\d+)',str(native.get('stdout',''))+'\n'+str(native.get('stderr',''))):
            raw.append({'path':m[1],'line':int(m[2]),'column':int(m[3]),'message':native.get('message','Verus diagnostic'),'certainty':'reported'})
    for row in raw[:200]:
        path=row.get('path');matches=[p for p in sources if path==p or str(path).endswith('/'+p)]
        if len(matches)==1:path=matches[0]
        elif sources:path=None
        line=count(row.get('line'));column=count(row.get('column'))
        if line==0:line=None
        if column==0:column=None
        if path in sources and line and line>len(sources[path].splitlines()):line=None
        diagnostics.append({'path':path,'line':line if path else None,'column':column if path else None,
            'severity':row.get('severity','error'),'kind':row.get('kind','unproved'),
            'message':str(row.get('message') or native.get('message','')),'certainty':row.get('certainty','possible'),
            'source_hash':hashes.get(path)})
    elapsed=native.get('elapsed_ms')
    if elapsed is None and isinstance(native.get('elapsed_sec'),(int,float)):elapsed=round(native['elapsed_sec']*1000)
    return VerificationReport(tool=tool,outcome=outcome,verified=verified,message=str(native.get('message','')),
        metric=metric,diagnostics=diagnostics,source_hashes=hashes,
        command=native.get('command') or native.get('verifier_command'),elapsed_ms=count(elapsed),
        exit_code=native.get('exit_code',native.get('returncode'))).model_dump()

def reported(tool):
    """Keep old adapter fields while supplying one versioned public report."""
    def decorate(fn):
        sig=signature(fn)
        @wraps(fn)
        def wrapped(*args,**kwargs):
            from acsl.infrastructure.task_control import remaining
            bound=sig.bind(*args,**kwargs);bound.apply_defaults()
            values=bound.arguments
            for key in ('timeout','timeout_sec','timeout_seconds'):
                if key in values:values[key]=remaining(values[key])
            files=values.get('files') or ([{'path':values.get('entry_path','submission.rs'),'content':values['code']}] if 'code' in values else [])
            if 'code' in values:files=[{**f,'content':values['code']} if f['path']==values.get('entry_path','submission.rs') else f for f in files]
            result=fn(*bound.args,**bound.kwargs)
            return {**result,'report':normalize_verification(result,tool,files)}
        return wrapped
    return decorate
