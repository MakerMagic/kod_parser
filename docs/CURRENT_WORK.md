# Current Work

## Current milestone

Blackstone PDF → raw structured JSON.

## Current focus

- Visual option/image cropping reliability.
- Table/text-heavy visual parsing.
- Issue classification and regression testing.

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
- Current issues snapshot stored in `docs/PARSING_ISSUES.md`; raw JSON remains unchanged by backtesting.
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

## Do not work on yet

- answer matching;
- categorization;
- final dataset export;
- new acquisition mechanisms;
- additional sources.

## Next task

-Review remaining flagged captions and shared/ambiguous layouts (including 2019 Q32), letter-puzzle option markers, and the isolated 2021 CID artifact using `docs/RAW_PARSER_BACKTEST.md`; compare structured HTML with original layout previews before later stages. Existing inputs remain in `acquisition/local/`.
- Investigate visual option parsing issues in Blackstone/TSA outputs.
- Review remaining genuinely shared/ambiguous visual groups and non-enclosed text-heavy visuals; compare stored crops with source PDFs before further confidence changes.
