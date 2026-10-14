# Current Work
- Define and implement raw → clean normalization rules.
- Add cleaning regression tests.
## Current milestone

Blackstone raw structured JSON → Blackstone clean structured JSON.

## Current focus

Implement deterministic normalization and cleaning of Blackstone raw question data while preserving raw records unchanged.

## Already completed

- Python environment created.
- GitHub repository connected.
- Basic project documentation added.
- Codex skills added.
- `AGENTS.md` added.
- Initial folder structure prepared.
- First Blackstone raw parser and CLI implemented in `parsers/blackstone/`.
- Full page text, question spans, source metadata, options, graphics references, and warnings preserved in raw JSON.
- Parser regression tests and local PDF validation added; no new dependencies.
- All 16 local PDFs parsed into 800 numbered raw records; 18 tests pass. Unresolved extraction details remain flagged.
- Raw question inspection and separate parsing-issues reports added, including automatic reporting after parser CLI runs.
- Current issues snapshot stored in `docs/RAW_PARSING_ISSUES.md`; raw JSON remains unchanged by backtesting.
- Raster/vector crops and question-page layout PNGs saved with ordered raw JSON references; universal self-contained HTML inspection added alongside text/JSON inspection.
- All 16 local PDFs reparsed with visual assets; original page/question/option text and identity fields verified unchanged. Visual extraction/missing-file issues are included in the refreshed report.
- Focused crops now exclude external prose while retaining diagram/table labels. Ordered raw-span-backed layout blocks and option image associations are shown in HTML; duplicate/shared choice geometry remains unresolved.
- Previous validation: 61 tests and lint/format checks passed. Attached 2010 questions 7/12, image-choice questions 14/20, and previously good 2022 question 50 have regression checks; original text/options/subparts remained preserved across all 800 records.
- All 16 PDFs regenerated with the refined geometry/association rules; saved-asset references and read-only text/JSON/HTML inspection validated.
- Fixed 2022 Q8/Q20 crop regressions with wrapped-paragraph barriers, nearest-graphic text ownership, and baseline-aware rotated labels. Repeated image choices now recover A–E without treating internal chart/table text as answer text; initial text candidates remain raw.
- Current validation: 67 tests plus lint/format checks pass. All 16 PDFs regenerated; all 800 raw page/question/options blocks, spans, identities, question text, and subparts verified unchanged. Structured option corrections are limited to 2022 Q8 and 2021 Q32; the visual issues report and HTML previews were refreshed.
- Graph-specific grouping now joins detached chart guides, respects one-letter/one-image option cells, and reconstructs rotated axis labels from PDF glyph order. 2021 Q26/Q37/Q38 were reparsed; Q32 option PNGs and 2017 Q13's rotated-text visual remain bit-identical, 2022 Q8/Q20/Q50 controls pass, and 2020 Q25 is an additional axis-label control. Current validation: 73 tests plus lint/format checks pass; the issues report was refreshed.
- Image-choice crops now exclude neighboring structural option letters; a crop that cannot be separated remains saved but unassigned and appears in QA. 2011 Q50 A no longer contains B. The issues report is grouped by nonempty categories with deterministic row order. All 16 local PDFs were reparsed and the report refreshed; vertical/grid/graph controls remain associated. Current validation: 76 tests, lint, and format checks pass.
- Image-answer association now accepts only a left-side option anchor. Invisible white vector masks and text-enclosure page frames no longer become visual assets; 2011 Q7 and text-only 2012 Q3 were regenerated and the aggregate issues report refreshed. Current validation: 78 tests plus lint/format checks pass.
- Verified the shifted CID font encoding in the 2012–2014 Oxford papers and decoded structured question/option text while preserving original CID page/question spans. Reparsed those three papers; the CID question-and-all-options issue count fell from 148 to 0. The generated issues report now shows per-category counts and a CID subcategory; 52 parser/backtest/visual tests pass.
- Page-margin white vector frames no longer become question visuals or merge into tables. Closed table borders now define focused crops, and a single enclosing option contour can resolve false per-edge ownership. All 16 PDFs were reparsed; the 2015 question-level issue count fell from 50 to 0, while the genuinely merged 2016 Q32 remains flagged. All 800 question numbers, page references, raw blocks, text, options, and subpoints matched the pre-change baseline; 80 focused tests pass.

- PDF drawing color spaces now preserve black spot-color grids, including the complete 2017 Q20 table. Category counts include unique document/page/question records; Source Metadata correctly shows 16 records without hiding provenance warnings. PowerShell parsing/inspection/report/test commands were verified. All 16 papers were reparsed; all 800 raw/text/numbering/page/option records matched the baseline, and representative existing crop pixels/associations stayed unchanged. 86 tests plus lint/format checks pass.

- Initial conservative Blackstone cleaning added under `processors/normalization/blackstone/`: separate clean JSON, complete raw snapshots/hashes/pointers, preserved warnings/assets, ordered body/prompt/options, and offline HTML comparison. All 800 clean records generated and audited; raw JSON and the renamed raw issues report remain byte-identical. Raw QA exports moved to `inspections_raw/`; clean QA uses `inspections_clean/`. Full suite: 117 passed; final cleaning/backtest safeguards: 51 passed; lint/format pass.

- Raw graph-cell top-guide handling now recognizes 2017 Q20's five A–E images without weakening foreign-letter boundaries; only that paper was reparsed. Cleaning saves separate geometry-verified answer crops and uses them in HTML: 246 derivatives audited (83 glyph removals, 163 unchanged copies), with every other answer pixel preserved. All 4,055 raw PNGs remain byte-identical; all 800 raw core text/identity/page/option records are preserved. Full suite: 138 passed; final clean/unsafe-crop checks: 49 passed; lint/format pass. Shared/unassigned raw visuals remain unresolved.

## Code navigation

- Clean transformation/CLI: `processors/normalization/blackstone/`; tests: `tests/test_blackstone_cleaning.py`.
- Derived answer PNGs: `option_assets.py` / `png_pixels.py` in the clean module; regression tests: `tests/test_blackstone_option_asset_crops.py`.
- Clean output: `data/clean/blackstone/*.clean.json`; commands: `docs/CLEANING_BACKTEST.md`.
- Reports: `docs/RAW_PARSING_ISSUES.md` and `docs/CLEANING_ISSUES.md`; raw inspection commands remain unchanged.

## Do not work on yet

- answer matching;
- categorization;
- final dataset generation;
- additional sources.

## Next task

- Backtest the 115 unique clean review records: 75 ambiguous prompt splits plus remaining ordering/option/encoding findings (categories overlap).
- Extend rules only after comparing multiple affected and unaffected records against original screenshots. Preserve raw uncertainty; do not solve upstream crop/association issues in cleaning.
