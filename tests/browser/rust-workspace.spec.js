const {test,expect}=require('@playwright/test');

test('Rust project creation, file isolation and generation controls',async({page})=>{
 const project={id:'a'.repeat(32),name:'Rust test',language:'Rust',revision:1,runs:[],files:[{path:'main.rs',content:'use vstd::prelude::*;\nverus! { proof fn ok() { assert(true); } }'},{path:'other.rs',content:'use vstd::prelude::*;\nverus! { proof fn other() { assert(true); } }'}]};
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url()),path=url.pathname;
  let body={};
  if(path==='/api/v1/projects'){
   if(route.request().method()==='POST'){
    const input=route.request().postDataJSON();expect(input.language).toBe('Rust');expect(input.files[0].path).toBe('main.rs');body=project;
   } else body={items:[]};
  }else if(path==='/api/v1/projects/'+project.id)body=project;
  else if(path.endsWith('/runs')&&path.includes('/projects/')){
   const input=route.request().postDataJSON();expect(input.entry_path).toBe('main.rs');expect(input.mode).toBe('rust-verify');
   project.runs.push({task_id:'rust-task',entry_path:'main.rs',mode:'rust-verify',revision:1,status:'pass'});body={task_id:'rust-task',status:'queued'};
  }else if(path==='/api/v1/models')body={models:['fake']};
  else if(path==='/api/v1/rust/status')body={verifier:{available:true,message:'本机验证器已就绪',expected_version:'test'},provider:{models:[{id:'fake',configured:true}],default_model_id:'fake'}};
  else if(path==='/api/v1/runs/rust-task')body={task_id:'rust-task',status:'pass',phases:[],engine:'live'};
  else if(path==='/api/v1/runs/rust-task/result')body={status:'Pass',result_code:project.files[0].content,summary:'验证通过',proof_stats:{proved_goals:1,total_goals:1},logs:{raw:'1 verified'}};
  else if(path==='/api/v1/rust/prepare')body={prompt:'offline prompt'};
  else if(path.endsWith('/health'))body={status:'ok',available_models:['fake'],live_capabilities:{}};
  else body={items:[]};
  await route.fulfill({json:body});
 });
 await page.goto('/#/projects');
 await page.getByRole('button',{name:'＋ 新建项目',exact:true}).click();
 await page.getByLabel('项目语言',{exact:true}).selectOption('Rust');
 await page.getByRole('button',{name:'创建项目 →',exact:true}).click();
 await expect(page.getByLabel('源代码编辑器')).toHaveValue(/proof fn ok/);
 await expect(page.locator('.vf-editor-toolbar option')).toHaveCount(2);
 await page.getByRole('button',{name:'▷ 验证当前文件',exact:true}).click();
 await expect(page.locator('.vf-proof-summary')).toContainText('验证通过');
 await page.locator('.vf-file-row').filter({hasText:'other.rs'}).click();
 await expect(page.locator('.vf-proof-summary')).toHaveCount(0);
 await page.getByLabel('验证模式').selectOption('rust-generate');
 await page.getByPlaceholder('描述要实现的功能、输入条件与预期结果').fill('increment safely');
 await page.getByRole('button',{name:'离线预览提示词',exact:true}).click();
 await expect(page.getByText('提示词（未调用模型）',{exact:true})).toBeVisible();
 expect(errors).toEqual([]);
});
