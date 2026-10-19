// README screenshots — seeds a demo backend with stock photos + captions and
// captures docs/shots/*.png in the dark theme.
//
// Usage:
//   python scripts/stock_photos.py                    # once, fills .scratch/stock
//   $env:DATA_DIR=".scratch/shot-data"; $env:ALLOW_SIGNUP="true"
//   $env:BASE_URL="https://memories.example.com"     # so shot links look real
//   python -m uvicorn backend.app:app --port 8019     # empty DATA_DIR
//   node visual/readme-shots.mjs
import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.env.VIS_BASE || 'http://127.0.0.1:8019';
const dir = path.dirname(fileURLToPath(import.meta.url));
const SHOTS = path.join(dir, '..', 'docs', 'shots');
const STOCK = path.join(dir, '..', '.scratch', 'stock');
fs.mkdirSync(SHOTS, { recursive: true });

const USER = 'sam';
const PASS = 'readme-demo-pass';

// Demo content: real stock photos, captions written to match what is in frame.
// Albums are created newest-last — /api/albums sorts by id DESC, so the hero
// album ends up first in the grid.
const HERO = 'Alpine Summer 2025';

const ALBUMS = [
  {
    title: 'Rainy Sundays',
    font: 'sans',
    transition: 'none',
    photos: [
      ['birthday-2024', 'Two coffees, three postcards.\nRain all day — perfect.'],
    ],
  },
  {
    title: "Bessie's First Summer",
    font: 'hand',
    transition: 'zoom',
    photos: [
      ['bessie-summer', 'She slept under the table for a month.\nNow she owns the house.'],
    ],
  },
  {
    title: 'Road Trip 2023',
    font: 'sans',
    transition: 'slide',
    photos: [
      ['road-trip-2023', "Dad's old Falcon.\nHe let me hold the wheel twice."],
    ],
  },
  {
    title: HERO,
    hero: true,
    font: 'serif',
    transition: 'fade',
    photos: [
      ['bay-morning', 'Ferry dock at seven.\nNobody awake but the gulls.'],
      ['harbour-cliffs', 'Detour off the main road.\nWorth the dust on the seats.'],
      ['summit-lake', 'The falls were louder than us.\nWe stayed ten minutes anyway.'],
      ['old-town-evening', 'Fog rolled down the valley at six.\nWe walked it out.'],
      ['night-market', 'Late market haul.\nNobody wanted to be the one carrying the bag.'],
      ['last-morning', 'Last morning before the drive home.\nNate left his sandals in the car.'],
    ],
  },
];

const api = async (p, o = {}) => {
  const r = await fetch(BASE + p, o);
  if (!r.ok) throw new Error(`${p}: ${r.status} ${await r.text()}`);
  return r.json();
};

const form = (path, u, pw) =>
  fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: u, password: pw }),
  }).then(async (r) => ({
    r,
    cookie: (r.headers.get('set-cookie') || '').match(/session=([^;]+)/)?.[1],
  }));

async function seed() {
  let { cookie } = await form('/api/register', USER, PASS).catch(() => ({ cookie: null }));
  if (!cookie) ({ cookie } = await form('/api/login', USER, PASS));

  const json = { Cookie: `session=${cookie}`, 'Content-Type': 'application/json' };
  // start from a clean slate so re-runs are idempotent
  for (const a of await api('/api/albums', { headers: json }))
    await fetch(`${BASE}/api/albums/${a.id}`, { method: 'DELETE', headers: { Cookie: `session=${cookie}` } });

  let mainLink = null;
  for (const a of ALBUMS) {
    const alb = await api('/api/albums', { method: 'POST', headers: json, body: JSON.stringify({ title: a.title }) });
    await api(`/api/albums/${alb.id}`, {
      method: 'PUT',
      headers: json,
      body: JSON.stringify({ font: a.font, transition: a.transition }),
    });
    for (const [slug, comment] of a.photos) {
      const file = path.join(STOCK, `${slug}.jpg`);
      if (!fs.existsSync(file)) throw new Error(`missing stock photo ${file} — run scripts/stock_photos.py`);
      const fd = new FormData();
      fd.append('files', new Blob([fs.readFileSync(file)], { type: 'image/jpeg' }), `${slug}.jpg`);
      const up = await fetch(`${BASE}/api/albums/${alb.id}/photos`, {
        method: 'POST',
        headers: { Cookie: `session=${cookie}` },
        body: fd,
      });
      if (!up.ok) throw new Error(`upload ${slug}: ${up.status} ${await up.text()}`);
      const { photos } = await api(`/api/albums/${alb.id}/photos`, { headers: json });
      const created = photos.find((p) => !p.comment);
      await api(`/api/photos/${created.id}`, {
        method: 'PUT',
        headers: json,
        body: JSON.stringify({ comment }),
      });
    }
    const full = await api(`/api/albums/${alb.id}/photos`, { headers: json });
    if (a.hero) mainLink = new URL(full.album.link).pathname;
  }
  if (!mainLink) throw new Error(`no album flagged hero:true (expected "${HERO}")`);
  // the examples are dark: for a signed-in user the theme is a server
  // setting, so set it here rather than in localStorage
  await api('/api/settings', { method: 'PUT', headers: json, body: JSON.stringify({ theme: 'dark' }) });
  console.log(`seeded ${ALBUMS.length} albums, ${ALBUMS.reduce((n, a) => n + a.photos.length, 0)} photos`);
  return mainLink;
}

async function main() {
  const pub = await seed();

  const b = await chromium.launch();
  // dark theme for every shot; `extra` seeds other persisted viewer prefs
  const prep = (ctx, extra = {}) =>
    ctx.addInitScript((e) => {
      localStorage.setItem('theme', 'dark');
      for (const [k, v] of Object.entries(e)) localStorage.setItem(k, v);
    }, extra);
  // viewer bars hide after 3s idle — hover to wake them for the screenshot
  const wake = async (p) => {
    await p.mouse.move(200, 300);
    await p.mouse.move(640, 400);
    await p.waitForTimeout(400);
  };
  const desktop = { viewport: { width: 1280, height: 800 } };

  // --- owner: albums grid, album screen, fullscreen viewer, settings, about
  const own = await b.newContext(desktop);
  await prep(own);
  const pg = await own.newPage();
  await pg.goto(BASE + '/');
  await pg.fill('#u', USER);
  await pg.fill('#p', PASS);
  await pg.click('text=Login');
  await pg.locator('#s-albums.on').waitFor();
  await pg.waitForTimeout(900);
  await pg.screenshot({ path: `${SHOTS}/albums.png` });

  await pg.click('.card.polaroid');
  await pg.locator('#s-album.on').waitFor();
  await pg.waitForTimeout(1400);
  await pg.screenshot({ path: `${SHOTS}/album.png` });

  // fullscreen viewer with the caption overlay. pseudo-full rather than the
  // real Fullscreen API: deterministic, and it forces .fscap to show.
  await pg.click('#thumbs .card >> nth=0');
  await pg.evaluate(() => document.getElementById('viewer').classList.add('pseudo-full'));
  await pg.waitForTimeout(1500);
  await pg.screenshot({ path: `${SHOTS}/viewer.png` });
  await pg.evaluate(() => document.getElementById('viewer').classList.remove('pseudo-full'));

  // loadSettings() populates the EXIF toggles; show('settings') alone would
  // render an empty box
  await pg.evaluate(() => loadSettings());
  await pg.locator('#s-settings.on').waitFor();
  await pg.waitForTimeout(600);
  await pg.screenshot({ path: `${SHOTS}/settings.png` });

  await pg.evaluate(() => show('about'));
  await pg.locator('#s-about.on').waitFor();
  await pg.waitForFunction(() => !document.getElementById('ver').textContent.includes('…'));
  await pg.waitForTimeout(600);
  await pg.screenshot({ path: `${SHOTS}/about.png` });

  // --- anonymous public link, desktop and tablet
  const anon = await b.newContext(desktop);
  await prep(anon);
  const ap = await anon.newPage();
  await ap.goto(BASE + pub);
  await ap.locator('#s-public.on').waitFor();
  await ap.waitForTimeout(2200);
  await wake(ap);
  await ap.screenshot({ path: `${SHOTS}/public.png` });

  // large view size so the photo fills the tall tablet frame
  const tab = await b.newContext({ viewport: { width: 820, height: 1180 }, hasTouch: true, isMobile: true });
  await prep(tab, { psize: 'large' });
  const tp = await tab.newPage();
  await tp.goto(BASE + pub);
  await tp.locator('#s-public.on').waitFor();
  await tp.waitForTimeout(2200);
  await wake(tp);
  await tp.screenshot({ path: `${SHOTS}/tablet-public.png` });

  await b.close();
  console.log('shots done:', fs.readdirSync(SHOTS).sort().join(', '));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
