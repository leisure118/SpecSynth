"""Project CLI tool events projected onto the run API without model reasoning."""
import json
import threading
from pathlib import Path
from acsl.adapters.storage import utcnow


class AgentProgress:
    def __init__(self, task, store):
        self.task,self.store=task,store
        self.state={'steps':[], 'current':'准备运行', 'round':0}
        task.metadata['agent_progress']=self.state

    def update(self, event):
        identifier=event.get('id')
        if not identifier or event.get('status') not in ('running','completed','failed'):return
        identifier=f"{self.state['round']}:{identifier}"
        step=next((s for s in self.state['steps'] if s['id']==identifier),None)
        if step is None:
            step={'id':identifier,'label':event.get('label','工具执行'),'started_at':event.get('at') or utcnow().isoformat()}
            self.state['steps'].append(step)
            self.state['steps']=self.state['steps'][-80:]
        step.update(status=event['status'],detail=event.get('detail',''))
        if event['status']!='running':step['finished_at']=event.get('at') or utcnow().isoformat()
        running=[s for s in self.state['steps'] if s['status']=='running']
        self.state['current']=running[-1]['label'] if running else '等待主 Agent 下一步' if event['status']=='completed' else step['label']+'失败'
        self.task.updated_at=utcnow()
        self.store.write_task(self.task)

    def finish(self, successful):
        for step in list(self.state['steps']):
            if step['status']=='running':step.update(status='failed',detail='任务结束，此步骤未完成',finished_at=utcnow().isoformat())
        self.state['current']='验证完成' if successful else '任务未通过'
        self.store.write_task(self.task)

    def watch(self, directory, round_number, *, reuse=False):
        owner=self
        runtime_label='复用原会话修复规约' if reuse else '启动官方 CLI'
        class Watch:
            def __enter__(self):
                owner.state['round']=round_number
                self.stop=threading.Event();self.offset=0;self.started=False;self.lock=threading.Lock()
                self.path=Path(directory)/'live-progress.jsonl'
                owner.update({'id':'runtime','label':runtime_label,'status':'running'})
                self.thread=threading.Thread(target=self.pump,daemon=True);self.thread.start()
                return self
            def read(self):
                with self.lock:self.consume()
            def consume(self):
                if not self.path.exists():return
                with self.path.open() as stream:
                    stream.seek(self.offset)
                    while True:
                        line=stream.readline()
                        if not line or not line.endswith('\n'):break
                        self.offset=stream.tell()
                        try:
                            if not self.started:
                                owner.update({'id':'runtime','label':runtime_label,'status':'completed'})
                                self.started=True
                            owner.update(json.loads(line))
                        except (ValueError,KeyError):continue
            def pump(self):
                while not self.stop.wait(.2):self.read()
            def __exit__(self,*args):
                self.stop.set();self.thread.join();self.read()
                if any(s['id']==f'{round_number}:main-analysis' for s in owner.state['steps']):
                    owner.update({'id':'main-analysis','label':'主 Agent 分析与编排','status':'failed' if args[0] else 'completed'})
                if not self.started:owner.update({'id':'runtime','label':runtime_label,'status':'failed' if args[0] else 'completed'})
        return Watch()
