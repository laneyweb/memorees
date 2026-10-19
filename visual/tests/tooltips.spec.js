// Tooltip containment: the controls pinned to a RIGHT edge must anchor their
// tooltip inward, so it never paints outside the viewport.
//
// Regression: every tooltip was centred on its button (left:50% +
// translateX(-50%)), but the delete x, the viewer fullscreen button, Edit and
// the A-/A+ zoom pair all sit at a right edge. On a right-most card at 420px
// that pushed "Delete album", "Delete photo" and "Edit comment" off screen.
// They now anchor right:0.
//
// One representative per type, at the width that broke (420px puts cards and
// thumbs two-up, so the right-column control is the one that used to clip).
//
// Run: cd visual && npx playwright test tests/tooltips.spec.js
const { test, expect } = require('@playwright/test');
const path = require('path');

// ::after has no box of its own, so materialise a real element carrying the
// pseudo-element's computed styles, read its width, then apply the alignment
// the stylesheet actually resolved to. Returns where the tooltip would paint.
function tipRect(el) {
  const cs = getComputedStyle(el, '::after');
  const tip = document.createElement('div');
  tip.textContent = el.getAttribute('data-tip');
  tip.style.font = cs.font;
  tip.style.letterSpacing = cs.letterSpacing;
  tip.style.padding = cs.padding;
  tip.style.whiteSpace = cs.whiteSpace;
  tip.style.maxWidth = cs.maxWidth;
  tip.style.position = 'absolute';
  tip.style.visibility = 'hidden';
  tip.style.left = '-9999px';
  document.body.appendChild(tip);
  const w = tip.getBoundingClientRect().width;
  tip.remove();

  const b = el.getBoundingClientRect();
  const centred = cs.transform && cs.transform !== 'none';
  const left = centred ? b.left + b.width / 2 - w / 2 : b.right - w;
  return { left: Math.round(left), right: Math.round(left + w) };
}

async function expectTipFits(page, el, label) {
  await expect(el, `${label} control missing`).toBeVisible();
  await el.hover();
  await page.waitForTimeout(25);
  const r = await el.evaluate(tipRect);
  const vw = page.viewportSize().width;
  expect(r.left, `${label}: tooltip clipped left at ${r.left}`).toBeGreaterThanOrEqual(0);
  expect(r.right, `${label}: tooltip clipped right at ${r.right} of ${vw}`).toBeLessThanOrEqual(vw);
}

test('right-edge tooltips stay inside the viewport', async ({ page }) => {
  test.setTimeout(90000);

  await page.setViewportSize({ width: 420, height: 900 });
  await page.goto('/');
  await page.fill('#u', 'tip' + Date.now().toString(36));
  await page.fill('#p', 'visualpass1');
  await page.click('text=Sign up');
  await expect(page.locator('#s-albums.on')).toBeVisible();

  // two albums: the second lands in the right-hand column at 420px
  await page.click('text=+ New album');
  await page.fill('#aname', 'First album');
  await page.press('#aname', 'Enter');
  for (let i = 0; i < 2; i++) {
    await page.setInputFiles('#files', path.join(__dirname, 'fixtures', 'probe.png'));
    await page.click('button:has-text("Upload")');
  }
  await expect(page.locator('#thumbs img')).toHaveCount(2, { timeout: 30000 });
  await page.click('#s-album button:has-text("Albums")');
  await page.click('text=+ New album');
  await page.fill('#aname', 'Second album');
  await page.press('#aname', 'Enter');
  await page.click('#s-album button:has-text("Albums")');
  await expect(page.locator('#albums .card.polaroid')).toHaveCount(2);

  // albums grid: delete x on the right-hand card
  await expectTipFits(page, page.locator('#albums .card.polaroid').nth(1).locator('.thumbx'), 'Delete album');

  // album screen: photo delete x (right column), Edit, A+ zoom, fullscreen.
  // pick by name: the grid sorts newest-first, so the first card is the empty one.
  await page.locator('#albums .card.polaroid', { hasText: 'First album' }).click();
  await expect(page.locator('#s-album.on')).toBeVisible();
  await page.waitForTimeout(300);
  await expectTipFits(page, page.locator('#thumbs .thumbx').nth(1), 'Delete photo');
  await expectTipFits(page, page.locator('#editBtn'), 'Edit comment');
  await expectTipFits(page, page.locator('#ex .mini').nth(1), 'A+ zoom');
  await expectTipFits(page, page.locator('#viewer .vbar .cbtn[data-tip]'), 'Fullscreen');
});
