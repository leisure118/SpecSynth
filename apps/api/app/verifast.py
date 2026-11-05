"""HTTP interface for independent VeriFast C verification."""
import json,re
from pathlib import Path
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field,model_validator
from engine.verification import verifast_runtime as runtime
from acsl.infrastructure.settings import settings
router=APIRouter(prefix='/api/v1/verifast',tags=['verifast'])


class SourceFile(BaseModel):
    path:str=Field(min_length=1,max_length=240)
    content:str=Field(max_length=262144)


class VerificationRequest(BaseModel):
    files:list[SourceFile]=Field(min_length=1,max_length=64)
    entry:str
    timeout_sec:int=Field(default=200,ge=1,le=600)

    @model_validator(mode='after')
    def check_files(self):
        runtime.validate_files([f.model_dump() for f in self.files],self.entry)
        return self


def directory(identifier):
    if not re.fullmatch(r'[a-f0-9]{32}',identifier):raise HTTPException(404,'找不到验证记录。')
    p=settings.runtime_dir/'verifast'/identifier
    if not (p/'result.json').is_file():raise HTTPException(404,'找不到验证记录。')
    return p


@router.get('/capabilities')
def capabilities():return runtime.capabilities()


@router.post('/verify')
def verify(body:VerificationRequest):return runtime.verify([f.model_dump() for f in body.files],body.entry,body.timeout_sec)


@router.get('/runs')
def history():
    base=settings.runtime_dir/'verifast';items=[]
    for p in sorted(base.glob('*/result.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:30]:
        d=json.loads(p.read_text());items.append({k:d.get(k) for k in ('id','entry','status','verified','elapsed_sec','message','version')})
    return {'items':items}


@router.get('/runs/{identifier}')
def result(identifier:str):return json.loads((directory(identifier)/'result.json').read_text())


@router.get('/runs/{identifier}/input')
def source(identifier:str):return json.loads((directory(identifier)/'input.json').read_text())


@router.get('/runs/{identifier}/log')
def log(identifier:str):return FileResponse(directory(identifier)/'verification.log',media_type='text/plain',filename='verifast.log')
