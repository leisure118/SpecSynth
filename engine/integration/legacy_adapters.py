from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path


_CAPABILITIES_CACHE_LOCK = threading.Lock()
_CAPABILITIES_CACHE: "LiveCapabilities | None" = None
_CAPABILITIES_CACHE_AT = 0.0
_CAPABILITIES_CACHE_TTL_SEC = max(int(os.getenv("ACSL_AGENT_CAPABILITIES_CACHE_TTL", "15") or "15"), 0)


def _local_toolchain_mode() -> bool:
    return os.getenv("ACSL_AGENT_LOCAL_TOOLCHAIN", "1") == "1"


@dataclass(frozen=True)
class LiveCapabilities:
    local_toolchain_mode: bool
    python: bool
    docker: bool
    docker_compose: bool
    docker_daemon: bool
    frama_c: bool
    frama_c_local: bool
    frama_c_container: bool
    autospec_image: bool
    termination_image: bool
    veri_clang: bool
    veri_clang_local: bool
    veri_clang_container: bool
    autospec_container: bool
    termination_container: bool
    gcc_local: bool = False

    @property
    def single_available(self) -> bool:
        if self.local_toolchain_mode:return self.python and self.frama_c_local and self.veri_clang_local
        return (
            self.python
            and self.docker
            and self.docker_compose
            and self.docker_daemon
            and self.autospec_image
            and self.autospec_container
        )

    @property
    def termination_available(self) -> bool:
        if self.local_toolchain_mode:return self.python and self.frama_c_local and self.gcc_local
        return (
            self.python
            and self.docker
            and self.docker_compose
            and self.docker_daemon
            and (self.termination_container or self.autospec_container)
        )

    @property
    def termination_service(self) -> str:
        return "termination" if self.termination_container else "autospec"

    @property
    def inter_modular_available(self) -> bool:
        return self.single_available

    @property
    def batch_available(self) -> bool:
        return self.single_available

    def mode_detail(self, mode: str) -> dict:
        if mode in {"single", "inter-modular", "batch"}:
            ready = getattr(self, f"{mode.replace('-', '_')}_available", self.single_available)
            details = self._single_like_details()
            hint = self._single_like_hint()
        elif mode == "termination":
            ready = self.termination_available
            details = self._termination_details()
            hint = self._termination_hint()
        else:
            ready = False
            details = [f"Unsupported mode: {mode}."]
            hint = "Inspect the submitted mode and backend mapping."
        summary = "当前模式的真实执行环境已就绪。" if ready else (details[0] if details else "当前模式的真实执行环境未就绪。")
        return {
            "mode": mode,
            "ready": ready,
            "summary": summary,
            "details": details,
            "actionable_hint": hint,
        }

    def _single_like_details(self) -> list[str]:
        details: list[str] = []
        if not self.python:
            details.append("未检测到 Python 运行环境。")
        if self.local_toolchain_mode:
            if not self.veri_clang_local:
                details.append("未检测到本地 veri-clang（期望位于 /app/third_party/autospec_llvm/bin）。")
            if not self.frama_c_local:
                details.append("未检测到本地 Frama-C。")
            return details
        if not self.docker:
            details.append("未检测到 Docker 客户端。")
        if self.docker and not self.docker_compose:
            details.append("未检测到 Docker Compose。")
        if self.docker and self.docker_compose and not self.docker_daemon:
            details.append("Docker daemon 未启动，请先启动 Docker Desktop。")
        if self.docker_daemon and not self.autospec_image:
            details.append("缺少 autospec 镜像 junjiehu1905/autospec:latest。")
        if self.docker_daemon and self.autospec_image and not self.autospec_container:
            details.append("autospec 容器自检失败，容器内 veri-clang 或 Frama-C 不可用。")
        return details

    def _termination_details(self) -> list[str]:
        details: list[str] = []
        if not self.python:
            details.append("未检测到 Python 运行环境。")
        if self.local_toolchain_mode:
            if not self.frama_c_local:
                details.append("未检测到本地 Frama-C。")
            if not self.gcc_local:
                details.append("未检测到本地 gcc（termination 阶段需要）。")
            return details
        if not self.docker:
            details.append("未检测到 Docker 客户端。")
        if self.docker and not self.docker_compose:
            details.append("未检测到 Docker Compose。")
        if self.docker and self.docker_compose and not self.docker_daemon:
            details.append("Docker daemon 未启动，请先启动 Docker Desktop。")
        if self.docker_daemon and not self.termination_image and not self.autospec_container:
            details.append("缺少 termination 镜像，且 autospec 容器无法提供终止性后备工具链。")
        if self.docker_daemon and self.termination_image and not self.termination_container:
            details.append("termination 容器自检失败，容器内 Frama-C 或 gcc 不可用。")
        return details

    def _single_like_hint(self) -> str:
        if self.local_toolchain_mode:
            if not self.veri_clang_local or not self.frama_c_local:
                return "请检查 unified 镜像中的 PATH、VERI_LIB_PATH 与 Frama-C 安装是否完整。"
            return "统一镜像本地工具链已就绪。"
        if not self.docker or not self.docker_compose or not self.docker_daemon:
            return "启动 Docker Desktop 后，在仓库根目录执行 docker compose pull；镜像就绪后刷新页面即可重试。"
        if not self.autospec_image:
            return "在仓库根目录执行 docker compose pull，拉取 autospec 镜像后重试。"
        if not self.autospec_container:
            return (
                "执行 docker compose run --rm -T autospec bash -lc "
                "\"veri-clang --version && frama-c -version\" 以检查容器内工具链。"
            )
        return "真实执行环境已就绪。"

    def _termination_hint(self) -> str:
        if self.local_toolchain_mode:
            if not self.frama_c_local or not self.termination_container:
                return "请检查 unified 镜像中的 Frama-C 与 gcc 安装。"
            return "统一镜像本地工具链已就绪。"
        if not self.docker or not self.docker_compose or not self.docker_daemon:
            return "启动 Docker Desktop 后，在仓库根目录执行 docker compose pull；镜像就绪后刷新页面即可重试。"
        if not self.termination_image and self.autospec_container:
            return "将使用现有 autospec 容器执行终止性分析。"
        if not self.termination_image:
            return "在仓库根目录执行 docker compose pull，拉取 termination 或 autospec 镜像后重试。"
        if not self.termination_container:
            return (
                "执行 docker compose run --rm -T termination bash -lc "
                "\"frama-c -version && gcc --version\" 以检查容器内工具链。"
            )
        return "真实执行环境已就绪。"

    def as_dict(self) -> dict:
        return {
            "local_toolchain_mode": self.local_toolchain_mode,
            "python": self.python,
            "docker": self.docker,
            "docker_compose": self.docker_compose,
            "docker_daemon": self.docker_daemon,
            "frama_c": self.frama_c,
            "frama_c_local": self.frama_c_local,
            "frama_c_container": self.frama_c_container,
            "autospec_image": self.autospec_image,
            "termination_image": self.termination_image,
            "veri_clang": self.veri_clang,
            "veri_clang_local": self.veri_clang_local,
            "veri_clang_container": self.veri_clang_container,
            "autospec_container": self.autospec_container,
            "termination_container": self.termination_container,
            "termination_service": self.termination_service,
            "termination_fallback": not self.termination_container and self.autospec_container,
            "single_available": self.single_available,
            "termination_available": self.termination_available,
            "inter_modular_available": self.inter_modular_available,
            "batch_available": self.batch_available,
            "mode_details": {
                "single": self.mode_detail("single"),
                "termination": self.mode_detail("termination"),
                "inter-modular": self.mode_detail("inter-modular"),
                "batch": self.mode_detail("batch"),
            },
        }


def _run_probe(command: list[str], timeout: int = 60) -> bool:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def detect_live_capabilities(*, force: bool = False) -> LiveCapabilities:
    global _CAPABILITIES_CACHE, _CAPABILITIES_CACHE_AT
    now = time.monotonic()
    with _CAPABILITIES_CACHE_LOCK:
        if (
            not force
            and _CAPABILITIES_CACHE is not None
            and _CAPABILITIES_CACHE_TTL_SEC > 0
            and now - _CAPABILITIES_CACHE_AT <= _CAPABILITIES_CACHE_TTL_SEC
        ):
            return _CAPABILITIES_CACHE

    has_python = shutil.which("python") is not None or shutil.which("python3") is not None
    local_mode = _local_toolchain_mode()
    has_docker = not local_mode and shutil.which("docker") is not None
    has_docker_compose = has_docker and _run_probe(["docker", "compose", "version"], timeout=30)
    has_docker_daemon = has_docker_compose and _run_probe(["docker", "info"], timeout=30)
    frama_c_local = shutil.which("frama-c") is not None
    veri_clang_local = shutil.which("veri-clang") is not None
    gcc_local = shutil.which("gcc") is not None
    autospec_image = False
    termination_image = False
    frama_c_container = False
    veri_clang_container = False
    autospec_container = False
    termination_container = False

    if not local_mode and has_docker_daemon:
        autospec_image = _run_probe(["docker", "image", "inspect", "junjiehu1905/autospec:latest"])
        termination_image = _run_probe(["docker", "image", "inspect", "junjiehu1905/termination_analysis:latest"])
        if autospec_image:
            autospec_container = _run_probe(
                [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "autospec",
                    "bash",
                    "-lc",
                    "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH ; "
                    "export VERI_LIB_PATH=/app/third_party/autospec_llvm ; "
                    "veri-clang --version >/dev/null && frama-c -version >/dev/null",
                ]
            )
        if termination_image:
            termination_container = _run_probe(
                [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "termination",
                    "bash",
                    "-lc",
                    "export PATH=/root/.opam/default/bin:/app/third_party/autospec_llvm/bin:/opt/clang/bin:$PATH ; "
                    "frama-c -version >/dev/null && gcc --version >/dev/null",
                ]
            )
        veri_clang_container = autospec_container
        frama_c_container = autospec_container or termination_container

    capabilities = LiveCapabilities(
        local_toolchain_mode=local_mode,
        gcc_local=gcc_local,
        python=has_python,
        docker=has_docker,
        docker_compose=has_docker_compose,
        docker_daemon=has_docker_daemon,
        frama_c=frama_c_local or frama_c_container,
        frama_c_local=frama_c_local,
        frama_c_container=frama_c_container,
        autospec_image=autospec_image,
        termination_image=termination_image,
        veri_clang=veri_clang_local or veri_clang_container,
        veri_clang_local=veri_clang_local,
        veri_clang_container=veri_clang_container,
        autospec_container=autospec_container,
        termination_container=termination_container,
    )
    with _CAPABILITIES_CACHE_LOCK:
        _CAPABILITIES_CACHE = capabilities
        _CAPABILITIES_CACHE_AT = time.monotonic()
    return capabilities


def build_single_command(target_rel: str, output_rel: str, model_name: str, enable_mutation: bool) -> list[str]:
    quoted_target = shlex.quote(target_rel)
    quoted_output = shlex.quote(output_rel)
    quoted_model = shlex.quote(model_name)
    if _local_toolchain_mode():
        inner = [
            "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
            "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
            "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
            "export AUTOSPEC_MAX_ITER=${AUTOSPEC_MAX_ITER:-5}",
            "export AUTOSPEC_MAX_CANDIDATE_VERIFY=${AUTOSPEC_MAX_CANDIDATE_VERIFY:-1}",
            "export AUTOSPEC_WP_GOAL_TIMEOUT=${AUTOSPEC_WP_GOAL_TIMEOUT:-4}",
            "export AUTOSPEC_WP_PROVERS=${AUTOSPEC_WP_PROVERS:-Z3}",
            f"/usr/bin/python3 engine/autospec/main.py -f {quoted_target} -m {quoted_model} -t 0 -o {quoted_output}",
        ]
        if enable_mutation:
            inner[-1] += " --enable-mutation"
        return ["/bin/bash", "-lc", " ; ".join(inner)]

    inner = [
        "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
        "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
        "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
        "export AUTOSPEC_MAX_ITER=${AUTOSPEC_MAX_ITER:-5}",
        "export AUTOSPEC_MAX_CANDIDATE_VERIFY=${AUTOSPEC_MAX_CANDIDATE_VERIFY:-1}",
        "export AUTOSPEC_WP_GOAL_TIMEOUT=${AUTOSPEC_WP_GOAL_TIMEOUT:-4}",
        "export AUTOSPEC_WP_PROVERS=${AUTOSPEC_WP_PROVERS:-Z3}",
        f"/usr/bin/python3 engine/autospec/main.py -f {quoted_target} -m {quoted_model} -t 0 -o {quoted_output}",
    ]
    if enable_mutation:
        inner[-1] += " --enable-mutation"
    command = " ; ".join(inner)
    return ["docker", "compose", "run", "--rm", "-T", "autospec", "bash", "-lc", command]


def build_inter_modular_command(file_args: list[str], model_name: str, workdir_rel: str) -> list[str]:
    quoted_inputs = " ".join(shlex.quote(item) for item in file_args)
    quoted_model = shlex.quote(model_name)
    if _local_toolchain_mode():
        quoted_workdir = shlex.quote(workdir_rel)
        inner = [
            "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
            "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
            "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
            "export AUTOSPEC_MAX_ITER=${AUTOSPEC_MAX_ITER:-5}",
            f"cd {quoted_workdir}",
            f"/usr/bin/python3 /app/engine/autospec/inter_modular_run.py -i {quoted_inputs} -m {quoted_model}",
        ]
        return ["/bin/bash", "-lc", " ; ".join(inner)]

    quoted_workdir = shlex.quote(f"/app/{workdir_rel}")
    inner = [
        "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
        "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
        "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
        "export AUTOSPEC_MAX_ITER=${AUTOSPEC_MAX_ITER:-5}",
        f"cd {quoted_workdir}",
        f"/usr/bin/python3 /app/engine/autospec/inter_modular_run.py -i {quoted_inputs} -m {quoted_model}",
    ]
    return ["docker", "compose", "run", "--rm", "-T", "autospec", "bash", "-lc", " ; ".join(inner)]


def build_batch_command(input_rel: str, model_name: str, workspace_rel: str, results_rel: str, output_rel: str) -> list[str]:
    quoted_input = shlex.quote(input_rel)
    quoted_model = shlex.quote(model_name)
    quoted_workspace = shlex.quote(workspace_rel)
    quoted_results = shlex.quote(results_rel)
    quoted_output = shlex.quote(output_rel)
    inner = [
        "export PATH=/app/third_party/autospec_llvm/bin:/opt/clang/bin:/root/.opam/default/bin:$PATH",
        "export VERI_LIB_PATH=/app/third_party/autospec_llvm",
        "export LD_LIBRARY_PATH=/app/third_party/clang_llvm/lib:$LD_LIBRARY_PATH",
        "export AUTOSPEC_MAX_ITER=${AUTOSPEC_MAX_ITER:-1}",
        f"export AUTOSPEC_BATCH_FILE_TIMEOUT=${{AUTOSPEC_BATCH_FILE_TIMEOUT:-{os.getenv('AUTOSPEC_BATCH_FILE_TIMEOUT', '45')}}}",
        (
            "/usr/bin/python3 engine/autospec/auto_run.py "
            f"-i {quoted_input} -m {quoted_model} "
            f"--workspace-root {quoted_workspace} --result-dir {quoted_results} --output-dir {quoted_output} "
            " --per-file-timeout ${AUTOSPEC_BATCH_FILE_TIMEOUT}"
        ),
    ]
    if _local_toolchain_mode():
        return ["/bin/bash", "-lc", " ; ".join(inner)]
    return ["docker", "compose", "run", "--rm", "-T", "autospec", "bash", "-lc", " ; ".join(inner)]


def build_termination_commands(
    stage1_rel: str,
    stage2_rel: str,
    verified_rel: str,
    model_name: str,
    *,
    service: str = "termination",
) -> list[list[str]]:
    quoted_model = shlex.quote(model_name)
    quoted_stage1 = shlex.quote(stage1_rel)
    quoted_stage2 = shlex.quote(stage2_rel)
    quoted_verified = shlex.quote(verified_rel)
    setup = (
        "export PATH=/root/.opam/default/bin:/app/third_party/autospec_llvm/bin:/opt/clang/bin:$PATH"
        f" ; export TERMINATION_LLM_MODEL={quoted_model}"
    )
    if _local_toolchain_mode():
        generate_cmd = [
            "/bin/bash",
            "-lc",
            f"{setup} ; /usr/bin/python3 engine/termination/generate_variant.py -i {quoted_stage1} -o {quoted_stage2}",
        ]
        verify_cmd = [
            "/bin/bash",
            "-lc",
            f"{setup} ; /usr/bin/python3 engine/termination/call_framac.py -i {quoted_stage2} -o {quoted_verified}",
        ]
    else:
        generate_cmd = [
            "docker",
            "compose",
            "run",
            "--rm",
            "-T",
            service,
            "bash",
            "-lc",
            f"{setup} ; /usr/bin/python3 engine/termination/generate_variant.py -i {quoted_stage1} -o {quoted_stage2}",
        ]
        verify_cmd = [
            "docker",
            "compose",
            "run",
            "--rm",
            "-T",
            service,
            "bash",
            "-lc",
            f"{setup} ; /usr/bin/python3 engine/termination/call_framac.py -i {quoted_stage2} -o {quoted_verified}",
        ]
    return [generate_cmd, verify_cmd]


def run_command(command: list[str], cwd: Path, timeout: int = 900, agent_instructions: str = "") -> subprocess.CompletedProcess[str]:
    # Compose does not inherit arbitrary parent variables into its containers.
    # Forward by name, never interpolate user instructions into shell source.
    command = list(command)
    if command[:3] == ['docker', 'compose', 'run']:
        command[3:3] = ['-e', 'XUANJIAN_AGENT_INSTRUCTIONS']
    return subprocess.run(
        command,
        cwd=str(cwd),
        env={**os.environ, "XUANJIAN_AGENT_INSTRUCTIONS": agent_instructions},
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
