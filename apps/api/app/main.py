from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from engine import spectool_adapter

from .config import APP_NAME, WEB_DIR, ensure_runtime_dirs, get_allowed_origins, get_available_models
from .demo_cases import list_demo_cases
from .schemas import (
    HealthResponse,
    RunCreateResponse,
    RunRequest,
    RunResult,
    RunTask,
    SpectoolGenerateRequest,
    SpectoolInjectRequest,
    SpectoolLocateRequest,
    SpectoolSliceRequest,
    SpectoolAdmitRequest,
    SpectoolVerifyRequest,
    UploadResponse,
)
from .service import RunManager
from .storage import JsonStore
from .workspace import create_workspace_router

ensure_runtime_dirs()
store = JsonStore()
manager = RunManager(store)
ARTIFACT_TEXT_EXTENSIONS = {
    ".c",
    ".h",
    ".i",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}

X509_BENCH_DIR = WEB_DIR.parents[2] / "x509-parser-bench"
X509_SPLIT_DIR = WEB_DIR.parents[2] / "x509-parser-bench-splited"


def _extract_c_function(source: str, function_name: str) -> str | None:
    """Return a function definition without exposing unrelated project files."""
    matcher = re.compile(rf"\b{re.escape(function_name)}\s*\(")
    for match in matcher.finditer(source):
        brace = source.find("{", match.end())
        semicolon = source.find(";", match.end())
        if brace < 0 or (semicolon >= 0 and semicolon < brace):
            continue
        depth = 0
        for index in range(brace, len(source)):
            char = source[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    line_start = source.rfind("\n", 0, match.start()) + 1
                    return source[line_start:index + 1]
    return None


@lru_cache(maxsize=256)
def _x509_function_details(function_name: str) -> dict:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", function_name):
        raise ValueError("Invalid function name.")
    contracts_path = X509_SPLIT_DIR / "contracts.json"
    if not contracts_path.exists():
        raise FileNotFoundError("X.509 verification data is not available.")
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    record = contracts.get(function_name)
    if record is None:
        raise KeyError(function_name)

    source_text = None
    source_path = None
    for candidate in sorted(X509_BENCH_DIR.glob("*.c")):
        extracted = _extract_c_function(candidate.read_text(encoding="utf-8", errors="replace"), function_name)
        if extracted:
            source_text = extracted
            source_path = candidate.name
            break
    split_relative_path = record.get("source", "")
    split_source = X509_SPLIT_DIR.parent / split_relative_path if split_relative_path else None
    split_text = split_source.read_text(encoding="utf-8", errors="replace") if split_source and split_source.exists() else ""
    if not split_text:
        split_text = "\n\n".join(part for part in (record.get("contract", ""), source_text or "") if part)
        split_relative_path = "由 contracts.json 规约与原始函数组合展示"
    return {
        "name": function_name,
        "signature": record.get("signature", ""),
        "contract": record.get("contract", ""),
        "verified_source": split_text,
        "verified_source_path": split_relative_path,
        "source": source_text or "/* 未在 x509-parser-bench 中找到该函数定义。 */",
        "source_path": source_path or "未找到",
        "status": record.get("status", "unknown"),
        "proved": record.get("proved", "N/A"),
        "failed_reason": record.get("failed_reason"),
    }

app = FastAPI(title=APP_NAME, version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    capabilities = manager.refresh_capabilities()
    return HealthResponse(
        name=APP_NAME,
        status="ok",
        live_capabilities=capabilities.as_dict(),
        available_models=get_available_models(),
        demo_case_count=len(list_demo_cases()),
    )


@app.get("/api/v1/models")
def models() -> dict:
    return {"models": get_available_models()}


@app.get("/api/v1/spectool/capabilities")
def spectool_capabilities() -> dict:
    payload = spectool_adapter.capabilities().as_dict()
    payload["available_models"] = get_available_models()
    return payload


@app.post("/api/v1/spectool/files/upload", response_model=UploadResponse)
async def spectool_upload_file(file: UploadFile = File(...)) -> UploadResponse:
    try:
        payload = await file.read()
        return UploadResponse.model_validate(spectool_adapter.create_upload(file.filename or "source.c", payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/files/upload-bundle", response_model=UploadResponse)
async def spectool_upload_bundle(
    files: list[UploadFile] = File(...),
    manifest: str = Form(...),
    root_dir: str | None = Form(default=None),
) -> UploadResponse:
    try:
        manifest_items = json.loads(manifest)
        if not isinstance(manifest_items, list) or len(files) != len(manifest_items):
            raise ValueError("Bundle manifest length does not match uploaded file count.")
        items = []
        for file, item in zip(files, manifest_items, strict=False):
            items.append({
                "relative_path": item.get("relative_path") or file.filename,
                "payload": await file.read(),
            })
        return UploadResponse.model_validate(spectool_adapter.create_bundle(items, root_dir=root_dir))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/spectool/files/{file_id}")
def spectool_files(file_id: str) -> dict:
    try:
        return {"file_id": file_id, "items": spectool_adapter.list_bundle_files(file_id)}
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/spectool/extract")
def spectool_extract(file_id: str, relative_path: str | None = None) -> dict:
    try:
        return spectool_adapter.extract_functions(file_id, relative_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/extract-one")
def spectool_extract_one(file_id: str, function_name: str, relative_path: str | None = None) -> dict:
    try:
        return spectool_adapter.extract_function(file_id, function_name, relative_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/list-functions")
def spectool_list_functions(file_id: str) -> dict:
    try:
        return spectool_adapter.list_project_functions(file_id)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/slice")
def spectool_slice(payload: SpectoolSliceRequest) -> dict:
    try:
        return spectool_adapter.generate_slice(payload.file_id, payload.function_name, payload.mode)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/inject")
def spectool_inject(payload: SpectoolInjectRequest) -> dict:
    try:
        return spectool_adapter.inject_annotations(
            payload.file_id,
            payload.relative_path,
            payload.function_name,
            payload.contract,
            payload.loop_specs,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/generate")
def spectool_generate(payload: SpectoolGenerateRequest) -> dict:
    try:
        return spectool_adapter.generate_annotations(
            payload.file_id,
            payload.relative_path,
            payload.function_name,
            payload.model_name,
            payload.inject_result,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/check-admit")
def spectool_check_admit(payload: SpectoolAdmitRequest) -> dict:
    try:
        return spectool_adapter.check_admits(payload.file_id, payload.relative_path, payload.source)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/verify")
def spectool_verify(payload: SpectoolVerifyRequest) -> dict:
    try:
        return spectool_adapter.verify(payload.file_id, payload.relative_path, payload.timeout_sec, payload.source)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/spectool/locate-fail")
def spectool_locate_fail(payload: SpectoolLocateRequest) -> dict:
    try:
        return spectool_adapter.locate_failures(payload.file_id, payload.wp_text, payload.source_basename)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/spectool/artifacts/{file_id}")
def spectool_artifacts(file_id: str) -> dict:
    try:
        return spectool_adapter.list_outputs(file_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/spectool/artifacts/{file_id}/{artifact_id}")
def spectool_artifact(file_id: str, artifact_id: str) -> dict:
    try:
        return spectool_adapter.read_output(file_id, artifact_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/demo-cases")
def demo_cases() -> dict:
    return {"items": list_demo_cases()}


@app.get("/api/v1/showcases/x509/functions/{function_name}")
def x509_function_details(function_name: str) -> dict:
    """Serve one X.509 function's checked and upstream views for the demo graph."""
    try:
        return _x509_function_details(function_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Function is not part of the X.509 verification set.") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/v1/overview")
def overview() -> dict:
    return manager.overview()


@app.post("/api/v1/files/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.endswith(".c"):
        raise HTTPException(status_code=400, detail="Only .c files are supported in the MVP.")
    payload = await file.read()
    meta = store.create_upload(file.filename, payload)
    return UploadResponse.model_validate(meta)


@app.post("/api/v1/files/upload-bundle", response_model=UploadResponse)
async def upload_bundle(
    files: list[UploadFile] = File(...),
    manifest: str = Form(...),
    root_dir: str | None = Form(default=None),
) -> UploadResponse:
    try:
        manifest_items = json.loads(manifest)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid bundle manifest: {exc}") from exc
    if len(files) != len(manifest_items):
        raise HTTPException(status_code=400, detail="Bundle manifest length does not match uploaded file count.")

    bundle_items = []
    for file, item in zip(files, manifest_items, strict=False):
        filename = item.get("relative_path") or file.filename
        if not filename or not str(filename).endswith((".c", ".h")):
            raise HTTPException(status_code=400, detail="Bundle upload supports only .c and .h files.")
        payload = await file.read()
        bundle_items.append({"relative_path": filename, "payload": payload})

    meta = store.create_bundle_upload(bundle_items, root_dir=root_dir)
    return UploadResponse.model_validate(meta)


def _submit_run(mode: str, payload: RunRequest) -> RunCreateResponse:
    task = manager.submit(mode, payload)
    return RunCreateResponse(task_id=task.task_id, status=task.status, detail=f"{mode} task submitted")


@app.post("/api/v1/runs/single", response_model=RunCreateResponse)
def run_single(payload: RunRequest) -> RunCreateResponse:
    return _submit_run("single", payload)


@app.post("/api/v1/runs/termination", response_model=RunCreateResponse)
def run_termination(payload: RunRequest) -> RunCreateResponse:
    return _submit_run("termination", payload)


@app.post("/api/v1/runs/inter-modular")
def run_inter_modular(payload: RunRequest) -> RunCreateResponse:
    return _submit_run("inter-modular", payload)


@app.post("/api/v1/runs/batch", include_in_schema=False)
def run_batch(payload: RunRequest) -> RunCreateResponse:
    return _submit_run("batch", payload)


@app.get("/api/v1/runs")
def list_runs(limit: int = 20) -> dict:
    manager.recover_incomplete_tasks(limit=limit)
    return {"items": [task.model_dump(mode="json") for task in store.list_tasks(limit=limit)]}


@app.get("/api/v1/runs/{task_id}", response_model=RunTask)
def get_run(task_id: str) -> RunTask:
    task, _ = manager.ensure_materialized(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@app.get("/api/v1/runs/{task_id}/result", response_model=RunResult)
def get_run_result(task_id: str) -> RunResult:
    _, result = manager.ensure_materialized(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task result not ready.")
    return RunResult.model_validate(result)


@app.get("/api/v1/runs/{task_id}/artifacts")
def get_run_artifacts(task_id: str) -> dict:
    task = store.read_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"items": store.list_artifacts(task_id)}


@app.get("/api/v1/runs/{task_id}/artifacts/content")
def get_run_artifact_content(task_id: str, relative_path: str) -> dict:
    task = store.read_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    normalized_path = relative_path.replace("\\", "/")
    if not normalized_path.startswith("artifacts/"):
        raise HTTPException(status_code=403, detail="Only artifact files can be previewed.")
    if not any(normalized_path.lower().endswith(ext) for ext in ARTIFACT_TEXT_EXTENSIONS):
        raise HTTPException(status_code=403, detail="Artifact preview is limited to approved text formats.")
    payload = manager._read_and_upgrade_artifact_log(task, relative_path)
    if payload is None:
        raise HTTPException(status_code=404, detail="Artifact content not available.")
    return payload


@app.get("/api/v1/runs/{task_id}/visualization")
def get_visualization(task_id: str) -> dict:
    task = store.read_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {
        "task_id": task_id,
        "status": task.status,
        "phases": [phase.model_dump(mode="json") for phase in task.phases],
    }


app.include_router(create_workspace_router(manager, store))


if WEB_DIR.exists():
    if (WEB_DIR / "brand").exists():
        app.mount("/brand", StaticFiles(directory=str(WEB_DIR / "brand")), name="web-brand")
    if (WEB_DIR / "fonts").exists():
        app.mount("/fonts", StaticFiles(directory=str(WEB_DIR / "fonts")), name="web-fonts")
    if (WEB_DIR / "dist").exists():
        app.mount("/dist", StaticFiles(directory=str(WEB_DIR / "dist")), name="web-dist")
    if (WEB_DIR / "samples").exists():
        app.mount("/samples", StaticFiles(directory=str(WEB_DIR / "samples")), name="web-samples")


@app.get("/{full_path:path}")
def serve_web(full_path: str) -> FileResponse:
    if full_path == "src" or full_path.startswith("src/"):
        raise HTTPException(status_code=404, detail="Static source assets are not exposed.")
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Web assets have not been generated yet.")
