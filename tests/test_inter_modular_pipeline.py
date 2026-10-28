from pathlib import Path

from apps.api.app.service import _build_project_call_graph, _build_project_verification, _classify_failure
from engine.autospec.inter_modular_run import FileManager


def test_merge_orders_local_include_dependencies_before_consumers(tmp_path: Path) -> None:
    utils = tmp_path / "utils.h"
    cert = tmp_path / "cert.h"
    parser = tmp_path / "parser.c"
    main = tmp_path / "main.c"
    utils.write_text("typedef unsigned int u32;\n", encoding="utf-8")
    cert.write_text('#include "utils.h"\nu32 parse_cert(void);\n', encoding="utf-8")
    parser.write_text('#include "cert.h"\nu32 parse_cert(void) { return 0; }\n', encoding="utf-8")
    main.write_text('#include "cert.h"\nint main(void) { return (int)parse_cert(); }\n', encoding="utf-8")

    merged = tmp_path / "merged.c"
    FileManager().merge_files([str(main), str(cert), str(parser), str(utils)], str(merged))
    text = merged.read_text(encoding="utf-8")

    assert text.index(f"MARKER: {utils}") < text.index(f"MARKER: {cert}")
    assert text.index(f"MARKER: {cert}") < text.index(f"MARKER: {parser}")
    assert text.index(f"MARKER: {parser}") < text.index(f"MARKER: {main}")


def test_merge_preserves_external_quoted_header_and_selects_framac_harness(tmp_path: Path) -> None:
    project_header = tmp_path / "project.h"
    parser = tmp_path / "parser.c"
    main = tmp_path / "main.c"
    project_header.write_text("int parse(void);\n", encoding="utf-8")
    parser.write_text(
        '#include "project.h"\n#if defined(__FRAMAC__)\n#include "__fc_builtin.h"\nint main(void) { return parse(); }\n#endif\nint parse(void) { return 0; }\n',
        encoding="utf-8",
    )
    main.write_text('#include "project.h"\nint main(void) { return parse(); }\n', encoding="utf-8")

    merged = tmp_path / "merged.c"
    FileManager().merge_files([str(main), str(parser), str(project_header)], str(merged))
    text = merged.read_text(encoding="utf-8")

    assert '// [AutoMerge] #include "project.h"' in text
    assert '#include "__fc_builtin.h"' in text
    assert "#if !defined(__FRAMAC__)" in text
    assert "#endif /* !defined(__FRAMAC__) */" in text


def test_call_graph_counts_known_function_calls_not_parentheses(tmp_path: Path) -> None:
    helper = tmp_path / "helper.c"
    caller = tmp_path / "caller.c"
    helper.write_text("int helper(void) { return 1; }\n", encoding="utf-8")
    caller.write_text(
        "int helper(void);\nint caller(int x) { if (x) { return helper(); } return (x); }\n",
        encoding="utf-8",
    )

    graph = _build_project_call_graph([helper, caller])

    assert graph["call_edge_count"] == 1
    assert graph["fan_out"]["caller.c"] == 1
    assert graph["edges"] == [{
        "source": "caller",
        "source_module": "caller.c",
        "target": "helper",
        "target_module": "helper.c",
    }]
    assert graph["entry_functions"] == ["caller"]
    assert graph["reachable_functions"] == ["caller", "helper"]


def test_project_verdict_rejects_local_goal_as_project_success(tmp_path: Path) -> None:
    helper = tmp_path / "helper.c"
    caller = tmp_path / "caller.c"
    helper.write_text("int helper(void) { return 1; }\n", encoding="utf-8")
    caller.write_text("int helper(void);\nint main(void) { return helper(); }\n", encoding="utf-8")
    graph = _build_project_call_graph([helper, caller])
    raw = "[CMD] frama-c -wp -wp-no-callee-precond -wp-fct helper file.c\n[wp] Proved goals: 2 / 2\n"

    verdict = _build_project_verification(raw, graph, status="Fail", final_result=False)

    assert verdict["verdict"] == "partially_verified"
    assert verdict["scope"]["verified_functions"] == 1
    assert verdict["scope"]["reachable_functions"] == 2
    assert not verdict["coverage"]["call_preconditions_enabled"]
    assert not verdict["coverage"]["rte_enabled"]
    assert not verdict["complete"]


def test_merge_build_error_takes_priority_over_stale_wp_timeout() -> None:
    failure = _classify_failure(
        "error: unknown type name 'u32'\nMerged translation unit preflight failed\n[wp] Timeout: 14"
    )

    assert failure["category"] == "merge-build"
    assert failure["label"] == "Merged Project Build Error"
