const {test,expect}=require('@playwright/test');
const sample={sample_id:'NL-001',category:'Simple',description:'Return the larger input.\nKeep the original requirements.',function_signature:'fn max(x: u64, y: u64) -> (r: u64)',verified_verus:'use vstd::prelude::*;\nverus! { proof fn reference() { assert(true); } }'};
async function mockApi(page){
 const submissions=[];
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),url=new URL(req.url()),path=url.pathname;
  let body={items:[]};
  if(path.endsWith('/overview'))body={demo_cases:[{id:'c-example',title:'C example',description:'C contract demo',modes:['single']} ]};
  else if(path.endsWith('/demo-cases'))body={items:[{id:'c-example',title:'C example',description:'C contract demo',modes:['single']}]};
  else if(path.endsWith('/dataset/stats'))body={total:25,categories:{Simple:13,Loops:12}};
  else if(path.endsWith('/dataset/tree'))body={total:1,groups:[{path:'NL',count:1,files:[{sample_id:'NL-001',name:'NL-001.txt',category:'Simple'}]}]};
  else if(path.endsWith('/dataset/tasks/NL-001/input'))body=sample;
  else if(path.endsWith('/dataset/tasks/NL-001'))body=sample;
  else if(path.endsWith('/dataset/tasks')){
   const filtered=url.searchParams.get('query')==='missing';
   body={items:filtered?[]:[sample],page:Number(url.searchParams.get('page')),total:filtered?0:25,pages:filtered?0:3};
  }else if(path.endsWith('/projects')&&req.method()==='POST'){
   submissions.push(req.postDataJSON());body={...req.postDataJSON(),id:'b'.repeat(32),revision:1,runs:[]};
  }else if(path.includes('/projects/'+ 'b'.repeat(32)))body={...submissions.at(-1),id:'b'.repeat(32),revision:1,runs:[]};
  else if(path.endsWith('/models'))body={models:['fake']};
  else if(path.endsWith('/rust/status'))body={verifier:{available:true,message:'本机验证器已就绪'},provider:{models:[{id:'fake',configured:true}],default_model_id:'fake'}};
  await route.fulfill({json:body});
 });
 return submissions;
}

test('case language tabs stay on the current page and Rust has one dataset card',async({page})=>{
 await mockApi(page);
 for(const path of ['/#/','/#/projects']){
  await page.goto(path);
  await expect(page.getByRole('tabpanel')).toContainText('C example');
  const before=page.url();
  await page.getByRole('tab',{name:'Rust / Verus'}).click();
  await expect(page.getByRole('tabpanel').locator('.vf-example-card')).toHaveCount(1);
  await expect(page.getByRole('tabpanel')).toContainText('NL2VBENCH');
  expect(page.url()).toBe(before);
  await page.getByRole('tab',{name:'C / ACSL'}).click();
  await expect(page.getByRole('tabpanel')).toContainText('C example');
 }
});

test('dataset browsing, filtering, paging and exact reference handoff',async({page})=>{
 const sent=await mockApi(page);
 await page.goto('/#/datasets/nl2vbench');
 await expect(page.getByRole('heading',{name:'NL2VBENCH',exact:true})).toBeVisible();
 await expect(page.locator('.vf-dataset-description')).toContainText('Keep the original requirements.');
 await page.getByRole('button',{name:'下一页',exact:true}).click();
 await expect(page.getByRole('navigation',{name:'任务分页'})).toContainText('第 2 / 3 页');
 await page.getByRole('button',{name:'Loops',exact:true}).click();
 await expect(page.getByRole('navigation',{name:'任务分页'})).toContainText('第 1 / 3 页');
 await page.getByRole('searchbox').fill('missing');
 await expect(page.getByText('没有匹配任务',{exact:true})).toBeVisible();
 await page.getByRole('searchbox').fill('');
 await page.getByRole('button',{name:'去验证 →',exact:true}).click();
 await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue(sample.verified_verus);
 expect(sent[0].language).toBe('Rust');expect(sent[0].files[0].content).toBe(sample.verified_verus);
});

test('generation import uses the task requirements without treating its reference as generated output',async({page})=>{
 const sent=await mockApi(page);
 await page.goto('/#/datasets/nl2vbench');
 await page.getByRole('button',{name:'导入生成器 →',exact:true}).click();
 await expect(page.getByLabel('验证模式')).toHaveValue('rust-generate');
 await expect(page.getByLabel('自然语言任务页面')).toContainText(sample.description);
 await expect(page.getByLabel('自然语言任务页面')).toContainText(sample.function_signature);
 expect(sent[0].files[0].content).not.toBe(sample.verified_verus);
});

test('project actions and GitHub import are wired to backend endpoints',async({page})=>{
 const first={id:'c'.repeat(32),name:'Example',language:'C',revision:1,file_count:1,runs:[],updated_at:new Date().toISOString(),files:[{path:'main.c',content:'int main(void){return 0;}'}]};
 let projects=[first];
 await page.route('**/api/v1/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname,method=req.method();let body={items:[]};
  if(path.endsWith('/models'))body={models:['test-model']};
  else if(path.endsWith('/rust/status'))body={verifier:{available:true,message:'ready'},provider:{models:[]}};
  else if(path.endsWith('/projects/from-github')){const input=req.postDataJSON();expect(input.repository).toBe('example/repo');expect(input.language).toBe('Rust');body={...first,id:'e'.repeat(32),name:'repo',language:'Rust',files:[{path:'lib.rs',content:'use vstd::prelude::*; verus! {}'}]};projects.push(body);}
  else if(path.endsWith('/projects'))body={items:projects};
  else if(path.endsWith('/duplicate')){const original=projects.find(p=>path.includes(p.id));body={...original,id:'d'.repeat(32),name:original.name+' 副本'};projects.push(body);}
  else if(path.includes('/projects/')){
   const id=path.split('/')[4],p=projects.find(p=>p.id===id);
   if(method==='PATCH'){Object.assign(p,req.postDataJSON(),{revision:p.revision+1});body=p}
   else if(method==='DELETE'){projects=projects.filter(p=>p.id!==id);body={archived:true}}
   else body=p;
  }
  await route.fulfill({json:body});
 });
 await page.goto('/#/projects');
 await page.getByRole('button',{name:'Example 项目操作',exact:true}).click();
 await page.getByRole('menuitem',{name:'重命名',exact:true}).click();
 await page.getByLabel('新项目名称',{exact:true}).fill('Renamed');
 await page.getByRole('button',{name:'保存名称',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Renamed',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Renamed 项目操作',exact:true}).click();
 await page.getByRole('menuitem',{name:'复制项目',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Renamed 副本',exact:true})).toBeVisible();
 page.on('dialog',dialog=>dialog.accept());
 await page.getByRole('button',{name:'Renamed 副本 项目操作',exact:true}).click();
 await page.getByRole('menuitem',{name:'归档项目',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Renamed 副本',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'＋ 新建项目',exact:true}).click();
 await page.getByRole('button',{name:'从 GitHub 导入',exact:true}).click();
 await page.getByLabel('仓库地址',{exact:true}).fill('example/repo');
 await page.getByLabel('导入语言',{exact:true}).selectOption('Rust');
 await page.getByRole('button',{name:'导入项目',exact:true}).click();
 await expect(page).toHaveURL(new RegExp('/projects/'+'e'.repeat(32)+'$'));
 await page.locator('.vf-project-source-folder > summary').click();
 await page.getByRole('button',{name:/RS lib.rs/}).click();
 await expect(page.getByLabel('Verus 代码编辑器')).toHaveValue('use vstd::prelude::*; verus! {}');
});
