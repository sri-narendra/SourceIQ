import { defineConfig, devices } from "@playwright/test";

const isWin = process.platform === "win32";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  workers: 1,
  reporter: "list",
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:3100",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: isWin
        ? "backend\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --app-dir backend --host 127.0.0.1 --port 8000"
        : "python -m uvicorn backend.main:app --app-dir backend --host 127.0.0.1 --port 8000",
      cwd: "..",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npx next dev --port 3100",
      cwd: ".",
      url: "http://localhost:3100/login",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});