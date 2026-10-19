// The settings screen: EXIF toggles, default font, theme, auto-save and the
// live preview - and what they mean for the public link.
//
// Run: cd visual && npx playwright test tests/settings.spec.js
const { test, expect } = require('@playwright/test');
const path = require('path');

const SHOTS = path.join(__dirname, '..', '..', 'visual-shots');
const BASEURL = process.env.VIS_BASE || 'http://127.0.0.1:8019';

test('settings drive what the public link shows', async ({ page, context }) => {
  test.setTimeout(120000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto('/');
  const user = 'set' + Date.now().toString(36);
  await page.fill('#u', user);
  await page.fill('#p', 'visualpass1');
  await page.click('text=Sign up');
  await expect(page.locator('#s-albums.on')).toBeVisible();

  // an album with one photo, so the preview has something real to show
  await page.click('text=+ New album');
  await page.fill('#aname', 'Settings album');
  await page.press('#aname', 'Enter');
  await page.setInputFiles('#files', path.join(__dirname, 'fixtures', 'probe.png'));
  await page.click('button:has-text("Upload")');
  await expect(page.locator('#thumbs img')).toHaveCount(1, { timeout: 30000 });
  const link = (await page.locator('#alink').textContent()).trim();
  const pubPath = new URL(link).pathname;

  // --- the settings screen itself
  await page.click('#s-album button:has-text("Settings")');
  await expect(page.locator('#s-settings.on')).toBeVisible();
  await expect(page.locator('#exbox input')).toHaveCount(4);
  await expect(page.locator('#stheme')).toBeVisible();
  await expect(page.locator('#sfont')).toBeVisible();
  // no Save button: changes save themselves
  await expect(page.locator('#s-settings button:has-text("Save")')).toHaveCount(0);
  await page.waitForTimeout(400);
  // the preview shows the real photo's details
  await expect(page.locator('#setprev .pill').first()).toContainText('Uploaded:');
  await page.screenshot({ path: `${SHOTS}/10-settings.png` });

  // --- switching a detail off saves itself and updates the preview
  const cam = page.locator('#exbox input[data-k="show_camera"]');
  const wasOn = await cam.isChecked();
  await cam.setChecked(!wasOn);
  await expect(page.locator('#savedNote')).toHaveText('Saved', { timeout: 5000 });
  await page.waitForTimeout(400);
  const camPill = page.locator('#setprev .pill', { hasText: 'Camera:' });
  await expect(camPill).toHaveCount(wasOn ? 0 : 1);
  await cam.setChecked(wasOn);
  await page.waitForTimeout(300);

  // --- the default font applies to new albums
  await page.selectOption('#sfont', 'serif');
  await page.waitForTimeout(500);
  // Back returns to the album we opened settings from
  await page.click('#s-settings button:has-text("Back")');
  await expect(page.locator('#s-album.on')).toBeVisible();
  await page.click('#s-album button:has-text("Albums")');
  await expect(page.locator('#s-albums.on')).toBeVisible();
  await page.click('text=+ New album');
  await page.fill('#aname', 'Font album');
  await page.press('#aname', 'Enter');
  await expect(page.locator('#afont')).toHaveValue('serif');
  await page.click('#s-album button:has-text("Albums")');
  await expect(page.locator('#s-albums.on')).toBeVisible();

  // --- the theme reaches the public link, server-rendered
  await page.click('#s-albums button:has-text("Settings")');
  await page.selectOption('#stheme', 'dark');
  await page.waitForTimeout(500);
  const anon = await context.browser().newContext();
  const pub = await anon.newPage();
  const res = await pub.goto(BASEURL + pubPath);
  expect(res.status()).toBe(200);
  // the theme is on <html> in the served HTML, not applied later by script
  expect(await pub.evaluate(() => document.documentElement.dataset.theme)).toBe('dark');
  await anon.close();

  // an anonymous visitor's own remembered choice wins over the owner's
  const anon2 = await context.browser().newContext();
  await anon2.addInitScript(() => localStorage.setItem('theme', 'light'));
  const pub2 = await anon2.newPage();
  await pub2.goto(BASEURL + pubPath);
  expect(await pub2.evaluate(() => document.documentElement.dataset.theme)).toBe('light');
  await anon2.close();

  // --- and the exif filter applies to the public link too
  await page.click('#s-settings button:has-text("Back")');
  await page.click('#s-albums button:has-text("Settings")');
  await page.locator('#exbox input[data-k="show_camera"]').setChecked(false);
  await page.waitForTimeout(600);
  const anon3 = await context.browser().newContext();
  const pub3 = await anon3.newPage();
  await pub3.goto(BASEURL + pubPath);
  await pub3.locator('#s-public.on').waitFor();
  await pub3.waitForTimeout(600);
  await expect(pub3.locator('#pex .pill', { hasText: 'Camera:' })).toHaveCount(0);
  await expect(pub3.locator('#pex .pill', { hasText: 'Uploaded:' })).toHaveCount(1);
  await anon3.close();

  expect(errors, 'page errors').toEqual([]);
});
