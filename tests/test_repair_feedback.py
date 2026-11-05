from engine.verification.repair_feedback import compact_feedback

def test_feedback_keeps_failed_goal_and_bounded_output_without_changing_raw():
    log='Goal Passed\nProver Z3 returns Valid\n'+'warning '*3000+'\nGoal Assertion line 19\nProve: x == 0.\nProver Alt-Ergo returns Timeout\n'
    check={'status':'failed','message':'1/2','stdout':log,'diagnostics':[{'path':'a.c','line':19,'message':'assertion not proved'}]}
    out=compact_feedback(check)
    assert len(out)<=5000 and 'line 19' in out and 'x == 0' in out and 'returns Valid' not in out
    assert check['stdout']==log

def test_compact_plan_uses_platform_handoff_without_changing_skills():
    from engine.nl2verus.c_compact import task_prompt
    skill='ORIGINAL SKILL BODY'
    out=task_prompt(skill,auto_handoff=True)
    assert out.startswith(skill)
    assert 'Do not copy, rephrase, re-emit or write that JSON' in out


def test_parser_type_error_retains_location_and_specific_precedence_hint():
    from engine.verification.diagnostics import verification_diagnostics
    log='[kernel:annot-error] /app/a.c:13: Warning: \n  invalid operands to binary |; unexpected 𝔹 and ℤ. Ignoring logic specification\n'
    files=[{'path':'a.c','content':'\n'*20}]
    diagnostics=verification_diagnostics(log,files)
    assert diagnostics[0]['line']==13 and diagnostics[0]['kind']=='type'
    check={'status':'compile_error','stdout':log,'diagnostics':diagnostics}
    out=compact_feedback(check)
    assert 'ENTIRE bitwise' in out and '"line": 13' in out


def test_multiline_syntax_error_is_located_for_editor_and_repair():
    from engine.verification.diagnostics import verification_diagnostics
    log='[kernel] /app/a.c:12: \n  syntax error:\n  Location: between lines 12 and 14\n'
    diagnostics=verification_diagnostics(log,[{'path':'a.c','content':'\n'*20}])
    assert diagnostics[0]['line']==12 and diagnostics[0]['kind']=='syntax'
    assert 'BEFORE the full loop contract' in compact_feedback({'stdout':log,'diagnostics':diagnostics})
