const {test,expect}=require('@playwright/test');

test('VeriFlow layout keeps the dual-track animation and existing feature routes',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/#/');
 await expect(page.locator('#hero-title')).toContainText('玄鉴');
 await expect(page.getByLabel('C 与 Rust 双轨形式化验证流程')).toBeVisible();
 await page.getByRole('button',{name:'Rust / Verus',exact:true}).click();
 await expect(page.locator('.x-route-label')).toHaveText('自然语言 → Verus → 机器验证');
 await page.getByRole('link',{name:'验证流程',exact:true}).click();
 expect(new URL(page.url()).hash).toBe('#/');
 await expect(page.locator('#workflow')).toBeInViewport();
 await page.locator('#home-navigation').getByRole('link',{name:'数据集',exact:true}).click();
 await expect(page.getByRole('heading',{name:'NL2VBENCH',exact:true})).toBeVisible();
 expect(errors).toEqual([]);
});

test('mobile navigation opens and does not overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/#/');
 const menu=page.getByRole('button',{name:'切换导航菜单',exact:true});
 await expect(menu).toBeVisible();await menu.click();
 await expect(menu).toHaveAttribute('aria-expanded','true');
 await expect(page.locator('#home-navigation').getByRole('link',{name:'工作台',exact:true})).toBeVisible();
 await menu.click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
});
