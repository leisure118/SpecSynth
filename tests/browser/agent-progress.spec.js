const {test,expect}=require('@playwright/test');
test('C verification polls real steps and shows green completed dots while later work runs',async({page})=>{
 const id='e'.repeat(32);let polls=0;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const project={id,name:'实时验证示例',language:'C',revision:1,files:[{path:'main.c',content:'int main(void){return 0;}'}],assistant:{agent:'deepseek-harness',workflow:'standard',sub_model:'',skills:[],skill_refs:[]},runs:[{task_id:'live-task',entry_path:'main.c',mode:'single',revision:1,status:'running'}]};
 await page.route('**/api/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;let body={items:[]};
  if(path==='/api/v1/projects/'+id)body=project;
  else if(path==='/api/v1/models')body={models:['deepseek-v4-flash-0731']};
  else if(path==='/api/v1/agents')body={items:[{id:'deepseek-harness',name:'DeepSeek Harness CLI',ready:true,default_model:'deepseek-v4-flash-0731'}]};
  else if(path==='/api/v1/runs/live-task'){
   polls++;body={task_id:'live-task',status:'running',engine:'live',phases:[],metadata:{agent_progress:{round:0,current:polls<2?'子 Agent 生成规约':'平台独立 Frama-C 验证',steps:[{id:'read',label:'读取源码',status:'completed'},{id:'child',label:'子 Agent 生成规约',status:polls<2?'running':'completed'},...(polls<2?[]:[{id:'proof',label:'平台独立 Frama-C 验证',status:'running'}])]}}};
  }else if(path==='/api/v1/health')body={status:'ok',available_models:[],live_capabilities:{}};
  await route.fulfill({json:body});
 });
 await page.goto('/#/projects/'+id);
 await page.locator('.vf-compact-progress summary').click();
 const panel=page.getByRole('region',{name:'实时验证步骤'});
 await expect(panel).toBeVisible();
 await expect(panel.getByRole('img',{name:'已完成'}).first()).toHaveCSS('background-color','rgb(22, 163, 106)');
 await expect(panel.locator('li').filter({hasText:'子 Agent 生成规约'}).locator('.completed')).toBeVisible();
 await expect(panel.locator('li').filter({hasText:'平台独立 Frama-C 验证'}).locator('.running')).toBeVisible();
 await page.screenshot({path:'runtime/agent-progress-preview.png',fullPage:true});
 expect(polls).toBeGreaterThanOrEqual(2);expect(errors).toEqual([]);
});
