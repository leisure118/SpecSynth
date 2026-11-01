const { test, expect } = require("@playwright/test");

async function submitReplay(request, mode, demoCaseId) {
  const response = await request.post(`/api/v1/runs/${mode}`, {
    data: { demo_case_id: demoCaseId, model_name: "qwen-turbo" },
  });
  expect(response.ok()).toBeTruthy();
  return await response.json();
}

async function openExample(page, demo='sum_loop_100000', mode='single') {
  await page.goto('/#/projects?demo='+demo+'&mode='+mode);
  await expect(page.getByLabel('源代码编辑器')).toBeVisible();
}
async function replayAndOpenResult(page) {
  await openExample(page);
  const created=page.waitForResponse(r=>/\/projects\/[^/]+\/runs$/.test(new URL(r.url()).pathname)&&r.request().method()==='POST'&&r.status()===201);
  await page.getByRole('button',{name:'▷ 回放案例',exact:true}).click();
  const id=(await (await created).json()).task_id;
  await expect(page.locator('.vf-run-id')).toContainText(id);
  await expect(page.locator('.vf-proof-summary')).toBeVisible({timeout:30000});
  await page.getByRole('link',{name:'完整结果与证据 ↗'}).click();
  await page.waitForURL(/#\/result\//);
}

test('首页案例通过项目工作台完成回放',async({page})=>{
  await page.goto('/#/');
  await expect(page.locator('#hero-title')).toContainText('可信软件智能验证');
  await expect(page.getByRole('navigation',{name:'主导航'}).getByText('任务启动')).toHaveCount(0);
  await replayAndOpenResult(page);
  await expect(page.getByRole('heading',{name:'证据链',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'规约摘要',exact:true})).toBeVisible();
  await expect(page.locator('.status-chip').first()).toHaveText(/通过/);
});

test('旧任务启动链接迁移到项目和新建对话框',async({page})=>{
  await page.goto('/#/upload');
  await page.waitForURL(/#\/projects\?new=1/);
  await expect(page.getByRole('dialog',{name:'新建项目'})).toBeVisible();
  await page.goto('/#/upload?demo=sum_loop_100000&mode=termination');
  await expect(page.getByLabel('验证模式')).toHaveValue('termination');
  await expect(page.locator('.vf-editor-toolbar option')).toHaveCount(3);
  await expect(page.getByRole('button',{name:'▷ 回放案例',exact:true})).toBeVisible();
});

test("多模块示例页展示 X.509 解析器验证图谱", async ({ page }) => {
  await openExample(page,'x509_inter_modular_replay','inter-modular');
  await page.getByRole('button',{name:'验证图谱',exact:true}).click();
  await expect(page.getByText("X.509 解析器验证图谱")).toBeVisible();
  const frame = page.frameLocator(".x509-showcase-frame");
  await expect(frame.locator(".info-bar")).toContainText("212 functions");
  const node = frame.locator("circle").first();
  await expect(node).toBeVisible();
  await node.click();
  await frame.getByRole('button',{name:'查看函数规约与源码'}).click();
  await page.waitForURL(/#\/x509-function\//);
  await expect(page.locator(".x509-function-page")).toBeVisible();
  await expect(page.locator(".x509-function-pane")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "原始函数源码" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "带 ACSL 规约的函数" })).toBeVisible();
  await expect(page.locator(".x509-function-pane").first()).toContainText("原始函数源码");
  await expect(page.locator(".x509-function-pane").last()).toContainText("带 ACSL 规约的函数");
  await page.getByRole('button',{name:'← 返回验证图谱'}).click();
  await expect(page.locator('.vf-workspace-graph')).toBeVisible();
});

test("结果页在调试视图中支持工件预览", async ({ page }) => {
  await replayAndOpenResult(page);
  await page.getByRole("button", { name: "展开调试视图" }).click();
  const preview = page.locator(".artifact-grid .code-block");
  const before = await preview.textContent();
  await page.getByRole("button", { name: "预览" }).last().click();
  await expect(preview).not.toHaveText(before || "");
});

test("结果页不会引入横向溢出", async ({ page }) => {
  await replayAndOpenResult(page);
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
    };
  });
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 2);
});

test("宽屏结果页遵循当前居中布局", async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await replayAndOpenResult(page);
  const metrics = await page.locator(".page-shell").evaluate((node) => {
    const rect = node.getBoundingClientRect();
    return { width: rect.width, left: rect.left, rightGap: window.innerWidth - rect.right };
  });
  expect(metrics.width).toBeGreaterThanOrEqual(1280);
  expect(metrics.width).toBeLessThanOrEqual(1360);
  expect(Math.abs(metrics.left - metrics.rightGap)).toBeLessThanOrEqual(24);
});

test("结果页在任务切换后会刷新为新任务数据", async ({ page, request }) => {
  const single = await submitReplay(request, "single", "sum_loop_100000");
  const termination = await submitReplay(request, "termination", "bubble_sort_total_correctness");

  await page.goto(`/#/result/${single.task_id}`, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".result-info-bar").getByText("单函数分析")).toBeVisible();
  await expect(page.locator(".status-chip")).toHaveText(/通过/);

  await page.goto(`/#/result/${termination.task_id}`, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".result-info-bar").getByText("终止性验证")).toBeVisible();
  await expect(page.getByRole("heading", { name: "冒泡排序总正确性" })).toBeVisible();
  await expect(page.locator(".status-chip")).toHaveText(/通过/);
});
