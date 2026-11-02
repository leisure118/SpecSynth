import time
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import app
from apps.api.app import demo_cases as demo_cases_module
from apps.api.app.demo_cases import get_demo_case
from apps.api.app.service import RunManager


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "ACSL AGENT"
    assert payload["demo_case_count"] >= 3
    assert "single_available" in payload["live_capabilities"]
    assert "termination_available" in payload["live_capabilities"]
    assert "veri_clang" in payload["live_capabilities"]


def test_demo_cases_endpoint() -> None:
    response = client.get("/api/v1/demo-cases")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["id"] == "sum_loop_100000" for item in items)
    assert any(item["id"] == "x509_inter_modular_replay" for item in items)
    openharmony_cases = [item for item in items if item["id"].startswith("openharmony_")]
    assert len(openharmony_cases) == 3
    assert all(item["modes"] == ["single"] for item in openharmony_cases)
    assert all(item["execution_mode"] == "replay" for item in openharmony_cases)
    assert all(item["sample_file"] and item["function_name"] and item["upstream_source"] for item in openharmony_cases)


X509_SPLIT_DIR = ROOT_DIR.parent / "x509-parser-bench-splited"


@pytest.mark.skipif(not (X509_SPLIT_DIR / "contracts.json").exists(), reason="external x509-parser-bench dataset is not installed")
def test_x509_showcase_returns_contract_and_upstream_source() -> None:
    response = client.get("/api/v1/showcases/x509/functions/parse_x509_cert_relaxed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pass"
    assert "assigns" in payload["contract"]
    assert "parse_x509_cert_relaxed" in payload["verified_source"]
    assert "parse_x509_cert_relaxed" in payload["source"]
    assert payload["source_path"] == "x509-parser.c"


@pytest.mark.skipif(not (X509_SPLIT_DIR / "contracts.json").exists(), reason="external x509-parser-bench dataset is not installed")
def test_every_x509_graph_function_has_both_code_views() -> None:
    contracts_path = X509_SPLIT_DIR / "contracts.json"
    function_names = json.loads(contracts_path.read_text(encoding="utf-8")).keys()
    assert len(function_names) == 212
    for function_name in function_names:
        response = client.get(f"/api/v1/showcases/x509/functions/{function_name}")
        assert response.status_code == 200, function_name
        payload = response.json()
        assert payload["verified_source"].strip(), function_name
        assert payload["source"].strip(), function_name
        assert payload["source_path"] != "未找到", function_name


@pytest.mark.parametrize("case_id", [
    "openharmony_circle_center_x",
    "openharmony_circle_radius",
    "openharmony_rect_edges",
])
def test_openharmony_examples_use_preverified_contract_without_llm(case_id: str) -> None:
    response = client.post(
        "/api/v1/runs/single",
        json={"demo_case_id": case_id, "model_name": "qwen-turbo"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    for _ in range(30):
        task = client.get(f"/api/v1/runs/{task_id}")
        assert task.status_code == 200
        assert task.json()["engine"] == "replay"
        if task.json()["status"] in {"pass", "fail", "timeout"}:
            break
        time.sleep(0.1)
    result = client.get(f"/api/v1/runs/{task_id}/result")
    assert result.status_code == 200
    payload = result.json()
    assert payload["status"] == "Pass"
    assert payload["command"].startswith("preset://openharmony/")
    assert payload["timing_stats"]["tokens_usage"] == 0
    assert payload["timing_stats"]["iteration_count"] == 0
    assert payload["engine_detail"]["runner"] == "replay-single"
    assert "requires option == \\null || \\valid(option);" in payload["result_code"]
    assert "LLM querying" not in payload["logs"]["raw"]


def test_overview_endpoint_exposes_competition_metrics() -> None:
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    payload = response.json()
    assert "headline_metrics" in payload
    assert "mode_rows" in payload
    assert "capability_rows" in payload
    assert "recent_evidence" in payload


def test_single_demo_run_reaches_pass() -> None:
    response = client.post("/api/v1/runs/single", json={"demo_case_id": "sum_loop_100000", "model_name": "qwen-turbo"})
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    for _ in range(30):
        task = client.get(f"/api/v1/runs/{task_id}")
        assert task.status_code == 200
        status = task.json()["status"]
        if status == "pass":
            break
        time.sleep(0.2)
    result = client.get(f"/api/v1/runs/{task_id}/result")
    assert result.status_code == 200
    payload = result.json()
    assert payload["status"] == "Pass"
    assert payload["specifications"]["loop_invariants"]
    assert "timing_stats" in payload
    assert "failure_analysis" in payload
    assert "task_summary" in payload
    artifacts = client.get(f"/api/v1/runs/{task_id}/artifacts").json()["items"]
    artifact_sizes = {item["relative_path"]: item["size"] for item in artifacts}
    assert artifact_sizes["artifacts/input/1.c"] == 215
    assert artifact_sizes["artifacts/output/single_result.c"] == 366
    # The replay transcript shape is versioned separately from the source
    # snapshot; assert it is present instead of freezing a byte count.
    assert artifact_sizes["artifacts/logs/run.log"] > 0
    assert payload["logs"]["raw"].startswith("[single]\n[DEBUG] target file name =  LLM4Veri/dataset/case4test/1.c")
    assert payload["logs"]["summary"][:2] == ["verifier-approved", "loop invariants synthesized"]
    assert payload["source_code"] == client.get(
        f"/api/v1/runs/{task_id}/artifacts/content",
        params={"relative_path": "artifacts/input/1.c"},
    ).json()["content"]
    artifact_content = client.get(
        f"/api/v1/runs/{task_id}/artifacts/content",
        params={"relative_path": "artifacts/logs/run.log"},
    )
    assert artifact_content.status_code == 200
    assert artifact_content.json()["content"] == payload["logs"]["raw"]


def test_single_replay_logs_match_live_transcript_shape() -> None:
    for case_id in ("manual_single_success_live", "arraymax_contract"):
        raw = RunManager._single_logs(get_demo_case(case_id))["raw"]
        assert raw.startswith("[single]\n[DEBUG] target file name =  ")
        assert "+++++++++++++++++++++++++++ start +++++++++++++++++++++++++++++" in raw
        assert "INFO:root:[CMD] Running `frama-c -wp -wp-rte " in raw
        assert "[wp] Proved goals:" in raw
        assert "@@@ Finished @@@" in raw
        assert raw.endswith("[done] status=Pass\n")


def test_recent_runs_endpoint_lists_created_tasks() -> None:
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    assert "items" in response.json()


def test_inter_modular_endpoint_creates_task() -> None:
    inter_response = client.post("/api/v1/runs/inter-modular", json={"demo_case_id": "x509_inter_modular_replay", "model_name": "qwen-turbo"})
    assert inter_response.status_code == 200
    task_id = inter_response.json()["task_id"]

    inter_task = client.get(f"/api/v1/runs/{task_id}")
    assert inter_task.status_code == 200
    assert inter_task.json()["mode"] == "inter-modular"

    for _ in range(30):
        task = client.get(f"/api/v1/runs/{task_id}")
        assert task.status_code == 200
        if task.json()["status"] == "pass":
            break
        time.sleep(0.2)

    result = client.get(f"/api/v1/runs/{task_id}/result")
    assert result.status_code == 200
    payload = result.json()
    assert payload["source_code"].startswith("/* === main.c === */")
    assert "/* === x509_utils.c === */" in payload["source_code"]
    assert "/* === x509_utils.h === */" in payload["source_code"]
    artifacts = client.get(f"/api/v1/runs/{task_id}/artifacts").json()["items"]
    assert [item["relative_path"] for item in artifacts] == [
        "artifacts/input/inter-modular/main.c",
        "artifacts/input/inter-modular/x509_utils.c",
        "artifacts/input/inter-modular/x509_utils.h",
        "artifacts/logs/run.log",
        "artifacts/output/merged_translation_unit.c",
    ]


def test_demo_cases_reload_when_config_changes(tmp_path) -> None:
    config_path = Path("configs/demo_cases.json")
    original_text = config_path.read_text(encoding="utf-8")
    original_payload = json.loads(original_text)

    try:
        initial = demo_cases_module.load_demo_cases()
        assert any(item["id"] == "manual_single_success_live" for item in initial)

        mutated_payload = []
        for item in original_payload:
            if item["id"] == "manual_single_success_live":
                updated = dict(item)
                updated["title"] = "热加载测试标题"
                mutated_payload.append(updated)
            else:
                mutated_payload.append(item)

        config_path.write_text(json.dumps(mutated_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        reloaded = demo_cases_module.load_demo_cases()
        current = next(item for item in reloaded if item["id"] == "manual_single_success_live")
        assert current["title"] == "热加载测试标题"
    finally:
        config_path.write_text(original_text, encoding="utf-8")
        demo_cases_module.load_demo_cases()
