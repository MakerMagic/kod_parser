# Blackstone raw parser

Run from the repository root with the existing dependencies in `requirements.txt`:

```powershell
python -m parsers.blackstone acquisition/local
python -m parsers.blackstone "acquisition/local/TSA Oxford 2020.pdf"
python -m pytest -q tests/test_blackstone_raw.py
```

Inputs may be any existing PDF paths or directories. Directory discovery checks document content, rather than requiring a Blackstone filename. It recognizes the TSA question papers currently available in `acquisition/local/`. No files are acquired or moved. The API is `parse_pdf(path, metadata=..., acquisition=...)`; neither acquisition metadata nor location determines extraction behavior.

Raw JSON is written to `data/raw/blackstone/` by default. Use `--output-dir PATH` to choose another raw location. Names include a file content hash to avoid collisions between different PDFs with the same filename. Existing outputs require explicit `--overwrite`.

The output follows `docs/DATA_SCHEMA.md`: source metadata, input reference, acquisition information, question identity, page references, raw blocks, question text, options, subpoints, images, and warnings. Additional extraction context includes full page text, PDF metadata, content SHA-256, graphic bounding boxes, and raw page spans. `validate_raw(data)` checks required records and reconstructs question blocks from unchanged page slices.

The source value `blackstone` identifies the selected parser profile. The current PDFs carry TSA/Cambridge provenance, so that original metadata is retained and the unverified Blackstone label is flagged. Acquisition is `unknown` unless provided by the caller. Missing year or section remains null; uncertain semantic question IDs remain null rather than being invented.

This first version uses the repeated left number column and vertically arranged A-E labels. Grouped graphical labels are retained as options with empty text and explicit uncertainty warnings; their content stays in the raw options block. Page margins only affect structured interpretation; full page text remains available. Subpoints with explicit numeric punctuation are recorded; all remaining statements remain in question text and raw blocks. Raster and vector graphics are references to the original PDF, without image-file export or precise option association. Empty text, malformed options, duplicate numbering, count discrepancies, and encoding artifacts produce warnings.

The 2012-2014 PDFs contain missing font maps. Raw `(cid:...)` tokens are retained. Their observed digit and A-E glyph markers are interpreted only for structural labels and explicitly marked for review; question and option wording is not repaired. No OCR, text normalization, answer matching, categorization, or final dataset export is performed.

CLI failure status is nonzero for file failures, no output, no detected questions, or a known question-count mismatch. Other extraction warnings remain visible in JSON and CLI output and should be reviewed before later stages.

If the repository virtual environment cannot launch in Codex, use its bundled Python with the existing package directory (no dependency changes):

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv/Lib/site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$parserPython = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $parserPython -m parsers.blackstone acquisition/local
& $parserPython -m pytest -q tests/test_blackstone_raw.py
```
