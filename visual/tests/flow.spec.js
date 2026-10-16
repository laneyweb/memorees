// Owner flow (desktop 1440) -> public link (anon) -> tablet (820, touch).
// Shares state via module vars; file runs serially in one worker.
const { test, expect } = require('@playwright/test');
const path = require('path');

const SHOTS = path.join(__dirname, '..', '..', 'visual-shots');
let PUBLIC_PATH = null;
// Tests in one file share a worker and run in order.

test('owner flow on desktop', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  const dialogs = [];
  page.on('dialog', async (d) => { dialogs.push(d.message()); await d.accept(); });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await expect(page.locator('#s-auth.on')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-auth.png` });

  await page.fill('#u', 'v' + Date.now().toString(36));
  await page.fill('#p', 'visualpass1');
  await page.click('text=Sign up');
  await expect(page.locator('#s-albums.on')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-albums-empty.png` });

  // New-album modal (form, never a system dialog)
  await page.click('text=+ New album');
  await expect(page.locator('#albumModal.on')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/03-album-modal.png` });
  await page.fill('#aname', 'Visual album');
  await page.press('#aname', 'Enter');
  await expect(page.locator('#atitle')).toContainText('Visual album');
  await expect(page.locator('#playB')).toHaveText('▶');

  // Empty state: friendly placeholder, no broken image, no controls
  await expect(page.locator('#noview')).toBeVisible();
  await expect(page.locator('#slide')).toBeHidden();
  await page.screenshot({ path: `${SHOTS}/04-album-empty.png` });

  // Upload + multiline comment round-trip
  await page.setInputFiles('#files', path.join(__dirname, 'fixtures', 'probe.png'));
  await page.click('text=⬆ Upload');
  await expect(page.locator('#noview')).toBeHidden({ timeout: 15000 });
  await page.fill('#cedit', 'line one\nline two');
  await page.click('text=💾 Save comment');
  await expect(page.locator('#cap')).toContainText('line two');
  // Draft must survive autoplay refreshes (regression: interval wiped typing)
  await page.fill('#cedit', 'draft in progress');
  await page.waitForTimeout(6500);
  await expect(page.locator('#cedit')).toHaveValue('draft in progress');

  // Settings + font/transition persist
  await page.selectOption('#afont', 'serif');
  await expect(page.locator('#capbox.font-serif')).toBeVisible();
  await page.click('#s-album button:has-text("Medium")');
  await expect.poll(() => page.evaluate(() => localStorage.vsize)).toBe('large');
  await page.screenshot({ path: `${SHOTS}/05-album-full.png` });

  // About Back returns (dead-button regression)
  await page.click('header button:has-text("About")');
  await expect(page.locator('#s-about.on')).toBeVisible();
  await page.click('#s-about button:has-text("Back")');
  await expect(page.locator('#s-album.on')).toBeVisible();

  // Dark theme
  await page.click('#themeBtn');
  await expect(page.locator('html[data-theme="dark"]')).toBeAttached();
  await page.screenshot({ path: `${SHOTS}/06-album-dark.png` });
  await page.click('#themeBtn');

  // Tooltip hover (human eyeballs the shot)
  await page.hover('#themeBtn');
  await page.screenshot({ path: `${SHOTS}/07-tooltip.png` });

  const link = (await page.locator('#alink').textContent()).trim();
  PUBLIC_PATH = new URL(link).pathname;
  expect(PUBLIC_PATH).toMatch(/^\/p\/[0-9a-f]+$/);
  expect(errors).toEqual([]);
});

test('public link with no login', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(PUBLIC_PATH);
  await expect(page.locator('#s-public.on')).toBeVisible();
  await expect(page.locator('#ptitle')).toContainText('Visual album');
  await expect(page.locator('#pcap')).toContainText('line two');
  const before = await page.locator('#pslide').getAttribute('src');
  await page.click('#s-public button:has-text("Large")');
  await expect(page.locator('#pviewer.full')).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.psize)).toBe('full');
  await page.click('#pviewer .vctrl button:has-text("▶")').catch(() => {});
  await page.locator('#pviewer').hover();
  await page.screenshot({ path: `${SHOTS}/08-public.png` });
  expect(before).toContain('/previews/');
  expect(errors).toEqual([]);
  await ctx.close();
});

test('tablet touch flow', async ({ browser }) => {
  const ctx = await browser.newContext({
    viewport: { width: 820, height: 1180 },
    hasTouch: true,
    isMobile: true,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(PUBLIC_PATH);
  await expect(page.locator('#s-public.on')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/09-tablet-public.png` });
  // Swipe left via touch events -> slide advances
  const before = await page.locator('#pslide').getAttribute('src');
  const cdp = await ctx.newCDPSession(page);
  const swipe = async (x0, x1) => {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x0, y: 500 }] });
    for (let x = x0; x !== x1; x += (x1 > x0 ? 20 : -20))
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: 500 }] });
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  };
  await swipe(600, 300);
  await page.waitForTimeout(800);
  const after = await page.locator('#pslide').getAttribute('src');
  // Single-photo album: src unchanged but handler must not throw
  expect(typeof after).toBe('string');
  await page.screenshot({ path: `${SHOTS}/10-tablet-after-swipe.png` });
  expect(errors).toEqual([]);
  await ctx.close();
});
