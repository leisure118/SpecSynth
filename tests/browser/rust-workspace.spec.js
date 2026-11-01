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
  else if(path==='/api/v1/rust/dataset/tree')body={total:1,groups:[{path:'TEST',count:1,files:[{sample_id:row.sample_id,name:row.sample_id+'.txt',category:row.category}]}]};
  else if(path==='/api/v1/rust/dataset/tasks/TEST-TASK/input')body=row;
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
 await page.getByRole('treeitem').filter({hasText:'TEST'}).click();await page.getByRole('treeitem',{name:/TEST-TASK.txt/}).click();
 await expect(page.getByLabel('自然语言任务页面')).toContainText('Increment safely');
 await page.getByRole('button',{name:'▷ 生成 Verus',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Verus 文件已就绪'})).toBeVisible();await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue(CODE);
 expect(await page.locator('.vf-verus-line.spec').count()).toBeGreaterThan(0);expect(await page.locator('.vf-verus-line.proof').count()).toBeGreaterThan(0);expect(await page.locator('.vf-verus-line.exec').count()).toBeGreaterThan(0);
 await page.getByRole('button',{name:'关闭当前文件',exact:true}).click();await expect(page.getByLabel('自然语言任务页面')).toBeVisible();await page.getByRole('button',{name:'关闭当前任务',exact:true}).click();await expect(page.getByLabel('空白代码编辑区')).toContainText('从一项任务开始');
 await page.reload();await expect(page.getByLabel('空白代码编辑区')).toBeVisible();await expect(page.getByRole('button',{name:/RS TEST-TASK.rs Ground truth/})).toBeVisible();
 expect(calls.generated).toBe(0);expect(errors).toEqual([]);
});

test('verification requires an explicitly opened project file and preserves file isolation',async({page})=>{
 const {project}=await mockApi(page,{existing:true});await page.goto('/#/projects/'+project.id);
 await page.getByLabel('验证模式').selectOption('rust-verify');await expect(page.getByRole('button',{name:'▷ 验证当前文件',exact:true})).toBeDisabled();
 await page.locator('.vf-project-source-folder > summary').click();await page.getByRole('button',{name:/^RS main.rs 未验证/}).click();await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue(CODE);
 await page.getByRole('button',{name:'▷ 验证当前文件',exact:true}).click();await expect(page.getByRole('region',{name:'运行进度与验证结果'})).toContainText('Verus 验证通过');
 await page.locator('.vf-file-row').filter({hasText:'other.rs'}).click();await expect(page.getByRole('region',{name:'运行进度与验证结果'})).toHaveCount(0);
});

test('independent skill library binds a pinned version to an agent',async({page})=>{
 const id='a'.repeat(32),skillId='b'.repeat(32),project={id,name:'Agent project',language:'C',revision:1,files:[{path:'main.c',content:'int main(void){return 0;}'}],runs:[]};
 let saved,submitted,skills=[];
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;let body={items:[]};
  if(path.endsWith('/models'))body={models:['test-model']};
  else if(path.endsWith('/agents'))body={items:[{id:'default',name:'默认验证流程',ready:true},{id:'codex',name:'Codex',ready:true,message:'登录记录已检测'}]};
  else if(path.endsWith('/skills')){if(req.method()==='POST'){skills=[{...req.postDataJSON(),id:skillId,version:1}];body=skills[0]}else body={items:skills};}
  else if(path.endsWith('/assistant')){saved=req.postDataJSON();project.assistant=saved;body=saved;}
  else if(path.endsWith('/runs')&&req.method()==='POST'){submitted=req.postDataJSON();body={task_id:'skill-task',status:'queued'};}
  else if(path.includes('/projects/'))body=project;
  else if(path.endsWith('/runs/skill-task'))body={task_id:'skill-task',status:'queued',phases:[]};
  await route.fulfill({json:body});
 });
 await page.goto('/#/projects/'+id);
 await page.locator('.vf-workspace-settings > summary').click();
 await page.getByRole('link',{name:'独立设置 Skill ↗',exact:true}).click();
 await page.getByLabel('Skill 名称',{exact:true}).fill('数组边界');
 await page.getByLabel('Skill 指令',{exact:true}).fill('Check all array boundaries.');
 await page.getByRole('button',{name:'创建 Skill',exact:true}).click();
 await expect(page.getByRole('heading',{name:/数组边界/})).toBeVisible();
 await page.getByRole('link',{name:'返回项目',exact:true}).click();
 await page.locator('.vf-workspace-settings > summary').click();
 await page.getByLabel('执行 Agent',{exact:true}).selectOption('codex');
 await page.getByRole('checkbox',{name:/数组边界/}).check();
 await page.getByRole('button',{name:'保存配置',exact:true}).click();
 await expect(page.getByRole('status')).toContainText('配置已保存');
 expect(saved.agent).toBe('codex');expect(saved.skill_refs[0]).toEqual({id:skillId,version:1,enabled:true});
 await page.reload();
 await page.locator('.vf-workspace-settings > summary').click();
 await expect(page.getByLabel('执行 Agent',{exact:true})).toHaveValue('codex');
 await expect(page.getByRole('checkbox',{name:/数组边界/})).toBeChecked();
 await page.getByRole('button',{name:'▷ 验证当前文件',exact:true}).click();
 await expect.poll(()=>submitted?.assistant?.agent).toBe('codex');
 expect(submitted.assistant.skill_refs[0].version).toBe(1);
});

test('pinned skill keeps its original metadata until explicitly upgraded',async({page})=>{
 const id='a'.repeat(32),skillId='b'.repeat(32);
 const project={id,name:'Pinned project',language:'C',revision:1,runs:[],files:[{path:'main.c',content:'int f(void){return 0;}'}],assistant:{agent:'codex',skills:[],skill_refs:[{id:skillId,version:1,enabled:true}]}};
 await page.route('**/api/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;let body={items:[]};
  if(path.endsWith('/models'))body={models:['test']};
  else if(path.endsWith('/agents'))body={items:[{id:'codex',name:'Codex',ready:true}]};
  else if(path.endsWith('/skills/'+skillId))body={id:skillId,name:'Original pinned',version:1,agents:['codex'],enabled:true};
  else if(path.endsWith('/skills'))body={items:[{id:skillId,name:'Changed latest',version:2,agents:['claude-code'],enabled:true}]};
  else if(path.includes('/projects/'))body=project;
  await route.fulfill({json:body});
 });
 await page.goto('/#/projects/'+id);
 await page.locator('.vf-workspace-settings > summary').click();
 await expect(page.getByRole('checkbox',{name:/Original pinned/})).toBeChecked();
 await expect(page.getByRole('checkbox',{name:/Changed latest/})).toHaveCount(0);
 await page.getByRole('button',{name:'升级 v2',exact:true}).click();
 await expect(page.getByRole('checkbox',{name:/Changed latest/})).toBeChecked();
 await expect(page.locator('.vf-agent-config')).toContainText('当前 Agent 不应用');
});
