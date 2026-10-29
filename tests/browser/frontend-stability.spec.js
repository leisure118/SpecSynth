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

async function openProject(page, mode, sample) {
  await page.goto('/#/projects?new=1');
  await page.getByLabel('项目名称',{exact:true}).fill('回归 · '+sample.name);
  await page.locator('.vf-new-form input[type=file]').first().setInputFiles(mode==='inter-modular'?listBundleFiles(sample.dir):absolute(sample.file));
  await page.getByRole('button',{name:'创建项目 →',exact:true}).click();
  await expect(page.getByLabel('源代码编辑器')).toBeVisible();
  await page.getByLabel('验证模式').selectOption(mode);
}

async function submitRunAndOpenResult(page, mode, sampleName, debugPreview) {
  const pageErrors = [];
  page.once("pageerror", (error) => pageErrors.push(String(error)));

  const created=page.waitForResponse(r=>/\/projects\/[^/]+\/runs$/.test(new URL(r.url()).pathname)&&r.request().method()==='POST'&&r.status()===201);
  await page.getByRole('button',{name:mode==='inter-modular'?'▷ 验证整个项目':'▷ 验证当前文件',exact:true}).click();
  const taskId=(await (await created).json()).task_id;
  await expect(page.locator('.vf-proof-summary')).toBeVisible({timeout:RUN_TIMEOUT_MS[mode]});
  await page.getByRole('link',{name:'完整结果与证据 ↗'}).click();
  await page.waitForURL(/#\/result\//);
  const resultStatus = await page.evaluate(async id=>(await (await fetch('/api/v1/runs/'+id+'/result')).json()).status,taskId);
  if(debugPreview){
    await page.getByRole('button',{name:'展开调试视图'}).click();
    await page.getByRole('button',{name:'预览',exact:true}).first().click();
  }
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
    test.skip(!process.env.ACSL_RUN_LIVE_TESTS, '真实验证需显式启用，可能调用已配置模型');
    test.setTimeout(RUN_TIMEOUT_MS[mode] * samples.length + 120000);
    for (let index = 0; index < samples.length; index += 1) {
      const sample = samples[index];
      await openProject(page, mode, sample);
      await submitRunAndOpenResult(page, mode, sample.name, index === 0);
    }
  });
}
