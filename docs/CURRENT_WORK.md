# Current Work

## Current milestone

Blackstone PDF → raw structured JSON.

## Current focus

Save and inspect Blackstone raw graphics without changing text extraction or downstream stages.

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
- Current validation: 47 tests and lint/format checks pass; all 1,763 referenced PNGs validated and all 800 questions have layouts. Actual 2022 questions 50/38 visually checked; one specimen coordinate mismatch uses a flagged full-page fallback.

## Do not work on yet

- answer matching;
- categorization;
- final dataset export;
- new acquisition mechanisms;
- additional sources.

## Next task

Manually review saved diagram crops and option associations using `docs/RAW_PARSER_BACKTEST.md`, then investigate remaining encoded-font and ambiguous-layout warnings before later stages. Existing inputs are in `acquisition/local/`; the parser also accepts arbitrary PDF paths.
