"""Transparent, conservative time-budget hints; never a proof of complexity."""
import re


def c_budget(files, requested=200, adaptive=True):
    text='\n'.join(f['content'] for f in files)
    stripped=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*',' ',text)
    loops=len(re.findall(r'\b(?:for|while)\s*\(',stripped))
    reasons=[]
    if loops>=2:reasons.append(f'{loops}个循环')
    if len(text.encode())>=8192:reasons.append('源码超过8 KiB')
    if sum(f['path'].endswith('.c') for f in files)>=2:reasons.append('多C文件工程')
    requested=requested or 200
    effective=max(requested,600) if adaptive and reasons else requested
    return {'requested_sec':requested,'effective_sec':effective,'adaptive':adaptive,'reasons':reasons,'policy':'c-complexity-v1'}
