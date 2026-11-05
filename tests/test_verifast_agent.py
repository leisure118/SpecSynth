"""Mock model transport, real VeriFast proof: never issue paid model calls from tests."""
import json
from types import SimpleNamespace
import pytest
from acsl.application import agent_execution as execution
from acsl.contracts.runs import RunRequest
from engine.verification import verifast_runtime

SOURCE='int count_to_limit(int limit)\n{\n int count = 0;\n while (count < limit) {\n  count = count + 1;\n }\n return count;\n}\n'
GOOD=SOURCE.replace('\n{','\n//@ requires 0 <= limit &*& limit <= 100000;\n//@ ensures result == limit;\n{',1).replace('while (count < limit) {','while (count < limit)\n //@ invariant 0 <= count &*& count <= limit;\n {')
BAD=GOOD.replace('result == limit','result == limit + 1')

@pytest.mark.parametrize('agent',['codex','claude-code','deepseek-harness'])
def test_generation_then_failed_proof_repair_uses_only_verifast(tmp_path,monkeypatch,agent):
    if not verifast_runtime.binary():pytest.skip('Native VeriFast not installed')
    source=tmp_path/'source.c';source.write_text(SOURCE)
    calls=[];artifacts=[]
    def generate(a,prompt,directory,timeout,model,**options):
        calls.append((a,prompt,model,options))
        assert options['verification_tool']=='verifast'
        assert 'Platform verification tool: VeriFast' in prompt
        assert 'Platform source classification: acsl' not in prompt
        return [{'path':'count.c','content':BAD if len(calls)==1 else GOOD}]
    monkeypatch.setattr(execution,'generate',generate)
    monkeypatch.setattr(execution,'verifier_preflight',lambda *args:pytest.fail('Frama-C preflight must not run'))
    store=SimpleNamespace(read_upload=lambda _: {'stored_path':str(source)},write_task=lambda _:None,
        write_text_artifact=lambda *args:artifacts.append(args))
    task=SimpleNamespace(task_id='test',task_dir=str(tmp_path/'run'),mode='single',metadata={},phases=[],model_name='test')
    manager=SimpleNamespace(store=store,_advance_phase=lambda *args:None,_build_result=lambda task,**body:body,
        _unavailable_result=lambda *args:pytest.fail('VeriFast unavailable'))
    payload=RunRequest(file_id='snapshot',entry_path='count.c',assistant={'agent':agent},verification_tool='verifast',
        model_name='test',description='Input 0 <= limit <= 100000. Prove return equals limit.',max_repair_rounds=3)
    result=execution.execute_agent(manager,task,payload)
    assert result['status']=='Pass' and len(calls)==2
    assert 'Previous candidate:' in calls[1][1] and 'Verifier diagnostics:' in calls[1][1]
    assert result['engine_detail']['verifier']=='VeriFast'
    assert result['proof_stats']['scope']=='compilation-unit'
    assert result['engine_detail']['attempts'][0]['verification']['verified'] is False
    assert result['result_code']==GOOD and result['source_code']==SOURCE
    assert source.read_text()==SOURCE
    assert all('Frama-C' not in step['label'] for step in task.metadata['agent_progress']['steps'])
