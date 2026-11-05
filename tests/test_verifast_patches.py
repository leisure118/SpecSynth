import json,subprocess,sys
from pathlib import Path
import pytest
from engine.verification.spec_patches import merge_spec_patches,patch_contract,patch_line_map,normalize_patch_delimiters
from engine.verification.spec_edit import source_tokens
from engine.verification import verifast_runtime

SOURCE='int count_to_limit(int limit)\n{\n    int count = 0;\n    while (count < limit) {\n        count = count + 1;\n    }\n    return count;\n}\n'
FILES=[{'path':'count.c','content':SOURCE}]
PATCHES={'patches':[
 {'path':'count.c','before_line':2,'annotation':'//@ requires 0 <= limit &*& limit <= 100000;\n//@ ensures result == limit;'},
 {'path':'count.c','before_line':4,'before_column':SOURCE.splitlines()[3].index('{')+1,'annotation':'//@ invariant 0 <= count &*& count <= limit;'}]}


def test_verifast_patches_merge_at_loop_brace_without_changing_c_tokens():
    merged=merge_spec_patches(FILES,PATCHES,verification_tool='verifast')
    assert source_tokens(merged[0]['content'])==source_tokens(SOURCE)
    assert 'while (count < limit) \n//@ invariant' in merged[0]['content']
    assert 'before_column' in patch_contract(FILES,verification_tool='verifast')
    rows=patch_line_map(FILES,PATCHES,verification_tool='verifast')
    assert any(r.get('original_column')==SOURCE.splitlines()[3].index('{')+1 for r in rows)
    if verifast_runtime.binary():
        check=verifast_runtime.verify(merged,'count.c',30)
        assert check['verified'],check['message']


def test_delimiter_normalization_preserves_expressions_and_rejects_c_code():
    malformed={'patches':[{'path':'count.c','before_line':4,'annotation':'@@ loop invariant 0 <= count <= limit;\nloop assigns count;\nloop variant limit - count;\n@@'}]}
    fixed,notes=normalize_patch_delimiters(malformed)
    assert fixed['patches'][0]['annotation']=='/*@\nloop invariant 0 <= count <= limit;\nloop assigns count;\nloop variant limit - count;\n*/'
    assert notes[0]['clauses_changed'] is False
    assert source_tokens(merge_spec_patches(FILES,malformed)[0]['content'])==source_tokens(SOURCE)
    bad={'patches':[{'path':'count.c','before_line':4,'annotation':'@@ return 1; @@'}]}
    with pytest.raises(ValueError,match='完整 ACSL'):merge_spec_patches(FILES,bad)
    with pytest.raises(ValueError,match='不能使用 ACSL'):merge_spec_patches(FILES,malformed,verification_tool='verifast')


def test_native_receipt_validator_uses_selected_dialect_and_records_normalization():
    root=Path(__file__).resolve().parents[1]
    for tool,data in [('verifast',PATCHES),('framac',{'patches':[{'path':'count.c','before_line':4,'annotation':'@@ loop invariant 0 <= count <= limit;\nloop assigns count;\nloop variant limit - count;\n@@'}]})]:
        result=subprocess.run([sys.executable,'-m','engine.verification.patch_receipt'],cwd=root,input=json.dumps({'files':FILES,'data':data,'verification_tool':tool}),capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        if tool=='framac':assert json.loads(result.stdout)['delimiter_normalization'][0]['clauses_changed'] is False


@pytest.mark.parametrize('column',[0,-1,999,True,'12'])
def test_invalid_columns_are_rejected(column):
    bad={'patches':[{**PATCHES['patches'][1],'before_column':column}]}
    with pytest.raises(ValueError):merge_spec_patches(FILES,bad,verification_tool='verifast')


def test_verifast_delimiter_normalization_still_requires_real_verifast_proof():
    data={'patches':[{**p,'annotation':'@@ '+p['annotation'].replace('//@ ','').strip()+'\n@@'} for p in PATCHES['patches']]}
    fixed,notes=normalize_patch_delimiters(data,'verifast')
    assert len(notes)==2 and fixed['patches'][0]['annotation'].startswith('//@ requires')
    merged=merge_spec_patches(FILES,data,verification_tool='verifast')
    assert source_tokens(merged[0]['content'])==source_tokens(SOURCE)
    if verifast_runtime.binary():
        result=verifast_runtime.verify(merged,'count.c',30)
        assert result['verified'],result['message']


def test_rejected_worker_patches_are_repair_context_not_accepted_source(tmp_path):
    from engine.verification.spec_patches import recover_patch_candidate,repairable_patch_receipt
    workspace=tmp_path/'workspace';workspace.mkdir()
    rejected={'patches':[{'path':'count.c','before_line':1,'annotation':'/* requires 0 <= limit; ensures result == limit; */'}]}
    (workspace/'.platform-worker-final.txt').write_text(json.dumps(rejected))
    assert recover_patch_candidate(workspace)==rejected
    assert repairable_patch_receipt(tmp_path)
    with pytest.raises(ValueError,match='完整 VeriFast'):
        merge_spec_patches(FILES,rejected,'verifast')
    assert not (workspace/'candidate-patches.json').exists()
    (workspace/'.platform-worker-final.txt').write_text('{"patches":[]}')
    assert not repairable_patch_receipt(tmp_path)
    (workspace/'.platform-worker-final.txt').write_text('Generated successfully')
    assert not repairable_patch_receipt(tmp_path)


def test_bare_acsl_frame_and_variant_rejected_for_verifast():
    for clause in ('assigns count;','variant limit - count;'):
        with pytest.raises(ValueError,match='不能使用 ACSL'):
            merge_spec_patches(FILES,{'patches':[{**PATCHES['patches'][1],'annotation':'//@ '+clause}]},'verifast')
