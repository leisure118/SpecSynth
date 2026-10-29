const BASE = '/api/v1'

async function request(url, options) {
  const res = await fetch(BASE + url, options || {})
  if (!res.ok) {
    const body = await res.text().catch(function(){ return '' })
    let message = body
    try { const parsed = JSON.parse(body); message = typeof parsed.detail === 'string' ? parsed.detail : Array.isArray(parsed.detail) ? parsed.detail.map(item => item.msg).join('；') : body } catch (_) {}
    throw new Error(message || 'API ' + res.status)
  }
  return res.json()
}

export function getHealth() { return request('/health') }
export function getModels() { return request('/models') }
export function getDemoCases() { return request('/demo-cases') }
export function getOverview() { return request('/overview') }

export function listRuns(limit) { return request('/runs?limit=' + (limit || 20)) }
export function getRun(id) { return request('/runs/' + id) }
export function getRunResult(id) { return request('/runs/' + id + '/result') }
export function getRunArtifacts(id) { return request('/runs/' + id + '/artifacts') }
export function getArtifactContent(id, rp) {
  return request('/runs/' + id + '/artifacts/content?relative_path=' + encodeURIComponent(rp))
}

export function getSpectoolCapabilities() { return request('/spectool/capabilities') }

export function uploadSpectoolFile(file) {
  var fd = new FormData(); fd.append('file', file)
  return request('/spectool/files/upload', { method: 'POST', body: fd })
}

export function uploadSpectoolBundle(files, manifest, rootDir) {
  var fd = new FormData()
  files.forEach(function(f){ fd.append('files', f) })
  fd.append('manifest', JSON.stringify(manifest))
  if (rootDir) fd.append('root_dir', rootDir)
  return request('/spectool/files/upload-bundle', { method: 'POST', body: fd })
}

export function listSpectoolFiles(fileId) { return request('/spectool/files/' + fileId) }
export function spectoolExtract(fileId, relativePath) {
  var query = '?file_id=' + encodeURIComponent(fileId)
  if (relativePath) query += '&relative_path=' + encodeURIComponent(relativePath)
  return request('/spectool/extract' + query, { method: 'POST' })
}
export function spectoolExtractOne(fileId, functionName, relativePath) {
  var query = '?file_id=' + encodeURIComponent(fileId) + '&function_name=' + encodeURIComponent(functionName)
  if (relativePath) query += '&relative_path=' + encodeURIComponent(relativePath)
  return request('/spectool/extract-one' + query, { method: 'POST' })
}
export function spectoolListFunctions(fileId) {
  return request('/spectool/list-functions?file_id=' + encodeURIComponent(fileId), { method: 'POST' })
}
export function spectoolSlice(payload) {
  return request('/spectool/slice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
export function spectoolInject(payload) {
  return request('/spectool/inject', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
export function spectoolGenerate(payload) {
  return request('/spectool/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
export function spectoolCheckAdmit(fileId, relativePath, source) {
  return request('/spectool/check-admit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, relative_path: relativePath || null, source: source || null }),
  })
}
export function spectoolVerify(payload) {
  return request('/spectool/verify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
export function spectoolLocateFail(payload) {
  return request('/spectool/locate-fail', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
export function listSpectoolArtifacts(fileId) {
  return request('/spectool/artifacts/' + encodeURIComponent(fileId))
}
export function getSpectoolArtifact(fileId, artifactId) {
  return request('/spectool/artifacts/' + encodeURIComponent(fileId) + '/' + encodeURIComponent(artifactId))
}

export function listProjects() { return request('/projects') }
export function createProject(payload) { return request('/projects', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }) }
export function getProject(id) { return request('/projects/' + encodeURIComponent(id)) }
export function saveProject(id, payload) { return request('/projects/' + encodeURIComponent(id), { method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }) }
export function runProject(id, payload) { return request('/projects/' + encodeURIComponent(id) + '/runs', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }) }

export function getRustStatus() { return request('/rust/status') }
export function getRustExamples(q='', page=1) { return request('/rust/examples?q='+encodeURIComponent(q)+'&page='+page) }
export function prepareRust(payload) { return request('/rust/prepare', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}) }
export function getDatasetStats() { return request('/rust/dataset/stats') }
export function getDatasetTasks(filters) { return request('/rust/dataset/tasks?'+new URLSearchParams(filters)) }
export function getDatasetTask(id) { return request('/rust/dataset/tasks/'+encodeURIComponent(id)) }
export function importExample(payload) { return request('/projects/from-demo', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}) }

export function saveAssistant(id, config) { return request('/projects/' + id + '/assistant', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(config)}) }

export function getAgents() { return request('/agents') }
export function listSkills() { return request('/skills') }
export function createSkill(body) { return request('/skills',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }
export function updateSkill(id,body) { return request('/skills/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }
export function archiveSkill(id) { return request('/skills/'+id,{method:'DELETE'}) }

export function importGithub(body) { return request('/projects/from-github',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }
export function renameProject(id,body) { return request('/projects/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }
export function duplicateProject(id) { return request('/projects/'+id+'/duplicate',{method:'POST'}) }
export function archiveProject(id) { return request('/projects/'+id,{method:'DELETE'}) }
export function runProjectBatch(id,body) { return request('/projects/'+id+'/batch-runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }

export function prepareAgent(id,body) { return request('/projects/'+id+'/agent-prompt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}) }

export function getSkill(id,version) { return request('/skills/'+id+'?version='+version) }

export function listBenchmarks(){return request("/benchmarks")}
export function getBenchmark(id){return request("/benchmarks/"+encodeURIComponent(id))}
export function getBenchmarkFile(id,file){return request("/benchmarks/"+encodeURIComponent(id)+"/file?file="+encodeURIComponent(file))}

export function getBenchmarkRuns(id,file){return request('/benchmarks/'+encodeURIComponent(id)+'/runs?file='+encodeURIComponent(file))}
export function submitBenchmarkRun(id,body){return request('/benchmarks/'+encodeURIComponent(id)+'/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
