from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


RunMode = Literal["single", "termination", "inter-modular", "batch", "rust-verify", "rust-generate"]
RunStatus = Literal["queued", "running", "pass", "fail", "invalid", "timeout", "unavailable"]
PhaseStatus = Literal["pending", "running", "completed", "failed", "skipped"]
ResultStatus = Literal["Pass", "Fail", "Invalid", "Timeout", "Unavailable"]


class PhaseState(BaseModel):
    key: str
    label: str
    status: PhaseStatus = "pending"
    detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ArtifactItem(BaseModel):
    name: str
    path: str
    relative_path: str
    category: str
    size: int | None = None


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    stored_path: str
    size: int
    kind: Literal["file", "bundle"] = "file"
    entry_count: int = 1
    root_dir: str | None = None


class RunRequest(BaseModel):
    verification_tool: Literal["framac", "verifast"] = "framac"
    manual_context: dict | None = None
    verification_only: bool = False
    benchmark_context: dict | None = None
    file_id: str | None = None
    demo_case_id: str | None = None
    upstream_task_id: str | None = None
    model_name: str = "qwen-turbo"
    entry_path: str | None = None
    rust_workflow: dict | None = None
    agent_instructions: str = Field(default="", max_length=80000)
    assistant: dict | None = None
    description: str = Field(default="", max_length=16000)
    function_signature: str = Field(default="", max_length=4000)
    max_repair_rounds: int = Field(default=3, ge=0, le=3)
    enable_mutation: bool = False
    timeout_sec: int | None = Field(default=None, ge=10, le=3600)
    adaptive_timeout: bool = True

    @model_validator(mode="after")
    def validate_source(self) -> "RunRequest":
        if not any([self.file_id, self.demo_case_id, self.upstream_task_id]):
            raise ValueError("One of file_id, demo_case_id, or upstream_task_id is required.")
        if self.assistant is not None:
            # Validate the agent identity here; pinned Skill resolution is an
            # application concern performed by the run manager.
            from acsl.domain.agents import AssistantConfig

            AssistantConfig(**self.assistant)
        return self


class RunTask(BaseModel):
    task_id: str
    mode: RunMode
    title: str
    source_type: Literal["upload", "demo", "derived"]
    status: RunStatus
    engine: Literal["replay", "live", "stub"]
    model_name: str | None = None
    demo_case_id: str | None = None
    file_id: str | None = None
    upstream_task_id: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    task_dir: str
    input_file: str | None = None
    message: str | None = None
    phases: list[PhaseState] = Field(default_factory=list)
    capabilities: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class RunCreateResponse(BaseModel):
    task_id: str
    status: RunStatus
    detail: str


class ProofStats(BaseModel):
    scope: Literal["proof-goals", "files", "invariants", "termination-goals", "compilation-unit"] = "proof-goals"
    unit: Literal["goals", "files", "items", "units"] = "goals"
    proved_goals: int = 0
    total_goals: int = 0
    timeout_goals: int = 0
    invalid_goals: int = 0
    open_goals: int = 0
    pass_rate: float = 0.0


class TimingStats(BaseModel):
    wall_clock_ms: int | None = None
    llm_time_sec: float = 0.0
    solve_time_sec: float = 0.0
    avg_item_time_sec: float = 0.0
    timeout_sec: int | None = None
    iteration_count: int = 0
    tokens_usage: int = 0


class FailureAnalysis(BaseModel):
    category: str = "none"
    label: str = "Verifier-approved"
    summary: str = ""
    evidence: list[str] = Field(default_factory=list)
    actionable_hint: str | None = None


class AggregateMetrics(BaseModel):
    total_items: int = 0
    pass_count: int = 0
    fail_count: int = 0
    invalid_count: int = 0
    timeout_count: int = 0
    unavailable_count: int = 0
    success_rate: float = 0.0
    closure_rate: float = 0.0
    avg_llm_time_sec: float = 0.0
    avg_total_solve_time_sec: float = 0.0
    max_total_solve_time_sec: float = 0.0
    timeout_sec: int | None = None
    failure_breakdown: dict[str, int] = Field(default_factory=dict)


class BatchItem(BaseModel):
    filename: str
    relative_path: str | None = None
    status: str
    status_category: str | None = None
    llm_time_sec: float = 0.0
    total_solve_time_sec: float = 0.0
    tokens_usage: int = 0
    iteration_count: int = 0
    error_type: str | None = None
    error: str | None = None
    result_path: str | None = None
    proof_stats: dict[str, Any] = Field(default_factory=dict)


class CallGraphSummary(BaseModel):
    source_file_count: int = 0
    header_file_count: int = 0
    entry_files: list[str] = Field(default_factory=list)
    merge_order: list[str] = Field(default_factory=list)
    call_edge_count: int = 0
    fan_out: dict[str, int] = Field(default_factory=dict)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    functions: list[dict[str, Any]] = Field(default_factory=list)
    entry_functions: list[str] = Field(default_factory=list)
    reachable_functions: list[str] = Field(default_factory=list)


class ModuleResult(BaseModel):
    path: str
    relative_path: str
    specifications: dict[str, list[str]] = Field(default_factory=dict)
    specification_counts: dict[str, int] = Field(default_factory=dict)
    has_contract_noise: bool = False
    noise_markers: list[str] = Field(default_factory=list)
    reachable_function_count: int = 0
    verified_function_count: int = 0
    verification_status: str = "not_applicable"


class SplitOutput(BaseModel):
    path: str
    relative_path: str
    specification_counts: dict[str, int] = Field(default_factory=dict)


class RunResult(BaseModel):
    task_id: str
    mode: RunMode
    status: ResultStatus
    engine: str
    title: str
    summary: str
    command: str | None = None
    repro_command: str | None = None
    source_code: str
    result_code: str
    partial_correctness_code: str | None = None
    specifications: dict
    logs: dict
    highlights: list[str] = Field(default_factory=list)
    paper_keywords: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    status_reason: str | None = None
    engine_detail: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    elapsed_ms: int | None = None
    phase_metrics: list[dict] = Field(default_factory=list)
    status_category: str = "unknown"
    proof_stats: ProofStats = Field(default_factory=ProofStats)
    timing_stats: TimingStats = Field(default_factory=TimingStats)
    failure_analysis: FailureAnalysis = Field(default_factory=FailureAnalysis)
    evidence_summary: list[str] = Field(default_factory=list)
    task_summary: dict[str, Any] = Field(default_factory=dict)
    aggregate_metrics: AggregateMetrics = Field(default_factory=AggregateMetrics)
    items: list[BatchItem] = Field(default_factory=list)
    call_graph_summary: CallGraphSummary = Field(default_factory=CallGraphSummary)
    module_results: list[ModuleResult] = Field(default_factory=list)
    merged_translation_unit: str | None = None
    split_outputs: list[SplitOutput] = Field(default_factory=list)
    input_manifest: list[dict] = Field(default_factory=list)
    failure_excerpt: str | None = None
    project_verification: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    name: str
    status: str
    live_capabilities: dict
    available_models: list[str]
    demo_case_count: int


class SpectoolInjectRequest(BaseModel):
    file_id: str
    relative_path: str | None = None
    function_name: str | None = None
    contract: str | None = None
    loop_specs: list[dict[str, Any]] | None = None


class SpectoolGenerateRequest(BaseModel):
    file_id: str
    relative_path: str | None = None
    function_name: str
    model_name: str = "qwen-turbo"
    inject_result: bool = True


class SpectoolSliceRequest(BaseModel):
    file_id: str
    function_name: str
    mode: Literal["inline", "stub"] = "inline"


class SpectoolVerifyRequest(BaseModel):
    file_id: str
    relative_path: str | None = None
    source: str | None = None
    timeout_sec: int = Field(default=8, ge=1, le=500)


class SpectoolAdmitRequest(BaseModel):
    file_id: str
    relative_path: str | None = None
    source: str | None = None


class SpectoolLocateRequest(BaseModel):
    file_id: str
    wp_text: str
    source_basename: str | None = None
