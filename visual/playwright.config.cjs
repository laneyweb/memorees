// Visual suite: boots a throwaway backend + DATA_DIR, drives real Chromium.
// Run: cd visual && npm install && npx playwright test
// Shots land in ../visual-shots (gitignored) for human review.
const { defineConfig } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 60000,
  reporter: [['list']],
  use: {
    baseURL: process.env.VIS_BASE || 'http://127.0.0.1:8019',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'python -m uvicorn backend.app:app --port 8019',
    url: 'http://127.0.0.1:8019/api/version',
    cwd: path.join(__dirname, '..'),
    env: {
      ...process.env,
      DATA_DIR: path.join(__dirname, '..', '.scratch', 'visual-data'),
      ALLOW_SIGNUP: 'true',
      BASE_URL: 'http://127.0.0.1:8019',
    },
    reuseExistingServer: false,
    timeout: 90000,
  },
});
