"""Public API projection: Skill bodies and prompt snapshots stay server-side."""
import json
import re
from functools import lru_cache
from pathlib import Path

PRIVATE_KEYS={'instructions','agent_instructions','worker_instructions','prompt','effective_prompt','system_prompt','skill_snapshot','native_events','agent_events'}
PRIVATE_ARTIFACT_MARKERS=('skill.md','skill-snapshot','skill_snapshot','prompt','harness-events','cli-events','cli-raw')
NOTICE='Skill 正文和执行提示词仅保存在后端。'


@lru_cache(maxsize=2)
def _fragments(signature):
    fragments=set()
    for filename,_ in signature:
        try:
            path=Path(filename)
            data={'instructions':path.read_text()} if path.suffix.lower()=='.md' else json.loads(path.read_text())
            if path.name=='project.json':data={'skills':data.get('assistant',{}).get('skills',[])}
        except (OSError,ValueError):continue
        def collect(value):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key in ('instructions','content') and isinstance(item,str) and len(item)>=24:
                        fragments.add(item)
                        fragments.update(p for p in item.split('\n\n') if len(p)>=80 and (re.search(r'[\u4e00-\u9fff]',p) or p.startswith('#')))
                    else:collect(item)
            elif isinstance(value,list):
                for item in value:collect(item)
        collect(data)
    return tuple(fragments)


def protected_fragments():
    from .skill_library import SKILLS_DIR
    from .config import RUNTIME_DIR,ROOT_DIR
    from .workspace import PROJECTS_DIR
    paths=list(SKILLS_DIR.glob('*.json'))+list(PROJECTS_DIR.glob('*/project.json'))+list((ROOT_DIR/'skills').glob('**/SKILL.md'))+list((ROOT_DIR/'resources/skills').glob('**/SKILL.md'))
    if (RUNTIME_DIR/'generation-skills.json').exists():paths.append(RUNTIME_DIR/'generation-skills.json')
    return _fragments(tuple(sorted((str(p),p.stat().st_mtime_ns) for p in paths)))


def private_artifact(path):
    value=str(path).lower().replace('\\','/')
    if '/skills/' in value:return True
    if Path(value).suffix in ('.c','.h','.rs','.i'):return False
    return any(marker in value for marker in PRIVATE_ARTIFACT_MARKERS)


def public_payload(value,fragments=None):
    if fragments is None:fragments=protected_fragments()
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            if key.lower() in PRIVATE_KEYS or ('prompt' in key.lower() and isinstance(item,(str,list,dict))):continue
            if key in ('events','input','arguments') and ('agent_runtime' in value or 'tool' in value or 'type' in value or 'command' in value):continue
            if key=='skills' and isinstance(item,list):
                result[key]=[{k:public_payload(v,fragments) for k,v in skill.items() if k in ('id','name','version','agents','enabled','description')} if isinstance(skill,dict) else skill for skill in item]
            else:result[key]=public_payload(item,fragments)
        # Raw native event streams can contain tasks with embedded Skill text.
        if value.get('events_kind') or value.get('package') in ('@deepseek-ai/dsh','@anthropic-ai/claude-agent-sdk'):
            result.pop('events',None)
        if isinstance(result.get('items'),list):
            result['items']=[item for item in result['items'] if not isinstance(item,dict) or not private_artifact(item.get('relative_path',''))]
        if 'content' in result and 'name' in result and str(result.get('id','')).startswith(('uploaded-','local-')):result.pop('content',None)
        return result
    if isinstance(value,list):return [public_payload(item,fragments) for item in value]
    if isinstance(value,str):
        # Decode previewed JSON/JSONL so private keys cannot hide in an artifact string.
        stripped=value.strip()
        if stripped.startswith(('{','[')):
            try:return json.dumps(public_payload(json.loads(value),fragments),ensure_ascii=False,indent=2)
            except (ValueError,TypeError):pass
        if any(marker in value for marker in ('# spec-split —','# spec-orchestrate —','# spec-bottomup —')):return NOTICE
        if any(fragment in value for fragment in fragments):return NOTICE
        return value
    return value


class SkillPrivacyMiddleware:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or not scope.get('path','').startswith('/api/'):
            return await self.app(scope,receive,send)
        start=None;chunks=[];is_json=False
        async def project(message):
            nonlocal start,is_json
            if message['type']=='http.response.start':
                start=message
                headers=dict(message.get('headers',[]));is_json=b'application/json' in headers.get(b'content-type',b'')
                if not is_json:await send(message)
            elif message['type']=='http.response.body' and is_json:
                chunks.append(message.get('body',b''))
                if not message.get('more_body'):
                    data=json.loads(b''.join(chunks));body=json.dumps(public_payload(data),ensure_ascii=False).encode()
                    start['headers']=[(k,v) for k,v in start['headers'] if k.lower() not in (b'content-length',b'etag')]+[(b'content-length',str(len(body)).encode()),(b'cache-control',b'no-store')]
                    await send(start);await send({'type':'http.response.body','body':body})
            else:await send(message)
        await self.app(scope,receive,project)
