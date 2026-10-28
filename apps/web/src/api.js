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

export function uploadFile(file) {
  var fd = new FormData(); fd.append('file', file)
  return request('/files/upload', { method: 'POST', body: fd })
}

export function uploadBundle(files, manifest, rootDir) {
  var fd = new FormData()
  files.forEach(function(f){ fd.append('files', f) })
  fd.append('manifest', JSON.stringify(manifest))
  if (rootDir) fd.append('root_dir', rootDir)
  return request('/files/upload-bundle', { method: 'POST', body: fd })
}

export function submitRun(mode, payload) {
  return request('/runs/' + mode, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

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
