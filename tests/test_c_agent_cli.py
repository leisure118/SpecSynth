import json,subprocess,sys
from pathlib import Path
from engine.c_agent_cli import project_event

ROOT=Path(__file__).resolve().parents[1]


def test_native_tool_progress_does_not_publish_reasoning():
    assert project_event('codex',{'type':'item.completed','item':{'type':'reasoning','text':'private'}})==[]
    assert project_event('codex',{'type':'item.started','item':{'type':'mcp_tool_call','id':'proof'}})[0]['status']=='running'
    assert project_event('claude-code',{'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'1','is_error':True}]}})[0]['status']=='failed'


def test_mcp_rejects_source_changes_before_invoking_verifier(tmp_path):
    work=tmp_path/'work';work.mkdir()
    manifest=tmp_path/'original.json';manifest.write_text(json.dumps([{'path':'main.c','content':'int main(){return 0;}'}]))
    (work/'answer.json').write_text(json.dumps({'files':[{'path':'main.c','content':'int main(){return 1;}'}]}))
    requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'verify_candidate','arguments':{}}}]
    run=subprocess.run([sys.executable,str(ROOT/'scripts/c_verifier_mcp.py'),str(work),str(manifest)],input='\n'.join(map(json.dumps,requests))+'\n',capture_output=True,text=True,check=True)
    replies=[json.loads(l) for l in run.stdout.splitlines()]
    assert replies[0]['result']['serverInfo']['name']=='platform-frama-c'
    assert replies[1]['result']['isError'] and '原始程序' in replies[1]['result']['content'][0]['text']
    assert not (work/'platform-verification.json').exists()


def test_mcp_prepares_real_slices_without_claiming_proof(tmp_path):
    work=tmp_path/'work';work.mkdir()
    manifest=tmp_path/'original.json';manifest.write_text(json.dumps([{'path':'main.c','content':'int main(void) {\n return 0;\n}\n'}]))
    request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'prepare_project','arguments':{}}}
    result=subprocess.run([sys.executable,str(ROOT/'scripts/c_verifier_mcp.py'),str(work),str(manifest)],input=json.dumps(request)+'\n',capture_output=True,text=True,check=True)
    reply=json.loads(result.stdout)['result'];assert not reply.get('isError')
    db=json.loads((work/'output/contracts.json').read_text())
    assert db['main']['status']=='pending' and db['main']['contract'] is None
    assert (work/'output/layer0/main/main.c').is_file()
    assert (work/'output/layer0/main/main.inline.c').is_file()


def test_private_docker_config_keeps_plugins_but_no_registry_auth(tmp_path,monkeypatch):
    from engine.docker_runtime import configure_docker
    fake=tmp_path/'home';config=fake/'.docker';config.mkdir(parents=True)
    plugins=tmp_path/'plugins';plugins.mkdir()
    (config/'config.json').write_text(json.dumps({'auths':{'private':{'auth':'secret'}},'cliPluginsExtraDirs':[str(plugins)]}))
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:fake))
    env={'PATH':'/usr/bin','PYTHONPATH':'/project'};work=tmp_path/'work';work.mkdir()
    passed=configure_docker(work,env)
    written=json.loads((work/'.docker/config.json').read_text())
    assert str(plugins) in written['cliPluginsExtraDirs'] and 'auths' not in written
    assert passed['DOCKER_CONFIG']==str(work/'.docker')
    assert 'secret' not in json.dumps(passed)


def test_complex_budget_is_bounded_transparent_and_can_be_disabled():
    from apps.api.app.time_budget import c_budget
    simple=[{'path':'a.c','content':'int f(){return 1;}'}]
    complex=[{'path':'a.c','content':'int f(){int x=0;while(x<2)x++;for(;x<4;x++);return x;}'}]
    assert c_budget(simple)['effective_sec']==200
    assert c_budget(complex)['effective_sec']==600
    assert c_budget(complex,900)['effective_sec']==900
    assert c_budget(complex,200,False)['effective_sec']==200
    assert c_budget([{'path':'a.c','content':'/* while(x) for(x) */ int f(){return 0;}'}])['effective_sec']==200


def test_codex_mcp_receives_native_verifier_environment(tmp_path,monkeypatch):
    monkeypatch.setenv('ACSL_VERIFIER_RUNTIME','host')
    from types import SimpleNamespace
    from engine import c_agent_cli as cli
    files=[{'path':'main.c','content':'int main(){return 0;}'}];seen={}
    monkeypatch.setattr(cli,'command',lambda agent:['fake-codex'])
    monkeypatch.setattr(cli.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0))
    class Process:
        returncode=0
        def __init__(self,args,**kw):
            seen['args']=args;seen['env']=kw['env'];self.out=kw['stdout']
            (Path(kw['cwd'])/'answer.json').write_text(json.dumps({'patches':[]}))
        def communicate(self,payload,timeout):
            events=[{'type':'item.completed','item':{'type':'mcp_tool_call','id':'p','server':'frama','tool':'verify_candidate','status':'completed','result':{'content':[{'type':'text','text':'{"verified":true}'}]}}},{'type':'turn.completed'}]
            self.out.write(('\n'.join(map(json.dumps,events))+'\n').encode())
    monkeypatch.setattr(cli.subprocess,'Popen',Process)
    result=cli.generate('codex','Original source:\n'+json.dumps(files),{'model':'test','base_url':'http://example.invalid/v1','api_key':'secret'},tmp_path/'agent',10)
    assert result['files']==files
    args=seen['args']
    assert not any(s.startswith('mcp_servers.frama.env.DOCKER_CONFIG=') for s in args)
    assert any(s.startswith('mcp_servers.frama.env.ACSL_VERIFIER_RUNTIME=') and 'host' in s for s in args)
    assert any(s.startswith('mcp_servers.frama.env.PYTHONPATH=') for s in args)
    assert not any(s.startswith('mcp_servers.frama.env.NL2VERUS_AGENT_KEY=') for s in args)


def test_verifast_mcp_runs_verifast_without_acsl_slicing(tmp_path,monkeypatch):
    monkeypatch.setenv("VERIFAST_RUNTIME","host")
    from engine.verification.verifast_runtime import binary
    import pytest
    if not binary():pytest.skip('Native VeriFast not installed')
    work=tmp_path/'vf';work.mkdir()
    source='int f(int x)\n//@ requires true;\n//@ ensures result == x;\n{return x;}\n'
    original='int f(int x)\n{return x;}\n'
    manifest=tmp_path/'original.json';manifest.write_text(json.dumps([{'path':'a.c','content':original}]))
    (work/'answer.json').write_text(json.dumps({'files':[{'path':'a.c','content':source}]}))
    request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'verify_candidate','arguments':{}}}
    run=subprocess.run([sys.executable,str(ROOT/'scripts/c_verifier_mcp.py'),str(work),str(manifest),'verifast'],input=json.dumps(request)+'\n',capture_output=True,text=True,check=True)
    reply=json.loads(run.stdout)['result']
    assert not reply.get('isError'),reply
    assert json.loads(reply['content'][0]['text'])['verified'] is True
    full=json.loads((work/'platform-verification.json').read_text())
    assert full['tool']=='verifast' and 'frama-c' not in full['command_text']
