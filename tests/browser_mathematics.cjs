// Optional acceptance smoke with the already available Playwright runtime.
// A selected inspection must already exist; this never generates question data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  const http = /^http:\/\/127\.0\.0\.1:\d+\//.test(url || '');
  assert(url && (http || fs.existsSync(url)), 'Supply a local selected HTML or loopback HTTP URL');
  const browser = await chromium.launch({ channel: 'msedge', headless: true, timeout: 20000 });
  try {
    const page = await browser.newPage({ viewport: { width: 1166, height: 900 } });
    const external = [];
    page.on('request', r => { if (/^https?:/.test(r.url()) && (!http || !r.url().startsWith(new URL(url).origin))) external.push(r.url()); });
    if (http) await page.goto(url);
    else await page.setContent(fs.readFileSync(url, 'utf8'));
    await page.locator('img').evaluateAll(images => Promise.all(images.map(i => i.decode())));
    for (const width of [1166, 1350]) {
      await page.setViewportSize({ width, height: 900 });
      await page.evaluate(w => document.body.style.setProperty('--preview-width', `${w}px`), width);
      const result = await page.evaluate(() => {
        const images = [...document.images].map(i => {
          const b = i.getBoundingClientRect();
          return { loaded: i.complete && i.naturalWidth > 0, ratioError: b.width && b.height ? Math.abs(b.width / b.height - i.naturalWidth / i.naturalHeight) : 0, overflow: b.right > innerWidth + 1 };
        });
        return {
          articles: document.querySelectorAll('article').length,
          fractions: document.querySelectorAll('mfrac').length,
          roots: document.querySelectorAll('msqrt,mroot').length,
          scripts: document.querySelectorAll('msup,msub').length,
          displayMath: document.querySelectorAll('math[display="block"]').length,
          systemRowsAligned: [...document.querySelectorAll('mtable')].every(table => {
            const lefts = [...table.querySelectorAll('mtd')].map(cell => cell.firstElementChild.getBoundingClientRect().left);
            return Math.max(...lefts) - Math.min(...lefts) < 1;
          }),
          rawDelimiters: /\\\(|\\\[/.test(document.querySelector('.website').innerText),
          answerScrollbars: [...document.querySelectorAll('.question-pane,.answer-options,.answer-option,.option-content')].some(p => {
            p.scrollTop = 20;
            return /auto|scroll|hidden|clip/.test(getComputedStyle(p).overflowY) || p.scrollTop !== 0;
          }),
          optionMathFits: [...document.querySelectorAll('.answer-option math')].every(n => {
            const b = n.getBoundingClientRect(), card = n.closest('.answer-option').getBoundingClientRect();
            return b.top >= card.top && b.bottom <= card.bottom && b.right <= card.right;
          }),
          documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
          images,
          mathRendered: [...document.querySelectorAll('mfrac')].every(n => n.getBoundingClientRect().height > 10),
        };
      });
      assert(result.articles > 0 && result.articles <= 10);
      assert(result.fractions && result.roots && result.scripts && result.displayMath && result.mathRendered);
      assert(result.systemRowsAligned, 'System rows must retain their shared left alignment');
      assert(!result.rawDelimiters && !result.documentOverflow && !result.answerScrollbars && result.optionMathFits);
      assert(result.images.every(i => i.loaded && i.ratioError < 0.02 && !i.overflow));
      console.log(JSON.stringify({ width, ...result, images: result.images.length }));
    }
    assert.equal(external.length, 0, 'Math rendering must be offline');
    if (process.argv[3]) {
      const article = page.locator('article').first();
      await article.screenshot({ path: process.argv[3] });
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
