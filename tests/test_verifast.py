import json,os,subprocess
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from acsl.infrastructure.settings import settings
from engine.verification import verifast_runtime as vf
from apps.api.app.verifast import router

SAMPLE='int increment(int x)\n//@ requires 0 <= x &*& x < 100;\n//@ ensures result == x + 1;\n{ return x + 1; }\n'
BINARY=Path(__file__).resolve().parents[1]/'runtime/tools/verifast/verifast-26.10/bin/verifast'


@pytest.mark.parametrize('path',['../a.c','/tmp/a.c','a\\b.c','a//b.c','a/./b.c','bad.py','C:/a.c'])
def test_unsafe_paths_rejected(path):
    with pytest.raises(ValueError):vf.validate_files([{'path':path,'content':SAMPLE}],path)


def test_duplicate_and_missing_entry_rejected():
    with pytest.raises(ValueError):vf.validate_files([{'path':'a.c','content':SAMPLE}]*2,'a.c')
    with pytest.raises(ValueError):vf.validate_files([{'path':'a.h','content':''}],'missing.c')


def envelope(result):return json.dumps(['VeriFast-Json',2,0,{'result':result}])


def test_exit_zero_does_not_make_a_failed_proof_pass(tmp_path):
    files=[{'path':'a.c','content':SAMPLE}]
    loc=['Lexed',[[str(tmp_path/'a.c'),3,20],[str(tmp_path/'a.c'),3,22]]]
    result=vf.parse_output(envelope(['SymbolicExecutionError',[],loc,'Cannot prove condition.',{}]),0,files,tmp_path)
    assert not result['verified'] and result['status']=='failed'
    assert result['diagnostics'][0]['line']==3 and len(result['diagnostics'])==1
    assert not vf.parse_output('0 errors found',0,files,tmp_path)['verified']
    assert not vf.parse_output(envelope(['success','0 errors found']),1,files,tmp_path)['verified']
    assert vf.parse_output(envelope(['success','0 errors found']),0,files,tmp_path)['verified']


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'runtime_dir',tmp_path)
    app=FastAPI();app.include_router(router)
    return TestClient(app)


def test_api_unavailable_snapshot_history_and_traversal(client,monkeypatch):
    monkeypatch.setattr(vf,'capabilities',lambda:{'ready':False,'runtime':None,'message':'not installed'})
    assert client.get('/api/v1/verifast/capabilities').json()['ready'] is False
    r=client.post('/api/v1/verifast/verify',json={'files':[{'path':'a.c','content':SAMPLE}],'entry':'a.c'})
    assert r.status_code==200 and r.json()['status']=='unavailable'
    identifier=r.json()['id']
    assert client.get('/api/v1/verifast/runs').json()['items'][0]['id']==identifier
    assert client.get('/api/v1/verifast/runs/'+identifier+'/input').json()['files'][0]['content']==SAMPLE
    assert client.get('/api/v1/verifast/runs/'+identifier+'/log').status_code==200
    assert client.get('/api/v1/verifast/runs/not-valid').status_code==404
    assert client.post('/api/v1/verifast/verify',json={'files':[{'path':'../a.c','content':SAMPLE}],'entry':'../a.c'}).status_code==422
    assert client.post('/api/v1/verifast/verify',json={'files':[{'path':'a.c','content':SAMPLE}],'entry':'a.c','timeout_sec':0}).status_code==422


@pytest.mark.skipif(not BINARY.exists(),reason='Official VeriFast binary not installed')
@pytest.mark.parametrize('scenario,status',[
 ('pass','verified'),('wrong_postcondition','failed'),('missing_contract','compile_error'),('assume','blocked')])
def test_real_official_binary_never_skips_missing_contracts_or_allows_assume(client,monkeypatch,scenario,status):
    monkeypatch.setenv('VERIFAST_BINARY',str(BINARY));monkeypatch.setenv('VERIFAST_RUNTIME','host')
    code=SAMPLE
    if scenario=='wrong_postcondition':code=code.replace('result == x + 1','result == x + 2')
    if scenario=='missing_contract':code='int increment(int x) { return x + 1; }\n'
    if scenario=='assume':code=code.replace('{ return','{\n//@ assume(false);\n return')
    r=client.post('/api/v1/verifast/verify',json={'files':[{'path':'a.c','content':code}],'entry':'a.c','timeout_sec':10})
    assert r.status_code==200
    d=r.json();assert d['status']==status and d['verified']==(status=='verified')
    if scenario=='assume':
        assert d['diagnostics'][0]['kind']=='unverified_assumption'
        return
    assert '-enforce_annotations' in d['command'] and '-safe_mode' in d['command']
    assert '-allow_assume' not in d['command'] and '-disable_overflow_check' not in d['command']
    if scenario=='wrong_postcondition':assert d['returncode']==0 and d['diagnostics'][0]['line']==3
    identifier=d['id'];assert (settings.runtime_dir/'verifast'/identifier/'source/a.c').read_text()==code
    assert client.get('/api/v1/verifast/runs/'+identifier).json()['source_hashes']==d['source_hashes']


def test_timeout_kills_owned_process_and_preserves_failure(monkeypatch,tmp_path):
    monkeypatch.setattr(settings,'runtime_dir',tmp_path)
    monkeypatch.setattr(vf,'capabilities',lambda:{'ready':True,'runtime':'host','message':'ready'})
    monkeypatch.setattr(vf,'binary',lambda:'/fake/verifast')
    killed=[];monkeypatch.setattr(vf.os,'killpg',lambda pid,sig:killed.append(pid))
    class Process:
        pid=123456;returncode=-9
        def __init__(self,*args,**kwargs):self.calls=0;assert 'API_KEY' not in kwargs['env']
        def wait(self,timeout=None):
            self.calls+=1
            if self.calls==1:raise subprocess.TimeoutExpired('verifast',1)
            return self.returncode
    monkeypatch.setattr(vf.subprocess,'Popen',Process)
    result=vf.verify([{'path':'a.c','content':SAMPLE}],'a.c',1)
    assert result['status']=='timeout' and not result['verified'] and killed==[123456]


@pytest.mark.skipif(not BINARY.exists(),reason='Official VeriFast binary not installed')
def test_real_project_relative_header_include_is_whitelisted(client,monkeypatch):
    monkeypatch.setenv('VERIFAST_BINARY',str(BINARY));monkeypatch.setenv('VERIFAST_RUNTIME','host')
    code='#include "../include/config.h"\n'+SAMPLE.replace('100','BOUND')
    files=[{'path':'src/main.c','content':code},{'path':'include/config.h','content':'#define BOUND 100\n'}]
    d=client.post('/api/v1/verifast/verify',json={'files':files,'entry':'src/main.c','timeout_sec':10}).json()
    assert d['verified'],d['message']
    assert '../include/config.h' in d['command']


def test_assume_text_in_c_strings_or_ordinary_comments_is_not_a_bypass():
    files=[{'path':'a.c','content':'// assume(false) is disallowed\nconst char *s="//@ assume(false);";'}]
    assert vf.bypass_diagnostics(files)==[]


@pytest.mark.parametrize('count',[0,1,3,123])
def test_native_statement_count_is_exposed_without_inventing_proof_total(tmp_path,count):
    message=f'0 errors found ({count} statements verified)'
    result=vf.parse_output(json.dumps(['VeriFast-Json',2,0,{'result':['success',message]}]),0,[{'path':'a.c','content':'int x;'}],tmp_path)
    assert result['verified_statements']==count
    assert 'total_goals' not in result
    assert result['verification_scope']=='compilation_unit'
