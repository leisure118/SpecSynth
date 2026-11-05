"""Public verifier-neutral evidence. Native metric units must remain distinct."""
from typing import Literal
from pydantic import BaseModel, Field

class VerificationMetric(BaseModel):
    unit: Literal['proof-goals','verified-statements','verification-items']
    verified: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    total_reported: bool = False

class VerificationDiagnostic(BaseModel):
    path: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    severity: str = 'error'
    kind: str = 'unproved'
    message: str
    certainty: str = 'possible'
    source_hash: str | None = None

class VerificationReport(BaseModel):
    schema_version: int = 1
    tool: Literal['framac','verifast','verus']
    outcome: Literal['verified','failed','invalid','timeout','unavailable','cancelled']
    verified: bool = False
    message: str = ''
    metric: VerificationMetric
    diagnostics: list[VerificationDiagnostic] = Field(default_factory=list)
    source_hashes: dict[str,str] = Field(default_factory=dict)
    command: list[str] | str | None = None
    elapsed_ms: int | None = Field(default=None, ge=0)
    exit_code: int | None = None
