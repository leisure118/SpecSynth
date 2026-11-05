"""One official runtime process per case; never share context between cases."""
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import tempfile
import threading
import time

_current=ContextVar('harness_case_session',default=None)

class Session:
    def __init__(self):
        self.directory=None
        self.proc=None
        self.lines=queue.Queue()
        self.rounds=0
        self.identity=None
        self.routes={}
        self.resources=ExitStack()
    def close(self):
        if self.proc is not None:
            if self.proc.poll() is None:
                os.killpg(self.proc.pid,signal.SIGKILL)
            self.proc.wait()
            self.proc.stdin.close(); self.proc.stdout.close()
        self.resources.close()
        if self.directory:self.directory.cleanup()
    def request(self,cmd,cwd,env,task,timeout,identity):
        deadline=time.monotonic()+timeout
        if self.identity is not None and self.identity!=identity:
            raise ValueError('A Harness case cannot change model configuration mid-session')
        if self.proc is None:
            self.identity=identity
            with (Path(cwd)/'.platform-cli-stderr.log').open('a') as errors:
                self.proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,start_new_session=True,text=True)
            def read():
                for line in self.proc.stdout:self.lines.put(line)
                self.lines.put(None)
            threading.Thread(target=read,daemon=True).start()
            self._read(deadline,'bridge_ready')
        if env.get('DSH_PROGRESS_FILE'):
            import shlex
            from acsl.application.terminal import safe_terminal_text
            with Path(env['DSH_PROGRESS_FILE']).open('a') as launch:
                launch.write(json.dumps({'id':'launch-command','label':'Agent 启动命令' if self.rounds==0 else '复用原会话修复规约','status':'completed','command':safe_terminal_text(shlex.join(cmd)) if self.rounds==0 else '',},ensure_ascii=False)+'\n')
        self.proc.stdin.write(json.dumps({'task':task,'progress':env.get('DSH_PROGRESS_FILE',''),'repair':env.get('DSH_REPAIR_MODE')=='1','require_subagent':env.get('DSH_REQUIRE_SUBAGENT')=='1'})+'\n');self.proc.stdin.flush()
        raw=self._read(deadline,'bridge_done')
        self.rounds+=1
        return raw
    def _read(self,deadline,terminal):
        output=[];size=0
        while True:
            try:line=self.lines.get(timeout=max(.001,deadline-time.monotonic()))
            except queue.Empty:
                if self.proc.poll() is None:os.killpg(self.proc.pid,signal.SIGKILL)
                self.proc.wait()
                self.proc.stdin.close();self.proc.stdout.close()
                self.proc=None
                error=TimeoutError('Persistent Harness round timed out');error.raw=''.join(output)
                raise error from None
            if line is None:
                error=RuntimeError('Persistent Harness process exited');error.raw=''.join(output);raise error
            event=json.loads(line)
            if event.get('type')==terminal:return ''.join(output)
            size+=len(line.encode())
            if size>2_000_000:raise ValueError('Harness output exceeds limit')
            output.append(line)
            if event.get('type')=='error':
                error=RuntimeError('Official Harness bridge reported an error');error.raw=''.join(output);raise error

@contextmanager
def case_session():
    # Nested callers keep the already isolated case scope.
    if _current.get() is not None:
        yield
        return
    session=Session();token=_current.set(session)
    try:yield
    finally:
        session.close();_current.reset(token)

@contextmanager
def workspace_directory(task_root):
    session=_current.get()
    if session is None:
        with tempfile.TemporaryDirectory(prefix='nl2verus-dsh-',dir=task_root) as folder:yield folder
    else:
        if session.directory is None:session.directory=tempfile.TemporaryDirectory(prefix='nl2verus-dsh-',dir=task_root)
        yield session.directory.name

def current_session():return _current.get()
