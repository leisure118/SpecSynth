"""Shared direct-verification endpoint; only the backend adapter varies."""
import tempfile
from pathlib import Path
from typing import Literal
from fastapi import APIRouter
from .verifast import VerificationRequest
from engine.verification import verifast_runtime, framac_runtime
from acsl.infrastructure.proof_limits import proof_slot
from acsl.infrastructure.settings import settings

router=APIRouter(prefix='/api/v1/verification',tags=['verification'])

class ToolVerificationRequest(VerificationRequest):
    verification_tool: Literal['framac','verifast']='framac'

@router.post('/verify')
def verify(body:ToolVerificationRequest):
    files=[f.model_dump() for f in body.files]
    with proof_slot(body.timeout_sec) as remaining:
        if body.verification_tool=='verifast':
            result=verifast_runtime.verify(files,body.entry,max(1,int(remaining)))
        else:
            settings.runtime_dir.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='direct-proof-',dir=settings.runtime_dir) as directory:
                result=framac_runtime.run_candidate(files,body.entry,'single',remaining,Path(directory))
    return {**result,'verification_tool':body.verification_tool,'result':'通过' if result.get('verified') else '未通过'}
