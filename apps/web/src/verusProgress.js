export function secondsBetween(start,end,now=Date.now()){
  const a=Date.parse(start),b=end?Date.parse(end):Number(now)
  return Number.isFinite(a)&&Number.isFinite(b)?Math.max(0,(b-a)/1000):0
}
export function duration(seconds){if(seconds>0&&seconds<1)return '<1s';const n=Math.floor(seconds);return n<60?n+'s':Math.floor(n/60)+'m '+String(n%60).padStart(2,'0')+'s'}
export function stageLabel(phase,round=0){return {preparing:'准备任务与 Skill',generating:'生成 Verus 代码',repairing:'自动修复 · 第 '+round+' 轮',verifying:round?'Verus 复验 · 第 '+round+' 轮':'Verus 首次验证'}[phase]||phase}
export function statusLabel(status){return {generating:'生成中',generated:'已生成',verifying:'验证中',verified:'验证通过',failed:'证明未通过',verification_failed:'证明未通过',compile_error:'编译错误',provider_error:'生成或 Agent 执行失败',tool_error:'工具执行失败',timeout:'验证超时',blocked:'代码检查阻止',cancelled:'已停止',repair_limit:'修复次数已达上限',output_limit:'模型输出被截断',no_checks:'未发现验证项',unavailable:'验证器不可用'}[status]||status||''}
export function progressStages(workflow={},active=false){
  let stages=workflow.stages||[]
  // Older runs have round timestamps but no persisted stage timing. Do not invent times.
  if(!stages.length)stages=(workflow.attempts||[]).flatMap(a=>[
    {phase:a.round?'repairing':'generating',round:a.round,started_at:null,finished_at:null,status:a.code?'completed':active?'running':'failed',message:a.code?'已返回候选代码':statusLabel(a.status)},
    ...(a.verification?[{phase:'verifying',round:a.round,started_at:null,finished_at:null,status:'completed',outcome:a.verification.status,message:a.verification.message}]:[])
  ])
  return stages.map(s=>({...s,state:s.status==='running'&&active?'active':s.status==='failed'?'error':['failed','verification_failed','compile_error','timeout','blocked','tool_error'].includes(s.outcome)?'warning':'done'}))
}

export function stageDescription(stage){
  if(stage.state==='active')return stage.message
  if(['error','warning'].includes(stage.state))return statusLabel(stage.outcome)||stage.message||'执行中断'
  return {preparing:'任务与选中 Skill 已准备',generating:'候选代码已返回',repairing:'修复代码已返回',verifying:statusLabel(stage.outcome)||stage.message||'验证已结束'}[stage.phase]||stage.message
}
