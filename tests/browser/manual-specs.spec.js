const {test,expect}=require('@playwright/test')
test('manual annotations save separately, failed lines clear after edits, and direct recheck passes',async({page,request})=>{
 const source='int main(void) {\n  int x=0;\n  /*@ loop invariant x < 0;\n      loop assigns x;\n      loop variant 1-x; */\n  while(x<1) { x++; }\n  return 0;\n}\n'
 const response=await request.post('/api/v1/projects',{data:{name:'Manual annotation UI check',language:'C',files:[{path:'manual.c',content:source}]}})
 expect(response.ok()).toBeTruthy();const project=await response.json()
 try{
  const runResponse=await request.post(`/api/v1/projects/${project.id}/runs`,{data:{revision:project.revision,entry_path:'manual.c',mode:'single',verification_only:true,timeout_sec:60}})
  expect(runResponse.ok()).toBeTruthy();const run=await runResponse.json()
  await expect.poll(async()=>{const r=await request.get(`/api/v1/runs/${run.task_id}`);return (await r.json()).status},{timeout:90000,intervals:[1000]}).toBe('fail')
  await request.put(`/api/v1/projects/${project.id}/assistant`,{data:{agent:'deepseek-harness',skills:[],skill_refs:[]}})
  await page.goto(`/#/projects/${project.id}`)
  await expect(page.locator('.ide-line.has-error')).toHaveCount(1)
  await expect(page.locator('.vf-source-diagnostics')).toContainText('行')
  const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true})
  const corrected=source.replace('x < 0','x >= 0')
  await editor.fill(corrected)
  await expect(page.locator('.ide-line.has-error')).toHaveCount(0)
  await page.getByRole('button',{name:'保存人工版本',exact:true}).click()
  await expect(page.getByRole('button',{name:'保存人工版本',exact:true})).toBeDisabled()
  const versionResponse=await request.get(`/api/v1/projects/${project.id}/versions/2`);expect(versionResponse.ok()).toBeTruthy()
  const version=await versionResponse.json();expect(version.origin).toBe('human');expect(version.files[0].content).toBe(corrected)
  const old=await request.get(`/api/v1/runs/${run.task_id}/result`);expect((await old.json()).result_code).toBe(source)
  await page.getByRole('button',{name:'仅验证当前规约',exact:true}).click()
  await expect(page.locator('.vf-proof-summary h3')).toHaveText('通过',{timeout:90000})
  await expect(page.locator('.ide-line.has-error')).toHaveCount(0)
  let continuation
  await page.route(`**/api/v1/projects/${project.id}/runs`,async route=>{
   continuation=route.request().postDataJSON()
   await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({detail:'Test preview only; no model request'})})
  })
  await page.getByRole('button',{name:'保存并让 Agent 继续',exact:true}).click()
  await expect.poll(()=>continuation?.resume_task_id).toBeTruthy()
  expect(continuation.assistant.agent).toBe('deepseek-harness')
  expect(continuation.max_repair_rounds).toBe(3)
  // This continuation request is intercepted; no paid model call is made.
 }finally{await request.delete(`/api/v1/projects/${project.id}`)}
})
