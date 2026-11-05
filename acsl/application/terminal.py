"""Redaction for native tool command/output projections (never model reasoning)."""
import os,re

def safe_terminal_text(text,limit=6000):
    for key,value in os.environ.items():
        if len(value)>=6 and any(marker in key.upper() for marker in ('KEY','TOKEN','SECRET','PASSWORD')):
            text=text.replace(value,'[REDACTED]')
    text=re.sub(r'(?i)(authorization[\s:"\']*(?:bearer\s+)?)[^\s"\']+',r'\1[REDACTED]',text)
    text=re.sub(r'(?i)((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+',r'\1[REDACTED]',text)
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
    from acsl.application.privacy import public_payload
    return public_payload(text[-max(1,min(limit,24000)):])


def native_terminal(task):
    """Read actual CLI command/output records, separately from platform progress."""
    import json
    from pathlib import Path
    from acsl.infrastructure.settings import resolve_project_path
    directory=resolve_project_path(task.task_dir)
    agent=(task.metadata or {}).get('agent') or ((task.metadata or {}).get('assistant') or {}).get('agent')
    rows={};budget=2*1024*1024
    for path in sorted((directory/'artifacts'/'agent').glob('round-*/live-progress.jsonl'))[:4]:
        if path.is_symlink() or not path.is_file():continue
        try:path.resolve().relative_to(directory.resolve())
        except ValueError:continue
        size=min(path.stat().st_size,512*1024,budget);budget-=size
        if size<=0:break
        with path.open('rb') as stream:data=stream.read(size).decode(errors='replace')
        for index,line in enumerate(data.splitlines()):
            try:event=json.loads(line)
            except ValueError:continue
            if not isinstance(event,dict) or not (event.get('command') or event.get('output')):continue
            key=path.parent.name+':'+str(event.get('id',index))
            row=rows.setdefault(key,{'id':key,'round':path.parent.name,'at':event.get('at'),'source':'native-cli'})
            for field in ('label','status','command','output','detail'):
                if event.get(field):row[field]=safe_terminal_text(str(event[field]),limit=24000)
    # Old tasks may retain native command projections in metadata only.
    if not rows:
        for step in (task.metadata or {}).get('agent_progress',{}).get('steps',[]):
            if not (step.get('command') or step.get('output')):continue
            key=str(step.get('id',len(rows)))
            rows[key]={'id':key,'at':step.get('started_at'),'source':'saved-cli-event',
                       **{field:safe_terminal_text(str(step[field]),limit=24000) for field in ('label','status','command','output','detail') if step.get(field)}}
    return {'agent':agent,'status':task.status,'source':'native-cli-events','events':list(rows.values())[-200:]}
