"""Task-scoped SSH forwarding for private model deployments, without an agent loop."""
from contextlib import contextmanager
import os
import re
import signal
import socket
import subprocess
import time
from urllib.parse import urlsplit, urlunsplit


@contextmanager
def model_route(profile, *, enabled=False):
    target=os.getenv('XUANJIAN_QWEN_SSH_TARGET','').strip()
    if not enabled or not target:
        yield profile
        return
    if not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+',target):
        raise ValueError('SSH 模型通道目标必须为 user@host。')
    remote=urlsplit(profile['base_url'])
    if remote.scheme!='http' or not remote.hostname or not re.fullmatch(r'[A-Za-z0-9_.-]+',remote.hostname):
        raise ValueError('SSH 模型转发需要有效的 HTTP 模型地址。')
    port=int(os.getenv('XUANJIAN_QWEN_SSH_PORT','22'))
    if not 1<=port<=65535:raise ValueError('SSH 通道端口无效。')
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1',0));local_port=reserve.getsockname()[1]
    args=['ssh','-N','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ExitOnForwardFailure=yes',
          '-o','ConnectTimeout=8','-p',str(port),'-L',f'127.0.0.1:{local_port}:{remote.hostname}:{remote.port or 80}',target]
    with subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True) as process:
        try:
            deadline=time.monotonic()+10
            while True:
                if process.poll() is not None:raise ValueError('SSH 模型通道启动失败，请检查可信 host key、SSH 身份和服务地址。')
                try:
                    with socket.create_connection(('127.0.0.1',local_port),timeout=.2):break
                except OSError:
                    if time.monotonic()>deadline:raise TimeoutError('SSH 模型通道连接超时。')
                    time.sleep(.05)
            yield {**profile,'base_url':urlunsplit(('http',f'127.0.0.1:{local_port}',remote.path,remote.query,''))}
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
