import json
from pathlib import Path
from fastapi.testclient import TestClient
from apps.api.app.main import app
from scripts.import_opus_benchmarks import import_bundle

client=TestClient(app)


def test_opus_configuration_is_separate_and_keeps_five_attempt_budget():
    rows={b['id']:b for b in client.get('/api/v1/benchmarks').json()['items']}
    assert rows['live25']['model']=='deepseek-v4-flash'
    assert rows['live25']['summary']['pass@5']['passed']==297
    expected={'opus46_live25':(273,339,360),'opus46_live24':(273,282,284),'opus46_autobench':(237,254,257)}
    for bid,(first,fifth,total) in expected.items():
        b=rows[bid]
        assert b['configuration_label']=='Claude Code + opus 4.6 + spec-skill'
        assert b['summary']['pass@1']['passed']==first
        assert b['summary']['pass@5']['passed']==fifth
        assert b['reported_total']==b['original_source_count']==total
    b=rows['opus46_live25'];assert b['passed_after_round5']==1 and b['passed_count']==340
    cases=client.get('/api/v1/benchmarks/opus46_live25').json()['items']
    assert sum(r['status']=='passed' and 1<=r['round']<=5 for r in cases)==339


def test_opus_file_has_both_code_versions_and_real_log_but_cheat_is_flagged():
    r=client.get('/api/v1/benchmarks/opus46_live24/file',params={'file':'code2_103.c'}).json()
    assert r['original_source'] and r['annotated_source'] and r['log']
    assert r['original_sha256'] and 'loop invariant' in r['annotated_source']
    cheat=client.get('/api/v1/benchmarks/opus46_autobench/file',params={'file':'241.c'}).json()
    assert cheat['status']=='flagged' and cheat['goal_rate']==100
    assert client.get('/api/v1/benchmarks/opus46_live24/file',params={'file':'../../.env'}).status_code==404


def test_import_does_not_count_zero_goals_cheats_or_sixth_round_as_pass5(tmp_path):
    source=tmp_path/'input';dest=tmp_path/'dest';dest.mkdir()
    old={'id':'existing','summary':{'pass@5':{'passed':10}}}
    (dest/'index.json').write_text(json.dumps([old]))
    rows=[{'file':'early','status':'pass','round':1,'proved':1,'total':1},
          {'file':'late','status':'pass','round':6,'proved':1,'total':1},
          {'file':'empty','status':'pass','round':1,'proved':0,'total':0},
          {'file':'cheat','status':'pass','round':1,'proved':1,'total':1,'error':'admit cheat'}]
    for folder in ('live25','live24','autobench'):
        p=source/folder;p.mkdir(parents=True)
        (p/'results.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
    imported=import_bundle(source,dest)
    assert all(b['summary']['pass@1']['passed']==b['summary']['pass@5']['passed']==1 for b in imported)
    assert all(b['passed_after_round5']==1 for b in imported)
    assert json.loads((dest/'index.json').read_text())[0]==old
