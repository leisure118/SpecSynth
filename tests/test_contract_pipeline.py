from pathlib import Path
from types import SimpleNamespace

import pytest
import subprocess

from apps.api.app.service import (
    RunManager,
    _classify_failure,
    _metrics_from_run_log,
    _successful_iteration_log,
    _timeout_output,
)
from engine.autospec.src.framac import run_framac_syntax_check
from engine.autospec.main import has_verifier_approved_result
from engine.integration.legacy_adapters import LiveCapabilities, build_termination_commands
from engine.autospec.src.simplify_acsl import is_removable_acsl_line, simplify_acsl
from engine.autospec.src.llmveri import (
    add_nullable_global_validity_guard,
    build_target_focused_prompt,
    candidate_matches_task_type,
    extract_target_function_name,
    extract_target_function_identifiers,
    extract_loop_body_local_identifiers,
    format_acsl_operator_spacing,
    normalize_candidate_spec_line,
    loop_spec_matches_target_scope,
    prune_candidate_specs,
    remove_nullable_behavior_conflicts,
    response_uses_named_behaviors,
    sanitize_contract_reply,
    strip_generated_acsl_wrapper,
    target_function_returns_void,
)


def test_non_acsl_declaration_is_rejected() -> None:
    assert normalize_candidate_spec_line(
        "const _crl_ext_oid * find_crl_ext_by_oid(const u8 *buf, u32 len);"
    ) is None


@pytest.mark.parametrize(
    "line",
    [
        "y = y + 1;",
        "a = a - 1;",
        "return y;",
        "while (a != 0) {",
        "}",
    ],
)
def test_c_statements_are_never_removable_as_acsl(line: str) -> None:
    assert not is_removable_acsl_line(line)


@pytest.mark.parametrize(
    "line",
    [
        "requires x >= 0;",
        "  ensures \\result == x;",
        "/*@ loop invariant a >= 0; */",
        "//@ loop assigns a, y;",
        "behavior valid_input:",
    ],
)
def test_generated_acsl_clauses_are_removable(line: str) -> None:
    assert is_removable_acsl_line(line)


def test_failed_goal_location_does_not_delete_c_statement(tmp_path: Path) -> None:
    merged = tmp_path / "183_merged.c"
    merged.write_text(
        "int test(int x) {\n"
        "  int a = x;\n"
        "  int y = 0;\n"
        "  y = y + 1;\n"
        "  a = a - 1;\n"
        "  return y;\n"
        "}\n",
        encoding="utf-8",
    )
    report = tmp_path / "wp.log"
    report.write_text(
        f"Goal LoopInvariant(file {merged}, line 4) in 'test':\n"
        "Prover qed returns Timeout (10ms)\n"
        "----------\n",
        encoding="utf-8",
    )

    before = merged.read_text(encoding="utf-8")
    removed = simplify_acsl(str(report), str(merged))

    assert removed == []
    assert merged.read_text(encoding="utf-8") == before
    assert "y = y + 1;" in before
    assert "a = a - 1;" in before


def test_failed_goal_without_removable_acsl_reports_no_progress(tmp_path: Path) -> None:
    merged = tmp_path / "arraymax_merged.c"
    merged.write_text(
        "int arraymax(int *a, int n) {\n"
        "  int max = a[0];\n"
        "  if (max < a[1]) max = a[1];\n"
        "  return max;\n"
        "}\n",
        encoding="utf-8",
    )
    report = tmp_path / "wp.log"
    report.write_text(
        f"Goal Assertion(file {merged}, line 3) in 'arraymax':\n"
        "Prover z3 returns Timeout (8s)\n"
        "----------\n",
        encoding="utf-8",
    )

    assert simplify_acsl(str(report), str(merged)) == []
    assert "if (max < a[1])" in merged.read_text(encoding="utf-8")


def test_live_result_keeps_latest_complete_valid_failure(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    old_iteration = output_root / "sample_0001" / "sample_0004"
    last_iteration = output_root / "sample_0001" / "sample_0005"
    old_iteration.mkdir(parents=True)
    last_iteration.mkdir(parents=True)

    (old_iteration / "final_result").write_text("Fail\n", encoding="utf-8")
    (old_iteration / "sample_merged.c").write_text("int old_failure;\n", encoding="utf-8")
    (old_iteration / "sample_merged_Pass_6_6.txt").write_text("6/6\n", encoding="utf-8")
    (old_iteration / "sample_merged_Fail_6_7.txt").write_text("6/7\n", encoding="utf-8")
    (last_iteration / "sample_merged.c").write_text("int terminal_invalid;\n", encoding="utf-8")
    (last_iteration / "sample_merged_Invalid.txt").write_text("invalid annotation\n", encoding="utf-8")

    collected = RunManager._collect_single_live_output(
        input_root,
        output_root,
        "invalid annotation",
        returncode=0,
        timeout_sec=240,
    )

    assert collected["status"] == "Fail"
    assert "old_failure" in collected["result_code"]
    assert "sample_0004" in collected["engine_detail"]["final_result_path"]
    assert "sample_0004" in collected["engine_detail"]["result_code_path"]
    assert collected["proof_stats"]["proved_goals"] == 6
    assert collected["proof_stats"]["total_goals"] == 7
    assert collected["failure_analysis"]["category"] == "proof-failed"


def test_live_result_uses_terminal_invalid_when_no_complete_round_exists(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    terminal = output_root / "sample_0001" / "sample_0001"
    terminal.mkdir(parents=True)
    (terminal / "sample_merged.c").write_text("int invalid_candidate;\n", encoding="utf-8")
    (terminal / "sample_merged_Invalid.txt").write_text("invalid annotation\n", encoding="utf-8")

    collected = RunManager._collect_single_live_output(
        input_root,
        output_root,
        "invalid annotation",
        returncode=0,
        timeout_sec=120,
    )

    assert collected["status"] == "Invalid"
    assert "invalid_candidate" in collected["result_code"]
    assert collected["engine_detail"]["final_result_path"] is None


def test_live_result_stops_at_first_whole_program_pass(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    passed = output_root / "sample_0001" / "sample_0002"
    stale = output_root / "sample_0001" / "sample_0003"
    passed.mkdir(parents=True)
    stale.mkdir(parents=True)
    (passed / "final_result").write_text("Pass\n", encoding="utf-8")
    (passed / "sample_merged.c").write_text("int verified;\n", encoding="utf-8")
    (passed / "sample_merged_Pass_4_4.txt").write_text("4/4\n", encoding="utf-8")
    (stale / "sample_merged.c").write_text("int stale_failure;\n", encoding="utf-8")
    (stale / "sample_merged_Invalid.txt").write_text("invalid\n", encoding="utf-8")

    assert has_verifier_approved_result(str(output_root))
    collected = RunManager._collect_single_live_output(
        input_root,
        output_root,
        "completed",
        returncode=0,
        timeout_sec=240,
    )

    assert collected["status"] == "Pass"
    assert "verified" in collected["result_code"]
    assert "sample_0002" in collected["engine_detail"]["final_result_path"]
    assert "sample_0002" in collected["engine_detail"]["result_code_path"]


def test_contract_clauses_are_emitted_in_framac_order() -> None:
    specs = prune_candidate_specs([
        "ensures \\result == 0;",
        "assigns \\nothing;",
        "requires len > 0;",
    ])
    assert specs == ["requires len > 0;", "assigns \\nothing;", "ensures \\result == 0;"]


def test_large_merged_prompt_is_focused_around_target() -> None:
    source = "A" * 30000 + "/* @ >>> INFILL <<< */\nint target(void) { return 0; }" + "B" * 30000
    focused = build_target_focused_prompt(source)
    assert len(focused) < len(source)
    assert "INFILL" in focused
    assert "int target" in focused


def test_log_metrics_survive_pickle_cleanup() -> None:
    metrics = _metrics_from_run_log(
        "total_tokens: 260\nllm_time_sec: 1.25\ntotal_tokens: 77\nllm_time_sec: 2.5\n"
    )
    assert metrics == {"tokens_usage": 337, "iteration_count": 2, "llm_time_sec": 3.75}


def test_timeout_output_decodes_subprocess_byte_buffers() -> None:
    exc = subprocess.TimeoutExpired(
        cmd=["autospec"],
        timeout=240,
        output="已完成第一轮\n".encode("utf-8"),
        stderr=b"verification timeout",
    )
    assert _timeout_output(exc) == "已完成第一轮\n\nverification timeout"


def test_termination_uses_autospec_when_dedicated_image_is_missing() -> None:
    capabilities = LiveCapabilities(
        local_toolchain_mode=False,
        python=True,
        docker=True,
        docker_compose=True,
        docker_daemon=True,
        frama_c=True,
        frama_c_local=False,
        frama_c_container=True,
        autospec_image=True,
        termination_image=False,
        veri_clang=True,
        veri_clang_local=False,
        veri_clang_container=True,
        autospec_container=True,
        termination_container=False,
    )
    assert capabilities.termination_available
    assert capabilities.termination_service == "autospec"
    commands = build_termination_commands(
        "stage1",
        "stage2",
        "verified",
        "qwen-turbo",
        service=capabilities.termination_service,
    )
    assert all(command[5] == "autospec" for command in commands)


def test_success_log_keeps_only_final_verified_iteration() -> None:
    raw = """clang version 12.0.1
[DEBUG] AutoSpec target file = sample.c
INFO:root:LLM querying ...
INFO:root:candidate: bad
INFO:root:failed verification
INFO:root:LLM querying ...
INFO:root:candidate: good
INFO:root:total_tokens: 45
INFO:root: Congratulations, you have successfully passed the verification.
"""
    saved = _successful_iteration_log(
        raw,
        proof_stats={"proved_goals": 3, "total_goals": 3},
    )
    assert "candidate: bad" not in saved
    assert "failed verification" not in saved
    assert saved.startswith("clang version 12.0.1")
    assert saved.index("AutoSpec target file") < saved.index("candidate: good")
    assert "verified-cache" not in saved
    assert "source_task:" not in saved
    assert "candidate: good" in saved
    assert saved.count("LLM querying") == 1
    assert "status=Pass" in saved


def test_loop_clause_cannot_reference_a_distant_function_scope() -> None:
    source = """int distant(void) { int i; return i; }
int target(unsigned n) {
  unsigned k;
  /* @ >>> INFILL <<< */
  for (k = 0; k < n; ++k) {}
  return 0;
}
"""
    identifiers = extract_target_function_identifiers(source)
    assert loop_spec_matches_target_scope("loop invariant k <= n;", identifiers)
    assert not loop_spec_matches_target_scope("loop invariant i <= n;", identifiers)


def test_loop_body_local_is_not_visible_at_annotation() -> None:
    source = """int target(unsigned n) {
  unsigned k;
  /* @ >>> INFILL <<< */
  for (k = 0; k < n; ++k) { int ret; ret = 0; }
  return 0;
}
"""
    identifiers = extract_target_function_identifiers(source)
    identifiers -= extract_loop_body_local_identifiers(source)
    assert "k" in identifiers
    assert "ret" not in identifiers
    assert not loop_spec_matches_target_scope("loop assigns ret;", identifiers)


def test_candidate_kind_must_match_current_autospec_task() -> None:
    assert candidate_matches_task_type("loop invariant k <= n;", 1)
    assert not candidate_matches_task_type("loop invariant k <= n;", 2)
    assert candidate_matches_task_type("requires n > 0;", 2)
    assert not candidate_matches_task_type("requires n > 0;", 1)


def test_named_behaviors_select_full_contract_verification() -> None:
    reply = """behavior null_option:
  assumes option == \\null;
  assigns \\nothing;
behavior valid_option:
  assumes option != \\null;
  assigns option->radius;
complete behaviors null_option, valid_option;"""
    assert response_uses_named_behaviors(reply)
    assert not response_uses_named_behaviors(
        "requires \\valid(option);\nassigns option->radius;"
    )


def test_target_function_name_is_found_for_contract_and_loop_markers() -> None:
    contract_source = "/* @ >>> INFILL <<< */\nint target(int n) { return n; }"
    loop_source = "int target(int n) { int k; /* @ >>> INFILL <<< */ for (k=0;k<n;k++){} return k; }"
    assert extract_target_function_name(contract_source) == "target"
    assert extract_target_function_name(loop_source) == "target"


def test_operator_spacing_preserves_pointer_access_and_implication() -> None:
    assert format_acsl_operator_spacing("ensures option->radius==radius;") == (
        "ensures option->radius == radius;"
    )


def test_generated_contract_wrapper_is_not_nested() -> None:
    reply = """/* @
behavior null_option:
  assumes option == \\null;
*/"""
    cleaned = strip_generated_acsl_wrapper(reply)
    assert cleaned.startswith("behavior null_option:")
    assert "/*" not in cleaned
    assert "*/" not in cleaned
    assert format_acsl_operator_spacing("ensures option!=\\null ==> option->radius==radius;") == (
        "ensures option!=\\null ==> option->radius == radius;"
    )


def test_void_contract_drops_result_and_nullable_global_requirement() -> None:
    question = """/* @ >>> INFILL <<< */
void set_radius(Circle *option, float radius) { if (!option) return; option->radius = radius; }
"""
    reply = """/* @
requires \\valid(option);
ensures \\result == 0;
behavior null_option:
  assumes option == \\null;
  assigns \\nothing;
behavior valid_option:
  assumes option != \\null;
  requires \\valid(option);
  assigns option->radius;
  ensures option->radius == radius;
complete behaviors null_option, valid_option;
disjoint behaviors null_option, valid_option;
@ */"""
    assert target_function_returns_void(question)
    cleaned = sanitize_contract_reply(reply, question)
    assert "\\result" not in cleaned
    assert cleaned.startswith("requires option == \\null || \\valid(option);")
    assert cleaned.count("requires \\valid(option);") == 1
    assert not cleaned.endswith("@")


def test_nullable_behavior_adds_global_wp_rte_guard() -> None:
    reply = """behavior null_option:
  assumes option == \\null;
  assigns \\nothing;
behavior valid_option:
  assumes option != \\null;
  requires \\valid(option);
  assigns option->centerX;
  ensures option->centerX == centerX;
complete behaviors null_option, valid_option;
disjoint behaviors null_option, valid_option;"""
    guarded = add_nullable_global_validity_guard(reply)
    assert guarded.startswith("requires option == \\null || \\valid(option);")
    assert guarded.count("requires option == \\null || \\valid(option);") == 1


@pytest.mark.parametrize(
    ("sample_name", "assigned_fields", "ensures"),
    [
        (
            "01_circle_center_x.c",
            ["option->centerX"],
            ["ensures option->centerX == centerX;"],
        ),
        (
            "02_circle_radius.c",
            ["option->radius"],
            ["ensures option->radius == radius;"],
        ),
        (
            "03_rect_edges.c",
            ["option->left", "option->right", "option->top", "option->bottom"],
            [
                "ensures option->left == left;",
                "ensures option->right == right;",
                "ensures option->top == top;",
                "ensures option->bottom == bottom;",
            ],
        ),
    ],
)
def test_openharmony_nullable_contracts_are_guarded_once(
    sample_name: str,
    assigned_fields: list[str],
    ensures: list[str],
) -> None:
    source_path = Path(__file__).resolve().parents[2] / "openharmony验证样例" / sample_name
    if not source_path.exists():
        bundled = Path(__file__).resolve().parents[1] / "resources" / "demo_cases" / "openharmony" / (Path(sample_name).stem + "_verified.c")
        if not bundled.exists():
            pytest.skip("external OpenHarmony sample is not installed")
        source_path = bundled
    source = source_path.read_text(encoding="utf-8")
    question = source.replace("\nvoid OH_", "\n/* @ >>> INFILL <<< */\nvoid OH_", 1)
    valid_body = [
        "behavior null_option:",
        "    assumes option == \\null;",
        "    assigns \\nothing;",
        "behavior valid_option:",
        "    assumes option != \\null;",
        "    requires \\valid(option);",
        "    assigns " + ", ".join(assigned_fields) + ";",
        *["    " + clause for clause in ensures],
        "complete behaviors null_option, valid_option;",
        "disjoint behaviors null_option, valid_option;",
    ]
    reply = "/*@\n" + "\n".join(valid_body) + "\n*/"

    cleaned = sanitize_contract_reply(reply, question)

    guard = "requires option == \\null || \\valid(option);"
    assert cleaned.startswith(guard)
    assert cleaned.count(guard) == 1
    assert "complete behaviors null_option, valid_option;" in cleaned
    assert "disjoint behaviors null_option, valid_option;" in cleaned
    for clause in ensures:
        assert clause in cleaned
    # Sanitizing a cached/generated answer again must not duplicate the guard.
    assert sanitize_contract_reply(cleaned, question) == cleaned


def test_nullable_behavior_removes_conflicting_global_pointer_clauses() -> None:
    reply = """requires \\valid(option);
ensures option->radius == radius;
behavior null_option:
  assumes option == \\null;
  assigns \\nothing;
behavior valid_option:
  assumes option != \\null;
  requires \\valid(option);
  assigns option->radius;
  ensures option->radius == radius;
complete behaviors null_option, valid_option;
disjoint behaviors null_option, valid_option;"""
    cleaned = remove_nullable_behavior_conflicts(reply)
    assert cleaned.startswith("behavior null_option:")
    assert cleaned.count("requires \\valid(option);") == 1
    assert cleaned.count("ensures option->radius == radius;") == 1


def test_annotation_parse_failure_is_reported_before_wp() -> None:
    failure = _classify_failure(
        "[kernel:annot-error] sample.c:31: Warning:\n"
        "unexpected token '>'\n"
        "Frama-C aborted: invalid user input.",
        invalid_markers=[Path("sample_Invalid.txt")],
    )
    assert failure["category"] == "acsl-syntax"
    assert "before any WP proof obligation" in failure["summary"]


def test_syntax_check_stops_before_wp_and_writes_marker(tmp_path, monkeypatch) -> None:
    class Completed:
        returncode = 1
        stdout = b"[kernel:annot-error] sample.c:3: unexpected token '>'\n"
        stderr = b"[kernel] Frama-C aborted: invalid user input.\n"

    monkeypatch.setattr("engine.autospec.src.framac.subprocess.run", lambda *args, **kwargs: Completed())
    marker = run_framac_syntax_check(str(tmp_path), "sample.c")
    assert marker is not None
    marker_path = Path(marker)
    assert marker_path.name == "sample_Invalid.txt"
    assert "annot-error" in marker_path.read_text(encoding="utf-8")


def test_successful_single_artifacts_keep_only_final_iteration(tmp_path) -> None:
    source = tmp_path / "sample.c"
    source.write_text("int main(void) { return 0; }\n", encoding="utf-8")
    Path(str(source) + ".pickle").write_bytes(b"trace")
    output = tmp_path / "output"
    failed_iteration = output / "sample_0001"
    failed_iteration.mkdir(parents=True)
    (failed_iteration / "sample_gen_0.c").write_text("bad", encoding="utf-8")

    RunManager._compact_successful_single_artifacts(
        source,
        output,
        {
            "status": "Pass",
            "result_code": "/*@ assigns \\nothing; */\nint main(void) { return 0; }\n",
            "proof_stats": {"proved_goals": 1, "total_goals": 1},
        },
    )

    assert sorted(path.name for path in output.iterdir()) == ["final_result", "final_verified.c"]
    assert not Path(str(source) + ".pickle").exists()


def test_verified_single_cache_requires_identical_source_and_closed_proof(tmp_path) -> None:
    source = tmp_path / "sample.c"
    source.write_text("int main(void) { return 0; }\n", encoding="utf-8")
    source_sha = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    candidate = SimpleNamespace(
        task_id="cached",
        mode="single",
        status="pass",
        demo_case_id="demo",
        metadata={"input_manifest": [{"sha256": source_sha}]},
    )
    store = SimpleNamespace(
        list_tasks=lambda limit: [candidate],
        read_result=lambda task_id: {
            "status": "Pass",
            "result_code": "verified",
            "proof_stats": {"proved_goals": 2, "total_goals": 2, "open_goals": 0},
        },
    )
    manager = object.__new__(RunManager)
    manager.store = store
    current = SimpleNamespace(task_id="new", demo_case_id="demo")

    cached = manager._find_verified_single_cache(current, source)
    assert cached is not None
    assert cached[0].task_id == "cached"


def test_verified_single_cache_skips_cache_chains(tmp_path) -> None:
    source = tmp_path / "sample.c"
    source.write_text("int main(void) { return 0; }\n", encoding="utf-8")
    source_sha = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
    cached = SimpleNamespace(
        task_id="cached-cache-hit",
        mode="single",
        status="pass",
        demo_case_id="demo",
        metadata={"input_manifest": [{"sha256": source_sha}]},
    )
    live = SimpleNamespace(
        task_id="real-verifier-run",
        mode="single",
        status="pass",
        demo_case_id="demo",
        metadata={"input_manifest": [{"sha256": source_sha}]},
    )
    results = {
        "cached-cache-hit": {
            "status": "Pass",
            "result_code": "verified",
            "proof_stats": {"proved_goals": 2, "total_goals": 2, "open_goals": 0},
            "engine_detail": {"cache_hit": True},
        },
        "real-verifier-run": {
            "status": "Pass",
            "result_code": "verified",
            "proof_stats": {"proved_goals": 2, "total_goals": 2, "open_goals": 0},
            "engine_detail": {"cache_hit": False},
        },
    }
    manager = object.__new__(RunManager)
    manager.store = SimpleNamespace(
        list_tasks=lambda limit: [cached, live],
        read_result=lambda task_id: results[task_id],
    )

    found = manager._find_verified_single_cache(
        SimpleNamespace(task_id="new", demo_case_id="demo"), source
    )
    assert found is not None
    assert found[0].task_id == "real-verifier-run"
