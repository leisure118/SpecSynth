import importlib.util
from pathlib import Path
from acsl.adapters.agent_runtime import AgentCallError
spec=importlib.util.spec_from_file_location('live25_runner',Path(__file__).resolve().parents[1]/'scripts/run_bailian_qwen9b_live25.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

def test_output_limit_does_not_trigger_service_failure_circuit():
    exc=AgentCallError('truncated');exc.code='output_limit'
    assert runner.runner_error_status(exc)=='output_limit'
    exc.code='agent_timeout';assert runner.runner_error_status(exc)=='timeout'
    exc.code='connection_error';assert runner.runner_error_status(exc)=='unavailable'

def test_pass_at_five_accepts_early_success_and_excludes_empty_proof():
    rows=[{'status':'passed','round':1,'total':2,'proved':2},{'status':'passed','round':4,'total':2,'proved':2},{'status':'passed','round':5,'total':0,'proved':0}]
    assert runner.metrics(rows)['pass@1']['passed']==1
    assert runner.metrics(rows)['pass@5']['passed']==2


def test_failed_patch_round_cannot_recover_previous_round_answer(tmp_path):
    import json
    (tmp_path/'workspace').mkdir()
    (tmp_path/'workspace/answer.json').write_text(json.dumps({'files':[{'path':'a.c','content':'int x;'}]}))
    (tmp_path/'harness-runtime.json').write_text(json.dumps({'agent_runtime':{'candidate_protocol':'acsl-patches-v1','terminal_reason':{'kind':'max-tokens'}}}))
    assert runner.recover_candidate(tmp_path,[{'path':'a.c','content':'int x;'}],'a.c') is None


def test_candidate_syntax_errors_are_not_classified_as_infrastructure():
    assert runner.failure_stage({'status':'compile_error'},0)=='specification_syntax'
    assert runner.failure_stage({'status':'blocked'},0)=='model_output'
    assert runner.failure_stage({'status':'failed'},22)=='proof'
    assert runner.failure_stage({'status':'unavailable'},0)=='infrastructure'


def test_gateway_context_mismatch_is_configuration_not_model_ability():
    assert runner.failure_stage({'status':'blocked','failure_category':'configuration'},0)=='configuration'
