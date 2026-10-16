// README screenshots — seeds a demo backend and captures docs/shots/*.png
// Run: (backend on :8019 with empty DATA_DIR) then: node visual/readme-shots.mjs
import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.env.VIS_BASE || 'http://127.0.0.1:8019';
const dir = path.dirname(fileURLToPath(import.meta.url));
const SHOTS = path.join(dir, '..', 'docs', 'shots');
const SRC = path.join(dir, '..', '.scratch', 'shot-src');
fs.mkdirSync(SHOTS, { recursive: true });

const api = async (p, o = {}) => {
  const r = await fetch(BASE + p, o);
  if (!r.ok) throw new Error(`${p}: ${r.status} ${await r.text()}`);
  return r.json();
};
const form = (u, pw, what) => fetch(BASE + what, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({ username: u, password: pw }),
}).then(async (r) => ({ r, cookie: (r.headers.get('set-cookie') || '').match(/session=([^;]+)/)?.[1] }));

async function main() {
  const U = 'readme', P = 'readme-demo-pass';
  let { cookie } = await form(U, P, '/api/register').catch(() => ({ cookie: null }));
  if (!cookie) ({ cookie } = await form(U, P, '/api/login'));
  const H = { Cookie: `session=${cookie}`, 'Content-Type': 'application/json' };
  for (const a of await api('/api/albums', { headers: H }))
    await fetch(BASE + `/api/albums/${a.id}`, { method: 'DELETE', headers: { Cookie: `session=${cookie}` } });
  const alb = await api('/api/albums', { method: 'POST', headers: H, body: JSON.stringify({ title: 'Summer holiday' }) });
  const captions = ['First morning light over the bay.\nCoffee tasted better here.', 'The climb was worth every step.\nWe stayed for sunset.', 'Night market colours.\nWe bought too much fruit.'];
  for (let i = 0; i < 3; i++) {
    const buf = fs.readFileSync(path.join(SRC, `shot${i + 1}.png`));
    const fd = new FormData();
    fd.append('files', new Blob([buf], { type: 'image/png' }), `shot${i + 1}.png`);
    await fetch(BASE + `/api/albums/${alb.id}/photos`, { method: 'POST', headers: { Cookie: `session=${cookie}` }, body: fd });
  }
  let photos = (await api(`/api/albums/${alb.id}/photos`, { headers: H })).photos;
  for (let i = 0; i < photos.length; i++)
    await api(`/api/photos/${photos[i].id}`, { method: 'PUT', headers: H, body: JSON.stringify({ comment: captions[i] }) });
  await api(`/api/albums/${alb.id}`, { method: 'PUT', headers: H, body: JSON.stringify({ font: 'serif' }) });
  const link = (await api(`/api/albums/${alb.id}/photos`, { headers: H })).album.link;
  const pub = new URL(link).pathname;

  const b = await chromium.launch();
  const pg = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await pg.goto(BASE + '/');
  await pg.fill('#u', U); await pg.fill('#p', P); await pg.click('text=Login');
  await pg.locator('#s-albums.on').waitFor();
  await pg.screenshot({ path: `${SHOTS}/albums.png` });
  await pg.click('.card.polaroid');
  await pg.locator('#s-album.on').waitFor();
  await pg.waitForTimeout(800);
  await pg.screenshot({ path: `${SHOTS}/album.png` });
  await pg.evaluate(() => loadSettings());
  await pg.locator('#s-settings.on').waitFor();
  await pg.waitForTimeout(500);
  await pg.screenshot({ path: `${SHOTS}/settings.png` });
  await pg.evaluate(() => show('about'));
  await pg.locator('#s-about.on').waitFor();
  await pg.waitForFunction(() => !document.getElementById('ver').textContent.includes('…'));
  await pg.waitForTimeout(600);
  await pg.screenshot({ path: `${SHOTS}/about.png` });
  const anon = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await anon.goto(BASE + pub);
  await anon.locator('#s-public.on').waitFor();
  await anon.waitForTimeout(800);
  await anon.screenshot({ path: `${SHOTS}/public.png` });
  const tab = await (await b.newContext({ viewport: { width: 820, height: 1180 }, hasTouch: true, isMobile: true })).newPage();
  await tab.goto(BASE + pub);
  await tab.locator('#s-public.on').waitFor();
  await tab.waitForTimeout(800);
  await tab.screenshot({ path: `${SHOTS}/tablet-public.png` });
  await b.close();
  console.log('shots done:', fs.readdirSync(SHOTS));
}
main().catch((e) => { console.error(e); process.exit(1); });
