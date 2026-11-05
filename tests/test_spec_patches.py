import json
import pytest
from engine.verification.spec_patches import merge_spec_patches,parse_patch_json,patch_line_map
FILES=[{'path':'a.c','content':'int main(){\n int i;\n for(i=0;i<2;i++){}\n return 0;\n}\n'}]
def patch(**kw):return {'patches':[{'path':'a.c','before_line':3,'annotation':'/*@ loop invariant 0 <= i <= 2; */',**kw}]}

def test_platform_inserts_only_annotations_and_retains_all_source():
    result=merge_spec_patches(FILES,patch())
    assert result[0]['content'].replace('/*@ loop invariant 0 <= i <= 2; */\n','')==FILES[0]['content']
    assert patch_line_map(FILES,patch())[2]=={'path':'a.c','generated_line':3,'original_line':3,'patch_index':0}
    assert patch_line_map(FILES,patch())[3]['original_line']==3

@pytest.mark.parametrize('change',[{'path':'../a.c'},{'before_line':0},{'before_line':True},{'before_line':99},{'annotation':'int i=1;'},{'annotation':'/*@ assert 1; */ return 1;'},{'annotation':'/*@ admit 1; */'},{'annotation':'/*@ loop invariant 1;'},{'annotation':'/* normal comment */'},{'anchor':'wrong source'}])
def test_invalid_patches_rejected(change):
    with pytest.raises(ValueError):merge_spec_patches(FILES,patch(**change))

def test_duplicate_positions_full_source_and_inline_comment_insertion_rejected():
    data=patch();data['patches']*=2
    with pytest.raises(ValueError):merge_spec_patches(FILES,data)
    with pytest.raises(ValueError):parse_patch_json(json.dumps({'files':FILES}))
    with pytest.raises(ValueError):merge_spec_patches([{'path':'a.c','content':'/* comment\n still comment */\nint x;'}],patch(before_line=2))

def test_crlf_and_multiple_files_remain_intact():
    files=[{'path':'a.c','content':'int x;\r\n'},{'path':'a.h','content':'int f();\n'}]
    result=merge_spec_patches(files,{'patches':[{'path':'a.c','before_line':1,'annotation':'/*@ assert 1; */'}]})
    assert result[0]['content'].endswith(files[0]['content']) and result[1]==files[1]


@pytest.mark.parametrize('worker_mode',['off','on'])
def test_real_adapter_repairs_patch_receipts_without_rewriting_source(tmp_path,monkeypatch,worker_mode):
    from engine.nl2verus import dsh_cli
    from engine.nl2verus.harness_session import Session,case_session
    monkeypatch.setenv('XUANJIAN_HARNESS_COMPACT','1')
    monkeypatch.setenv('XUANJIAN_HARNESS_SPEC_PATCHES','1')
    monkeypatch.setattr(dsh_cli,'installed',lambda:True)
    monkeypatch.setenv('XUANJIAN_HARNESS_WORKER_THINKING',worker_mode)
    observed=[]
    def request(self,cmd,cwd,env,task,timeout,identity):
        observed.append((cwd,task,env.copy()))
        config=json.loads(__import__('pathlib').Path(cmd[cmd.index('--patch')+1]).read_text())
        providers=next(e['config']['providers'] for e in config if e.get('id')=='llm-pi-ai')
        child=providers['platform-subagent']
        assert child['reasoning']==('low' if worker_mode=='on' else 'off') and 'off' in child['models'][0]['reasoningEfforts']
        assert child['compat']['supportsDeveloperRole'] is False
        assert child['models'][0]['contextWindow']<=31744
        assert not (cwd/'candidate-patches.json').exists()
        index=self.rounds
        if index<2:
            body=patch(annotation='/*@ loop invariant 0 <= i <= %d; */'%(1 if index==0 else 2))
            (cwd/'candidate-patches.json').write_text(json.dumps(body))
        (cwd/'subagent-audit.jsonl').write_text(json.dumps({'type':'end','stop_reason':'completed'})+'\n' if index==0 else '')
        self.rounds+=1
        tool='delegate_spec' if index==0 else 'submit_spec_patches'
        return '\n'.join(map(json.dumps,[{'type':'session','sessionId':'same'},{'type':'tool_call','callId':'tool','tool':tool},{'type':'tool_result','callId':'tool','status':'completed'},{'type':'final','reason':{'kind':'completed'}}]))
    monkeypatch.setattr(Session,'request',request)
    profile={'model':'test','base_url':'http://invalid/v1','api_key':''}
    prompt='Pinned Skill\nOriginal source:\n'+json.dumps(FILES)
    from engine.nl2verus.model_provider import ProviderError
    with case_session():
        a=dsh_cli.generate(prompt,profile,output_format='files',artifact_dir=tmp_path/'first',require_subagent=True)
        continuation=prompt+'\nPrevious candidate:\n'+a['code']+'\nVerifier diagnostics:\nInvariant at line 3 is not preserved.'
        b=dsh_cli.generate(continuation,profile,output_format='files',artifact_dir=tmp_path/'second',require_subagent=True)
        assert '0 <= i <= 2' in json.loads(b['code'])['files'][0]['content']
        assert b['agent_runtime']['process_reused'] and b['agent_runtime']['candidate_protocol']=='acsl-patches-v1'
        assert observed[0][0]==observed[1][0]
        assert 'submit_spec_patches' in observed[1][1] and observed[1][2]['DSH_REPAIR_MODE']=='1'
        with pytest.raises(ProviderError,match='未提交新的规约补丁'):
            dsh_cli.generate(continuation,profile,output_format='files',artifact_dir=tmp_path/'third')
    assert not json.loads(a['code'])['files'][0]['content'].endswith('return 1;}')


def test_invalid_annotation_receipt_is_repairable_but_arbitrary_source_is_not(tmp_path):
    from engine.verification.spec_patches import repairable_patch_receipt
    work=tmp_path/'workspace';work.mkdir()
    receipt=work/'candidate-patches.json'
    receipt.write_text(json.dumps(patch(annotation='/*@ admit 1; */')))
    assert repairable_patch_receipt(tmp_path)
    receipt.write_text(json.dumps({'files':FILES}))
    assert not repairable_patch_receipt(tmp_path)


def test_native_receipt_validator_rejects_malformed_annotation_without_proof(tmp_path):
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','engine.verification.patch_receipt'],input=json.dumps({'files':FILES,'data':patch(annotation='@ loop invariant i >= 0;')}),capture_output=True,text=True)
    assert result.returncode==1 and 'ACSL' in result.stderr
    result=subprocess.run([sys.executable,'-m','engine.verification.patch_receipt'],input=json.dumps({'files':FILES,'data':patch()}),capture_output=True,text=True)
    assert result.returncode==0 and not result.stderr


@pytest.mark.parametrize('annotation',[
 '/*@ ensures \\result == ((x[0] | x[1])) | (x[2] | x[3]); */',
 '/*@ loop invariant i >= 0; */\n/*@ assert i >= 0; */',
])
def test_known_type_and_loop_attachment_errors_rejected_before_handoff(annotation):
    with pytest.raises(ValueError):merge_spec_patches(FILES,patch(annotation=annotation))


def test_complete_bitwise_expression_and_assert_before_contract_are_accepted():
    merge_spec_patches(FILES,patch(annotation='/*@ ensures \\result == ((x[0] | x[1]) | x[2]); */'))
    merge_spec_patches(FILES,patch(annotation='/*@ assert i >= 0; */\n/*@ loop invariant i >= 0; */'))


@pytest.mark.parametrize('annotation',[
 '//@ assert(i >= 0)',
 '/*@ assigns i; loop invariant i >= 0; */',
])
def test_missing_semicolon_and_wrong_assigns_rejected(annotation):
    with pytest.raises(ValueError):merge_spec_patches(FILES,patch(annotation=annotation))


def test_loop_contract_before_declaration_is_rejected():
    with pytest.raises(ValueError,match='实际循环'):
        merge_spec_patches(FILES,patch(before_line=2))


def test_empty_loop_candidate_is_not_accepted_as_generated_specification(tmp_path):
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','engine.verification.patch_receipt'],input=json.dumps({'files':FILES,'data':{'patches':[]}}),capture_output=True,text=True)
    assert result.returncode==1 and '未生成实际规约' in result.stderr


def test_coverage_does_not_extend_a_contract_across_code_or_declarations():
    from engine.verification.spec_patches import candidate_quality
    files=[{'path':'a.c','content':'int f(){\nint i;\n/*@ loop invariant i >= 0; */\nfor(i=0;i<2;i++){}\nfor(i=0;i<3;i++){}\n}'}]
    q=candidate_quality(files,{'patches':[]})
    assert q['loop_count_estimate']==2 and q['covered_loop_count_estimate']==1
    assert not q['coverage_is_proof']


def test_worker_adapter_preserves_skill_text_but_separates_execution_roles():
    from engine.verification.worker_contract import worker_prompt,thinking_policy
    skill='UNCHANGED: run spectool; save summary.json\nrequires x > 0;'
    task=worker_prompt(skill,FILES)
    assert skill in task and 'BEGIN UNCHANGED' in task
    assert 'platform owns' in task and 'never claim verified/pass/injected' in task
    assert 'Loop inventory' in task and 'loop assigns' in task


def test_thinking_modes_are_independent_and_validated(monkeypatch):
    from engine.verification.worker_contract import thinking_policy
    monkeypatch.setenv('XUANJIAN_HARNESS_MAIN_THINKING','off')
    monkeypatch.setenv('XUANJIAN_HARNESS_WORKER_THINKING','on')
    policy=thinking_policy()
    assert policy['main']=='off' and policy['worker']=='on' and policy['output_budget_includes_thinking']
    monkeypatch.setenv('XUANJIAN_HARNESS_WORKER_THINKING','unbounded')
    with pytest.raises(ValueError):thinking_policy()


def test_loop_assigns_accepts_whitespace_and_preserves_existing_annotations():
    merge_spec_patches(FILES,patch(annotation='/*@ loop invariant i >= 0; loop\n  assigns i; */'))
    from engine.verification.spec_patches import candidate_quality
    annotated=[{'path':'a.c','content':'int f(){\nint i;\n/*@ loop invariant i >= 0; */\nfor(i=0;i<2;i++){}\n}'}]
    q=candidate_quality(annotated,{'patches':[]})
    assert q['covered_loop_count_estimate']==q['loop_count_estimate']==1


def test_empty_or_status_only_worker_output_is_explained_as_generation_failure():
    from engine.verification.worker_contract import missing_receipt_message
    assert '空 patches' in missing_receipt_message('{"patches":[]}',FILES)
    assert '报告或无效 JSON' in missing_receipt_message('{"status":"pass"}',FILES)
    assert '静态检查' in missing_receipt_message(json.dumps(patch(annotation='//@ assert i >= 0')),FILES)
