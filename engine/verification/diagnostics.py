"""Conservative source locations for unproved goals; never edit specifications."""
import hashlib
import re
from pathlib import PurePosixPath


def verification_diagnostics(stdout, files):
    def find_source(path):
        matches=[f for f in files if path==f['path'] or path.endswith('/'+f['path'])]
        if len(matches)==1:return matches[0]
        matches=[f for f in files if PurePosixPath(f['path']).name==PurePosixPath(path).name]
        return matches[0] if len(matches)==1 else None
    locations=[]
    for block in re.split(r'(?=^Goal )',stdout,flags=re.M):
        if not block.startswith('Goal '):continue
        # A different prover may have discharged the same goal.
        if re.search(r'Prover .* returns Valid\b|Prove:\s*true\.',block):continue
        if not re.search(r'returns (?:Timeout|Unknown|Failed|Invalid)|Prove:\s*false\.',block):continue
        header=block.split('\n\n',1)[0]
        match=re.search(r'\(file ([^\n]+?), line (\d+)\)',header)
        if not match:continue
        f=find_source(match[1])
        if f is None:continue
        line=int(match[2])
        if not 1<=line<=len(f['content'].splitlines()):continue
        locations.append({'path':f['path'],'line':line,'severity':'error','kind':'unproved',
                          'message':header[:700],'certainty':'possible'})
    # Frama-C syntax/type errors can report a location before any WP goal exists.
    for match in re.finditer(r'([^\s:]+\.(?:c|h)):(\d+)(?::\d+)?:[^\n]*(?:Error|error|syntax error)',stdout):
        f=find_source(match[1])
        if f and 1<=int(match[2])<=len(f['content'].splitlines()):
            locations.append({'path':f['path'],'line':int(match[2]),'severity':'error','kind':'syntax','message':match[0][:700],'certainty':'reported'})
    # Parser errors often place the message on indented lines after a Warning.
    for match in re.finditer(r'([^\s:]+\.(?:c|h)):(\d+)(?::\d+)?:([^\n]*(?:\n[ \t]+[^\n]*){0,4})',stdout):
        body=match[3]
        if not re.search(r'syntax error|invalid operands|unbound logic|type error|parse error',body,re.I):continue
        f=find_source(match[1]);line=int(match[2])
        if f and 1<=line<=len(f['content'].splitlines()):
            locations.append({'path':f['path'],'line':line,'severity':'error','kind':'type' if 'invalid operands' in body else 'syntax','message':body.strip()[:700],'certainty':'reported'})
    unique={(d['path'],d['line'],d['message']):d for d in locations}
    return list(unique.values())[:200]


def attach_diagnostics(result,files):
    result['diagnostics']=verification_diagnostics(result.get('stdout','')+'\n'+result.get('stderr',''),files)
    result['source_hashes']={f['path']:hashlib.sha256(f['content'].encode()).hexdigest() for f in files}
    return result
