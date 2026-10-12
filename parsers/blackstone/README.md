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

This parser uses the repeated left number column and vertically arranged A-E labels. Grouped graphical labels are retained as options with empty text and explicit uncertainty warnings; their content stays in the raw options block. Page margins only affect structured interpretation; full page text remains available. Subpoints with explicit numeric punctuation are recorded; all remaining statements remain in question text and raw blocks. Raster/vector regions and question-page layouts are saved as PNG crops under `OUTPUT_DIR/assets/<source-content-hash>/`, with references and spatial metadata in `visual_assets`, `visual_previews`, and existing `images` records. Confident option associations are also recorded in `options[].images`; ambiguous associations are flagged. Empty text, malformed options, duplicate numbering, count discrepancies, and encoding artifacts produce warnings.

The 2012-2014 PDFs contain missing font maps. Raw `(cid:...)` tokens are retained. Their observed digit and A-E glyph markers are interpreted only for structural labels and explicitly marked for review; question and option wording is not repaired. No OCR, text normalization, answer matching, categorization, or final dataset export is performed.

CLI failure status is nonzero for file failures, no output, no detected questions, or a known question-count mismatch. Other extraction warnings remain visible in JSON and CLI output and should be reviewed before later stages.

## Raw inspection and unresolved issues

Inspect the exact stored record, without rerunning the parser:

```powershell
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA Oxford 2020.pdf" --year 2020 --question 12
python -m parsers.blackstone.backtest report --raw-json data/raw/blackstone --output docs/PARSING_ISSUES.md
python -m pytest -q tests/test_blackstone_backtest.py tests/test_blackstone_raw.py
```

Every parser CLI run that saves raw output also generates a separate `OUTPUT_DIR/PARSING_ISSUES.md`. Use `--issues-report docs/PARSING_ISSUES.md` to choose the documentation location instead. Inspection supports stored paths/filenames/URLs, optional metadata selectors, text/JSON/HTML export, and complete stored page context. See [the backtest guide](../../docs/RAW_PARSER_BACKTEST.md) for commands, asset naming, and limitations. Reports include missing/failed visual assets; graphics presence alone is informational. Inspection does not modify raw JSON.

```powershell
python -m parsers.blackstone acquisition/local --overwrite --issues-report docs/PARSING_ISSUES.md
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA_2022.pdf" --year 2022 --question 50 --format html --output inspections/TSA_2022_q50.html
python -m pytest -q tests/test_blackstone_raw.py tests/test_blackstone_backtest.py tests/test_blackstone_visuals.py
```

Double-click the new HTML file to view embedded graphics offline. HTML shows the stored `layout_blocks` text/visual sequence with component labels and option images, alongside expandable original layouts and the full record. Existing text/JSON inspection remains available. Exports require a new filename.

Individual assets now use focused PDF bounds, local labels, paragraph barriers, and four-point padding; broader layout previews remain separate. Table text, diagram labels, and captions are preserved, with warnings for ambiguous boundaries. Label-only choices are associated using nearby row/column anchors, including labels above/below their image. `options[].images` and `visual_assets[].placement` expose those associations. Shared graphics spanning several choices stay unresolved rather than guessed. See the backtest guide for schema details and manual regression examples.

```powershell
python -m pytest -q tests/test_blackstone_visual_structure.py tests/test_blackstone_visuals.py
```

If the repository virtual environment cannot launch in Codex, use its bundled Python with the existing package directory (no dependency changes):

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv/Lib/site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$parserPython = 'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $parserPython -m parsers.blackstone acquisition/local
& $parserPython -m pytest -q tests/test_blackstone_raw.py
```
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA_2022.pdf" --year 2022 --question 38
