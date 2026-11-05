from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent
DEFAULT_SPECTOOL_PACKAGE_DIR = WORKSPACE_DIR / "spectool" / "spectool"
SPECTOOL_PACKAGE_DIR = Path(os.getenv("SPECTOOL_PACKAGE_DIR", str(DEFAULT_SPECTOOL_PACKAGE_DIR))).resolve()

if SPECTOOL_PACKAGE_DIR.exists() and str(SPECTOOL_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(SPECTOOL_PACKAGE_DIR))

try:
    from engine.spectool_core import admit, cextract, framac, inject as inject_mod, locate, slice_engine
    from engine import spectool_llm
except ImportError as local_exc:  # pragma: no cover - compatibility fallback for external installs
    try:
        from CLI.vendored import admit, cextract, framac, inject as inject_mod, locate, slice_engine
        from engine import spectool_llm
    except ImportError as external_exc:  # pragma: no cover - exercised by doctor/status when absent
        admit = cextract = framac = inject_mod = locate = slice_engine = spectool_llm = None
        _IMPORT_ERROR = f"local core: {local_exc}; external fallback: {external_exc}"
    else:
        _IMPORT_ERROR = None
else:
    _IMPORT_ERROR = None


SPECTOOL_RUNTIME_DIR = ROOT_DIR / "runtime" / "spectool"
UPLOADS_DIR = SPECTOOL_RUNTIME_DIR / "uploads"
OUTPUTS_DIR = SPECTOOL_RUNTIME_DIR / "outputs"
TEXT_EXTENSIONS = {".c", ".h", ".i", ".json", ".log", ".txt"}
CONTAINER_PROBE_CACHE_TTL_SEC = max(int(os.getenv("SPECTOOL_CONTAINER_PROBE_CACHE_TTL", "30") or "30"), 0)
_CONTAINER_PROBE_CACHE: dict[str, Any] | None = None
_CONTAINER_PROBE_CACHE_AT = 0.0


@dataclass(frozen=True)
class SpectoolCapabilities:
    package_available: bool
    package_dir: str
    frama_c: bool
    veri_clang: bool
    alt_ergo: bool
    z3: bool
    frama_c_container: bool = False
    veri_clang_container: bool = False
    alt_ergo_container: bool = False
    z3_container: bool = False
    frama_c_local: bool = False
    veri_clang_local: bool = False
    alt_ergo_local: bool = False
    z3_local: bool = False
    verify_runner: str | None = None
    container_service: str | None = None

    @property
    def deterministic_ready(self) -> bool:
        return self.package_available

    @property
    def verify_ready(self) -> bool:
        return (
            self.package_available
            and self.verify_runner in {"host", "container"}
            and self.frama_c
            and (self.alt_ergo or self.z3)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_available": self.package_available,
            "package_dir": self.package_dir,
            "deterministic_ready": self.deterministic_ready,
            "verify_ready": self.verify_ready,
            "verify_runner": self.verify_runner,
            "container_service": self.container_service,
            "tools": {
                "frama_c": self.frama_c,
                "veri_clang": self.veri_clang,
                "alt_ergo": self.alt_ergo,
                "z3": self.z3,
            },
            "tool_sources": {
                "local": {
                    "frama_c": self.frama_c_local,
                    "veri_clang": self.veri_clang_local,
                    "alt_ergo": self.alt_ergo_local,
                    "z3": self.z3_local,
                },
                "container": {
                    "frama_c": self.frama_c_container,
                    "veri_clang": self.veri_clang_container,
                    "alt_ergo": self.alt_ergo_container,
                    "z3": self.z3_container,
                },
            },
            "import_error": _IMPORT_ERROR,
        }


def ensure_spectool_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def _local_tool_probe() -> dict[str, bool]:
    configured = (os.getenv("SPECTOOL_FRAMAC", "") or "").strip()
    if configured:
        frama_c = Path(configured).exists() or shutil.which(configured) is not None
    else:
        frama_c = shutil.which("frama-c") is not None
    return {
        "frama_c": frama_c,
        "veri_clang": shutil.which("veri-clang") is not None,
        "alt_ergo": shutil.which("alt-ergo") is not None,
        "z3": shutil.which("z3") is not None,
    }


def capabilities() -> SpectoolCapabilities:
    mode=(os.getenv("SPECTOOL_VERIFY_RUNNER","host") or "host").strip().lower()
    container = _container_tool_probe() if mode in ('auto','container') else {"service":None,"tools":dict.fromkeys(('frama_c','veri_clang','alt_ergo','z3'),False)}
    container_tools = container["tools"]
    local = _local_tool_probe()
    host_verify_ready = mode != "container" and local["frama_c"] and (local["alt_ergo"] or local["z3"])
    container_verify_ready = container_tools["frama_c"] and (container_tools["alt_ergo"] or container_tools["z3"])
    verify_runner = "host" if host_verify_ready else "container" if container_verify_ready else None
    return SpectoolCapabilities(
        package_available=_IMPORT_ERROR is None,
        package_dir=str(SPECTOOL_PACKAGE_DIR),
        frama_c=local["frama_c"] or container_tools["frama_c"],
        veri_clang=local["veri_clang"] or container_tools["veri_clang"],
        alt_ergo=local["alt_ergo"] or container_tools["alt_ergo"],
        z3=local["z3"] or container_tools["z3"],
        frama_c_container=container_tools["frama_c"],
        veri_clang_container=container_tools["veri_clang"],
        alt_ergo_container=container_tools["alt_ergo"],
        z3_container=container_tools["z3"],
        frama_c_local=local["frama_c"],
        veri_clang_local=local["veri_clang"],
        alt_ergo_local=local["alt_ergo"],
        z3_local=local["z3"],
        verify_runner=verify_runner,
        container_service=container["service"] if verify_runner == "container" else None,
    )


def _container_services() -> list[str]:
    raw = os.getenv("SPECTOOL_VERIFY_CONTAINER_SERVICES", "autospec,termination")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _container_env_setup() -> str:
    return " ; ".join(
        [
            "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
            "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
            "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
        ]
    )


def _container_tool_probe() -> dict[str, Any]:
    global _CONTAINER_PROBE_CACHE, _CONTAINER_PROBE_CACHE_AT
    now = time.monotonic()
    if (
        _CONTAINER_PROBE_CACHE is not None
        and CONTAINER_PROBE_CACHE_TTL_SEC > 0
        and now - _CONTAINER_PROBE_CACHE_AT <= CONTAINER_PROBE_CACHE_TTL_SEC
    ):
        return _CONTAINER_PROBE_CACHE

    aggregate = {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}
    selected_service = None
    for service in _container_services():
        tools = _probe_container_service_tools(service)
        for key, ready in tools.items():
            aggregate[key] = aggregate[key] or ready
        if selected_service is None and tools["frama_c"] and (tools["alt_ergo"] or tools["z3"]):
            selected_service = service
    result = {"tools": aggregate, "service": selected_service}
    _CONTAINER_PROBE_CACHE = result
    _CONTAINER_PROBE_CACHE_AT = now
    return result


def _probe_container_service_tools(service: str) -> dict[str, bool]:
    script = (
        _container_env_setup()
        + " ; "
        + "for item in frama-c veri-clang alt-ergo z3; do "
        + "if command -v $item >/dev/null 2>&1; then echo $item=1; else echo $item=0; fi; "
        + "done"
    )
    try:
        completed = subprocess.run(
            ["docker", "compose", "run", "--rm", "-T", service, "bash", "-lc", script],
            cwd=str(ROOT_DIR),
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}
    if completed.returncode != 0:
        return {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}
    values = {"frama_c": False, "veri_clang": False, "alt_ergo": False, "z3": False}
    name_map = {"frama-c": "frama_c", "veri-clang": "veri_clang", "alt-ergo": "alt_ergo", "z3": "z3"}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        name, raw_value = line.strip().split("=", 1)
        key = name_map.get(name)
        if key:
            values[key] = raw_value == "1"
    return values


def _sanitize_malformed_acsl_blocks(source: str) -> tuple[str, list[str]]:
    """Remove legacy malformed ACSL comment blocks that wrap C code.

    Some upstream generators may emit fragments such as::

        /*@
          int main() { /*@ requires true;
          ensures true;
          */ };
        */

    C comments do not nest, so Frama-C parses the trailing ``}; */`` as C code
    and verification fails before spectool's generated annotations are used. We
    only drop ACSL comment blocks that either contain nested block comments or a
    C function definition, leaving normal ACSL contracts/invariants untouched.
    """
    lines = source.splitlines(keepends=True)
    output: list[str] = []
    warnings: list[str] = []
    function_def_pattern = re.compile(
        r"\b(?:void|char|short|int|long|float|double|signed|unsigned|static|extern|inline|const|struct\s+\w+|enum\s+\w+)"
        r"[\w\s\*]*\s+\w+\s*\([^;{}]*\)\s*\{"
    )
    i = 0
    while i < len(lines):
        line = lines[i]
        if "/*@" not in line:
            output.append(line)
            i += 1
            continue

        block = [line]
        opens = line.count("/*")
        closes = line.count("*/")
        nested = opens > 1
        contains_function_definition = bool(function_def_pattern.search(line))
        j = i + 1
        while j < len(lines) and closes < opens:
            block_line = lines[j]
            block.append(block_line)
            opens += block_line.count("/*")
            closes += block_line.count("*/")
            if block_line.count("/*"):
                nested = nested or opens > 1
            contains_function_definition = contains_function_definition or bool(function_def_pattern.search(block_line))
            j += 1

        block_text = "".join(block)
        if nested or contains_function_definition:
            start_line = i + 1
            end_line = i + len(block)
            warnings.append(f"removed malformed ACSL block at lines {start_line}-{end_line}")
        else:
            output.append(block_text)
        i = j

    return "".join(output), warnings


def require_package() -> None:
    if _IMPORT_ERROR is not None:
        raise RuntimeError(f"spectool package unavailable: {_IMPORT_ERROR}")


def create_upload(filename: str, payload: bytes) -> dict[str, Any]:
    ensure_spectool_dirs()
    suffix = Path(filename).suffix.lower()
    if suffix not in {".c", ".h"}:
        raise ValueError("spectool supports only .c and .h source files.")
    file_id = uuid.uuid4().hex[:12]
    target_dir = UPLOADS_DIR / file_id
    target_dir.mkdir(parents=True, exist_ok=False)
    target_path = target_dir / Path(filename).name
    decoded = payload.decode("utf-8", errors="replace")
    cleaned, warnings = _sanitize_malformed_acsl_blocks(decoded)
    target_path.write_text(cleaned, encoding="utf-8")
    stored_size = target_path.stat().st_size
    return {
        "file_id": file_id,
        "filename": target_path.name,
        "stored_path": str(target_path),
        "size": stored_size,
        "kind": "file",
        "warnings": warnings,
    }


def create_bundle(files: list[dict[str, Any]], root_dir: str | None = None) -> dict[str, Any]:
    ensure_spectool_dirs()
    file_id = uuid.uuid4().hex[:12]
    target_dir = UPLOADS_DIR / file_id
    target_dir.mkdir(parents=True, exist_ok=False)
    manifest = []
    total_size = 0
    for item in files:
        relative_path = _normalize_relative_path(str(item["relative_path"]))
        if Path(relative_path).suffix.lower() not in {".c", ".h"}:
            raise ValueError("spectool bundle upload supports only .c and .h files.")
        payload = item["payload"]
        decoded = payload.decode("utf-8", errors="replace")
        cleaned, warnings = _sanitize_malformed_acsl_blocks(decoded)
        target = target_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(cleaned, encoding="utf-8")
        stored_size = target.stat().st_size
        total_size += stored_size
        manifest_item = {"relative_path": relative_path, "stored_path": str(target), "size": stored_size}
        if warnings:
            manifest_item["warnings"] = warnings
        manifest.append(manifest_item)
    return {
        "file_id": file_id,
        "filename": root_dir or f"{file_id}_spectool_bundle",
        "stored_path": str(target_dir),
        "size": total_size,
        "kind": "bundle",
        "entry_count": len(manifest),
        "root_dir": root_dir,
        "manifest": manifest,
    }


def resolve_source_path(file_id: str, relative_path: str | None = None) -> Path:
    base = (UPLOADS_DIR / file_id).resolve()
    if not base.exists():
        raise FileNotFoundError(f"spectool upload not found: {file_id}")
    if relative_path:
        target = (base / _normalize_relative_path(relative_path)).resolve()
    else:
        candidates = [path for path in sorted(base.rglob("*")) if path.is_file() and path.suffix.lower() == ".c"]
        if not candidates:
            raise FileNotFoundError("no .c file found in spectool upload.")
        target = candidates[0].resolve()
    if base not in target.parents and target != base:
        raise ValueError("source path escapes spectool upload directory.")
    if target.suffix.lower() not in {".c", ".h"} or not target.is_file():
        raise FileNotFoundError("source file not found.")
    return target


def list_bundle_files(file_id: str) -> list[dict[str, Any]]:
    base = (UPLOADS_DIR / file_id).resolve()
    if not base.exists():
        raise FileNotFoundError(f"spectool upload not found: {file_id}")
    return [
        {
            "relative_path": path.relative_to(base).as_posix(),
            "size": path.stat().st_size,
            "kind": path.suffix.lower().lstrip("."),
        }
        for path in sorted(base.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".c", ".h"}
    ]


def extract_functions(file_id: str, relative_path: str | None = None) -> dict[str, Any]:
    require_package()
    source_path = resolve_source_path(file_id, relative_path)
    source = source_path.read_text(encoding="utf-8", errors="replace")
    functions = [
        {"name": name, "start_line": start, "end_line": end, "lines": end - start + 1}
        for name, _, start, end in cextract.extract_functions(source)
    ]
    return {
        "ok": True,
        "file_id": file_id,
        "relative_path": _relative_to_upload(file_id, source_path),
        "count": len(functions),
        "functions": functions,
    }


def extract_function(file_id: str, function_name: str, relative_path: str | None = None) -> dict[str, Any]:
    require_package()
    source_path = resolve_source_path(file_id, relative_path)
    source = source_path.read_text(encoding="utf-8", errors="replace")
    match = cextract.extract_one(source, function_name)
    if match is None:
        available = [name for name, _, _, _ in cextract.extract_functions(source)]
        raise ValueError(f"function '{function_name}' not found. Available: {', '.join(available)}")
    function_source, start, end = match
    return {
        "ok": True,
        "file_id": file_id,
        "relative_path": _relative_to_upload(file_id, source_path),
        "name": function_name,
        "start_line": start,
        "end_line": end,
        "source": function_source,
    }


def list_project_functions(file_id: str) -> dict[str, Any]:
    require_package()
    project_dir = (UPLOADS_DIR / file_id).resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"spectool upload not found: {file_id}")
    _, all_functions, _, _ = slice_engine.build_project_index(str(project_dir))
    functions = []
    for name, info in sorted(all_functions.items()):
        file_path = Path(info["file"]).resolve()
        functions.append(
            {
                "name": name,
                "relative_path": _relative_to_upload(file_id, file_path),
                "start_line": int(info["sig_start"]) + 1,
                "end_line": int(info["end"]) + 1,
                "lines": int(info["end"]) - int(info["sig_start"]) + 1,
            }
        )
    return {"ok": True, "file_id": file_id, "count": len(functions), "functions": functions}


def generate_slice(file_id: str, function_name: str, mode: str = "inline") -> dict[str, Any]:
    require_package()
    if mode not in {"inline", "stub"}:
        raise ValueError("slice mode must be inline or stub.")
    project_dir = (UPLOADS_DIR / file_id).resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"spectool upload not found: {file_id}")
    source = slice_engine.generate_slice(function_name, str(project_dir), mode)
    if source is None:
        raise ValueError(f"function '{function_name}' not found in project.")
    out_path = _new_output_path(file_id, f"{function_name}_{mode}_slice.c")
    out_path.write_text(source, encoding="utf-8")
    return {
        "ok": True,
        "file_id": file_id,
        "function": function_name,
        "mode": mode,
        "lines": source.count("\n") + 1,
        "source": source,
        "artifact_path": str(out_path),
        "artifact_id": out_path.name,
    }


def inject_annotations(
    file_id: str,
    relative_path: str | None,
    function_name: str | None,
    contract: str | None,
    loop_specs: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    require_package()
    source_path = resolve_source_path(file_id, relative_path)
    source = source_path.read_text(encoding="utf-8", errors="replace")
    if not contract and not loop_specs:
        raise ValueError("nothing to inject: provide contract and/or loop_specs.")
    annotated = inject_mod.inject(source, func_contract=contract, func_name=function_name, loop_specs=loop_specs or [])
    out_path = _new_output_path(file_id, f"{source_path.stem}.acsl.c")
    out_path.write_text(annotated, encoding="utf-8")
    return {
        "ok": True,
        "file_id": file_id,
        "relative_path": _relative_to_upload(file_id, source_path),
        "source": annotated,
        "artifact_path": str(out_path),
        "artifact_id": out_path.name,
        "injected_contract": bool(contract),
        "injected_loops": len(loop_specs or []),
    }


def generate_annotations(
    file_id: str,
    relative_path: str | None,
    function_name: str,
    model_name: str,
    inject_result: bool = True,
) -> dict[str, Any]:
    require_package()
    if spectool_llm is None:
        raise RuntimeError("spectool LLM integration is unavailable.")
    source_path = resolve_source_path(file_id, relative_path)
    source = source_path.read_text(encoding="utf-8", errors="replace")
    generated = spectool_llm.generate_annotations(source, function_name, model_name)
    generated_path = _new_output_path(file_id, f"{source_path.stem}.{function_name}.llm_acsl.json")
    generated_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "ok": True,
        "file_id": file_id,
        "relative_path": _relative_to_upload(file_id, source_path),
        "function_name": function_name,
        "model_name": model_name,
        "contract": generated.get("contract"),
        "loop_specs": generated.get("loop_specs", []),
        "notes": generated.get("notes", []),
        "loop_candidates": generated.get("loop_candidates", []),
        "tokens_usage": generated.get("tokens_usage", 0),
        "generation_mode": generated.get("generation_mode", "llm"),
        "artifact_id": generated_path.name,
        "artifact_path": str(generated_path),
    }
    if inject_result:
        annotated = inject_mod.inject(
            source,
            func_contract=generated.get("contract"),
            func_name=function_name,
            loop_specs=generated.get("loop_specs", []),
        )
        out_path = _new_output_path(file_id, f"{source_path.stem}.{function_name}.llm_acsl.c")
        out_path.write_text(annotated, encoding="utf-8")
        result.update(
            {
                "source": annotated,
                "source_artifact_id": out_path.name,
                "source_artifact_path": str(out_path),
                "injected_contract": bool(generated.get("contract")),
                "injected_loops": len(generated.get("loop_specs", [])),
            }
        )
    return result


def check_admits(file_id: str, relative_path: str | None = None, source: str | None = None) -> dict[str, Any]:
    require_package()
    if source is None:
        source_path = resolve_source_path(file_id, relative_path)
        source = source_path.read_text(encoding="utf-8", errors="replace")
        resolved_relative_path = _relative_to_upload(file_id, source_path)
    else:
        resolved_relative_path = relative_path or "inline-source.acsl.c"
    result = admit.check_admits(source)
    result.update({"file_id": file_id, "relative_path": resolved_relative_path})
    return result


def verify(file_id: str, relative_path: str | None = None, timeout_sec: int = 8, source: str | None = None) -> dict[str, Any]:
    require_package()
    inline_source = source is not None
    if inline_source:
        source_path = _new_output_path(file_id, "inline_verify.acsl.c")
        source_path.write_text(source or "", encoding="utf-8")
    else:
        source_path = resolve_source_path(file_id, relative_path)
    log_path = _new_output_path(file_id, f"{source_path.stem}_wp.log")
    started = time.monotonic()
    raw, runner, container_service = _run_wp(source_path, timeout_sec)
    log_path.write_text(raw.get("stdout", ""), encoding="utf-8")
    result_type = raw.get("result_type", "UK")
    proved, total = framac.parse_proved(result_type)
    verdict = framac.verdict_of(result_type)
    if verdict == "Unknown" and result_type == "UK":
        verdict = "Invalid"
    failures = locate.locate_failures(raw.get("stdout", ""), src_basename=source_path.name)
    return {
        "ok": True,
        "file_id": file_id,
        "relative_path": "inline-source.acsl.c" if inline_source else _relative_to_upload(file_id, source_path),
        "result": verdict,
        "raw_result_type": result_type,
        "proved": proved,
        "total": total,
        "elapsed_sec": raw.get("elapsed_sec", round(time.monotonic() - started, 3)),
        "timed_out": raw.get("timed_out", False),
        "returncode": raw.get("returncode"),
        "runner": runner,
        "container_service": container_service,
        "stdout": raw.get("stdout", ""),
        "stdout_file": str(log_path),
        "stderr_tail": raw.get("stderr", "")[-2000:],
        "failures": failures,
        "failure_count": len(failures),
    }


def _run_wp(source_path: Path, timeout_sec: int) -> tuple[dict[str, Any], str, str | None]:
    # Shared spectool verification prefers host Frama-C. AutoSpec's image is
    # never required here; set SPECTOOL_VERIFY_RUNNER=container to force the
    # dedicated/legacy container probe explicitly.
    runner = (os.getenv("SPECTOOL_VERIFY_RUNNER", "host") or "host").strip().lower()
    if runner in {"auto", "host"}:
        configured = (os.getenv("SPECTOOL_FRAMAC", "") or "").strip()
        binary = configured if configured and (Path(configured).exists() or shutil.which(configured)) else shutil.which("frama-c")
        if binary:
            try:
                raw = framac.run_framac_with_wp(
                    str(source_path),
                    timeout_sec,
                    subprocess_timeout=max(30, min(framac.SUBPROCESS_TIMEOUT, timeout_sec * 10)),
                    binary=binary,
                )
                return raw, "host", None
            except FileNotFoundError:
                if runner == "host":
                    raise RuntimeError("本机 Frama-C 不可用。") from None
        elif runner == "host":
            raise RuntimeError("未检测到本机 Frama-C。请在服务器安装 Frama-C 并配置可执行文件路径。")

    container = _container_tool_probe()
    service = container.get("service")
    tools = container.get("tools", {})
    if not service or not tools.get("frama_c") or not (tools.get("alt_ergo") or tools.get("z3")):
        raise RuntimeError("Frama-C/WP is unavailable because no local or containerized verifier is ready.")
    return _run_framac_in_container(source_path, timeout_sec, service), "container", service


def _run_framac_in_container(source_path: Path, timeout_sec: int, service: str) -> dict[str, Any]:
    container_path = _container_path(source_path)
    cmd = [
        "frama-c",
        "-wp",
        "-wp-rte",
        "-wp-precond-weakening",
        "-wp-prover",
        "Alt-Ergo,Z3",
        "-wp-print",
        "-wp-timeout",
        str(timeout_sec),
        container_path,
    ]
    script = _container_env_setup() + " ; " + " ".join(shlex.quote(part) for part in cmd)
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(
            ["docker", "compose", "run", "--rm", "-T", service, "bash", "-lc", script],
            cwd=str(ROOT_DIR),
            text=True,
            capture_output=True,
            timeout=framac.SUBPROCESS_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return {
            "result_type": "Invalid",
            "stdout": stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="replace"),
            "stderr": stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="replace"),
            "elapsed_sec": round(time.monotonic() - started, 3),
            "returncode": None,
            "timed_out": timed_out,
        }
    except FileNotFoundError as exc:
        raise RuntimeError("Docker is required for containerized spectool verification.") from exc
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "result_type": "Invalid" if timed_out else framac.get_result_type(stdout),
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "returncode": completed.returncode,
        "timed_out": timed_out,
    }


def _container_path(path: Path) -> str:
    try:
        return "/app/" + path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError as exc:
        raise ValueError("spectool verification input must be inside the project root.") from exc


def locate_failures(file_id: str, wp_text: str, source_basename: str | None = None) -> dict[str, Any]:
    require_package()
    failures = locate.locate_failures(wp_text, src_basename=source_basename)
    return {"ok": True, "file_id": file_id, "failures": failures, "count": len(failures)}


def list_outputs(file_id: str) -> dict[str, Any]:
    base = (OUTPUTS_DIR / file_id).resolve()
    if not base.exists():
        return {"file_id": file_id, "items": []}
    items = []
    for path in sorted(base.iterdir(), key=lambda item: item.stat().st_mtime_ns, reverse=True):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        items.append(
            {
                "artifact_id": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "modified_at": path.stat().st_mtime,
            }
        )
    return {"file_id": file_id, "items": items}


def read_output(file_id: str, artifact_id: str) -> dict[str, Any]:
    base = (OUTPUTS_DIR / file_id).resolve()
    target = (base / Path(artifact_id).name).resolve()
    if base not in target.parents and target != base:
        raise ValueError("artifact path escapes spectool output directory.")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("spectool artifact not found.")
    if target.suffix.lower() not in TEXT_EXTENSIONS:
        raise ValueError("artifact preview is limited to text files.")
    return {"path": str(target), "artifact_id": target.name, "content": target.read_text(encoding="utf-8", errors="replace")}


def _new_output_path(file_id: str, filename: str) -> Path:
    ensure_spectool_dirs()
    output_dir = OUTPUTS_DIR / file_id
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    target = output_dir / safe_name
    if target.exists():
        target = output_dir / f"{Path(safe_name).stem}_{uuid.uuid4().hex[:8]}{Path(safe_name).suffix}"
    return target


def _relative_to_upload(file_id: str, path: Path) -> str:
    base = (UPLOADS_DIR / file_id).resolve()
    try:
        return path.resolve().relative_to(base).as_posix()
    except ValueError:
        return path.name


def _normalize_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/").lstrip("/")
    parts = [part for part in normalized.split("/") if part and part not in {".", ".."}]
    return "/".join(parts) or Path(value).name


def parse_loop_specs(raw: str | None) -> list[dict[str, Any]] | None:
    if not raw:
        return None
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("loop_specs must be a JSON list.")
    return payload
