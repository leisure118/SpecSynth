from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import app


def wait_for_task(client: TestClient, task_id: str, timeout_s: int) -> dict:
    started = time.time()
    while time.time() - started < timeout_s:
        task = client.get(f"/api/v1/runs/{task_id}").json()
        if task["status"] in {"pass", "fail", "invalid", "timeout", "unavailable"}:
            return task
        time.sleep(1)
    raise TimeoutError(f"Task {task_id} did not finish within {timeout_s}s.")


def run_case(client: TestClient, endpoint: str, payload: dict, timeout_s: int) -> None:
    response = client.post(endpoint, json=payload)
    response.raise_for_status()
    task_id = response.json()["task_id"]
    task = wait_for_task(client, task_id, timeout_s=timeout_s)
    result = client.get(f"/api/v1/runs/{task_id}/result")
    result.raise_for_status()
    body = result.json()
    print(f"[{endpoint}] {task_id}")
    print(f"task_status: {task['status']}")
    print(f"result_status: {body['status']}")
    print(f"summary: {body['summary']}")
    print(f"elapsed_ms: {body.get('elapsed_ms')}")
    print(f"artifacts: {len(body['artifacts'])}")
    print("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ACSL AGENT demo cases through the unified API.")
    parser.add_argument("--with-batch", action="store_true", help="Additionally run the hidden batch API path for CLI verification.")
    args = parser.parse_args()

    client = TestClient(app)
    run_case(
        client,
        "/api/v1/runs/single",
        {"demo_case_id": "sum_loop_100000", "model_name": "qwen-turbo"},
        timeout_s=30,
    )
    run_case(
        client,
        "/api/v1/runs/termination",
        {"demo_case_id": "bubble_sort_total_correctness", "model_name": "qwen-turbo"},
        timeout_s=30,
    )
    run_case(
        client,
        "/api/v1/runs/inter-modular",
        {"demo_case_id": "x509_inter_modular_replay", "model_name": "qwen-turbo"},
        timeout_s=30,
    )

    if args.with_batch:
        run_case(
            client,
            "/api/v1/runs/batch",
            {"demo_case_id": "test_folder_batch_live", "model_name": "qwen-turbo"},
            timeout_s=360,
        )


if __name__ == "__main__":
    main()
