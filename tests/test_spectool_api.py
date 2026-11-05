from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import app


client = TestClient(app)

SAMPLE_SOURCE = b"""int helper(int value) {
    return value + 1;
}

int sum_to(int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += helper(i);
    }
    return sum;
}
"""


def upload_sample() -> str:
    response = client.post(
        "/api/v1/spectool/files/upload",
        files={"file": ("sample.c", SAMPLE_SOURCE, "text/x-c")},
    )
    assert response.status_code == 200
    return response.json()["file_id"]


def upload_malformed_source() -> str:
    source = b'''#include<limits.h>\n\nint test(int x) {\n    int a = x;\n    int y = 0;\n\n    while(a != 0) {\n        y = y + 1;\n        a = a - 1;\n    }\n    return y;\n}\n\n/*@\n  int main() { /*@ requires true;\n  ensures true;\n  */ };\n*/\nint main() {\n    int num = test(3);\n    //@ assert num == 3;\n    return 0;\n}\n'''
    response = client.post(
        "/api/v1/spectool/files/upload",
        files={"file": ("bad.c", source, "text/x-c")},
    )
    assert response.status_code == 200
    return response.json()["file_id"]


def test_spectool_capabilities_and_extract() -> None:
    capabilities = client.get("/api/v1/spectool/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["package_available"] is True

    file_id = upload_sample()
    response = client.post("/api/v1/spectool/extract", params={"file_id": file_id})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert [item["name"] for item in payload["functions"]] == ["helper", "sum_to"]

    one = client.post(
        "/api/v1/spectool/extract-one",
        params={"file_id": file_id, "function_name": "sum_to"},
    )
    assert one.status_code == 200
    assert "int sum_to(int n)" in one.json()["source"]


def test_spectool_verify_prefers_host_runner() -> None:
    file_id = upload_sample()
    raw = {
        "result_type": "Pass_1_1",
        "stdout": "[wp] Proved goals:    1 / 1\n",
        "stderr": "",
        "elapsed_sec": 0.01,
        "returncode": 0,
        "timed_out": False,
    }
    with patch.dict(os.environ, {"SPECTOOL_VERIFY_RUNNER":"host"}), patch("engine.spectool_adapter.shutil.which", return_value="/usr/bin/frama-c"), patch(
        "engine.spectool_adapter.framac.run_framac_with_wp", return_value=raw
    ) as runner, patch("engine.spectool_adapter._container_tool_probe") as probe:
        response = client.post(
            "/api/v1/spectool/verify",
            json={"file_id": file_id, "relative_path": "sample.c", "timeout_sec": 1},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "Pass"
    assert payload["runner"] == "host"
    assert payload["container_service"] is None
    runner.assert_called_once()
    probe.assert_not_called()


def test_spectool_verify_uses_container_runner_when_forced() -> None:
    file_id = upload_sample()
    with patch.dict(os.environ, {"SPECTOOL_VERIFY_RUNNER": "container"}), patch(
        "engine.spectool_adapter._container_tool_probe"
    ) as probe, patch("engine.spectool_adapter._run_framac_in_container") as runner:
        probe.return_value = {
            "service": "autospec",
            "tools": {"frama_c": True, "veri_clang": True, "alt_ergo": True, "z3": True},
        }
        runner.return_value = {
            "result_type": "Pass_1_1",
            "stdout": "[wp] Proved goals:    1 / 1\n",
            "stderr": "",
            "elapsed_sec": 0.01,
            "returncode": 0,
            "timed_out": False,
        }

        response = client.post(
            "/api/v1/spectool/verify",
            json={"file_id": file_id, "relative_path": "sample.c", "timeout_sec": 1},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "Pass"
    assert payload["runner"] == "container"
    assert payload["container_service"] == "autospec"
    runner.assert_called_once()


def test_spectool_capabilities_prefer_host_when_available() -> None:
    with patch.dict(os.environ, {"SPECTOOL_VERIFY_RUNNER":"host"}), patch("engine.spectool_adapter._local_tool_probe") as local, patch(
        "engine.spectool_adapter._container_tool_probe"
    ) as probe:
        local.return_value = {"frama_c": True, "veri_clang": False, "alt_ergo": True, "z3": True}
        probe.return_value = {"service": None, "tools": {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}}
        payload = client.get("/api/v1/spectool/capabilities").json()

    assert payload["verify_ready"] is True
    assert payload["verify_runner"] == "host"
    assert payload["container_service"] is None
    assert payload["tool_sources"]["local"]["frama_c"] is True


def test_spectool_capabilities_report_container_verify_runner() -> None:
    with patch.dict(os.environ, {"SPECTOOL_VERIFY_RUNNER":"container"}), patch("engine.spectool_adapter._local_tool_probe") as local, patch(
        "engine.spectool_adapter._container_tool_probe"
    ) as probe:
        local.return_value = {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}
        probe.return_value = {
            "service": "autospec",
            "tools": {"frama_c": True, "veri_clang": True, "alt_ergo": True, "z3": True},
        }
        payload = client.get("/api/v1/spectool/capabilities").json()

    assert payload["verify_ready"] is True
    assert payload["verify_runner"] == "container"
    assert payload["container_service"] == "autospec"
    assert payload["tool_sources"]["local"]["frama_c"] is False
    assert payload["tool_sources"]["container"]["frama_c"] is True


def test_spectool_generate_annotations_with_llm_and_injects() -> None:
    file_id = upload_sample()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"contract":"requires n >= 0;\\nensures \\\\result >= 0;","loop_specs":[{"line":7,"acsl":"loop invariant 0 <= i <= n;"}],"notes":["generated"]}'))]
    mock_response.usage = Mock(total_tokens=42)

    mock_config = Mock(
        api_key="test-key",
        base_url="https://example.test/v1",
        model_name="qwen-turbo",
        params={"temperature": 0.1, "max_tokens": 1200, "timeout": 30},
    )
    with patch("engine.spectool_llm.ConfigLoader.get_model_config", return_value=mock_config), patch("engine.spectool_llm.OpenAI") as openai_cls:
        openai_cls.return_value.chat.completions.create.return_value = mock_response
        response = client.post(
            "/api/v1/spectool/generate",
            json={"file_id": file_id, "function_name": "sum_to", "model_name": "qwen-turbo", "inject_result": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "qwen-turbo"
    assert payload["contract"].startswith("requires n >= 0;")
    assert payload["loop_specs"] == [{"line": 7, "acsl": "loop invariant 0 <= i <= n;"}]
    assert payload["tokens_usage"] == 42
    assert payload["generation_mode"] == "llm"
    assert payload["injected_contract"] is True
    assert payload["injected_loops"] == 1
    assert "/*@" in payload["source"]
    assert "loop invariant 0 <= i <= n;" in payload["source"]
    assert payload["artifact_id"].endswith(".json")
    assert payload["source_artifact_id"].endswith(".c")


def test_spectool_generate_handles_malformed_acsl_source() -> None:
    file_id = upload_malformed_source()
    response = client.post(
        "/api/v1/spectool/generate",
        json={"file_id": file_id, "function_name": "test", "model_name": "qwen-turbo", "inject_result": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["generation_mode"] == "spectool-template"
    assert payload["contract"] == "requires x >= 0;\nassigns \\nothing;\nensures \\result == x;"
    assert "int main() { /*@ requires true;" not in payload["source"]
    assert "loop invariant 0 <= a <= x;" in payload["source"]
    assert "main" in payload["source"]


def test_spectool_inject_admit_and_slice() -> None:
    file_id = upload_sample()
    injected = client.post(
        "/api/v1/spectool/inject",
        json={
            "file_id": file_id,
            "function_name": "sum_to",
            "contract": "requires n >= 0;\nensures \\result >= 0;",
            "loop_specs": [{"line": 7, "acsl": "loop invariant 0 <= i <= n;"}],
        },
    )
    assert injected.status_code == 200
    payload = injected.json()
    assert payload["injected_contract"] is True
    assert payload["injected_loops"] == 1
    assert "/*@" in payload["source"]
    assert "loop invariant 0 <= i <= n;" in payload["source"]

    admit = client.post(
        "/api/v1/spectool/check-admit",
        json={"file_id": file_id, "source": "//@ admit x > 0;\n"},
    )
    assert admit.status_code == 200
    assert admit.json()["illegal_admits"] == 1

    sliced = client.post(
        "/api/v1/spectool/slice",
        json={"file_id": file_id, "function_name": "sum_to", "mode": "inline"},
    )
    artifacts = client.get(f"/api/v1/spectool/artifacts/{file_id}")
    assert artifacts.status_code == 200
    artifact_ids = [item["artifact_id"] for item in artifacts.json()["items"]]
    assert sliced.json()["artifact_id"] in artifact_ids

    content = client.get(f"/api/v1/spectool/artifacts/{file_id}/{sliced.json()['artifact_id']}")
    assert content.status_code == 200
    assert "int sum_to(int n)" in content.json()["content"]
