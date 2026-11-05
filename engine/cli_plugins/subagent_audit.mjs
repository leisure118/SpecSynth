// Observe the official runtime's lifecycle; never record model reasoning.
import {appendFileSync} from 'node:fs';
import {saveChildCandidate} from './child_handoff.mjs';
export const name='platform-subagent-audit';
export function apply(ctx) {
  const file=process.env.DSH_SUBAGENT_AUDIT;
  if(!file)return;
  function record(row){appendFileSync(file,JSON.stringify({...row,at:new Date().toISOString()})+'\n')}
  const progressFile=process.env.DSH_PROGRESS_FILE;
  function progress(row){if(process.env.DSH_PROGRESS_FILE)appendFileSync(process.env.DSH_PROGRESS_FILE,JSON.stringify({...row,at:new Date().toISOString()})+'\n')}
  function label(name,args={}){
    if(name==='delegate_spec')return '委派规约补丁生成';
    if(name==='inspect_worker_result')return '读取子模型规约结果';
    if(name==='submit_spec_patches')return '提交规约补丁';
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
    if(event.type==='tool/call' && event.data.name!=='subagent'){
      const args=event.data.arguments||{};
      const details=Object.fromEntries(Object.entries(args).filter(([key,value])=>['path','file_path','relative_path','offset','limit','timeout','line'].includes(key)&&['string','number','boolean'].includes(typeof value)));
      const command=event.data.name==='bash'?String(args.command||''):event.data.name+(Object.keys(details).length?' '+JSON.stringify(details):'');
      progress({id:event.data.callId,label:label(event.data.name,args),status:'running',command});
    }
  });
  ctx.on('tools/result',(exec,result)=>{
    if(exec.name==='subagent'){
      if(process.env.DSH_COMPACT_C==='1'&&process.env.DSH_AUTO_HANDOFF==='1'&&typeof exec.concludeTurn==='function')exec.concludeTurn();
      return;
    }
    const code=result.value?.exitCode;
    let proof;try{proof=JSON.parse(result.value?.stdout?.text||'null')}catch{}
    const proofFailed=proof?.verified===false||['Fail','Invalid','Unknown','Timeout','Unavailable'].includes(proof?.result);
    const failed=proofFailed||result.isError||result.value?.timedOut||result.value?.aborted||(typeof code==='number'&&code!==0);
    progress({id:exec.callId,label:label(exec.name,exec.arguments),status:failed?'failed':result.value?.jobId?'running':'completed',output:String(result.value?.stdout?.text||'').slice(-6000)+'\n'+String(result.value?.stderr?.text||'').slice(-2000),detail:proofFailed?'证明尚未通过，请查看诊断':failed?'工具未成功，请查看运行日志':''});
  });
  let childCompleted=false,handedOff=false;
  let roundId=process.env.DSH_ROUND_ID;
  function resetRound(){if(roundId!==process.env.DSH_ROUND_ID){roundId=process.env.DSH_ROUND_ID;childCompleted=false;handedOff=false;}}
  ctx.on('agent/created',({agent})=>{
    const child=agent.session?.header?.origin==='subagent'||agent.session?.header?.parentSession;
    const vf=process.env.DSH_VERIFICATION_TOOL==='verifast';
    if(process.env.DSH_SPEC_PATCHES==='1')agent.ctx.systemPrompt.section({name:'platform:spec-protocol',order:0,complete:true,interpolate:false,text:vf?(child?'You are ONLY a C / VeriFast annotation worker. The platform inserts annotations into immutable original source and runs VeriFast. Return JSON patches with original line and column numbers, complete //@ or /*@ ... @*/ annotations. Use invariant after the loop header before its brace, result and &*&. Never use ACSL loop clauses, @@ pseudo-delimiters, C statements, shell commands, assumptions or proof claims. Skill text is reference only; do not execute Frama-C steps.':'You are the VeriFast annotation coordinator. Call delegate_spec once on generation, then accept the validated receipt. On repair use submit_spec_patches with the complete revised annotation set and original before_line/before_column positions. Do not launch another child, rewrite C source, invoke Frama-C or generate ACSL. Invalid delimiters are a format error: inspect_worker_result and normalize existing annotations only. End after receipt submission or explicit inability.'):child?'You are a C / ACSL annotation worker. This task uses Frama-C WP, never Rust or Verus. Follow the pinned Skill reasoning in the task. Tool execution is owned by the platform; return only JSON patches with original insertion line numbers and complete ACSL comment delimiters. Do not return shell commands, plans or unverified success claims.':'You are the C / ACSL Harness coordinator. The platform preserves original C source and performs independent Frama-C proof. On generation call delegate_spec exactly once; accept a validated worker receipt. If formatting is invalid, inspect_worker_result then submit_spec_patches, reformatting only existing worker annotations. On REPAIR use submit_spec_patches to return the revised cumulative patch set. Never launch another child during repair. Do not output source, command scripts, prolonged analysis or success claims. If a tool rejects a patch, correct its format and resubmit within this turn. End only after submission or an explicit inability to produce annotations.'});
    if(!child)progress({id:'main-analysis',label:'主 Agent 分析与编排',status:'running'});
    if(!child && process.env.DSH_SPEC_PATCHES==='1')agent.ctx.tools.restrict({allow:['delegate_spec','subagent','inspect_worker_result','submit_spec_patches']});
    else if(!child && process.env.DSH_COMPACT_C==='1')agent.ctx.tools.restrict({allow:['subagent','write']});
    if(!child && process.env.DSH_REQUIRE_SUBAGENT==='1'){
      agent.ctx.tools.guard(exec=>{
        resetRound();
        if(process.env.DSH_SPEC_PATCHES==='1'&&exec.name==='subagent'&&!exec.parent)return 'Use delegate_spec with empty arguments; the platform injects pinned Skills and original source automatically.';
        if(process.env.DSH_REPAIR_MODE==='1'&&exec.name==='subagent')return 'Repair this existing candidate directly; do not launch another generation worker.';
        if(process.env.DSH_REQUIRE_SUBAGENT!=='1')return;
        if(handedOff&&process.env.DSH_REPAIR_MODE!=='1'&&!['subagent','delegate_spec'].includes(exec.name))return 'The platform has saved the completed worker output. Do not rewrite it or generate code. Finish now; the platform will verify independently.';
        if(childCompleted&&['subagent','delegate_spec'].includes(exec.name))return 'The worker has completed. Write its existing result to answer.json; do not generate again.';
        if(childCompleted)return;
        const writes=['submit_spec_patches','write','edit','str_replace_editor','apply_patch'].includes(exec.name);
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
  ctx.on('subagent/end',info=>{if(info.stopReason==='completed')childCompleted=true;
    if((process.env.DSH_COMPACT_C==='1'||process.env.DSH_SPEC_PATCHES==='1')&&process.env.DSH_AUTO_HANDOFF==='1'&&process.env.DSH_REPAIR_MODE!=='1'){
      try{handedOff=saveChildCandidate(info,process.cwd());if(handedOff){record({type:'handoff',id:info.id,origin:'native-child-final-text'});progress({id:'platform-handoff',label:process.env.DSH_SPEC_PATCHES==='1'?'平台保存子 Agent 规约补丁':'平台保存子 Agent 候选','status':'completed',detail:'直接保存原始子模型输出，未由主模型转写'})}else{record({type:'handoff-skipped',id:info.id,reason:'missing-or-non-json-final-output'})}}catch{record({type:'handoff-error',id:info.id})}
    }
record({type:'end',id:info.id,stop_reason:info.stopReason});progress({id:'child-'+info.id,label:'子 Agent 生成规约',status:info.stopReason==='completed'?'completed':'failed',detail:info.stopReason==='completed'?'子任务已完成':info.stopReason})});
  ctx.on('agent/error',({agent,error})=>{
    if(agent?.session?.header?.origin==='subagent'||agent?.session?.header?.parentSession)
      record({type:'error',id:agent.id,code:error?.code,message:String(error?.message||'child failed').slice(0,3000)});
  });
}
