"""Scoped MCP tool: validate one task's candidate and run platform Frama-C."""
from pathlib import Path
import sys,json,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
workspace=Path(sys.argv[1]).resolve();manifest=Path(sys.argv[2]).resolve()


def prepare():
    from engine.spectool_core import slice_engine
    source=json.loads(manifest.read_text());folder=workspace/'input';folder.mkdir(exist_ok=True)
    for item in source:
        target=folder/item['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(item['content'])
    _,functions,_,_=slice_engine.build_project_index(str(folder))
    layers,graph=slice_engine.compute_layers(functions)
    output=workspace/'output';output.mkdir(exist_ok=True)
    db={}
    for name,info in functions.items():
        if not __import__('re').fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name):raise ValueError('Invalid function name')
        directory=output/('layer'+str(layers[name]))/name;directory.mkdir(parents=True,exist_ok=True)
        for mode,suffix in [('stub','.c'),('inline','.inline.c')]:
            code=slice_engine.generate_slice(name,str(folder),mode)
            if code is None:raise ValueError('Could not create slice')
            (directory/(name+suffix)).write_text(code)
        db[name]={'layer':layers[name],'callees':sorted(graph.get(name,[])),'signature':slice_engine.extract_function_declaration(info),'status':'pending','contract':None}
    (output/'contracts.json').write_text(json.dumps(db,ensure_ascii=False,indent=2))
    return {'functions':db,'directory':'output','next':'Read slices, generate ACSL annotations bottom-up, preserve original input paths in answer.json, and invoke verify_candidate.'}


def verify():
    from apps.api.app.agent_execution import validate_candidates,verify_candidates
    source=json.loads(manifest.read_text());target=workspace/'answer.json'
    if target.is_symlink() or not target.is_file() or target.stat().st_size>2*1024*1024:raise ValueError('Write a valid answer.json in the task workspace first.')
    candidate=validate_candidates(source,json.loads(target.read_text())['files'],False,source[0]['path'],'single')
    with tempfile.TemporaryDirectory(dir=workspace) as folder:
        result=verify_candidates(candidate,source[0]['path'],'inter-modular',Path(folder),90)
    (workspace/'platform-verification.json').write_text(json.dumps(result,ensure_ascii=False))
    return result


for line in sys.stdin:
    try:
        request=json.loads(line);method=request.get('method');identifier=request.get('id')
        if identifier is None:continue
        if method=='initialize':result={'protocolVersion':request.get('params',{}).get('protocolVersion','2024-11-05'),'capabilities':{'tools':{}},'serverInfo':{'name':'platform-frama-c','version':'1.0'}}
        elif method=='ping':result={}
        elif method=='tools/list':result={'tools':[{'name':'prepare_project','description':'Perform deterministic spec-split: create function DAG layers, contract skeleton and stub/inline slices for this fixed input project.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},{'name':'verify_candidate','description':'Independently check answer.json preserves original C tokens and assertions, then run real Frama-C/WP. Read actual diagnostics and repair annotations until verified is true.','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]}
        elif method=='tools/call':
            name=request.get('params',{}).get('name')
            if name not in ('verify_candidate','prepare_project'):raise ValueError('Unknown tool')
            try:result={'content':[{'type':'text','text':json.dumps(verify() if name=='verify_candidate' else prepare(),ensure_ascii=False)}]}
            except Exception as exc:result={'isError':True,'content':[{'type':'text','text':str(exc)}]}
        else:raise ValueError('Unsupported method')
        print(json.dumps({'jsonrpc':'2.0','id':identifier,'result':result},ensure_ascii=False),flush=True)
    except Exception as exc:
        print(json.dumps({'jsonrpc':'2.0','id':request.get('id') if 'request' in locals() else None,'error':{'code':-32603,'message':str(exc)}}),flush=True)
