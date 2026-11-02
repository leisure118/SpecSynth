export const statusLabels = {queued:'排队中',running:'验证中',pass:'通过',fail:'未通过',invalid:'无效',timeout:'超时',unavailable:'环境不可用',unknown:'记录不可用',Pass:'通过',Fail:'未通过',Invalid:'无效',Timeout:'超时',Unavailable:'环境不可用'}
export function isRunning(status) { return status === 'queued' || status === 'running' }
export function matchingRuns(runs, path, mode, allFileModes=false) {
  return runs.filter(r=>mode==='inter-modular' ? r.mode==='inter-modular' : r.entry_path===path && r.mode!=='inter-modular' && (allFileModes||r.mode===mode)).slice().reverse()
}
