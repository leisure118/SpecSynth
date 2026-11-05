"""Independent VeriFast runner; original input snapshots, bounded execution, strict JSON verdicts."""
from __future__ import annotations
import hashlib,json,os,posixpath,re,shlex,shutil,signal,subprocess,tempfile,time,uuid
from pathlib import Path,PurePosixPath
from acsl.infrastructure.settings import settings
VERSION='26.10'
STDLIB=json.loads(Path(__file__).with_name('verifast_std_headers.json').read_text())


def binary():
    configured=os.getenv('VERIFAST_BINARY','').strip()
    path=Path(configured) if configured else settings.runtime_dir/'tools/verifast'/('verifast-'+VERSION)/'bin/verifast'
    if path.is_file() and os.access(path,os.X_OK):return str(path.resolve())
    return shutil.which(configured or 'verifast')


def capabilities():
    mode=os.getenv('VERIFAST_RUNTIME','host').strip().lower()
    if mode not in ('auto','host','container'):return {'ready':False,'runtime':None,'message':'VERIFAST_RUNTIME must be auto, host or container'}
    exe=binary()
    if exe and mode!='container':
        try:
            p=subprocess.run([exe,'-help'],capture_output=True,text=True,timeout=5)
            first=(p.stdout or p.stderr).splitlines()[0]
            if p.returncode==0 and first.startswith('VeriFast '):return {'ready':True,'runtime':'host','version':first,'message':'VeriFast 已就绪'}
        except (OSError,subprocess.SubprocessError,IndexError):pass
    if mode!='host' and shutil.which('docker'):
        try:
            p=subprocess.run(['docker','image','inspect','acsl-verifast:'+VERSION],capture_output=True,timeout=5)
            if p.returncode==0:return {'ready':True,'runtime':'container','version':VERSION,'message':'VeriFast 验证容器已就绪'}
        except (OSError,subprocess.SubprocessError):pass
    return {'ready':False,'runtime':None,'version':VERSION,'message':'VeriFast 尚未安装：运行 scripts/install_verifast.py，或构建 verifast Docker 服务。'}


def validate_files(files,entry):
    if not 1<=len(files)<=64:raise ValueError('提交 1–64 个源文件。')
    seen=set();size=0
    for f in files:
        path=f['path'];p=PurePosixPath(path)
        if not path or p.is_absolute() or '\\' in path or ':' in path or any(ord(c)<32 for c in path) or any(s in ('','.','..') for s in path.split('/')) or p.suffix not in ('.c','.h','.gh') or path in seen:
            raise ValueError('文件路径必须是唯一的工程内 C、H 或 GH 相对路径。')
        seen.add(path);size+=len(f['content'].encode())
    if size>2*1024*1024:raise ValueError('工程超过 2 MiB 限制。')
    if entry not in seen or not entry.endswith('.c'):raise ValueError('请选择工程中的 C 文件作为验证入口。')


def _locations(value,files,root):
    locations=[];known={f['path']:f['content'] for f in files}
    def walk(x):
        if not isinstance(x,list):return
        if len(x)==2 and x[0]=='Lexed':
            try:
                path,line,column=x[1][0];relative=Path(path).relative_to(root).as_posix()
                if relative in known and 1<=line<=len(known[relative].splitlines()):locations.append({'path':relative,'line':line,'column':column,'severity':'error','certainty':'reported'})
            except (ValueError,TypeError,IndexError):pass
        for item in x:walk(item)
    walk(value);return list({(d['path'],d['line'],d['column']):d for d in locations}.values())[:100]


def parse_output(stdout,returncode,files,root):
    envelope=None
    for line in stdout.splitlines():
        try:
            data=json.loads(line)
            if isinstance(data,list) and len(data)==4 and data[:3]==['VeriFast-Json',2,0]:envelope=data[3]
        except ValueError:pass
    if not isinstance(envelope,dict) or not isinstance(envelope.get('result'),list):return {'status':'error','verified':False,'message':'VeriFast 未返回受支持的 JSON 验证结果。','diagnostics':[]}
    outcome=envelope['result'];kind=outcome[0] if outcome else '';success=kind=='success' and returncode==0
    message=outcome[1] if kind=='success' and len(outcome)>1 else next((v for v in outcome[1:] if isinstance(v,str)),kind)
    status='verified' if success else 'compile_error' if kind=='StaticError' else 'failed'
    location=outcome[2] if kind=='SymbolicExecutionError' and len(outcome)>2 else outcome[1] if len(outcome)>1 else []
    diagnostics=_locations(location,files,root) if not success else []
    for d in diagnostics:d.update(kind='syntax' if kind=='StaticError' else 'unproved',message=message[:1500])
    count=re.search(r'\b(\d+)\s+statements?\s+verified\b',str(message),re.I) if kind=='success' else None
    return {'status':status,'verified':success,'message':message,'diagnostics':diagnostics,'native_result_kind':kind,'verified_statements':int(count[1]) if count else None,'verification_scope':'compilation_unit','link_checked':False}


def bypass_diagnostics(files):
    diagnostics=[]
    tokens=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*@.*?\*/|//@[^\n]*',re.S)
    for f in files:
        regions=[(m.start(),m[0]) for m in tokens.finditer(f['content']) if m[0].startswith(('/*@','//@'))]
        if f['path'].endswith('.gh'):regions=[(0,f['content'])]
        for offset,body in regions:
            match=re.search(r'\b(?:assume|admit)\s*\(',body)
            if match:
                line=f['content'].count('\n',0,offset+match.start())+1
                diagnostics.append({'path':f['path'],'line':line,'column':1,'kind':'unverified_assumption','severity':'error','certainty':'reported','message':'输入包含未证明的 assume/admit 假设，不能计为验证通过。'})
    return diagnostics


from engine.verification.report import reported

@reported("verifast")
def verify(files,entry,timeout=200):
    validate_files(files,entry)
    identifier=uuid.uuid4().hex;directory=settings.runtime_dir/'verifast'/identifier;source=directory/'source';source.mkdir(parents=True)
    for f in files:
        p=source/f['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(f['content'])
    manifest={'files':files,'entry':entry,'source_hashes':{f['path']:hashlib.sha256(f['content'].encode()).hexdigest() for f in files}}
    (directory/'input.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    blocked=bypass_diagnostics(files)
    info=capabilities() if not blocked else {'ready':False,'runtime':None,'message':'输入包含未证明的 assume/admit 假设，不能计为验证通过。'}
    result={'id':identifier,'tool':'verifast','runtime':info['runtime'],'version':info.get('version'),'source_hashes':manifest['source_hashes'],'entry':entry,'verified':False,'status':'unavailable','message':info['message'],'diagnostics':[]}
    if blocked:result.update(status='blocked',diagnostics=blocked)
    if info['ready']:
        container=info['runtime']=='container';cwd=Path('/work')/identifier/'source' if container else source.resolve()
        args=['verifast','-safe_mode','-enforce_annotations','-c','-json','-I',str(cwd)]
        # Safe mode limits include access; only trusted release headers and input bundle headers are allowed.
        headers={f['path'] for f in files if f['path'].endswith(('.h','.gh'))}
        aliases=set()
        for f in files:
            for include in re.findall(r'#\s*include\s*[\"<]([^\">]+)[\">]',f['content']):
                resolved=posixpath.normpath(str(PurePosixPath(f['path']).parent/include))
                if resolved in headers:aliases.add(include)
        for h in sorted(set(STDLIB)|headers|aliases):args+=['-allow_header',h]
        args.append(str(cwd/entry))
        if container:command=['docker','compose','--profile','verifast','run','--rm','-T','--no-deps','--name','acsl-verifast-'+identifier,'verifast',*args]
        else:args[0]=binary();command=args
        result.update(command=args,command_text=shlex.join(args),timeout_sec=timeout,verification_scope='compilation_unit',link_checked=False)
        started=time.monotonic()
        # Do not pass provider keys or user HOME into this independent verifier.
        env={k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR','SYSTEMROOT','DOCKER_HOST','DOCKER_CONFIG')}
        with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
            try:
                p=subprocess.Popen(command,cwd=str(settings.root_dir if container else source),env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
                try:p.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL);p.wait()
                    if container:
                        subprocess.run(['docker','rm','-f','acsl-verifast-'+identifier],env=env,capture_output=True,timeout=10)
                    result.update(status='timeout',message='VeriFast 验证超时，已终止运行。')
                if out.tell()+err.tell()>4*1024*1024:result.update(status='error',message='VeriFast 输出超过 4 MiB 限制。')
                else:
                    out.seek(0);err.seek(0);stdout=out.read().decode(errors='replace');stderr=err.read().decode(errors='replace')
                    result.update(stdout=stdout,stderr=stderr,returncode=p.returncode)
                    if result['status']!='timeout':result.update(parse_output(stdout,p.returncode,files,cwd))
            except OSError:result.update(status='unavailable',message='VeriFast 运行器启动失败，请检查安装和运行环境。')
        result['elapsed_sec']=round(time.monotonic()-started,3)
    result['display_log']=result.get('command_text','')+'\n'+result['message']+'\n'+'\n'.join(f"{d['path']}:{d['line']}:{d['column']}: {d['message']}" for d in result['diagnostics'])+'\n'+result.get('stderr','')
    from .report import normalize_verification
    result['report']=normalize_verification(result,'verifast',files)
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (directory/'verification.log').write_text(result.get('stdout','')+'\n'+result.get('stderr',''))
    return result
