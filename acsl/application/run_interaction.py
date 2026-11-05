"""Bounded task messages, consumed only at repair boundaries."""
import json,threading,uuid
from pathlib import Path
from acsl.adapters.storage import utcnow
_lock=threading.Lock()

def enqueue(directory,text):
    text=text.strip()
    if not text or len(text)>4000:raise ValueError('补充指令须为1至4000个字符。')
    with _lock:
        path=Path(directory)/'user-feedback.json'
        rows=json.loads(path.read_text()) if path.exists() else []
        if len(rows)>=30:raise ValueError('本任务最多接收30条补充指令。')
        row={'id':uuid.uuid4().hex,'text':text,'at':utcnow().isoformat(),'status':'pending'}
        rows.append(row);path.write_text(json.dumps(rows,ensure_ascii=False))
        return row

def consume(directory,round_number):
    with _lock:
        path=Path(directory)/'user-feedback.json'
        rows=json.loads(path.read_text()) if path.exists() else []
        pending=[r for r in rows if r['status']=='pending']
        for r in pending:r.update(status='applied',round=round_number)
        if pending:path.write_text(json.dumps(rows,ensure_ascii=False))
        return pending

def messages(directory):
    with _lock:
        path=Path(directory)/'user-feedback.json'
        return json.loads(path.read_text()) if path.exists() else []
