// Sequential JSONL bridge over the installed official Agent runtime.
// No provider replacement and no private reasoning projection.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
const require=createRequire(process.env.DSH_PACKAGE_JSON);
const {installModelSelection}=await import(pathToFileURL(require.resolve('@deepseek-ai/dsh-agent')));
const {createUserMessage}=await import(pathToFileURL(require.resolve('@deepseek-ai/dsh-llm')));
const {projectJsonRun}=await (async()=>{
  // Version-pinned upstream projection, also used by the official headless driver.
  const {readdirSync}=await import('node:fs');
  const {dirname,join}=await import('node:path');
  const dir=dirname(require.resolve('@deepseek-ai/dsh-headless'));
  const file=readdirSync(dir).find(n=>/^json-stream-.*\.js$/.test(n));
  if(!file)throw Error('Unsupported Harness projection version');
  const mod=await import(pathToFileURL(join(dir,file)));
  return {projectJsonRun:mod.n};
})();
export const name='platform-persistent-harness';
export const inject=['agentDefaultModel','agents','sessions'];
export function apply(ctx){
  async function run(){
    await ctx.get('loader')?.await();
    const selection=ctx.get('agentDefaultModel').currentSelection();
    const {agent}=await ctx.get('agents').create({sessionId:`session-${randomUUID()}`,meta:{cwd:process.cwd()},agentOptions:{provider:selection.provider,model:selection.model},setup(agentCtx){installModelSelection(agentCtx,{current:selection,assembled:undefined})}});
    await agent.whenIdle();
    process.stdout.write(JSON.stringify({type:'bridge_ready'})+'\n');
    for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
      const request=JSON.parse(line);
      process.env.DSH_PROGRESS_FILE=request.progress;
      process.env.DSH_ROUND_ID=randomUUID();
      process.env.DSH_REPAIR_MODE=request.repair?'1':'0';
      process.env.DSH_REQUIRE_SUBAGENT=request.require_subagent?'1':'0';
      const projection=projectJsonRun(ctx,agent,process.stdout,{cwd:process.cwd()});
      let failure,childCompleted=false;
      const stopChild=ctx.on('subagent/end',info=>{if(info.stopReason==='completed')childCompleted=true});
      const dispose=ctx.on('agent/error',({agent:subject,error})=>{if(subject===agent)failure=error});
      try{
        agent.followup(createUserMessage({content:[{type:'text',text:request.task}],source:{kind:'user'}}));
        while(true){await agent.whenIdle();const seq=agent.session.seq;if(!await ctx.get('subagents')?.waitForChildren(agent)&&agent.status==='idle'&&agent.session.seq===seq)break;}
        // A model turn ending is not the application handoff completing.
        // Continue once in the same session; never relaunch a worker or invent its output.
        if(request.require_subagent&&childCompleted&&!existsSync(resolve(process.cwd(),'answer.json'))){
          agent.followup(createUserMessage({content:[{type:'text',text:'The specification worker has completed and its result is already in this session. The required answer.json file is missing. Complete the handoff now: use the native write tool to save the worker result as answer.json with the complete files array. Do not launch any subagent, regenerate annotations, run a verifier, or merely paste code in chat. Preserve the worker output and original program.'}],source:{kind:'user'}}));
          await agent.whenIdle();
        }
        await ctx.get('sessions').flush(agent.session);
        if(failure)throw failure;
        projection.finish('');
      }finally{stopChild();dispose();projection.dispose();}
      process.stdout.write(JSON.stringify({type:'bridge_done'})+'\n');
    }
    ctx.get('appExit')(0);
  }
  run().catch(()=>{process.stdout.write(JSON.stringify({type:'error',message:'Persistent Harness runtime failed'})+'\n');ctx.get('appExit')(1)});
}
