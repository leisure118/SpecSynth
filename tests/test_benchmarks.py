from fastapi.testclient import TestClient
from apps.api.app.main import app

client=TestClient(app)

def test_benchmark_catalog_preserves_reported_metrics_and_names():
    rows={x['id']:x for x in client.get('/api/v1/benchmarks').json()['items']}
    assert rows['live25']['name']=='LiveFMBench 2025'
    assert rows['live24']['name']=='LiveFMBench 2024'
    assert rows['autobench_v2']['name']=='autobench'
    assert rows['live25']['summary']['pass@5']['passed']==297
    assert rows['autobench_v2']['indexed_total']==262
    assert rows['autobench_v2']['reported_total']==257

def test_flagged_file_keeps_goal_rate_but_is_not_passed():
    data=client.get('/api/v1/benchmarks/live25').json()
    flagged=next(r for r in data['items'] if r['status']=='flagged')
    r=client.get('/api/v1/benchmarks/live25/file',params={'file':flagged['path']}).json()
    assert r['status']=='flagged'
    assert r['source'] is not None
    assert 'admit' in r['source']
    assert 'artifacts' not in r

def test_missing_artifacts_and_zero_goals_are_not_reported_as_passed():
    r=client.get('/api/v1/benchmarks/live25/file',params={'file':'array-cav19_array_doub_access_init_const.c'}).json()
    assert r['status']=='failed'
    assert r['goal_rate'] is None
    assert r['source'] is not None
    assert r['original_source'] == r['source']
    assert r['annotated_source'] is None
    assert r['original_filename']=='array-cav19_array_doub_access_init_const.c'

def test_benchmark_paths_are_only_resolved_from_index():
    assert client.get('/api/v1/benchmarks/unknown').status_code==404
    assert client.get('/api/v1/benchmarks/live25/file',params={'file':'../../.env'}).status_code==404


def test_original_sources_preserve_all_live_cases_and_historical_metrics():
    rows={x['id']:x for x in client.get('/api/v1/benchmarks').json()['items']}
    assert rows['live25']['original_source_count']==360
    assert rows['live24']['original_source_count']==284
    assert rows['autobench_v2']['original_source_count']==257
    assert rows['live25']['summary']['pass@5']['passed']==297
    r=client.get('/api/v1/benchmarks/live24/file',params={'file':"nabinkrsah_Sum of first n numbers using 'while' loop with precondition and postcondition.c"}).json()
    assert r['original_source'] is not None
    assert '‘while’' in r['original_filename']
