const {test,expect}=require('@playwright/test');
const content='int increment(int x)\n//@ requires 0 <= x &*& x < 100;\n//@ ensures result == x + 1;\n{ return x + 1; }\n';

test('one project workspace dispatches VeriFast through the shared task lifecycle',async({page,request})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const response=await request.post('/api/v1/projects',{data:{name:'Shared verifier check',language:'C',files:[{path:'increment.c',content}]}});
 expect(response.ok()).toBeTruthy();const project=await response.json();
 try{
  await page.goto('/#/projects/'+project.id);
  const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true});
  await expect(editor).toHaveValue(content);
  await page.getByLabel('验证工具',{exact:true}).selectOption('verifast');
  await expect(editor).toHaveValue(content);
  await expect(page.locator('.vf-workspace-grid')).toBeVisible();
  await expect.poll(async()=> (await (await request.get('/api/v1/projects/'+project.id)).json()).verification_tool).toBe('verifast');
  await page.reload();
  await expect(page.getByLabel('验证工具',{exact:true})).toHaveValue('verifast');
  await expect(editor).toHaveValue(content);
  await page.getByRole('button',{name:'仅验证当前规约',exact:true}).click();
  await expect(page.locator('.vf-proof-summary h3')).toHaveText('通过');
  await expect(page.locator('.vf-proof-summary small')).toContainText('语句验证');
  await page.getByRole('button',{name:'终端与交互',exact:true}).click();
  await expect(page.locator('.vf-run-log')).toContainText('verifast');
  await editor.fill(content.replace('result == x + 1','result == x + 2'));
  await page.getByRole('button',{name:'仅验证当前规约',exact:true}).click();
  await expect(page.locator('.vf-proof-summary h3')).toHaveText('未通过');
  await expect(page.locator('.ide-line.has-error')).toHaveCount(1);
  await expect(page.locator('.ide-line').nth(2)).toHaveClass(/has-error/);
  await page.getByRole('button',{name:'历史',exact:true}).click();
  await expect(page.locator('.vf-history-row')).toHaveCount(2);
  const saved=await (await request.get('/api/v1/projects/'+project.id)).json();
  expect(saved.runs.every(r=>r.verification_tool==='verifast')).toBeTruthy();
  await page.getByLabel('验证工具',{exact:true}).selectOption('framac');
  await expect(editor).toHaveValue(content.replace('result == x + 1','result == x + 2'));
  await expect(page.locator('.vf-history-row')).toHaveCount(0);
  expect(errors).toEqual([]);
 }finally{await request.delete('/api/v1/projects/'+project.id)}
});

test('toolbox reuses its file editor and result surface for both tools',async({page})=>{
 await page.goto('/#/spectool');
 await page.getByLabel('验证工具',{exact:true}).selectOption('verifast');
 await page.locator('input[type=file]').first().setInputFiles({name:'increment.c',mimeType:'text/plain',buffer:Buffer.from(content)});
 const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true});
 await expect(editor).toHaveValue(content);
 await page.getByRole('button',{name:'VeriFast',exact:true}).click();
 await expect(page.locator('.spectool-result-list')).toContainText('通过');
 await expect(page.locator('.vf-run-log')).toContainText('verifast');
 await page.getByLabel('验证工具',{exact:true}).selectOption('framac');
 await expect(editor).toHaveValue(content);
 await expect(page.locator('.spectool-pipeline-panel')).toBeVisible();
});

test('benchmark uses the same verification dialog and shared task API',async({page})=>{
 await page.goto('/#/benchmarks/live24?file=frama-c-wp-tutorial-en_10.c');
 await page.getByRole('button',{name:'▷ 验证',exact:true}).click();
 const dialog=page.getByRole('dialog');
 await dialog.getByLabel('验证工具',{exact:true}).selectOption('verifast');
 await expect(dialog.getByLabel('重跑方式')).toBeVisible();
 await expect(dialog.locator('.spectool-studio-grid')).toHaveCount(0);
 await dialog.getByLabel('验证工具',{exact:true}).selectOption('framac');
 await expect(dialog.getByLabel('重跑方式')).toBeVisible();
});

test('VeriFast reuses agent, main model and sub-agent selectors for all three agents',async({page,request})=>{
 const response=await request.post('/api/v1/projects',{data:{name:'VeriFast generation controls check',language:'C',files:[{path:'counter.c',content:'int f(int x) { return x; }\n'}]}});
 const project=await response.json();let submitted;
 try{
  await page.route('**/api/v1/projects/'+project.id+'/runs',async route=>{
   submitted=route.request().postDataJSON();await route.fulfill({status:422,contentType:'application/json',body:JSON.stringify({detail:'Preview only; no model call'})});
  });
  await page.goto('/#/projects/'+project.id);
  await page.getByLabel('验证工具',{exact:true}).selectOption('verifast');
  await page.locator('.vf-workspace-settings summary').click();
  const agent=page.getByLabel('执行 Agent',{exact:true}),model=page.getByLabel('生成模型',{exact:true});
  await expect(agent).toBeVisible();await expect(model).toBeVisible();
  for(const id of ['codex','claude-code','deepseek-harness']){
   await agent.selectOption(id);
   await page.getByLabel('Sub-agent 模型',{exact:true}).selectOption('qwen35-9b-mix64');
   await page.getByRole('button',{name:'▷ 验证当前文件',exact:true}).click();
   await expect.poll(()=>submitted?.assistant?.agent).toBe(id);
   expect(submitted.verification_tool).toBe('verifast');expect(submitted.verification_only).toBe(false);
   expect(submitted.model_name).toBeTruthy();expect(submitted.assistant.sub_model).toBe('qwen35-9b-mix64');
  }
 }finally{await request.delete('/api/v1/projects/'+project.id)}
});

test('VeriFast shows native statement count and inserts VeriFast annotations while preserving C',async({page,request})=>{
 const code='int count_to_limit(int limit)\n//@ requires 0 <= limit &*& limit <= 100000;\n//@ ensures result == limit;\n{\n int count = 0;\n while (count < limit)\n //@ invariant 0 <= count &*& count <= limit;\n { count = count + 1; }\n return count;\n}\n';
 const response=await request.post('/api/v1/projects',{data:{name:'VeriFast statements and editor check',language:'C',files:[{path:'count.c',content:code}]}});
 const project=await response.json();
 try{
  await page.goto('/#/projects/'+project.id);
  await page.getByLabel('验证工具',{exact:true}).selectOption('verifast');
  const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true});
  await page.getByRole('button',{name:'仅验证当前规约',exact:true}).click();
  await expect(page.locator('.vf-proof-summary h3')).toHaveText('通过');
  await expect(page.locator('.vf-proof-summary>strong')).toHaveText('3 / 3');
  await expect(page.locator('.vf-proof-summary>small')).toContainText('语句验证');
  await editor.fill(code.replace('return count','return 0'));
  await expect(editor).toHaveValue(code);
  await expect(page.locator('.vf-spec-edit-warning')).toHaveText('仅允许修改 VeriFast 规约，原始源码已锁定。');
  await editor.press('ControlOrMeta+End');
  await page.getByRole('button',{name:'插入规约',exact:true}).click();
  await expect(editor).toHaveValue(code+'//@ \n');
  await editor.fill(code.replace('result == limit','result == limit &*& result >= 0'));
  await expect(page.locator('.vf-spec-edit-warning')).toHaveCount(0);
  await page.getByRole('button',{name:'保存人工版本',exact:true}).click();
  await expect(page.getByRole('button',{name:'保存人工版本',exact:true})).toBeDisabled();
  const saved=await (await request.get('/api/v1/projects/'+project.id)).json();
  expect(saved.files[0].content).toContain('result == limit &*& result >= 0');
 }finally{await request.delete('/api/v1/projects/'+project.id)}
});
