// Existing Tesseract.js runtime, local English model only; no network acquisition.
const fs = require('node:fs');
const path = require('node:path');
let Tesseract;
try { Tesseract = require('tesseract.js'); }
catch { Tesseract = require(path.resolve(path.dirname(process.execPath), '../node_modules/tesseract.js')); }
async function main() {
  const [image, modelDirectory, layout='11'] = process.argv.slice(2);
  if (!fs.existsSync(path.join(modelDirectory, 'eng.traineddata'))) throw new Error('Local English model required');
  const worker = await Tesseract.createWorker('eng', 1, {
    cachePath: modelDirectory, langPath: modelDirectory, gzip: false, cacheMethod: 'readOnly',
  });
  try {
    await worker.setParameters({tessedit_pageseg_mode: layout});
    const {data} = await worker.recognize(image, {}, {text: true, blocks: true});
    const words = (data.blocks || []).flatMap(b => b.paragraphs || [])
      .flatMap(p => p.lines || []).flatMap(l => l.words || [])
      .map(w => ({text:w.text,x:w.bbox.x0,y:w.bbox.y0,width:w.bbox.x1-w.bbox.x0,height:w.bbox.y1-w.bbox.y0,confidence:w.confidence}));
    process.stdout.write(JSON.stringify({text:data.text,lines:data.text.split('\n'),words,method:'local_tesseractjs_sparse_text'}));
  } finally { await worker.terminate(); }
}
main().catch(e => { process.stderr.write(String(e)); process.exitCode=1; });
