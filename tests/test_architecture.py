"""Executable architecture rules for the layered backend."""
from __future__ import annotations

import ast
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYER_PACKAGES = ("acsl/domain", "acsl/contracts", "acsl/application", "acsl/adapters")


def _module_files(package: str) -> list[Path]:
    return sorted((ROOT / package).rglob("*.py"))


def _imports(path: Path) -> set[str]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def _assert_no_imports(package: str, forbidden: tuple[str, ...]) -> None:
    violations = []
    for path in _module_files(package):
        for name in _imports(path):
            if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden):
                violations.append(f"{path.relative_to(ROOT)} imports {name}")
    assert not violations, "\n".join(violations)


def test_domain_has_no_outward_dependencies() -> None:
    _assert_no_imports("acsl/domain", ("acsl.application", "acsl.adapters", "apps", "engine", "fastapi"))


def test_contracts_do_not_depend_on_application_or_adapters() -> None:
    _assert_no_imports("acsl/contracts", ("acsl.application", "acsl.adapters", "apps", "engine", "fastapi"))


def test_adapters_do_not_depend_on_application() -> None:
    _assert_no_imports("acsl/adapters", ("acsl.application", "apps", "fastapi"))


def test_application_does_not_depend_on_http_interface() -> None:
    _assert_no_imports("acsl/application", ("apps", "fastapi"))


def test_engine_never_imports_the_web_application() -> None:
    _assert_no_imports("engine", ("apps",))


def test_run_manager_is_composed_from_run_modules() -> None:
    from acsl.application.runs.collection import RunCollectionMixin
    from acsl.application.runs.live import RunLiveMixin
    from acsl.application.runs.manager import RunManager
    from acsl.application.runs.recovery import RunRecoveryMixin
    from acsl.application.runs.results import RunResultMixin

    assert issubclass(RunManager, (RunLiveMixin, RunRecoveryMixin, RunResultMixin, RunCollectionMixin))
    for name in (
        "_run_live",
        "_recover_task_from_artifacts",
        "_build_result",
        "_collect_single_live_output",
    ):
        assert callable(getattr(RunManager, name))


def test_application_services_are_framework_free() -> None:
    from acsl.application.benchmarks import BenchmarkRunService
    from acsl.application.projects import ProjectService
    from acsl.application.runs.manager import RunManager

    for service in (ProjectService, BenchmarkRunService, RunManager):
        source = Path(service.__module__.replace(".", "/") + ".py")
        text = (ROOT / source).read_text(encoding="utf-8")
        assert "HTTPException" not in text, service.__name__


def test_layer_packages_exist() -> None:
    for package in LAYER_PACKAGES:
        assert (ROOT / package / "__init__.py").is_file()
    for module in (
        "acsl/application/runs/manager.py",
        "acsl/application/runs/live.py",
        "acsl/application/runs/recovery.py",
        "acsl/application/runs/results.py",
        "acsl/application/runs/collection.py",
        "acsl/application/runs/metrics.py",
        "acsl/application/runs/analysis.py",
        "acsl/application/projects.py",
        "acsl/application/benchmarks.py",
        "acsl/application/skills.py",
        "acsl/adapters/storage.py",
        "acsl/adapters/agent_runtime.py",
        "acsl/adapters/github_import.py",
        "acsl/infrastructure/settings.py",
    ):
        assert (ROOT / module).is_file(), module
