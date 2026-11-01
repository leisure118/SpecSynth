// Observe the official runtime's lifecycle; never record model reasoning.
import {appendFileSync} from 'node:fs';
export const name='platform-subagent-audit';
export function apply(ctx) {
  const file=process.env.DSH_SUBAGENT_AUDIT;
  if(!file)return;
  function record(row){appendFileSync(file,JSON.stringify({...row,at:new Date().toISOString()})+'\n')}
  const progressFile=process.env.DSH_PROGRESS_FILE;
  function progress(row){if(process.env.DSH_PROGRESS_FILE)appendFileSync(process.env.DSH_PROGRESS_FILE,JSON.stringify({...row,at:new Date().toISOString()})+'\n')}
  function label(name,args={}){
    if(name==='bash'){
      const command=String(args.command||'');
      const names={'list-layers':'分析函数依赖与分层','init-contracts':'初始化合约库',slice:'生成函数切片','fill-contracts':'填充已证明合约',inject:'注入 ACSL 规约',verify:'Frama-C 验证','save-contract':'验证并保存函数合约','check-admit':'检查证明完整性','locate-fail':'定位未证明目标'};
      if(command.includes('harness_verify_c.py'))return 'CLI 内部最终验证';
      for(const [key,value] of Object.entries(names))if(new RegExp('\\b'+key+'\\b').test(command))return value;
      return '执行工作区命令';
    }
    if(['read','read_file'].includes(name))return '读取源码与工具结果';
    if(['write','edit','str_replace_editor','apply_patch'].includes(name))return '写入候选规约与产物';
    if(['job_list','list_agents','send_message'].includes(name))return '协调子 Agent';
    return '执行 '+name;
  }
  ctx.on('session/event',(_session,event)=>{
    if(event.type==='tool/call' && event.data.name!=='subagent')progress({id:event.data.callId,label:label(event.data.name,event.data.arguments),status:'running'});
  });
  ctx.on('tools/result',(exec,result)=>{
    if(exec.name==='subagent')return;
    const code=result.value?.exitCode;
    let proof;try{proof=JSON.parse(result.value?.stdout?.text||'null')}catch{}
    const proofFailed=proof?.verified===false||['Fail','Invalid','Unknown','Timeout','Unavailable'].includes(proof?.result);
    const failed=proofFailed||result.isError||result.value?.timedOut||result.value?.aborted||(typeof code==='number'&&code!==0);
    progress({id:exec.callId,label:label(exec.name,exec.arguments),status:failed?'failed':result.value?.jobId?'running':'completed',detail:proofFailed?'证明尚未通过，请查看诊断':failed?'工具未成功，请查看运行日志':''});
  });
  let childCompleted=false;
  let roundId=process.env.DSH_ROUND_ID;
  function resetRound(){if(roundId!==process.env.DSH_ROUND_ID){roundId=process.env.DSH_ROUND_ID;childCompleted=false;}}
  ctx.on('agent/created',({agent})=>{
    const child=agent.session?.header?.origin==='subagent'||agent.session?.header?.parentSession;
    if(!child)progress({id:'main-analysis',label:'主 Agent 分析与编排',status:'running'});
    if(!child && process.env.DSH_COMPACT_C==='1')agent.ctx.tools.restrict({allow:['subagent','write']});
    if(!child && process.env.DSH_REQUIRE_SUBAGENT==='1'){
      agent.ctx.tools.guard(exec=>{
        resetRound();
        if(process.env.DSH_REPAIR_MODE==='1'&&exec.name==='subagent')return 'Repair this existing candidate directly; do not launch another generation worker.';
        if(process.env.DSH_REQUIRE_SUBAGENT!=='1')return;
        if(childCompleted)return;
        const writes=['write','edit','str_replace_editor','apply_patch'].includes(exec.name);
        const earlyProof=exec.name==='bash'&&/answer\.json|\.acsl\.c|harness_verify_c/.test(String(exec.arguments?.command||''));
        if(writes||earlyProof)return 'Workflow prerequisite: first delegate specification generation with the native subagent tool and wait for its successful completion. The configured child model must generate the annotations; do not solve the task yourself. Read sources and prepare slices before delegation if needed.';
      });
    }
    if(agent.options?.provider==='platform-subagent'){
      agent.ctx.tools.restrict({allow:[]});
      record({type:'policy',id:agent.id,model:agent.options.model,mode:'text-only'});
    }
  });
  ctx.on('subagent/start',info=>{record({type:'start',id:info.id,provider:info.provider});progress({id:'child-'+info.id,label:'子 Agent 生成规约',status:'running'})});
  ctx.on('subagent/end',info=>{if(info.stopReason==='completed')childCompleted=true;record({type:'end',id:info.id,stop_reason:info.stopReason});progress({id:'child-'+info.id,label:'子 Agent 生成规约',status:info.stopReason==='completed'?'completed':'failed',detail:info.stopReason==='completed'?'子任务已完成':info.stopReason})});
  ctx.on('agent/error',({agent,error})=>{
    if(agent?.session?.header?.origin==='subagent'||agent?.session?.header?.parentSession)
      record({type:'error',id:agent.id,code:error?.code,message:String(error?.message||'child failed').slice(0,3000)});
  });
}
