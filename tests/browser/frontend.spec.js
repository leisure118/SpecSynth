const { test, expect } = require("@playwright/test");

async function submitReplay(request, mode, demoCaseId) {
  const response = await request.post(`/api/v1/runs/${mode}`, {
    data: { demo_case_id: demoCaseId, model_name: "qwen-turbo" },
  });
  expect(response.ok()).toBeTruthy();
  return await response.json();
}

test("首页与单函数回放链路可在浏览器中完成", async ({ page }) => {
  await page.goto("/#/", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "玄鉴——AI赋能的可信软件智能验证平台" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "模式比较" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近证据" })).toBeVisible();

  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "统一任务启动台" })).toBeVisible();
  await page.locator(".source-tab").getByText("示例用例").click();
  await page.getByRole("button", { name: "提交运行" }).click();

  await page.waitForURL(/#\/run\//, { timeout: 30000 });
  await expect(page.getByRole("heading", { name: "运行状态" })).toBeVisible();
  await expect(page.locator(".run-meta-grid").getByText(/^单函数分析$/)).toBeVisible();

  await page.getByRole("link", { name: "查看结果" }).click();
  await page.waitForURL(/#\/result\//, { timeout: 30000 });
  await expect(page.getByRole("heading", { name: "证据链" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "规约摘要" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "工件列表" })).toBeVisible();
  await expect(page.locator(".status-chip")).toHaveText(/通过/);
});

test("启动页只展示三个主模块", async ({ page }) => {
  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  const modeGrid = page.locator(".mode-grid");
  await expect(modeGrid.getByRole("button", { name: /单函数分析/ })).toBeVisible();
  await expect(modeGrid.getByRole("button", { name: /终止性验证/ })).toBeVisible();
  await expect(modeGrid.getByRole("button", { name: /多模块分析/ })).toBeVisible();
  await expect(modeGrid.getByRole("button", { name: /batch/i })).toHaveCount(0);

  await modeGrid.getByRole("button", { name: /多模块分析/ }).click();
  await expect(page.getByText("工程上传")).toBeVisible();
  const sections = await page.locator(".launcher-config-grid").evaluate((grid) => {
    const input = grid.querySelector(".launcher-input-section").getBoundingClientRect();
    const model = grid.querySelector(".launcher-model-section").getBoundingClientRect();
    return { inputBottom: input.bottom, modelTop: model.top, widthDelta: Math.abs(input.width - model.width) };
  });
  expect(sections.modelTop).toBeGreaterThanOrEqual(sections.inputBottom);
  expect(sections.widthDelta).toBeLessThanOrEqual(2);
});

test("多模块示例页展示 X.509 解析器验证图谱", async ({ page }) => {
  await page.goto("/#/upload?mode=inter-modular&demo=x509_inter_modular_replay", { waitUntil: "domcontentloaded" });
  await expect(page.getByText("X.509 解析器验证图谱")).toBeVisible();
  const frame = page.frameLocator(".x509-showcase-frame");
  await expect(frame.locator(".info-bar")).toContainText("212 functions");
  const node = frame.locator("circle").first();
  await expect(node).toBeVisible();
  await node.click();
  await page.waitForURL(/#\/x509-function\//);
  await expect(page.locator(".x509-function-page")).toBeVisible();
  await expect(page.locator(".x509-function-pane")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "原始函数源码" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "带 ACSL 规约的函数" })).toBeVisible();
  await expect(page.locator(".x509-function-pane").first()).toContainText("原始函数源码");
  await expect(page.locator(".x509-function-pane").last()).toContainText("带 ACSL 规约的函数");
});

test("结果页在调试视图中支持工件预览", async ({ page }) => {
  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  await page.locator(".source-tab").getByText("示例用例").click();
  await page.getByRole("button", { name: "提交运行" }).click();
  await page.waitForURL(/#\/run\//, { timeout: 30000 });
  await page.getByRole("link", { name: "查看结果" }).click();
  await page.waitForURL(/#\/result\//, { timeout: 30000 });
  await page.getByRole("button", { name: "展开调试视图" }).click();
  const preview = page.locator(".artifact-grid .code-block");
  const before = await preview.textContent();
  await page.getByRole("button", { name: "预览" }).last().click();
  await expect(preview).not.toHaveText(before || "");
});

test("结果页不会引入横向溢出", async ({ page }) => {
  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  await page.locator(".source-tab").getByText("示例用例").click();
  await page.getByRole("button", { name: "提交运行" }).click();
  await page.waitForURL(/#\/run\//, { timeout: 30000 });
  await page.getByRole("link", { name: "查看结果" }).click();
  await page.waitForURL(/#\/result\//, { timeout: 30000 });
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
    };
  });
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 2);
});

test("宽屏结果页能利用可用视口宽度", async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  await page.locator(".source-tab").getByText("示例用例").click();
  await page.getByRole("button", { name: "提交运行" }).click();
  await page.waitForURL(/#\/run\//, { timeout: 30000 });
  await page.getByRole("link", { name: "查看结果" }).click();
  await page.waitForURL(/#\/result\//, { timeout: 30000 });
  const metrics = await page.locator(".page-shell").evaluate((node) => {
    const rect = node.getBoundingClientRect();
    return { width: rect.width, left: rect.left, rightGap: window.innerWidth - rect.right };
  });
  expect(metrics.width).toBeGreaterThan(1500);
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
