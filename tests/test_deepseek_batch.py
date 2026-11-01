from scripts.run_deepseek_benchmarks import metrics

def test_batch_metrics_never_report_pending_as_final_rate():
    rows=[{'status':'passed','round':1,'proved':1,'total':1},{'status':'running','round':0}]
    assert metrics(rows)['pass@1']=={'passed':1,'total':2,'rate':None}
    rows[1]={'status':'failed','round':5}
    assert metrics(rows)['pass@5']=={'passed':1,'total':2,'rate':50.0}

def test_batch_five_round_budget():
    rows=[{'status':'passed','round':1,'proved':1,'total':1},{'status':'passed','round':5,'proved':1,'total':1},{'status':'passed','round':6,'proved':1,'total':1},{'status':'error','round':1}]
    assert metrics(rows)['pass@1']['rate']==25.0
    assert metrics(rows)['pass@5']['rate']==50.0


def test_zero_goals_cannot_be_counted_as_success():
    assert metrics([{'status':'passed','round':1,'proved':0,'total':0}])['pass@1']['rate']==0


def test_parallel_publish_keeps_all_dataset_updates(tmp_path,monkeypatch):
    import json
    from concurrent.futures import ThreadPoolExecutor
    from scripts import run_deepseek_benchmarks as batch
    monkeypatch.setattr(batch,'DATA',tmp_path)
    (tmp_path/'index.json').write_text('[]')
    snapshots=[{'benchmark':{'id':'b'+str(i)},'items':[{'status':'passed','round':1,'proved':1,'total':1}]} for i in range(6)]
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(batch.publish,snapshots))
    assert len(json.loads((tmp_path/'index.json').read_text()))==6


def test_proof_admission_releases_slot_after_exception(tmp_path,monkeypatch):
    import pytest
    from apps.api.app import proof_limits
    monkeypatch.setattr(proof_limits,'RUNTIME_DIR',tmp_path)
    monkeypatch.setenv('XUANJIAN_PROOF_CONCURRENCY','1')
    with pytest.raises(ValueError):
        with proof_limits.proof_slot(1):raise ValueError('test')
    with proof_limits.proof_slot(1) as left:assert left>0


def test_proof_admission_enforces_cross_process_slot_limit(tmp_path,monkeypatch):
    import pytest
    from apps.api.app import proof_limits
    monkeypatch.setattr(proof_limits,'RUNTIME_DIR',tmp_path)
    monkeypatch.setenv('XUANJIAN_PROOF_CONCURRENCY','1')
    with proof_limits.proof_slot(1):
        with pytest.raises(TimeoutError):
            with proof_limits.proof_slot(.02):pass


def test_queue_balances_remaining_cases_not_absolute_file_index():
    from scripts.run_deepseek_benchmarks import pending_jobs
    a={'items':[{'id':str(i),'status':'pending'} for i in range(20)]}
    b={'items':[{'id':str(i),'status':'passed' if i<10 else 'pending'} for i in range(20)]}
    jobs=list(pending_jobs([a,b]))
    assert [r['id'] for _,r in jobs[:4]]==['0','10','1','11']
    assert len(jobs)==30


def test_recovered_draft_preserves_program_and_original_assertion(tmp_path):
    import json
    from scripts.run_deepseek_benchmarks import recover_candidate
    original=[{'path':'main.c','content':'int main(){int x=1; //@ assert x == 1;\nreturn 0;}'}]
    folder=tmp_path/'workspace';folder.mkdir()
    target=folder/'answer.json'
    target.write_text(json.dumps({'files':[{'path':'main.c','content':'int main(){int x=1; return 0;}'}]}))
    assert recover_candidate(tmp_path,original,'main.c') is None
    target.write_text(json.dumps({'files':original}))
    assert recover_candidate(tmp_path,original,'main.c')==original
    target.write_text(json.dumps({'files':[{'path':'main.c','content':original[0]['content'].replace('x=1','x=2')}]}))
    assert recover_candidate(tmp_path,original,'main.c') is None


def test_compact_plan_keeps_native_delegation_and_independent_platform_proof():
    from engine.nl2verus.c_compact import task_prompt
    text=task_prompt('Original source:\n[]\nPrevious candidate: draft\nVerifier diagnostics: unproved')
    assert 'Previous candidate: draft' in text and 'Verifier diagnostics: unproved' in text
    assert 'native subagent tool ONCE' in text
    assert 'Do not run an internal proof' in text
    assert 'platform independently validates' in text
