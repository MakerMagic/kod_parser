// Render generated, restricted MathML locally for source-shape comparison.
const fs = require('node:fs');
const { chromium } = require('playwright');

(async () => {
  const [manifestPath, outputDir] = process.argv.slice(2);
  const entries = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({ channel: 'msedge', headless: true, timeout: 30000 });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 500 }, deviceScaleFactor: 2 });
    const external = [];
    page.on('request', request => { if (/^https?:/.test(request.url())) external.push(request.url()); });
    for (const entry of entries) {
      await page.setContent(`<html><body style="margin:0;background:white"><div id="formula" style="display:inline-block;padding:5px;font:36px serif;color:black">${entry.mathml}</div></body></html>`);
      await page.evaluate(() => document.fonts.ready);
      const path = `${outputDir}/${entry.id}.png`;
      await page.locator('#formula').screenshot({ path });
      entry.rendered_path = path;
    }
    if (external.length) throw new Error(`Offline renderer attempted external requests: ${external.join(', ')}`);
    fs.writeFileSync(`${outputDir}/manifest.json`, JSON.stringify(entries, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
