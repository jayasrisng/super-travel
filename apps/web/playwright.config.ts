import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  timeout: 60000,
  use: {
    baseURL: `http://127.0.0.1:${process.env.WONDER_WEB_PORT || 5173}`,
    viewport: { width: 1280, height: 900 },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run python ../../scripts/run_consumer.py",
      url: `http://127.0.0.1:${process.env.WONDER_API_PORT || 8000}/openapi.json`,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      env: {
        WONDER_AGENT_MODE: "fixture",
        WONDER_DB_PATH: "../../wonder-e2e.sqlite3",
      },
    },
    {
      command: "pnpm dev",
      url: `http://127.0.0.1:${process.env.WONDER_WEB_PORT || 5173}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
  ],
  workers: 1,
  reporter: "list",
});
