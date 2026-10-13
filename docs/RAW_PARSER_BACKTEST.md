# Inspecting Blackstone raw output

Run commands from the repository root. These utilities read existing raw JSON; inspection does not reopen the PDF or rerun extraction.

## PowerShell setup

Run this once in the same PowerShell session. This repository's `.venv` launcher
is currently broken; the installed Codex Python can use its existing packages:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$parserPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $parserPython --version
```

If using another working Python with the required packages, set `$parserPython`
to its executable instead. All commands below use PowerShell's `&` call operator;
no Bash line-continuation syntax is required.

## Parse and report

```powershell
& $parserPython -m parsers.blackstone 'acquisition\local' --output-dir 'data\raw\blackstone' --overwrite --issues-report 'docs\RAW_PARSING_ISSUES.md'
```

This reruns extraction from the local acquisition directory, replacing the
parser's raw JSON/assets explicitly. It does not download files or delete old
unreferenced PNGs. To start an isolated run instead, choose a new output directory:

```powershell
$freshOutput = 'inspections_raw\fresh-raw-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
& $parserPython -m parsers.blackstone 'acquisition\local' --output-dir $freshOutput
```

Parsing saves raw JSON, visual assets, and a separate Markdown issues report. Without `--issues-report`, the report is `RAW_PARSING_ISSUES.md` inside the selected raw output directory. It covers all `*.raw.json` files in that directory, including previous outputs. Use a separate output directory to isolate a run. Raw page/question/options text remains unchanged; structured image-option text can be corrected using geometric evidence. Rerun with `--overwrite` to upgrade older outputs.

## Inspect a stored question

```powershell
& $parserPython -m parsers.blackstone.backtest inspect --raw-json 'data\raw\blackstone' --source 'TSA Oxford 2020.pdf' --year 2020 --question 12
```

`--raw-json` accepts explicit JSON files or a directory of `*.raw.json` files. `--source` accepts the stored PDF filename, path, input URL/reference, or recorded acquisition origin. URLs are compared as stored strings and are never fetched. A supplied path must match the recorded path; it does not fall back to the filename.

Optional selectors are `--year`, `--session`, `--paper`, `--variant`, `--section`, and `--question-id`. Session matching requires an existing session field; no session is inferred. Ambiguous matches produce an error instead of selecting the first record.

The default text view includes document metadata, every stored question field, and the verbatim raw question block. Add `--include-pages` for the complete stored pages in the recorded page range. Missing and null components are listed separately, without modifying the question. Empty optional lists are kept as stored; absent answers or explanations are expected for question-only parsing.

For an exact JSON representation of the question plus its document context:

```powershell
$inspectionJson = 'inspections_raw\question-12-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.json'
& $parserPython -m parsers.blackstone.backtest inspect --raw-json 'data\raw\blackstone' --source 'TSA Oxford 2020.pdf' --year 2020 --question 12 --format json --output $inspectionJson
```

Exports require a new file. Existing files, including raw JSON, are never overwritten by inspection.

## Visual inspection (all questions)

```powershell
& $parserPython -m parsers.blackstone.backtest inspect --raw-json 'data\raw\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 50
$inspectionHtml = 'inspections_raw\TSA_2017_q20-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m parsers.blackstone.backtest inspect --raw-json 'data\raw\blackstone' --source 'TSA Oxford 2017.pdf' --year 2017 --question 20 --format html --output $inspectionHtml
Invoke-Item -LiteralPath $inspectionHtml
```

Open the exported HTML in any browser (double-click it). It embeds saved PNGs, works offline, and needs neither the PDF nor an asset folder after export. This universal view includes page-ordered question layout crops, individual graphic crops, stored text/options, issues, and the complete raw record. Layout crops preserve the position of graphics among text, subparts, and answers; individual assets use page/top/left order. Console and JSON inspection remain available. Inspection only reads raw JSON and saved assets, never rerenders the PDF or changes raw output.

Assets live under `OUTPUT_DIR/assets/<source-content-hash>/`. Names such as `blackstone_2022_q050_r050_p034_asset_01_<bbox-hash>.png` include year, question, record index, page, order, and bounds; `view` denotes a complete question-page layout crop. Source-content folders prevent filename collisions. JSON paths are relative to the raw JSON directory: move JSON together with its `assets/` folder. The API accepts `parse_pdf(path, asset_dir=..., overwrite_assets=False)`; the CLI selects its output directory automatically.

`visual_assets` stores rendered regions with original object IDs/types, coordinates, source identity, component/option association, order, PNG size/hash, and warnings. `visual_previews` stores question-page layout crops. Original `images` records retain object bounds and point to saved regions. PDFium renders raster and vector content together at 144 DPI; no OCR or text cleanup is applied. Region grouping uses nearby objects, local labels, and padding. White page backgrounds use layout previews rather than isolated crops. Unassigned document graphics are retained at page level.

### Focused crops and structured placement

Individual crops use PDF object bounds, nearby label words, and four-point padding. Internal table/diagram text is retained. External sentence/paragraph lines form barriers: a few nearby words from a long sentence can no longer pull the whole sentence into a crop. Short local labels and numbered figure/table captions are retained; ambiguous long captions are flagged. Padding is constrained by excluded prose. Layout previews still include surrounding question text. No new image-processing dependency is required.

Table detection accepts stroked lines and thin filled rectangle rules only when
they form a repeated intersecting grid with text in multiple rows and columns.
Separators and outer borders alone are not tables. PDF color-space metadata
distinguishes white backgrounds from black spot-color ink, preserving Q20's
2017 grid. Its full 12-row table now has a focused crop; separate answer-chart
ambiguities remain reported. Borderless tables and unusual grid structures may
still require review. Attached footnotes/named captions retain the conservative
label-aware crop and its warnings rather than being cut off at the grid border.
Long/multiple external notes may still be incomplete in individual crops (for
example 2021 Q19); use the full layout/raw text and retain manual review.

Wrapped paragraphs now include short endings such as "been incorrectly plotted."
in the exclusion barrier. Nearby text belongs to the closest graphic, rather
than expanding every neighboring crop. Slanted labels are grouped along their
PDF text baseline before ownership is decided, keeping all four year digits
with the correct chart. Padding cannot cross another graphic's bounds;
overlapping content remains saved with a review warning.

Repeated charts with standalone A–E (or longer contiguous) anchors, matching
dimensions/alignment, unique visual matches, and no outside answer text become
image-only options. This also handles extracted rows such as `A 100 B 100`.
`options[].text` is empty, `content_type` is `image`, and `images` references the
correct crop. Internal chart text stays in the PNG and `visual_text`, not in
ordinary answer text. The initial text interpretation is retained separately
in `raw.text_option_candidates`. Ambiguous repeated layouts stay unresolved;
genuine text-plus-image answers are not forced into image-only form. Inspection
also reports broken image-option mappings, alongside missing files/crop warnings.

`layout_blocks` records text and graphic blocks in page/top/left reading order, with exact raw text spans. Each visual asset's `placement` records a component and neighboring raw spans: stimulus, question body, subpart, option, intermediate, or unknown. These are geometric/structural estimates; the original saved layout remains the reference for ambiguous multi-column reading order. HTML now shows this structured sequence first, including explicit component labels, and displays option images under the corresponding stored answer option. Original layouts and complete raw JSON remain available in expandable sections. Old JSON uses the previous inspection fallback.

Label-only choices are associated using local row/column anchors, including labels above, beside, or below images. Clear associations populate `options[].images` without inventing text. Contiguous labels beyond E are supported; prose starting with "I" does not create an extra option. Anchor-separated close diagrams are regrouped with a smaller gap. Connected/shared geometry spanning several choices remains saved but unresolved, not arbitrarily cut or assigned.

Filename bounds hashes change when cropping changes. Previously generated, unreferenced PNGs and embedded HTML previews are not deleted automatically; use the current JSON references and export to a new HTML filename to inspect the latest results.

For bar/line graphs, repeated PDF guides and plotted marks distinguish a graph
from a table. A uniquely aligned detached top guide is joined to that graph;
option-letter anchors delimit the graph's cell and prevent a following letter
from entering the crop. Other diagrams and tables keep their previous grouping
path. Transformed vertical glyphs are read in PDF stream order, not reversed
from the extracted line. `axis_labels` records the canonical graph label and
its raw spans. Graph-owned extracted lines are excluded from derived
`question_text` (the former value is kept in `raw.text_question_candidate`),
while `raw.question_block`, page text and `layout_blocks` retain the original
evidence. HTML displays corrected axis labels beside the crop.

Regression examples: 2021 Q26 should show five separate A–E graph options,
one PNG each, without a following option letter; Q32's five table-choice PNGs
should remain unchanged. Q37 should show `distance (km)` and `day` (singular
in the PDF), and Q38 `Number of people` and `Year`, inside the graph crops.
The two formerly split bottom graphs cited for Q26 belong to option E in the
source layout; option A has its own graph in the top-left cell. Check both the
saved layout and the focused crop. 2020 Q25 is an additional rotated `Price`
label control. Uncertain/shared graph boundaries remain in the issues report.

Complete, separated image rows are matched one-to-one in horizontal order, avoiding greedy nearest-letter errors on wide charts. Question prose between a graphic and the labels blocks this row match. Duplicate parsed labels remain unresolved; letter-valued text choices such as `A V` retain their original text rather than becoming additional image-choice labels.

Reports also flag excessive prose overlap, possible incomplete crops/captions, shared multi-option graphics, unknown placement, and inconsistent layout spans/references/order. Resolved image-only choices are not marked empty solely because text is absent. Remaining limits include heuristic caption identification, overlapping/shared frames, missing font maps, text-only diagrams without detected PDF objects, and ambiguous reading order. Full layouts preserve context for manual review.

Structural option letters now act as crop barriers for every image-choice layout,
not just graphs. The parser retains an option's own anchor, excludes other
option anchors from nearby-label expansion, and checks the final crop before
linking it to an answer. When a foreign letter lies inside the graphic itself,
the full visual is saved but its option association is left unresolved with
`foreign_option_letter_in_crop`. Saved `options[].label_bbox` and `page` support
the same read-only check during inspection. Letters printed *inside* a diagram
are not treated as option anchors. Also review significant overlap between
different option visuals. TSA 2011 Q50 option A is a concrete regression: its
focused PNG must not include B.

Manual regression examples: 2010 questions 7 (digital clock) and 12 (sale table) must exclude surrounding prose in individual crops while keeping it in layout/raw text. 2022 question 50 must retain all town labels and five sign tables; 2022 question 38 must retain chart legends. Inspect these with the same command, changing source/year/question and using a new HTML output filename.

For the latest regressions, export 2022 questions 8 and 20 to new HTML files
(for example `inspections_raw/TSA_2022_q08_cropfix.html`). Q8 must show a separate
table and shared key, then five isolated A–E charts with complete axes/years;
no chart may contain a piece of its neighbor. Q20's scatter plot must exclude
the paragraph ending above it. Compare the expanded original layout with the
individual crops. The conservative image-only detector currently requires at
least five similarly sized, top/left-anchored choices; other layouts retain
existing association logic and may require manual review. Scanned text, unusual
captions, shared frames, and severely overlapping labels remain limitations.

Grouping and option association are geometric heuristics: nearby diagrams may share a crop, diagonal/overlapping layouts can be ambiguous, and subpart association is not inferred without reliable anchors. A disagreement between extraction and renderer page coordinates falls back to a complete rendered page with explicit warnings, rather than risking a partial crop. Use layout previews and the original PDF to check completeness and order. Unknown associations, inconsistent bounds/order, failed saves, uncovered graphics, and missing/corrupt PNGs appear in the issues report with saved paths and manual-review status. Graphics presence alone is not an error; header/footer context outside questions is not flagged merely for being unassigned. Legacy JSON without saved visual references requires reparsing. Report regeneration detects subsequently missing assets; HTML also shows these problems inline.

Narrow external reference: [render_q38.py](https://github.com/LegionHH/parsing/blob/main/render_q38.py) illustrates rendered PDF crops; [split_q38.py](https://github.com/LegionHH/parsing/blob/main/split_q38.py) illustrates padded option crops. Only these general visual ideas informed this implementation; no code, fixed coordinates, dependencies, architecture, or unrelated parsing logic was copied.

## Refresh the issues report without reparsing

```powershell
& $parserPython -m parsers.blackstone.backtest report --raw-json 'data\raw\blackstone' --output 'docs\RAW_PARSING_ISSUES.md'
```

Reports list source file, available year/session/paper/variant/section, question number, pages, affected components, reasons, saved asset paths, manual-review status, and raw JSON location. Document-level issues use an explicit document row rather than inventing a question number. Shared source/year issues are reported once per document.

The generated report groups detected reasons under `##` category headings
(for example Foreign Option Letter in Crop, Option Association Issues, and
Question Text Parsing Issues). Only nonempty categories appear. A question may
appear in several categories, but its reasons are combined into one row within
each category; rows are sorted by year, source, question, and page. The raw
inspection and JSON are unchanged by report generation.

Heading counts are unique displayed **records**, including document/page rows,
not just numbered questions. Multiple reasons on one record are combined within
each category. Source provenance notices remain unresolved unless the PDF
actually verifies the source; correcting a count does not resolve provenance.

Review rows come from actual parser warnings, explicit unresolved/low-confidence flags, empty essential text, duplicate/invalid numbers, or inconsistent page references/spans. General graphics-presence notices, blank-page notices, empty subpoint lists, and absent answers/explanations alone are not treated as faults. Numeric confidence values are preserved by inspection but no new confidence threshold is invented. A report with no issues is not proof of correctness.

Compare flagged records against the original PDF: wording and context, numbering, option labels and continuation lines, subparts, diagrams and their associations, page spans, and exam metadata. Font artifacts and grouped diagram options remain extraction limitations; the utility does not repair them or track manual review decisions. Reports are reproducible snapshots and refresh only files bearing their generated-report marker; unrelated Markdown files are protected.

## Tests

```powershell
& $parserPython -m pytest -q tests/test_blackstone_backtest.py tests/test_blackstone_raw.py tests/test_blackstone_visuals.py tests/test_blackstone_visual_structure.py tests/test_blackstone_image_options.py
```
