from __future__ import annotations

import os
import platform
import signal
import re
import subprocess
import tempfile
import time
from pathlib import Path


VERUS_VERSION = "0.2026.01.10.531beb1"
PROJECT_ROOT = Path(__file__).resolve().parent
PLATFORM_DIR = ("verus-arm64-macos" if platform.system() == "Darwin" and platform.machine() == "arm64"
                else "verus-x86-macos" if platform.system() == "Darwin"
                else "verus-x86-win" if os.name == "nt" else "verus-x86-linux")
DEFAULT_VERUS_PATH = PROJECT_ROOT.parents[1] / "tools" / "verus" / VERUS_VERSION / PLATFORM_DIR / ("verus.exe" if os.name == "nt" else "verus")
MAX_CODE_BYTES = 256 * 1024
DEFAULT_TIMEOUT_SECONDS = 30


class VerifierUnavailableError(RuntimeError):
    """The installed verifier cannot satisfy the exact version requirement."""


def verus_path() -> Path:
    configured = os.getenv("VERUS_EXECUTABLE")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_VERUS_PATH


def _run_process(arguments: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with subprocess.Popen(arguments, cwd=verus_path().parent, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                          shell=False, creationflags=creation_flags, start_new_session=os.name != "nt") as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(arguments, timeout, output=stdout, stderr=stderr) from None
        return subprocess.CompletedProcess(arguments, process.returncode, stdout, stderr)



def verifier_info() -> dict[str, object]:
    executable = verus_path()
    if not executable.is_file():
        return {
            "available": False,
            "mode": "native",
            "version": "",
            "expected_version": VERUS_VERSION,
            "platform": "unknown",
            "executable": str(executable),
            "message": "未找到项目内的 Verus 可执行文件",
        }

    try:
        completed = _run_process([str(executable), "--version"], timeout=10)
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        output = re.sub(r"\x1b\[[0-9;]*m", "", output)
        version = re.search(r"Version:\s*([^\s]+)", output)
        platform = re.search(r"Platform:\s*([^\s]+)", output)
        actual_version = version.group(1) if version else ""
        available = completed.returncode == 0 and actual_version == VERUS_VERSION
        if available:
            message = "本机验证器已就绪"
        elif actual_version and actual_version != VERUS_VERSION:
            message = f"Verus 版本不匹配：需要 {VERUS_VERSION}，实际为 {actual_version}"
        elif "toolchain" in output and "not" in output:
            message = "缺少 Verus 所需的 Rust 1.92.0 工具链，请运行安装脚本。"
        else:
            message = "无法确认指定 Verus 版本，请检查可执行文件。" + (f" {output}" if output else "")
        return {
            "available": available,
            "mode": "native",
            "version": actual_version,
            "expected_version": VERUS_VERSION,
            "platform": platform.group(1) if platform else PLATFORM_DIR,
            "executable": str(executable),
            "message": message,
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "available": False,
            "mode": "native",
            "version": "",
            "expected_version": VERUS_VERSION,
            "platform": "unknown",
            "executable": str(executable),
            "message": f"无法启动 Verus：{error}",
        }


from engine.verification.report import reported

@reported("verus")
def verify_code(code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, *, files: list[dict] | None = None, entry_path: str = "submission.rs") -> dict[str, object]:
    executable = verus_path()
    if not executable.is_file():
        raise FileNotFoundError(f"Verus executable not found: {executable}")

    encoded = code.encode("utf-8")
    if not encoded.strip():
        raise ValueError("请输入需要验证的 Verus 代码")
    if len(encoded) > MAX_CODE_BYTES:
        raise ValueError("代码不能超过 256 KiB")

    for item in files or [{"content": code}]:
        # A native verifier is not a filesystem sandbox. Do not allow uploaded
        # source to pull arbitrary host files through Rust compiler macros.
        text = item["content"]
        if re.search(r'\binclude(?:_str|_bytes)?\s*!|#\s*\[\s*path\s*=|\b(?:env|option_env)\s*!', text):
            raise ValueError("Rust 工作台不支持 include!、path 属性或环境读取宏；请将模块作为项目文件上传。")
    started = time.perf_counter()
    runtime = verifier_info()
    if not runtime["available"]:
        raise VerifierUnavailableError(str(runtime["message"]))
    with tempfile.TemporaryDirectory(prefix="nl2verus-verify-") as temp_dir:
        source_path = Path(temp_dir) / entry_path
        for item in files or [{"path": entry_path, "content": code}]:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".rs":
                raise ValueError("非法 Rust 文件路径")
            target = Path(temp_dir) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item["content"], encoding="utf-8")
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(encoded)
        command=[str(executable), str(source_path), "--crate-type", "lib", "--crate-name", "submission"]
        try:
            completed = _run_process(
                command,
                timeout=max(1, min(timeout_seconds, 3600)),
            )
        except subprocess.TimeoutExpired as error:
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            stdout = error.stdout or ""
            stderr = error.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return {
                "command": command,
                "status": "timeout",
                "verified": False,
                "exit_code": None,
                "elapsed_ms": elapsed_ms,
                "verified_count": None,
                "error_count": None,
                "stdout": stdout,
                "stderr": stderr,
                "message": f"验证超过 {timeout_seconds} 秒，已终止",
                "verus_version": VERUS_VERSION,
            }

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    summary = re.search(r"^verification results::\s*(\d+) verified,\s*(\d+) errors", combined, re.MULTILINE)
    verified_count = int(summary.group(1)) if summary else None
    error_count = int(summary.group(2)) if summary else None
    verified = completed.returncode == 0 and error_count == 0 and verified_count is not None and verified_count > 0
    status = "verified" if verified else "failed"
    message = "验证通过" if verified else "验证未通过，请查看诊断信息"
    if summary is None:
        status = "tool_error"
        message = "未识别到 Verus 验证摘要，不能判断验证通过。"
        if completed.returncode != 0 and "panicked" not in combined and re.search(r"^error(?:\[|:)", combined, re.MULTILINE):
            status = "compile_error"
            message = "代码未通过编译，请先处理语法、类型或入口函数错误。"
        elif "panicked" in combined:
            message = "Verus 工具异常退出，请查看诊断；本次不能判断证明是否通过。"
    elif completed.returncode == 0 and error_count == 0 and verified_count == 0:
        status = "no_checks"
        message = "没有实际验证项（0 verified），请检查是否包含待验证的 Verus 函数或证明。"
    return {
        "command": command,
        "status": status,
        "verified": verified,
        "exit_code": completed.returncode,
        "elapsed_ms": elapsed_ms,
        "verified_count": verified_count,
        "error_count": error_count,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "message": message,
        "verus_version": VERUS_VERSION,
    }
