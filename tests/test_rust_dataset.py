from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.app import rust


def test_dataset_stats_filter_pagination_and_full_reference(monkeypatch):
    rows=[{'sample_id':'NL-1','category':'Simple','description':'Safely add one.','function_signature':'fn increment(x: u64)','verified_verus':'FIRST ORIGINAL REFERENCE'},
          {'sample_id':'NL-2','category':'Loops','description':'Sum a sequence.','function_signature':'fn sum(values: Vec<u64>)','verified_verus':'SECOND ORIGINAL REFERENCE'},
          {'sample_id':'NL-3','category':'Simple','description':'Add two.','function_signature':'fn add(x: u64)','verified_verus':'THIRD ORIGINAL REFERENCE'}]
    monkeypatch.setattr(rust,'load_tasks',lambda:tuple(rows))
    app=FastAPI();app.include_router(rust.router);client=TestClient(app)
    base='/api/v1/rust/dataset'
    assert client.get(base+'/stats').json()=={'total':3,'categories':{'Loops':1,'Simple':2},'source':'NL2VBench'}
    result=client.get(base+'/tasks',params={'category':'simple','page_size':1,'page':2}).json()
    assert result['total']==2 and result['pages']==2 and result['items'][0]['sample_id']=='NL-3'
    assert 'verified_verus' not in result['items'][0]
    for query in ['increment','NL-1','safely']:
        assert client.get(base+'/tasks',params={'query':query}).json()['items'][0]['sample_id']=='NL-1'
    assert client.get(base+'/tasks/NL-2').json()['verified_verus']==rows[1]['verified_verus']
    assert client.get(base+'/tasks',params={'query':'nothing'}).json()['total']==0
    assert client.get(base+'/tasks/missing').status_code==404
    for params in [{'page':0},{'page_size':51},{'query':'a'*201}]:
        assert client.get(base+'/tasks',params=params).status_code==422
