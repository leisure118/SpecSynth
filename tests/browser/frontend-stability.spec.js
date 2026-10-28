const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const REPORT_DIR = path.join(REPO_ROOT, "runtime", "reports");
const REPORT_PATH = path.join(
  REPORT_DIR,
  `frontend-stability-${new Date().toISOString().replace(/[:.]/g, "-")}.json`
);

const SAMPLE_SETS = {
  single: [
    { name: "case4test-1", file: "resources/datasets/autospec/case4test/1.c" },
    { name: "fib-161", file: "resources/datasets/autospec/AutoBench/46_fib/161.c" },
    { name: "fib-177", file: "resources/datasets/autospec/AutoBench/46_fib/177.c" },
    { name: "arraymax-181", file: "resources/datasets/autospec/AutoBench/frama-c-problem/181.c" },
    { name: "bubble-sort-222", file: "resources/datasets/autospec/AutoBench/frama-c-problem/222.c" },
  ],
  termination: [
    { name: "stage1-1", file: "resources/demo_cases/termination/stage1_verified_files/1_verified.c" },
    { name: "stage1-2", file: "resources/demo_cases/termination/stage1_verified_files/2_verified.c" },
    { name: "stage1-3", file: "resources/demo_cases/termination/stage1_verified_files/3_verified.c" },
    { name: "stage1-222", file: "resources/demo_cases/termination/stage1_verified_files/222_verified.c" },
    { name: "stage2-1", file: "resources/demo_cases/termination/stage2_result_files/1.c" },
  ],
  "inter-modular": [
    { name: "x509-resource", dir: "resources/datasets/autospec/inter-modular" },
    { name: "test-folder", dir: "resources/datasets/autospec/test_folder" },
    { name: "legacy-web-014831", dir: "archive/legacy_outputs/out/web_demo_runs/20260321_014831/single_input" },
    { name: "legacy-web-020146", dir: "archive/legacy_outputs/out/web_demo_runs/20260321_020146/input" },
    { name: "legacy-web-020239", dir: "archive/legacy_outputs/out/web_demo_runs/20260321_020239/input" },
  ],
};

const MODE_LABELS = {
  single: "单函数分析",
  termination: "终止性验证",
  "inter-modular": "多模块分析",
};

const RUN_TIMEOUT_MS = {
  single: 240000,
  termination: 300000,
  "inter-modular": 600000,
};

const runRecords = [];

const RESULT_STATUS_TEXT = {
  Pass: "通过",
  Fail: "失败",
  Invalid: "无效",
  Timeout: "超时",
  Unavailable: "不可用",
};

function absolute(relPath) {
  return path.join(REPO_ROOT, relPath);
}

function listBundleFiles(relDir) {
  const dir = absolute(relDir);
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && [".c", ".h"].includes(path.extname(entry.name)))
    .map((entry) => path.join(dir, entry.name))
    .sort();
}

async function openLauncher(page) {
  await page.goto("/#/upload", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "统一任务启动台" })).toBeVisible();
}

async function selectMode(page, mode) {
  await page.locator(".mode-grid").getByRole("button", { name: new RegExp(MODE_LABELS[mode]) }).click();
  await expect(page.locator(".mode-btn.active")).toContainText(MODE_LABELS[mode]);
}

async function uploadSingleFile(page, relPath) {
  const input = page.locator(".upload-zone input[type='file']").first();
  await input.setInputFiles(absolute(relPath));
  await expect(page.locator(".el-tag").filter({ hasText: "已上传" }).first()).toBeVisible();
}

async function uploadBundle(page, relDir) {
  const input = page.locator("input.bundle-file-input").first();
  await input.setInputFiles(listBundleFiles(relDir));
  await expect(page.locator(".el-tag").filter({ hasText: "已上传" }).first()).toBeVisible();
}

async function submitRunAndOpenResult(page, mode, sampleName, debugPreview) {
  const pageErrors = [];
  page.once("pageerror", (error) => pageErrors.push(String(error)));

  await page.getByRole("button", { name: "提交运行" }).click();
  await page.waitForURL(/#\/run\//, { timeout: 30000 });

  const runUrl = page.url();
  const taskId = runUrl.split("/run/")[1];
  await expect(page.getByRole("heading", { name: "运行状态" })).toBeVisible();
  await expect(page.locator(".run-meta-grid")).toContainText(MODE_LABELS[mode]);

  await expect(page.getByRole("link", { name: "查看结果" })).toBeVisible({ timeout: RUN_TIMEOUT_MS[mode] });
  await Promise.all([
    page.waitForResponse((response) => response.url().includes(`/api/v1/runs/${taskId}/result`) && response.ok(), {
      timeout: 30000,
    }),
    page.waitForURL(/#\/result\//, { timeout: 30000 }),
    page.getByRole("link", { name: "查看结果" }).click(),
  ]);
  await expect(page.getByRole("heading", { name: "证据链" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "聚合指标" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "工件列表" })).toBeVisible();
  await expect(page.locator(".result-header-actions .status-chip")).toBeVisible();

  if (debugPreview) {
    await page.getByRole("button", { name: "展开调试视图" }).click();
    const preview = page.locator(".artifact-grid .code-block");
    const before = await preview.textContent();
    await page.getByRole("button", { name: "预览" }).first().click();
    await expect(preview).not.toHaveText(before || "");
  }

  const resultStatus = await page.evaluate(async (id) => {
    const response = await fetch(`/api/v1/runs/${id}/result`);
    const payload = await response.json();
    return payload.status;
  }, taskId);
  const artifactCount = await page.locator(".module-results .module-card").count();
  expect(artifactCount).toBeGreaterThan(0);
  expect(pageErrors).toEqual([]);

  runRecords.push({
    module: mode,
    sample: sampleName,
    task_id: taskId,
    result_url: page.url(),
    status_text: RESULT_STATUS_TEXT[resultStatus] || resultStatus,
    artifact_count: artifactCount,
  });
}

test.afterAll(async () => {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(
    REPORT_PATH,
    JSON.stringify(
      {
        generated_at: new Date().toISOString(),
        totals: {
          single: runRecords.filter((item) => item.module === "single").length,
          termination: runRecords.filter((item) => item.module === "termination").length,
          "inter-modular": runRecords.filter((item) => item.module === "inter-modular").length,
        },
        runs: runRecords,
      },
      null,
      2
    ),
    "utf-8"
  );
  console.log(`frontend stability report: ${REPORT_PATH}`);
});

for (const [mode, samples] of Object.entries(SAMPLE_SETS)) {
  test(`${MODE_LABELS[mode]} 前端上传链路覆盖五个样例`, async ({ page }) => {
    test.setTimeout(RUN_TIMEOUT_MS[mode] * samples.length + 120000);
    for (let index = 0; index < samples.length; index += 1) {
      const sample = samples[index];
      await openLauncher(page);
      await selectMode(page, mode);
      if (mode === "inter-modular") {
        await uploadBundle(page, sample.dir);
      } else {
        await uploadSingleFile(page, sample.file);
      }
      await submitRunAndOpenResult(page, mode, sample.name, index === 0);
    }
  });
}
