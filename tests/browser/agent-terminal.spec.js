const {test,expect}=require('@playwright/test')
test('native commands are visible and additional instructions are submitted',async({page})=>{
 const id='e'.repeat(32);let sent='',cancelled=0;const errors=[];page.on('pageerror',e=>errors.push(e.message))
 const project={id,name:'Terminal test',language:'C',revision:1,files:[{path:'main.c',content:'int main(){return 0;}'}],assistant:{agent:'deepseek-harness',skills:[],skill_refs:[]},runs:[{task_id:'live-task',entry_path:'main.c',mode:'single',revision:1,status:'running'}]}
 await page.route('**/api/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;let body={items:[]}
  if(path==='/api/v1/projects/'+id)body=project
  else if(path==='/api/v1/models')body={models:['test-model']}
  else if(path==='/api/v1/agents')body={items:[{id:'deepseek-harness',name:'DeepSeek Harness CLI',ready:true}]}
  else if(path==='/api/v1/runs/live-task')body={task_id:'live-task',status:'running',phases:[],metadata:{agent_progress:{steps:[{id:'tool',label:'Frama-C 验证',status:'completed',command:'frama-c -wp main.c',output:'7/7 goals'}]}}}
  else if(path.endsWith('/cancel')){cancelled++;expect(route.request().method()).toBe('POST');body={cancel_requested:true}}
  else if(path.endsWith('/terminal'))body={agent:'deepseek-harness',events:[{id:'launch',command:'node dsh.js --profile headless --json -',status:'completed',source:'native-cli'},{id:'tool',command:'frama-c -wp main.c',output:'7/7 goals',status:'completed',source:'native-cli'}]}
  else if(path.endsWith('/interaction')){
   if(route.request().method()==='POST'){sent=route.request().postDataJSON().text;body={id:'message',status:'pending'}}
   else body={items:sent?[{id:'message',status:'pending',text:sent}]:[]}
  }
  await route.fulfill({json:body})
 })
 await page.goto('/#/projects/'+id)
 await page.getByRole('button',{name:'终端与交互',exact:true}).click()
 await expect(page.locator('.vf-terminal-command').last()).toContainText('frama-c -wp main.c')
 await expect(page.locator('.vf-terminal-command').first()).toContainText('node dsh.js')
 await page.locator('.vf-native-command-details summary').first().click()
 await expect(page.locator('.vf-terminal-command-full').first()).toBeVisible()
 await page.getByRole('button',{name:'展开终端',exact:true}).click()
 await expect(page.locator('.vf-agent-terminal')).toHaveClass(/is-expanded/)
 await page.keyboard.press('Escape')
 await expect(page.locator('.vf-agent-terminal')).not.toHaveClass(/is-expanded/)
 await expect(page.locator('.vf-terminal-screen')).toContainText('7/7 goals')
 await page.getByRole('textbox',{name:'补充指令',exact:true}).fill('保留第二个循环的不变式')
 await page.getByRole('button',{name:'发送补充指令',exact:true}).click()
 await expect.poll(()=>sent).toBe('保留第二个循环的不变式')
 await expect(page.locator('.vf-terminal-message')).toContainText('等待下一次修复')
 await page.getByRole('button',{name:'停止任务',exact:true}).click()
 await expect(page.getByRole('button',{name:'已请求停止',exact:true})).toBeDisabled()
 await expect.poll(()=>cancelled).toBe(1)
 expect(errors).toEqual([])
})
