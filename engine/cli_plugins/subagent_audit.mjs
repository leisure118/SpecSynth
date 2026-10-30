// Observe the official runtime's lifecycle; never record model reasoning.
import {appendFileSync} from 'node:fs';
export const name='platform-subagent-audit';
export function apply(ctx) {
  const file=process.env.DSH_SUBAGENT_AUDIT;
  if(!file)return;
  function record(row){appendFileSync(file,JSON.stringify({...row,at:new Date().toISOString()})+'\n')}
  ctx.on('agent/created',({agent})=>{
    if(agent.options?.provider==='platform-subagent'){
      agent.ctx.tools.restrict({allow:[]});
      record({type:'policy',id:agent.id,model:agent.options.model,mode:'text-only'});
    }
  });
  ctx.on('subagent/start',info=>record({type:'start',id:info.id,provider:info.provider}));
  ctx.on('subagent/end',info=>record({type:'end',id:info.id,stop_reason:info.stopReason}));
  ctx.on('agent/error',({agent,error})=>{
    if(agent?.session?.header?.origin==='subagent'||agent?.session?.header?.parentSession)
      record({type:'error',id:agent.id,code:error?.code,message:String(error?.message||'child failed').slice(0,3000)});
  });
}
