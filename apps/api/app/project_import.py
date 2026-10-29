"""Read-only GitHub source import; never executes repository hooks or scripts."""
import os
import re
from pathlib import Path
import subprocess
import tempfile
from fastapi import HTTPException
from pydantic import BaseModel,Field
from typing import Literal
from .config import RUNTIME_DIR
from .agent_runners import run_process

class GithubImport(BaseModel):
    repository:str=Field(min_length=3,max_length=250)
    ref:str=Field(default='',max_length=120)
    language:Literal['C','Rust']='C'
    name:str=Field(default='',max_length=120)


def import_sources(body):
    match=re.fullmatch(r'(?:https://github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?',body.repository.strip())
    if not match:raise HTTPException(422,'请输入 GitHub HTTPS 仓库地址或 owner/repository。')
    owner,repo=match.groups()
    if any(v in ('.','..') for v in (owner,repo)):raise HTTPException(422,'仓库地址无效。')
    if body.ref and (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*',body.ref) or '..' in body.ref or body.ref.endswith('/')):
        raise HTTPException(422,'分支或标签名称无效。')
    RUNTIME_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='github-import-',dir=RUNTIME_DIR) as temp:
        args=['git','-c','core.hooksPath=/dev/null','clone','--depth','1','--single-branch','--quiet']
        if body.ref:args+=['--branch',body.ref]
        args+=['https://github.com/'+owner+'/'+repo+'.git',str(Path(temp)/'repo')]
        try:
            code,_,_=run_process(args,cwd=RUNTIME_DIR,timeout=45,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
        except (OSError,TimeoutError):raise HTTPException(422,'无法读取 GitHub 仓库，请检查网络与 Git 登录状态。') from None
        if code:raise HTTPException(422,'GitHub 导入失败，请检查仓库、分支和当前 Git 的读取权限。')
        root=Path(temp)/'repo';files=[];size=0
        excluded={'.git','node_modules','target','vendor','runtime','.venv','venv','dist','build'}
        allowed={'.rs'} if body.language=='Rust' else {'.c','.h'}
        for directory,dirs,names in os.walk(root,followlinks=False):
            dirs[:]=[d for d in sorted(dirs) if d not in excluded and not (Path(directory)/d).is_symlink()]
            for filename in sorted(names):
                path=Path(directory)/filename
                if path.suffix not in allowed or path.is_symlink():continue
                if path.stat().st_size>2_000_000:raise HTTPException(422,'源文件超过 2 MB，请缩小导入范围。')
                size+=path.stat().st_size
                if size>10_000_000 or len(files)>=200:raise HTTPException(422,'源文件超过 200 个或 10 MB，请导入精简仓库。')
                try:content=path.read_text(encoding='utf-8-sig')
                except UnicodeError:raise HTTPException(422,'源文件需要 UTF-8 编码。') from None
                files.append({'path':path.relative_to(root).as_posix(),'content':content})
        if not any(f['path'].endswith('.rs' if body.language=='Rust' else '.c') for f in files):raise HTTPException(422,'仓库中未找到对应语言源文件。')
    return {'name':body.name.strip() or repo,'language':body.language,'files':files}, {'repository':owner+'/'+repo,'ref':body.ref or 'default'}
