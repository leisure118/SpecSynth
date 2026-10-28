const { defineConfig, devices } = require("@playwright/test");

const browserChannel = process.env.PLAYWRIGHT_CHANNEL || undefined;
const browserProfile = browserChannel === "msedge" ? devices["Desktop Edge"] : devices["Desktop Chrome"];
const pythonCommand = process.env.ACSL_AGENT_PYTHON || "python";

module.exports = defineConfig({
  testDir: "./tests/browser",
  timeout: 120000,
  expect: {
    timeout: 15000,
  },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "runtime/playwright-report" }]],
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
    ...(browserChannel ? { channel: browserChannel } : {}),
    ...browserProfile,
  },
  webServer: {
    command: `${pythonCommand} scripts/run_api.py`,
    url: "http://127.0.0.1:8000/api/v1/health",
    reuseExistingServer: true,
    timeout: 120000,
  },
});
