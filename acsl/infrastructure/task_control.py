"""Cooperative task lifetime shared by server-side execution and nested jobs."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import time

class TaskCancelled(Exception):pass

class TaskControl:
    def __init__(self,directory,timeout):
        self.directory=Path(directory);self.started=time.monotonic();self.deadline=self.started+timeout
    def set_timeout(self,seconds):self.deadline=self.started+seconds
    def cancelled(self):return (self.directory/'cancel.requested').is_file()
    def checkpoint(self):
        if self.cancelled():raise TaskCancelled('任务已取消，停止后续生成和验证。')
        if time.monotonic()>=self.deadline:raise TimeoutError('任务总预算已耗尽，停止后续生成和验证。')
    def remaining(self,limit=None):
        self.checkpoint();left=max(.01,self.deadline-time.monotonic())
        return min(left,limit) if limit is not None else left

_ACTIVE=ContextVar('task_control',default=None)
def current():return _ACTIVE.get()
def checkpoint():
    control=current()
    if control:control.checkpoint()
def remaining(limit):
    control=current()
    return control.remaining(limit) if control else limit

@contextmanager
def task_scope(directory,timeout):
    control=TaskControl(directory,timeout);token=_ACTIVE.set(control)
    try:yield control
    finally:_ACTIVE.reset(token)
