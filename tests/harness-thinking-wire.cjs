// Exercise the installed upstream serializer: assertions concern HTTP body fields,
// not just our provider configuration. No external request is made.
const assert=require('node:assert/strict'),path=require('node:path');
(async()=>{
 const seen=[];globalThis.fetch=async(_url,init)=>{
  seen.push(JSON.parse(init.body));
  return new Response('data: '+JSON.stringify({id:'test',object:'chat.completion.chunk',created:0,model:'test',choices:[{index:0,delta:{content:'{}'},finish_reason:null}]})+'\n\ndata: '+JSON.stringify({id:'test',object:'chat.completion.chunk',created:0,model:'test',choices:[{index:0,delta:{},finish_reason:'stop'}]})+'\n\ndata: [DONE]\n\n',{headers:{'content-type':'text/event-stream'}});
 };
 const {stream}=await import(path.resolve('runtime/cli/deepseek/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js'));
 for(const enabled of [false,true])for(const format of ['qwen','qwen-chat-template']){
  const model={id:'test',name:'test',api:'openai-completions',provider:'test',baseUrl:'https://mock.invalid/v1',reasoning:true,thinkingLevelMap:{low:'low'},input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:16384,maxTokens:4096,compat:{thinkingFormat:format,supportsReasoningEffort:false,supportsDeveloperRole:false}};
  const events=stream(model,{messages:[{role:'system',content:[{type:'text',text:'C / ACSL only'}],timestamp:0},{role:'user',content:[{type:'text',text:'Return patches'}],timestamp:0}]},{apiKey:'test',maxTokens:4096,...(enabled?{reasoningEffort:'low'}:{})});
  for await(const e of events){assert.notEqual(e.type,'error',JSON.stringify(e));}
 }
 assert.equal(seen.length,4);for(const body of seen)assert.equal(body.messages[0].role,'system');assert.equal(seen[0].enable_thinking,false);assert.equal(seen[1].chat_template_kwargs.enable_thinking,false);
 assert.equal(seen[2].enable_thinking,true);assert.equal(seen[3].chat_template_kwargs.enable_thinking,true);assert.equal(seen[0].reasoning_effort,undefined);assert.equal(seen[1].reasoning_effort,undefined);
 console.log('Upstream wire parameters explicitly control thinking on/off for Bailian and Qwen');
})().catch(e=>{console.error(e);process.exitCode=1});
