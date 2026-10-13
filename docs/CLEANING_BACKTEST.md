# Blackstone raw → clean inspection

Run from the repository root. Cleaning reads stored raw JSON/PNG assets only;
it never opens PDFs, acquires files, matches answers, or categorizes questions.

## PowerShell commands

Use a working Python with the existing dependencies. For this checkout:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$parserPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\CLEANING_ISSUES.md'
```

For a repeat run, add `--overwrite`; it replaces only clean JSON belonging to
the same raw input. Output inside a raw input directory is rejected. Input
may be one or more explicit raw JSON files or directories of `*.raw.json`.

```powershell
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 8
$cleanHtml = 'inspections_clean\TSA_2022_q08-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 8 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

HTML is universal, self-contained, offline, and contains embedded PNGs. Exports
require a new filename. `--format json` exports the full clean/raw comparison.
Selectors include `--session`, `--paper`, `--variant`, `--section`, and
`--question-id`. Ambiguous matches fail instead of picking a record silently.

```powershell
& $parserPython -m processors.normalization.blackstone.backtest report --clean-json 'data\clean\blackstone' --output 'docs\CLEANING_ISSUES.md'
& $parserPython -m pytest -q tests/test_blackstone_cleaning.py tests/test_blackstone_backtest.py
```

Raw workflows retain their existing module/commands. The raw report is now
`docs/RAW_PARSING_ISSUES.md` (parser default: `OUTPUT_DIR/RAW_PARSING_ISSUES.md`).
Existing raw QA exports moved to `inspections_raw/`; the raw guide already had
a clear name, [RAW_PARSER_BACKTEST.md](RAW_PARSER_BACKTEST.md). Explicit legacy
report paths still work. No raw JSON or referenced PNG was renamed or edited.

## Initial rules and evidence

- NFC composes canonical Unicode equivalents; it does not apply NFKC, replace
  mathematical symbols, guess CID maps, or remove hyphens. Accents/composed
  controls and valid `½`, `×`, `−`, and currency characters are regression tested.
- Strip line-edge whitespace and collapse common spaces/tabs/NBSP. Repeated
  trailing whitespace was inspected across 2012 Q3/Q4/Q5, with unaffected
  2010/2022 controls.
- Join only long prose lines followed by lowercase continuation, retaining
  paragraph gaps, numbered/bulleted items, numeric rows, standalone symbols,
  and hyphen-ended lines. Wrapped 2008 Q3 options and multiple prose papers
  supplied evidence; table/list/math controls remain separate.
- Trim existing option labels; preserve their order, multiline content,
  subpoint labels, visual references, and all original warnings. Never regroup
  options or infer an image association. Image-only options keep empty text.
- Metadata types/values are retained: no evidence-based metadata correction
  rule is established yet. Missing, null, and empty fields remain distinguishable
  in availability lists, including per-option fields.
- No header/footer/artifact deletion rule is enabled. Displaced punctuation,
  CID/control/replacement glyphs and malformed components are retained/reported.

## Structure and comparison

The HTML header shows question number/year, followed by:

1. **Main Body**: one section for all context text, tables, diagrams, subpoints,
   and intermediate support. Text/visual order follows stored layout when it
   can be aligned to the readable structured text.
2. **Main Question**: one complete explicit prompt, separated only when there
   is a single supported candidate. Otherwise null, with all text retained in
   Main Body and a cleaning issue.
3. **Main Answers**: original option order, cleaned text, and preserved option
   image references (including mixed text/images).
4. **Original Screenshot**: all full-question page crops saved by raw parsing.
5. **Source / Document Metadata**.
6. **Missing / Null Field Availability** (also lists empty/unavailable fields).
7. **Visual Inspection Issues**: raw/document/visual warnings plus clean issues.

Raw visual-label text is represented by its crop, not repeated as answer text.
Already decoded CID structured lines are aligned only when upstream recorded
a verified decode and the raw/readable line counts agree; cleaning does not
decode CID tokens. Failed alignment retains readable text and assets with an
ordering issue rather than guessing insertion points. Supporting context that
was after the prompt remains ordered within Main Body; raw block coordinates
and the original screenshot preserve its exact source position.

## Traceability and limitations

`*.clean.json` is separate, deterministic schema v1. Each record stores the
unchanged question ID/source key/page mapping, complete `raw_record` snapshot,
raw JSON absolute path/SHA-256/JSON pointer, warnings, text transformation hashes,
and line-level `content_accounting`. Body blocks retain raw block IDs/spans/page
coordinates. Assets retain their original paths, IDs, order, associations,
coordinates, and warnings; paths resolve relative to the **raw JSON**, not clean
JSON. Keep the original raw JSON/assets available; HTML embeds the images it
successfully reads and remains standalone after export.

`CLEANING_ISSUES.md` groups only clean-stage discoveries by category and counts
unique records. It does not copy raw warnings or claim they are solved. Missing
assets and changed/missing raw references are checked again during inspection
and report regeneration. Neither operation modifies raw or clean JSON.

Review ambiguous/multiple/imperative or embedded prompts, unaligned layouts,
displaced punctuation (2020 Q12), and the remaining CID token (2021 Q7).
Unknown/shared raw visuals remain unresolved; cleaning cannot restore missing
content, fix crop boundaries, repair equations, or rerender missing screenshots.
Compare 2017 Q20, 2022 Q8, 2021 Q32/Q37 and decoded 2012 Q3 with their original
screenshots. No issue row is proof that the representation is faithful.
