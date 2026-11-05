import hashlib
import pytest
from engine.verification.report import normalize_verification

@pytest.mark.parametrize('tool,unit',[('framac','proof-goals'),('verus','verification-items')])
def test_native_metric_units_and_unknown_counts(tool,unit):
    report=normalize_verification({'status':'verified','verified':True,'verified_count':3,'error_count':0},tool)
    assert report['metric']==dict(unit=unit,verified=3,total=3,total_reported=True)
    assert normalize_verification({'status':'tool_error','verified':True},tool)['verified'] is False
    assert normalize_verification({'status':'failed','verified_count':None,'error_count':None},tool)['metric']['total'] is None


def test_verifast_statement_count_never_invents_goal_total():
    for ok in (True,False):
        report=normalize_verification({'status':'verified' if ok else 'failed','verified':ok,'verified_statements':3,'verified_count':1,'error_count':0},'verifast')
        assert report['metric']==dict(unit='verified-statements',verified=3,total=None,total_reported=False)


def test_diagnostics_resolve_exact_sources_and_attach_hash_without_ambiguous_basename():
    files=[{'path':'a/main.rs','content':'line one\nline two\n'},{'path':'b/main.rs','content':'other'}]
    check={'status':'failed','message':'unproved','stderr':'error\n --> /tmp/snapshot/a/main.rs:2:5\n --> main.rs:1:1'}
    report=normalize_verification(check,'verus',files)
    assert report['diagnostics'][0]['path']=='a/main.rs'
    assert report['diagnostics'][0]['source_hash']==hashlib.sha256(files[0]['content'].encode()).hexdigest()
    assert report['diagnostics'][1]['path'] is None and report['diagnostics'][1]['line'] is None
    assert 'report' not in check
