const {test,expect}=require('@playwright/test')
test('source changes blocked, annotation edits and insertion allowed',async({page,request})=>{
 const original='int main(void) {\n  /*@ assert 1; */\n  return 0;\n}\n'
 const response=await request.post('/api/v1/projects',{data:{name:'Spec lock UI check',language:'C',files:[{path:'main.c',content:original}]}})
 expect(response.ok()).toBeTruthy();const project=await response.json()
 try{
  await page.goto('/#/projects/'+project.id)
  const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true})
  await editor.fill(original.replace('return 0','return 1'))
  await expect(editor).toHaveValue(original)
  await expect(page.locator('.vf-spec-edit-warning')).toBeVisible()
  const annotated=original.replace('assert 1','assert 2')
  await editor.fill(annotated)
  await expect(editor).toHaveValue(annotated)
  await page.getByRole('button',{name:'保存人工版本',exact:true}).click()
  await expect(page.getByRole('button',{name:'保存人工版本',exact:true})).toBeDisabled()
  const saved=await (await request.get('/api/v1/projects/'+project.id)).json()
  expect(saved.files[0].content).toBe(annotated)
  const rejected=await request.put('/api/v1/projects/'+project.id,{data:{name:project.name,language:'C',revision:saved.revision,files:[{path:'main.c',content:annotated.replace('return 0','return 2')}]}})
  expect(rejected.status()).toBe(422)
  await page.getByRole('button',{name:'插入规约',exact:true}).click()
  await expect(editor).not.toHaveValue(annotated)
 }finally{await request.delete('/api/v1/projects/'+project.id)}
})

test('annotation delimiters can be deleted character by character while original C stays locked',async({page,request})=>{
 const original='int main(void) {\n  //@\n  return 0;\n}\n';
 const response=await request.post('/api/v1/projects',{data:{name:'Annotation delimiter deletion check',language:'C',files:[{path:'main.c',content:original}]}});
 const project=await response.json();
 try{
  await page.goto('/#/projects/'+project.id);
  const editor=page.getByRole('textbox',{name:'C 源代码编辑器',exact:true});
  await expect(editor).toHaveValue(original);
  await editor.evaluate(el=>{el.focus();const end=el.value.indexOf('//@')+3;el.setSelectionRange(end,end)});
  await editor.press('Backspace');await expect(editor).toHaveValue(original.replace('//@','//'));
  await editor.press('Backspace');await expect(editor).toHaveValue(original.replace('//@','/'));
  await editor.press('Backspace');const clean=original.replace('//@','');await expect(editor).toHaveValue(clean);
  await expect(page.locator('.vf-spec-edit-warning')).toHaveCount(0);
  await editor.fill(clean.replace('return 0','return 1'));await expect(editor).toHaveValue(clean);
  await page.getByRole('button',{name:'保存人工版本',exact:true}).click();
  await expect(page.getByRole('button',{name:'保存人工版本',exact:true})).toBeDisabled();
  expect((await (await request.get('/api/v1/projects/'+project.id)).json()).files[0].content).toBe(clean);
 }finally{await request.delete('/api/v1/projects/'+project.id)}
});
