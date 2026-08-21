import { defineConfig, devices } from "@playwright/test";

// For specs that need the real backend. Run `scripts/start.sh` (or
// `scripts/start.ps1`) first — this config does not start a server itself.
export default defineConfig({
  testDir: "./tests/docker",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
