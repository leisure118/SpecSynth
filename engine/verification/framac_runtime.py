"""Frama-C/WP runtime selection for shared C verification paths.

The AutoSpec image contains a complete AutoSpec pipeline (veri-clang, its own
Python environment, Frama-C/WP).  It is the right runtime only for the legacy
AutoSpec workflow.  Shared flows -- agent candidates, spectool and the
workbench's verify-only action -- must not depend on that image.

Selection order for the shared flows:

  auto (default)  host Frama-C when available, otherwise a dedicated verifier
                  container (ACSL_VERIFIER_SERVICE, default ``verifier``)
  host            require host Frama-C
  container       require the dedicated verifier container
  legacy          explicitly use the AutoSpec container (AutoSpec workflow only)

The result shape intentionally matches the old ``verify_candidates`` contract
so callers need only switch their runner.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from engine.spectool_core.framac import SUBPROCESS_TIMEOUT, get_result_type, parse_proved, verdict_of

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PROVERS = "Alt-Ergo,Z3"
RUNTIME_ENV = "ACSL_VERIFIER_RUNTIME"
SERVICE_ENV = "ACSL_VERIFIER_SERVICE"
DEFAULT_SERVICE = "verifier"
LEGACY_SERVICE = "autospec"

_PROBE_LOCK = threading.Lock()
_PROBE_CACHE: dict[str, Any] | None = None
_PROBE_AT = 0.0
_PROBE_TTL_SEC = max(int(os.getenv("ACSL_VERIFIER_CACHE_TTL", "30") or "30"), 0)


def requested_runtime() -> str:
    value = (os.getenv(RUNTIME_ENV, "auto") or "auto").strip().lower()
    return value if value in {"auto", "host", "container", "legacy"} else "auto"


def framac_binary() -> str | None:
    configured = (os.getenv("SPECTOOL_FRAMAC", "") or "").strip()
    if configured:
        return configured if (Path(configured).exists() or shutil.which(configured)) else None
    return shutil.which("frama-c")


def host_tools() -> dict[str, bool]:
    return {
        "frama_c": framac_binary() is not None,
        "alt_ergo": shutil.which("alt-ergo") is not None,
        "z3": shutil.which("z3") is not None,
    }


def _host_ready(tools: dict[str, bool] | None = None) -> bool:
    tools = tools or host_tools()
    return tools["frama_c"] and (tools["alt_ergo"] or tools["z3"])


def _docker_service_ready(service: str) -> bool:
    try:
        completed = subprocess.run(
            ["docker", "compose", "run", "--rm", "-T", service, "sh", "-lc",
             "command -v frama-c >/dev/null 2>&1 && { command -v alt-ergo >/dev/null 2>&1 || command -v z3 >/dev/null 2>&1; }"],
            cwd=str(ROOT_DIR),
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def runtime_info(*, force: bool = False) -> dict[str, Any]:
    """Return the selected runtime, its readiness and a stable reason key."""
    global _PROBE_CACHE, _PROBE_AT
    now = time.monotonic()
    with _PROBE_LOCK:
        if not force and _PROBE_CACHE is not None and (_PROBE_TTL_SEC <= 0 or now - _PROBE_AT <= _PROBE_TTL_SEC):
            return _PROBE_CACHE

    mode = requested_runtime()
    tools = host_tools()
    host_ready = _host_ready(tools)
    info: dict[str, Any]
    if mode in {"auto", "host"} and host_ready:
        info = {"runtime": "host", "ready": True, "service": None, "framac": framac_binary(), "tools": tools,
                "message": "使用本机 Frama-C/WP。"}
    elif mode in {"auto", "container"}:
        service = (os.getenv(SERVICE_ENV, DEFAULT_SERVICE) or DEFAULT_SERVICE).strip()
        ready = _docker_service_ready(service)
        info = {"runtime": "container" if ready else None, "ready": ready,
                "service": service if ready else None, "framac": None, "tools": tools,
                "message": "使用专用验证容器。" if ready else "未检测到专用 Frama-C 验证容器。"}
    elif mode == "legacy":
        ready = _docker_service_ready(LEGACY_SERVICE)
        info = {"runtime": "legacy" if ready else None, "ready": ready,
                "service": LEGACY_SERVICE if ready else None, "framac": None, "tools": tools,
                "message": "使用 AutoSpec 容器（仅兼容旧流程）。" if ready else "AutoSpec 容器不可用。"}
    else:
        info = {"runtime": None, "ready": False, "service": None, "framac": None, "tools": tools,
                "message": "未检测到可用的 Frama-C/WP 运行时。"}

    if not info["ready"] and mode in {"auto", "host"}:
        if not tools["frama_c"]:
            info["message"] = "未检测到本机 Frama-C。请安装 Frama-C，或配置专用验证容器。"
        elif not (tools["alt_ergo"] or tools["z3"]):
            info["message"] = "本机 Frama-C 已安装，但未检测到 Alt-Ergo 或 Z3。"
        elif mode == "host":
            info["message"] = "已强制要求本机 Frama-C，但当前环境不满足 Frama-C/WP 依赖。"
    with _PROBE_LOCK:
        _PROBE_CACHE, _PROBE_AT = info, now
    return info


def preflight() -> tuple[bool, str]:
    """Return ``(ready, message)`` for the shared verifier runtime."""
    info = runtime_info()
    return bool(info["ready"]), str(info["message"])


def _include_dirs(paths: list[Path], workdir: Path) -> list[Path]:
    dirs: list[Path] = []
    for path in [workdir, *(p.parent for p in paths)]:
        if path not in dirs:
            dirs.append(path)
    return dirs


def _frama_c_args(paths: list[Path], timeout_sec: int, function: str | None, mode: str,
                  include_dirs: list[Path] | None = None, container_root: str | None = None) -> list[str]:
    from .framac_options import wp_arguments
    args = ['frama-c', *wp_arguments(max(1,min(15,timeout_sec)))]
    if mode == "termination":
        args += ["-wp-no-definitions-terminate", "-wp-no-declarations-terminate", "-wp-variant-with-terminates"]
    if function:
        args += ["-wp-fct", function]
    if container_root:
        args.append("-cpp-extra-args=-I" + container_root)
    else:
        for directory in include_dirs or []:
            args.append("-cpp-extra-args=-I" + str(directory))
    args += [str(path) for path in paths]
    return args


def _check_from_output(result_type: str, stdout: str, stderr: str, elapsed: float, timed_out: bool,
                       returncode: int | None, runner: str, runtime: str, command: list[str] | None = None) -> dict[str, Any]:
    from .framac_options import profile_metadata
    profile={**profile_metadata(),'verifier_command':list(command or [])}
    if timed_out:
        return {**profile,"status": "timeout", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": stdout, "stderr": stderr, "elapsed_sec": round(elapsed, 3),
                "returncode": returncode, "runner": runner, "runtime": runtime,
                "message": "Frama-C 验证超时。"}
    proved, total = parse_proved(result_type)
    verdict = verdict_of(result_type)
    if verdict == "Pass":
        status, verified = "verified", True
        message = f"Frama-C 证明目标 {proved}/{total}"
    elif verdict == "Fail":
        status, verified = "failed", False
        message = f"Frama-C 证明目标 {proved}/{total}，仍有目标未证明"
    else:
        status, verified = "compile_error", False
        proved, total = proved or 0, total or 0
        message = "Frama-C 未产生有效证明结果。"
    return {
        **profile,
        "status": status,
        "verified": verified,
        "verified_count": int(proved or 0),
        "error_count": max(0, int(total or 0) - int(proved or 0)),
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_sec": round(elapsed, 3),
        "returncode": returncode,
        "runner": runner,
        "runtime": runtime,
        "message": message,
    }


def run_candidate(files: list[dict[str, str]], entry: str, mode: str, timeout_sec: int,
                  workdir: Path, function: str | None = None) -> dict[str, Any]:
    """Write candidates and run Frama-C/WP through the selected runtime."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    for item in files:
        target = workdir / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
    entry_path = workdir / entry
    if not entry_path.is_file():
        return {"status": "compile_error", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": None, "runtime": None,
                "message": f"找不到入口文件：{entry}"}
    paths = [workdir / item["path"] for item in files if item["path"].endswith(".c")] if mode == "inter-modular" else [entry_path]
    info = runtime_info()
    if not info["ready"]:
        return {"status": "unavailable", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": None, "runtime": None, "message": info["message"]}
    from .diagnostics import attach_diagnostics
    if info["runtime"] == "host":
        result = _run_host(paths, workdir, mode, timeout_sec, function)
    else:
        result = _run_container(paths, workdir, mode, timeout_sec, function, info["service"], info["runtime"])
    return attach_diagnostics(result,files)


def _run_host(paths: list[Path], workdir: Path, mode: str, timeout_sec: int, function: str | None) -> dict[str, Any]:
    binary = framac_binary()
    if not binary:
        return {"status": "unavailable", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": "host", "runtime": "host",
                "message": "未检测到本机 Frama-C。"}
    args = _frama_c_args(paths, timeout_sec, function, mode, include_dirs=_include_dirs(paths, workdir))
    args[0] = binary
    started = time.monotonic()
    try:
        completed = subprocess.run(args, cwd=str(workdir), text=True, capture_output=True,
                                   timeout=max(30, min(SUBPROCESS_TIMEOUT, timeout_sec)), check=False)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        return _check_from_output("Invalid", stdout, stderr, time.monotonic() - started, True, None, "host", "host", args)
    except FileNotFoundError:
        return {"status": "unavailable", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": "host", "runtime": "host",
                "message": "未检测到本机 Frama-C。"}
    stdout, stderr = completed.stdout or "", completed.stderr or ""
    return _check_from_output(get_result_type(stdout), stdout, stderr,
                              time.monotonic() - started, False, completed.returncode, "host", "host", args)


def _container_path(path: Path) -> str:
    return "/app/" + path.resolve().relative_to(ROOT_DIR).as_posix()


def _run_container(paths: list[Path], workdir: Path, mode: str, timeout_sec: int, function: str | None,
                   service: str | None, runtime: str) -> dict[str, Any]:
    if not service:
        return {"status": "unavailable", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": runtime, "runtime": runtime,
                "message": "未配置可用的 Frama-C 验证容器。"}
    container_root = "/app/" + workdir.resolve().relative_to(ROOT_DIR).as_posix()
    container_paths = [container_root + "/" + path.relative_to(workdir).as_posix() for path in paths]
    args = _frama_c_args([Path(p) for p in container_paths], timeout_sec, function, mode, container_root=container_root)
    env_setup = ("export PATH=/root/.opam/default/bin:/opt/clang/bin:$PATH" if runtime == "legacy" else "")
    script = (env_setup + " ; " if env_setup else "") + " ".join(shlex.quote(part) for part in args)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["docker", "compose", "run", "--rm", "-T", service, "sh", "-lc", script],
            cwd=str(ROOT_DIR), text=True, capture_output=True,
            timeout=max(30, min(SUBPROCESS_TIMEOUT, timeout_sec)), check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        return _check_from_output("Invalid", stdout, stderr, time.monotonic() - started, True, None, service, runtime, args)
    except FileNotFoundError:
        return {"status": "unavailable", "verified": False, "verified_count": 0, "error_count": 0,
                "stdout": "", "stderr": "", "runner": service, "runtime": runtime,
                "message": "未检测到 Docker。"}
    stdout, stderr = completed.stdout or "", completed.stderr or ""
    return _check_from_output(get_result_type(stdout), stdout, stderr,
                              time.monotonic() - started, False, completed.returncode, service, runtime, args)
