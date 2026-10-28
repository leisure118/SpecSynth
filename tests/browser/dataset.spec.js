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
 await expect(page.getByLabel('源代码编辑器')).toHaveValue(sample.verified_verus);
 expect(sent[0].language).toBe('Rust');expect(sent[0].files[0].content).toBe(sample.verified_verus);
});

test('generation import uses the task requirements without treating its reference as generated output',async({page})=>{
 const sent=await mockApi(page);
 await page.goto('/#/datasets/nl2vbench');
 await page.getByRole('button',{name:'导入生成器 →',exact:true}).click();
 await expect(page.getByLabel('验证模式')).toHaveValue('rust-generate');
 await expect(page.getByPlaceholder('描述要实现的功能、输入条件与预期结果')).toHaveValue(sample.description);
 await expect(page.getByPlaceholder('fn increment(x: u64) -> (r: u64)')).toHaveValue(sample.function_signature);
 expect(sent[0].files[0].content).not.toBe(sample.verified_verus);
});
