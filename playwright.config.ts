import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  timeout: 120000,
  use: { headless: true, viewport: { width: 1366, height: 800 } },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
