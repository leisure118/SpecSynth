const {test,expect}=require('@playwright/test');
test('Skill page displays metadata and edits it without fetching or resubmitting private instructions',async({page})=>{
 let row={id:'a'.repeat(32),name:'spec-bottomup',version:1,enabled:true,agents:['deepseek-harness']};let saved=false;
 await page.route('**/api/v1/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;let body={items:[]};
  if(path==='/api/v1/skills')body={items:[row]};
  else if(path==='/api/v1/skills/'+row.id&&request.method()==='PUT'){
   const input=request.postDataJSON();expect(input).not.toHaveProperty('instructions');row={...row,...input,version:2};saved=true;body=row;
  }else if(path==='/api/v1/health')body={status:'ok',available_models:[],live_capabilities:{}};
  await route.fulfill({json:body});
 });
 await page.goto('/#/skills');
 await expect(page.getByRole('heading',{name:/spec-bottomup/})).toBeVisible();
 await expect(page.getByText('正文仅在后端加载')).toBeVisible();
 await expect(page.locator('textarea')).toHaveCount(0);
 await page.getByRole('button',{name:'编辑',exact:true}).click();
 await page.getByLabel('Skill 名称',{exact:true}).fill('规约生成');
 await page.getByRole('button',{name:'保存新版本',exact:true}).click();
 await expect(page.getByRole('heading',{name:/规约生成/})).toBeVisible();
 expect(saved).toBe(true);await expect(page.locator('textarea')).toHaveCount(0);
});
