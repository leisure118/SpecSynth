export function displayedRunId(liveId,selectedId,tasks,pendingId=''){
  return liveId&&(pendingId===liveId||['queued','running'].includes(tasks[liveId]?.status))?liveId:selectedId
}
export function matchingRunResult(task,result){
  if(!task||!result||['queued','running'].includes(task.status))return null
  return result.task_id&&result.task_id!==task.task_id?null:result
}
export function outputSourceName(input={}){
  if(input.sample_id)return input.sample_id
  if(input.source_name||input.name)return input.source_name||input.name
  const signature=input.function_signature||''
  return signature.match(/\bfn\s+([A-Za-z_]\w*)/)?.[1]||input.entry_path||'custom-task'
}
export function generatedFileName(input,files=[],id=''){
  const existing=files.find(f=>f.id===id)
  if(existing&&!/^generated-[\w-]+\.rs$/.test(existing.name))return existing.name
  let stem=String(outputSourceName(input)).replace(/\\/g,'/').split('/').pop().replace(/\.(txt|md|markdown|json|rs)$/i,'')
  stem=stem.replace(/[^\p{L}\p{N}_.-]+/gu,'-').replace(/^\.+|[. -]+$/g,'').slice(0,120)||'custom-task'
  let name=stem+'.verus.rs',n=2
  while(files.some(f=>f.id!==id&&f.name===name))name=stem+'.verus-'+(n++)+'.rs'
  return name
}
