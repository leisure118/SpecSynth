import json
from pathlib import Path
import sys
import tempfile
import unittest
from engine.nl2verus.harness_session import case_session,current_session,workspace_directory

BRIDGE='''import sys,json,os
print(json.dumps({'type':'bridge_ready'}),flush=True)
for line in sys.stdin:
 request=json.loads(line)
 print(json.dumps({'type':'test','pid':os.getpid(),'task':request['task']}),flush=True)
 print(json.dumps({'type':'bridge_done'}),flush=True)
'''
class SessionTests(unittest.TestCase):
 def test_reuses_process_and_workspace_but_isolates_cases(self):
  with tempfile.TemporaryDirectory() as root:
   with case_session():
    s=current_session()
    with workspace_directory(root) as first:
     a=json.loads(s.request([sys.executable,'-u','-c',BRIDGE],first,{},'first',3,('model',)))
    with workspace_directory(root) as second:
     b=json.loads(s.request([],second,{},'repair',3,('model',)))
    self.assertEqual(first,second);self.assertEqual(a['pid'],b['pid']);self.assertEqual(b['task'],'repair')
    proc=s.proc
    with self.assertRaises(ValueError):s.request([],second,{},'bad',3,('different',))
   self.assertIsNotNone(proc.poll());self.assertFalse(Path(first).exists());self.assertIsNone(current_session())
   with case_session():
    with workspace_directory(root) as third:self.assertNotEqual(first,third)
 def test_timeout_terminates_process_but_keeps_artifacts_until_case_exit(self):
  with tempfile.TemporaryDirectory() as root,case_session():
   with workspace_directory(root) as folder:
    s=current_session()
    with self.assertRaises(TimeoutError):s.request([sys.executable,'-u','-c','import time; time.sleep(10)'],folder,{},'x',.1,('m',))
    self.assertTrue(Path(folder).exists());self.assertIsNone(s.proc)
 def test_nested_scope_preserves_outer_session(self):
  with case_session():
   first=current_session()
   with case_session():self.assertIs(first,current_session())
   self.assertIs(first,current_session())


def test_repair_turn_uses_existing_candidate_without_new_worker(tmp_path,monkeypatch):
 from engine.nl2verus import dsh_cli
 from engine.nl2verus.harness_session import Session
 monkeypatch.setenv('XUANJIAN_HARNESS_COMPACT','1')
 monkeypatch.setattr(dsh_cli,'installed',lambda:True)
 captured=[]
 def request(self,cmd,cwd,env,task,timeout,identity):
  captured.append((task,env.copy()))
  (cwd/'answer.json').write_text(json.dumps({'files':[{'path':'a.c','content':'int main(){return 0;}'}]}))
  self.rounds+=1
  return '\n'.join(json.dumps(e) for e in [
   {'type':'session','sessionId':'same-session'},
   {'type':'tool_call','callId':'write1','tool':'write'},
   {'type':'tool_result','callId':'write1','status':'completed'},
   {'type':'final','reason':{'kind':'completed'}}])
 monkeypatch.setattr(Session,'request',request)
 with case_session():
  current_session().rounds=1
  result=dsh_cli.generate('Original source:\n[]\nPrevious candidate:\nCURRENT-ANNOTATIONS\nVerifier diagnostics:\nFAILED-GOAL',{'model':'test','base_url':'http://localhost:1/v1','api_key':''},artifact_dir=tmp_path,output_format='files',require_subagent=True)
 assert result['agent_runtime']['operation']=='repair'
 assert result['agent_runtime']['process_reused']
 task,env=captured[0]
 assert 'CURRENT-ANNOTATIONS' in task and 'FAILED-GOAL' in task
 assert 'Do not restart specification generation' in task
 assert env['DSH_REQUIRE_SUBAGENT']=='0'
 assert env['DSH_REPAIR_MODE']=='1'
