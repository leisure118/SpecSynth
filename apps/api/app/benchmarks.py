"""HTTP interface for read-only benchmark snapshots and re-run tasks."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from acsl.application.benchmarks import (
    BenchmarkCatalog,
    BenchmarkError,
    BenchmarkRunRequest,
    BenchmarkRunService,
)
from acsl.infrastructure.settings import settings

DATA_DIR = settings.root_dir / "resources" / "benchmarks"
_catalog = BenchmarkCatalog(DATA_DIR)
router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarks"])


def _http(exc: BenchmarkError) -> HTTPException:
    return HTTPException(exc.status_code, str(exc))


def snapshot(benchmark_id):
    try:
        return _catalog.snapshot(benchmark_id)
    except BenchmarkError as exc:
        raise _http(exc) from exc


def catalog():
    return _catalog.catalog()


def detail(benchmark_id: str):
    try:
        return _catalog.detail(benchmark_id)
    except BenchmarkError as exc:
        raise _http(exc) from exc


def file_detail(benchmark_id: str, file: str):
    try:
        return _catalog.file_detail(benchmark_id, file)
    except BenchmarkError as exc:
        raise _http(exc) from exc


@router.get("")
def list_catalog():
    return catalog()


@router.get("/{benchmark_id}")
def benchmark_detail(benchmark_id: str):
    return detail(benchmark_id)


@router.get("/{benchmark_id}/file")
def benchmark_file(benchmark_id: str, file: str):
    return file_detail(benchmark_id, file)


def create_benchmark_runs_router(manager, store):
    service = BenchmarkRunService(manager, store, _catalog)
    runs_router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmark-runs"])

    def call(function, *args):
        try:
            return function(*args)
        except BenchmarkError as exc:
            raise _http(exc) from exc

    @runs_router.get("/{benchmark_id}/runs")
    def list_runs(benchmark_id: str, file: str):
        return {"items": call(service.list_runs, benchmark_id, file)}

    @runs_router.post("/{benchmark_id}/runs", status_code=201)
    def submit_run(benchmark_id: str, body: BenchmarkRunRequest):
        return call(service.submit_run, benchmark_id, body)

    return runs_router
