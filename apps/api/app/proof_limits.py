"""Optional process-wide proof admission control, shared by native CLI children."""
from contextlib import contextmanager
import os
import time
from .config import RUNTIME_DIR

@contextmanager
def proof_slot(timeout):
    count=int(os.getenv('XUANJIAN_PROOF_CONCURRENCY','0'))
    if count<=0:
        yield timeout
        return
    import fcntl
    root=RUNTIME_DIR/'proof-slots';root.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic()+timeout
    handles=[(root/str(i)).open('a') for i in range(min(count,16))]
    acquired=None
    try:
        while acquired is None:
            for handle in handles:
                try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired=handle;break
                except BlockingIOError:pass
            if acquired is None:
                if time.monotonic()>=deadline:raise TimeoutError('等待证明资源超时')
                time.sleep(.05)
        yield max(.1,deadline-time.monotonic())
    finally:
        if acquired is not None:fcntl.flock(acquired,fcntl.LOCK_UN)
        for handle in handles:handle.close()
