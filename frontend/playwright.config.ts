import { defineConfig, devices } from '@playwright/test';

/**
 * Configuration Playwright pour GuinéeCare Hospital Suite
 *
 * Démarre automatiquement le frontend Vite si nécessaire.
 * Le backend FastAPI (port 8000) doit être démarré séparément avant les tests.
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:5173',
    // Reuse an existing Vite server if one is already running (local dev + CI script).
    // In pure GitHub Actions, no server is pre-started, so Playwright starts one itself.
    reuseExistingServer: true,
    timeout: 60_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
