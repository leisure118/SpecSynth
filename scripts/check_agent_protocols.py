"""Optional local Codex Responses mock smoke test; no external API or real credentials. Requires installed Agent runtimes."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import threading,tempfile,subprocess,json,os,time
CODE='use vstd::prelude::*;\nverus! { fn inc(x: u64) -> (r: u64) requires x < 100, ensures r == x + 1, { x + 1 } }\n'
seen=[]
results=[]
def event(kind,**data):return f'event: {kind}\ndata: '+json.dumps({'type':kind,**data})+'\n\n'
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));seen.append(self.path)
  if '/responses' in self.path:
   msg={'id':'msg_1','type':'message','status':'completed','role':'assistant','content':[{'type':'output_text','text':CODE,'annotations':[]}],'phase':'final_answer'}
   response={'id':'resp_1','object':'response','created_at':int(time.time()),'status':'completed','model':body['model'],'output':[msg],'usage':{'input_tokens':10,'output_tokens':30,'total_tokens':40}}
   chunks=event('response.created',response={**response,'status':'in_progress','output':[]})+event('response.output_item.added',output_index=0,item={**msg,'status':'in_progress','content':[]})+event('response.content_part.added',item_id='msg_1',output_index=0,content_index=0,part={'type':'output_text','text':'','annotations':[]})+event('response.output_text.delta',item_id='msg_1',output_index=0,content_index=0,delta=CODE)+event('response.output_text.done',item_id='msg_1',output_index=0,content_index=0,text=CODE)+event('response.content_part.done',item_id='msg_1',output_index=0,content_index=0,part=msg['content'][0])+event('response.output_item.done',output_index=0,item=msg)+event('response.completed',response=response)
  else:
   message={'id':'msg_1','type':'message','role':'assistant','model':body['model'],'content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':10,'output_tokens':0}}
   chunks=event('message_start',message=message)+event('content_block_start',index=0,content_block={'type':'text','text':''})+event('content_block_delta',index=0,delta={'type':'text_delta','text':CODE})+event('content_block_stop',index=0)+event('message_delta',delta={'stop_reason':'end_turn','stop_sequence':None},usage={'output_tokens':30})+event('message_stop')
  if not body.get('stream',True):
   raw=json.dumps({**message,'content':[{'type':'text','text':CODE}],'stop_reason':'end_turn'}).encode();kind='application/json'
  else:raw=chunks.encode();kind='text/event-stream'
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
for agent,model,prefix in [('codex','gpt-4o','/v1')]:
 before=len(seen)
 with tempfile.TemporaryDirectory() as folder:
  data={'agent':agent,'prompt':'Generate complete Verus for increment with precondition x<100 and ensures r=x+1. Return code only.','profile':{'api_key':'test-key-not-a-real-credential','base_url':f'http://127.0.0.1:{server.server_port}'+prefix,'model':model},'workingDirectory':folder}
  try:
   r=subprocess.run(['node',str(Path(__file__).resolve().parent/'agent_bridge.mjs')],input=json.dumps(data),text=True,capture_output=True,timeout=40,env={k:v for k,v in os.environ.items() if k in ('PATH','TMPDIR')},start_new_session=True)
   try:ok=json.loads(r.stdout).get('code','').strip()==CODE.strip()
   except ValueError:ok=False
   results.append(ok and r.returncode==0)
   print(json.dumps({'agent':agent,'requests':seen[before:],'code_received':ok,'exit_code':r.returncode}),flush=True)
  except subprocess.TimeoutExpired:
   results.append(False)
   print(json.dumps({'agent':agent,'timeout':True,'requests':seen[before:]}),flush=True)
server.shutdown()
raise SystemExit(0 if all(results) else 1)
