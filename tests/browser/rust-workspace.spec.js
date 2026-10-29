const {test,expect}=require('@playwright/test');
const CODE='use vstd::prelude::*;\nverus! {\nspec fn positive(x: int) -> bool { x > 0 }\nproof fn lemma() { assert(true); }\nfn inc(x: u64) -> (r: u64)\n    requires x < 100,\n    ensures r == x + 1,\n{ x + 1 }\n}';
async function mockApi(page,{existing=false}={}){
 const project={id:'a'.repeat(32),name:'Rust test',language:'Rust',revision:1,runs:[],files:existing?[{path:'main.rs',content:CODE},{path:'other.rs',content:CODE}]:[{path:'main.rs',content:''}]};
 const row={sample_id:'TEST-TASK',description:'Increment safely',function_signature:'fn inc(x: u64) -> (r: u64)',category:'Arithmetic'};
 const calls={generated:0};
 await page.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url()),path=url.pathname;let body={};
  if(path==='/api/v1/projects'){
   if(route.request().method()==='POST'){const input=route.request().postDataJSON();expect(input.language).toBe('Rust');expect(input.files).toEqual([{path:'main.rs',content:''}]);body=project}else body={items:[]};
  }else if(path==='/api/v1/projects/'+project.id)body=project;
  else if(path.endsWith('/runs')&&path.includes('/projects/')){
   const input=route.request().postDataJSON();if(input.mode==='rust-generate')calls.generated++;
   expect(input.entry_path).toBe('main.rs');expect(input.mode).toBe('rust-verify');
   project.runs.push({task_id:'rust-task',entry_path:'main.rs',mode:'rust-verify',revision:1,status:'pass'});body={task_id:'rust-task',status:'queued'};
  }else if(path==='/api/v1/models')body={models:['fake']};
  else if(path==='/api/v1/rust/status')body={verifier:{available:true,message:'本机验证器已就绪',expected_version:'test'},provider:{models:[]},agents:[{id:'direct',name:'模型直连',available:true,models:[],protocol:'chat'}],skills:[]};
  else if(path==='/api/v1/rust/dataset/tasks')body={items:[row],page:1,pages:1,total:1};
  else if(path==='/api/v1/rust/dataset/tasks/TEST-TASK')body={...row,verified_verus:CODE};
  else if(path==='/api/v1/runs/rust-task')body={task_id:'rust-task',status:'pass',phases:[],engine:'live'};
  else if(path==='/api/v1/runs/rust-task/result')body={status:'Pass',result_code:CODE,summary:'验证通过',proof_stats:{proved_goals:1,total_goals:1},logs:{raw:'1 verified'}};
  else if(path.endsWith('/health'))body={status:'ok',available_models:['fake'],live_capabilities:{}};
  else body={items:[]};
  await route.fulfill({json:body});
 });
 return {project,calls};
}

test('Rust starts blank; offline ground truth creates a file without API generation',async({page})=>{
 const {calls}=await mockApi(page);const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/#/projects');await page.getByRole('button',{name:'＋ 新建项目',exact:true}).click();
 await page.getByLabel('项目语言',{exact:true}).selectOption('Rust');await page.getByRole('button',{name:'创建项目 →',exact:true}).click();
 await expect(page.getByLabel('空白代码编辑区')).toBeVisible();await expect(page.getByLabel('Verus 代码编辑器')).toHaveCount(0);
 await page.getByRole('button',{name:'选择数据集',exact:true}).click();await page.getByRole('button',{name:/^TEST-TASK Arithmetic/}).click();
 await page.getByRole('button',{name:'▷ 生成 Verus',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Verus 文件已就绪'})).toBeVisible();await expect(page.getByLabel('空白代码编辑区')).toBeVisible();
 await page.getByRole('button',{name:'打开代码 →',exact:true}).click();await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue(CODE);
 expect(await page.locator('.vf-verus-line.spec').count()).toBeGreaterThan(0);expect(await page.locator('.vf-verus-line.proof').count()).toBeGreaterThan(0);expect(await page.locator('.vf-verus-line.exec').count()).toBeGreaterThan(0);
 await page.getByRole('button',{name:'关闭当前文件',exact:true}).click();await expect(page.getByLabel('空白代码编辑区')).toBeVisible();
 await page.reload();await expect(page.getByLabel('空白代码编辑区')).toBeVisible();await expect(page.getByRole('button',{name:/RS TEST-TASK.rs Ground truth/})).toBeVisible();
 expect(calls.generated).toBe(0);expect(errors).toEqual([]);
});

test('verification requires an explicitly opened project file and preserves file isolation',async({page})=>{
 const {project}=await mockApi(page,{existing:true});await page.goto('/#/projects/'+project.id);
 await page.getByLabel('验证模式').selectOption('rust-verify');await expect(page.getByRole('button',{name:'▷ 验证当前文件',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:/^RS main.rs 未验证/}).click();await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue(CODE);
 await page.getByRole('button',{name:'▷ 验证当前文件',exact:true}).click();await expect(page.locator('.vf-proof-summary')).toContainText('验证通过');
 await page.locator('.vf-file-row').filter({hasText:'other.rs'}).click();await expect(page.locator('.vf-proof-summary')).toHaveCount(0);
});
