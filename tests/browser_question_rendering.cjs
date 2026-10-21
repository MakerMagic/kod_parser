// Optional browser regression using the existing Playwright + Edge runtime.
// Input is a disposable four-case HTML produced by test_question_rendering.py.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true, timeout: 20000 });
  try {
    const page = await browser.newPage();
    await page.setContent(fs.readFileSync(process.argv[2], 'utf8'));
    await page.locator('img').evaluateAll(images => Promise.all(images.map(i => i.decode())));
    for (const width of [1166, 1350]) {
      await page.setViewportSize({ width, height: 900 });
      await page.evaluate(w => document.body.style.setProperty('--preview-width', `${w}px`), width);
      const result = await page.evaluate(() => {
        const articles = [...document.querySelectorAll('.question-preview')];
        const panels = [...document.querySelectorAll('.question-pane,.answer-options,.answer-option,.option-content')];
        const passage = articles[1].querySelector('.body-pane');
        passage.scrollTop = 100;
        const images = [...document.querySelectorAll('.simulation-grid img')];
        const answerBottoms = articles.map(a => {
          const options = a.querySelector('.answer-options');
          return options.lastElementChild.getBoundingClientRect().bottom <=
            a.querySelector('.exam-footer').getBoundingClientRect().top + 1;
        });
        const longAnswer = articles[2].querySelector('.question-pane');
        return {
          cases: articles.length,
          scrollingPanels: panels.filter(p => /auto|scroll|hidden|clip/.test(getComputedStyle(p).overflowY)).length,
          clippedPanels: panels.filter(p => p.scrollHeight > p.clientHeight + 1).length,
          passageScrolls: passage.scrollTop > 0 && passage.scrollHeight > passage.clientHeight,
          longAnswersExpand: longAnswer.clientHeight > 560,
          allOptionsAboveFooter: answerBottoms.every(Boolean),
          imagesFit: images.length > 0 && images.every(i => {
            const b = i.getBoundingClientRect(), p = i.closest('.option-content').getBoundingClientRect();
            return i.naturalWidth > 0 && Math.abs(b.width / b.height - i.naturalWidth / i.naturalHeight) < .01 && b.right <= p.right + 1;
          }),
          horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
        };
      });
      assert.equal(result.cases, 4);
      assert.equal(result.scrollingPanels, 0);
      assert.equal(result.clippedPanels, 0);
      for (const key of ['passageScrolls', 'longAnswersExpand', 'allOptionsAboveFooter', 'imagesFit']) assert(result[key], key);
      assert(!result.horizontalOverflow);
      console.log(JSON.stringify({ width, ...result }));
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
