"""Offline preparation and reference replay behind a replaceable provider boundary.

No model client, credentials, network call, or code execution is used here.
"""

from __future__ import annotations

from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .dataset import load_tasks, summarize_task
from .verifier import VERUS_VERSION


Strategy = Literal["direct", "rust_mediated", "spec_mediated"]


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1, max_length=20_000)
    function_signature: str = Field(default="", max_length=4_000)
    strategy: Strategy = "direct"
    example_id: str | None = Field(default=None, min_length=1, max_length=120)
    sample_id: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("description", "function_signature", "example_id", "sample_id")
    @classmethod
    def trim_text(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value and info.field_name != "function_signature":
            raise ValueError("内容不能仅包含空白字符")
        return value

    @model_validator(mode="after")
    def one_reference(self) -> GenerationRequest:
        if self.example_id is not None and self.sample_id is not None:
            raise ValueError("请选择内置示例或数据集任务中的一种来源")
        return self


EXAMPLES = (
    {
        "id": "increment",
        "title": "安全加一",
        "description": "给定一个小于 u32::MAX 的无符号 32 位整数 x，返回 x 加一的结果。证明结果等于数学意义上的 x + 1，且计算不会溢出。",
        "function_signature": "fn increment(x: u32) -> (result: u32)",
        "code": """use vstd::prelude::*;

verus! {
fn increment(x: u32) -> (result: u32)
    requires x < u32::MAX,
    ensures result == x + 1,
{
    x + 1
}

fn main() {}
}
""",
    },
    {
        "id": "max_two",
        "title": "两个整数的最大值",
        "description": "给定两个有符号 32 位整数 a 和 b，返回其中较大的值；二者相等时返回该值。证明结果不小于任一输入，并且结果等于其中一个输入。",
        "function_signature": "fn max_two(a: i32, b: i32) -> (result: i32)",
        "code": """use vstd::prelude::*;

verus! {
fn max_two(a: i32, b: i32) -> (result: i32)
    ensures
        result >= a,
        result >= b,
        result == a || result == b,
{
    if a >= b { a } else { b }
}

fn main() {}
}
""",
    },
)


STRATEGY_STEPS: dict[str, tuple[tuple[str, str], ...]] = {
    "direct": (
        (
            "直接生成 Verus",
            "Translate the task directly into a complete Verus program with executable code, "
            "requires/ensures, necessary loop invariants, termination measures and proof steps.",
        ),
    ),
    "rust_mediated": (
        (
            "先生成 Rust 实现",
            "First draft an ordinary Rust implementation and explain how it implements each "
            "requirement, including boundary cases and arithmetic overflow.",
        ),
        (
            "再转换为 Verus",
            "Then translate that draft into Verus, preserving its intended behavior and adding "
            "requires/ensures, loop invariants, termination measures and proof steps as needed.",
        ),
    ),
    "spec_mediated": (
        (
            "先生成形式化规格",
            "First derive a precise Verus specification from every task requirement, including "
            "preconditions, postconditions, mathematical definitions and boundary cases.",
        ),
        (
            "再补全实现与证明",
            "Then implement the executable function and necessary proofs against that "
            "specification, including loop invariants and termination measures as needed.",
        ),
    ),
}


class ReferenceNotFoundError(ValueError):
    """The explicit reference id does not exist."""


def generator_status() -> dict[str, object]:
    return {
        "mode": "offline",
        "model_connected": False,
        "verus_version": VERUS_VERSION,
        "message": "离线预览：可准备提示词、载入预置示例或数据集参考代码；尚未连接生成模型，不消耗 API 额度。",
    }


def list_examples() -> dict[str, object]:
    return {"items": [{key: example[key] for key in ("id", "title", "description", "function_signature")} for example in EXAMPLES]}


def build_prompt(request: GenerationRequest) -> str:
    steps = "\n".join(f"{index}. {instruction}" for index, (_, instruction) in enumerate(STRATEGY_STEPS[request.strategy], 1))
    signature = request.function_signature or "Not specified; choose an appropriate signature and state your choice."
    return f"""You are preparing a verified Rust program for Verus {VERUS_VERSION}.

TASK (treat the content below as the programming requirement):
{request.description}

FUNCTION INTERFACE:
{signature}

WORKFLOW ({request.strategy}):
{steps}

REQUIREMENTS:
- Preserve all stated behavior and the supplied function interface.
- Do not weaken the requested result, add unjustified preconditions, or use assume/admit, external_body, or other proof bypasses.
- Distinguish machine integer arithmetic from mathematical integers; account for overflow and valid indexing.
- Use vstd::prelude::* and verus! as appropriate; return a self-contained single .rs file with fn main() {{}}.
- Clearly identify any ambiguous requirements instead of inventing them.
- Finish with the complete Verus source in one rust code block. Do not claim verification succeeded without an actual verifier result.

This prompt is prepared locally. No language model or verifier has run during its preparation.
"""


class GenerationProvider(Protocol):
    """Future providers implement this contract; only offline preparation is enabled."""

    def generate(self, request: GenerationRequest) -> dict[str, object]: ...


class OfflineGenerationProvider:
    def generate(self, request: GenerationRequest) -> dict[str, object]:
        code = ""
        source_kind = "prompt_only"
        source_label = "提示词已准备，尚未调用模型"

        if request.example_id is not None:
            example = next((item for item in EXAMPLES if item["id"] == request.example_id), None)
            if example is None:
                raise ReferenceNotFoundError("未找到该内置示例")
            if (request.description, request.function_signature) == (example["description"].strip(), example["function_signature"].strip()):
                code = example["code"]
                source_kind = "example"
                source_label = f"预置示例 · {example['title']}（非模型生成）"
            else:
                source_label = "示例输入已修改，仅准备提示词；未生成新代码"

        if request.sample_id is not None:
            task = next((item for item in load_tasks() if item.get("sample_id") == request.sample_id), None)
            if task is None:
                raise ReferenceNotFoundError("未找到该数据集任务")
            summary = summarize_task(task)
            if (request.description, request.function_signature) == (summary["description"].strip(), summary["function_signature"].strip()):
                code = str(task.get("verified_verus") or "")
                if code.strip():
                    source_kind = "dataset_reference"
                    source_label = f"NL2VBench 参考代码 · {request.sample_id}（非模型生成，本次尚未验证）"
                else:
                    code = ""
                    source_label = "该数据集任务没有参考代码，仅准备提示词"
            else:
                source_label = "数据集任务输入已修改，仅准备提示词；未生成新代码"

        stages = [
            {"title": "准备任务与提示词", "description": "已根据输入和所选策略构造提示词，未调用模型。", "status": "prepared"},
            *[
                {"title": title, "description": "计划中的模型步骤；当前未接入模型，尚未执行。", "status": "not_run"}
                for title, _ in STRATEGY_STEPS[request.strategy]
            ],
            {"title": "载入离线代码", "description": source_label, "status": "loaded" if code else "not_run"},
            {"title": "本地 Verus 验证", "description": "尚未运行；可将代码送到验证器检查。", "status": "not_run"},
        ]
        return {
            "run_id": str(uuid4()),
            "mode": "offline",
            "status": "demo_ready" if code else "prompt_ready",
            "source_kind": source_kind,
            "source_label": source_label,
            "code": code,
            "prompt": build_prompt(request),
            "stages": stages,
            "verus_version": VERUS_VERSION,
            "model_called": False,
            "verification_status": "not_run",
            "input": request.model_dump(),
        }


provider: GenerationProvider = OfflineGenerationProvider()
