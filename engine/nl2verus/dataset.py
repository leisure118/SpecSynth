from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "data" / "NL2VBench.jsonl"
DATASET_PATH = Path(os.getenv("NL2VERUS_DATASET_PATH", str(DEFAULT_DATASET_PATH))).expanduser().resolve()


@lru_cache(maxsize=1)
def load_tasks() -> tuple[dict[str, Any], ...]:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    tasks: list[dict[str, Any]] = []
    with DATASET_PATH.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                task = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}") from exc
            tasks.append(task)
    return tuple(tasks)


def summarize_task(task: dict[str, Any]) -> dict[str, Any]:
    description = str(task.get("description") or "")
    signature = str(task.get("function_signature") or "")
    if not signature:
        signature = description.strip().splitlines()[-1] if description.strip() else ""
    return {
        "sample_id": task.get("sample_id"),
        "category": task.get("category") or "Uncategorized",
        "description": description,
        "function_signature": signature,
    }
