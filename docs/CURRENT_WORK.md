# Current Work

## Current milestone

Blackstone PDF → raw structured JSON.

## Current focus

Set up the first Blackstone raw parser using already available local input PDFs.

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

## Do not work on yet

- answer matching;
- categorization;
- final dataset export;
- new acquisition mechanisms;
- additional sources.

## Next task

Review raw extraction warnings, especially encoded fonts and graphical options. Improve those extraction cases before implementing later pipeline stages. Existing inputs are in `acquisition/local/`; the parser also accepts arbitrary PDF paths.
