# Inspecting Blackstone raw output

Run commands from the repository root. These utilities read existing raw JSON; inspection does not reopen the PDF or rerun extraction.

## Parse and report

```powershell
python -m parsers.blackstone acquisition/local --overwrite --issues-report docs/PARSING_ISSUES.md
```

Parsing saves raw JSON, visual assets, and a separate Markdown issues report. Without `--issues-report`, the report is `PARSING_ISSUES.md` inside the selected raw output directory. It covers all `*.raw.json` files in that directory, including previous outputs. Use a separate output directory to isolate a run. Existing text fields remain unchanged; rerun with `--overwrite` to upgrade older outputs without visual files.

## Inspect a stored question

```powershell
python -m parsers.blackstone.backtest inspect --raw-json "data/raw/blackstone/TSA Oxford 2020-ca4ee526afb0.raw.json" --source "TSA Oxford 2020.pdf" --year 2020 --question 12
```

`--raw-json` accepts explicit JSON files or a directory of `*.raw.json` files. `--source` accepts the stored PDF filename, path, input URL/reference, or recorded acquisition origin. URLs are compared as stored strings and are never fetched. A supplied path must match the recorded path; it does not fall back to the filename.

Optional selectors are `--year`, `--session`, `--paper`, `--variant`, `--section`, and `--question-id`. Session matching requires an existing session field; no session is inferred. Ambiguous matches produce an error instead of selecting the first record.

The default text view includes document metadata, every stored question field, and the verbatim raw question block. Add `--include-pages` for the complete stored pages in the recorded page range. Missing and null components are listed separately, without modifying the question. Empty optional lists are kept as stored; absent answers or explanations are expected for question-only parsing.

For an exact JSON representation of the question plus its document context:

```powershell
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA Oxford 2020.pdf" --year 2020 --question 12 --format json --output question-12-inspection.json
```

Exports require a new file. Existing files, including raw JSON, are never overwritten by inspection.

## Visual inspection (all questions)

```powershell
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA_2022.pdf" --year 2022 --question 50
python -m parsers.blackstone.backtest inspect --raw-json data/raw/blackstone --source "TSA_2022.pdf" --year 2022 --question 50 --format html --output inspections/TSA_2022_q50.html
```

Open the exported HTML in any browser (double-click it). It embeds saved PNGs, works offline, and needs neither the PDF nor an asset folder after export. This universal view includes page-ordered question layout crops, individual graphic crops, stored text/options, issues, and the complete raw record. Layout crops preserve the position of graphics among text, subparts, and answers; individual assets use page/top/left order. Console and JSON inspection remain available. Inspection only reads raw JSON and saved assets, never rerenders the PDF or changes raw output.

Assets live under `OUTPUT_DIR/assets/<source-content-hash>/`. Names such as `blackstone_2022_q050_r050_p034_asset_01_<bbox-hash>.png` include year, question, record index, page, order, and bounds; `view` denotes a complete question-page layout crop. Source-content folders prevent filename collisions. JSON paths are relative to the raw JSON directory: move JSON together with its `assets/` folder. The API accepts `parse_pdf(path, asset_dir=..., overwrite_assets=False)`; the CLI selects its output directory automatically.

`visual_assets` stores rendered regions with original object IDs/types, coordinates, source identity, component/option association, order, PNG size/hash, and warnings. `visual_previews` stores question-page layout crops. Original `images` records retain object bounds and point to saved regions. PDFium renders raster and vector content together at 144 DPI; no OCR or text cleanup is applied. Region grouping uses nearby objects, local labels, and padding. White page backgrounds use layout previews rather than isolated crops. Unassigned document graphics are retained at page level.

Grouping and option association are geometric heuristics: nearby diagrams may share a crop, diagonal/overlapping layouts can be ambiguous, and subpart association is not inferred without reliable anchors. A disagreement between extraction and renderer page coordinates falls back to a complete rendered page with explicit warnings, rather than risking a partial crop. Use layout previews and the original PDF to check completeness and order. Unknown associations, inconsistent bounds/order, failed saves, uncovered graphics, and missing/corrupt PNGs appear in the issues report with saved paths and manual-review status. Graphics presence alone is not an error; header/footer context outside questions is not flagged merely for being unassigned. Legacy JSON without saved visual references requires reparsing. Report regeneration detects subsequently missing assets; HTML also shows these problems inline.

Narrow external reference: [render_q38.py](https://github.com/LegionHH/parsing/blob/main/render_q38.py) illustrates rendered PDF crops; [split_q38.py](https://github.com/LegionHH/parsing/blob/main/split_q38.py) illustrates padded option crops. Only these general visual ideas informed this implementation; no code, fixed coordinates, dependencies, architecture, or unrelated parsing logic was copied.

## Refresh the issues report without reparsing

```powershell
python -m parsers.blackstone.backtest report --raw-json data/raw/blackstone --output docs/PARSING_ISSUES.md
```

Reports list source file, available year/session/paper/variant/section, question number, pages, affected components, reasons, saved asset paths, manual-review status, and raw JSON location. Document-level issues use an explicit document row rather than inventing a question number. Shared source/year issues are reported once per document.

Review rows come from actual parser warnings, explicit unresolved/low-confidence flags, empty essential text, duplicate/invalid numbers, or inconsistent page references/spans. General graphics-presence notices, blank-page notices, empty subpoint lists, and absent answers/explanations alone are not treated as faults. Numeric confidence values are preserved by inspection but no new confidence threshold is invented. A report with no issues is not proof of correctness.

Compare flagged records against the original PDF: wording and context, numbering, option labels and continuation lines, subparts, diagrams and their associations, page spans, and exam metadata. Font artifacts and grouped diagram options remain extraction limitations; the utility does not repair them or track manual review decisions. Reports are reproducible snapshots and refresh only files bearing their generated-report marker; unrelated Markdown files are protected.

## Tests

```powershell
python -m pytest -q tests/test_blackstone_backtest.py tests/test_blackstone_raw.py tests/test_blackstone_visuals.py
```

If the existing virtual environment cannot launch, use the bundled-runtime setup in `parsers/blackstone/README.md` and replace `python` in these commands with `& $parserPython`.