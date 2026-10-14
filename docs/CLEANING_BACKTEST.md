# Blackstone raw → clean inspection

Run from the repository root. Cleaning reads stored raw JSON/PNG assets only;
it never opens PDFs, acquires files, matches answers, or categorizes questions.

Raw CID visual-option recovery now supplies distinct A–E image references for
the affected 2012–2014 layouts. Regenerate clean output with the command below
after reparsing; cleaning does not guess missing raw associations. Clean layout
alignment now verifies each decoded/raw line, including the previously unresolved
2012 Q8 body layout. Incorrect or unverified encodings still require review.

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

Regenerate clean JSON and derived answer PNGs after upgrading the cleaner:

```powershell
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\CLEANING_ISSUES.md' --overwrite
$cleanHtml = 'inspections_clean\TSA_2017_q20-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA Oxford 2017.pdf' --year 2017 --question 20 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

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
& $parserPython -m pytest -q tests/test_blackstone_cleaning.py tests/test_blackstone_clean_structure.py tests/test_blackstone_option_asset_crops.py tests/test_blackstone_backtest.py
```

Raw workflows retain their existing module/commands. The raw report is now
`docs/RAW_PARSING_ISSUES.md` (parser default: `OUTPUT_DIR/RAW_PARSING_ISSUES.md`).
Existing raw QA exports moved to `inspections_raw/`; the raw guide already had
a clear name, [RAW_PARSER_BACKTEST.md](RAW_PARSER_BACKTEST.md). Explicit legacy
report paths still work. Cleaning never edits raw JSON or referenced raw PNGs.

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
2. **Main Question**: one complete supported request, including its conditional
   preface and attached parenthetical answer instructions. Otherwise null, with
   all text retained in Main Body and a cleaning issue.
3. **Main Answers**: original option order, cleaned text, and image references
   (including mixed text/images). Image-only answers use saved derived clean PNGs
   without a repeated option letter, when safe removal was verified.
4. **Original Screenshot**: all full-question page crops saved by raw parsing.
5. **Source / Document Metadata**.
6. **Missing / Null Field Availability** (also lists empty/unavailable fields).
7. **Visual Inspection Issues**: raw/document/visual warnings plus clean issues.

Raw visual-label text is represented by its crop, not repeated as answer text.
For CID-backed layout, cleaning requires the upstream verified-font declaration,
checks every block's exact original raw span, and reuses that existing decoder
only as an equality view against already-readable structured lines. It does not
infer a new font map, replace question text, or align merely by equal line counts.
Exact blank/space blocks and the initial number anchor are not content lines.
Failed alignment retains readable text and assets with an ordering issue rather
than guessing insertion points. Supporting context that
was after the prompt remains ordered within Main Body; raw block coordinates
and the original screenshot preserve its exact source position.

Stored visual-contained text is accounted for under its existing asset rather
than repeated in Main Body. Ownership must already be supplied by raw layout,
with consistent page/bounds and a non-ambiguous body asset. Unknown owners or
questionable crop geometry retain the text with `visual_text_ownership_unresolved`.
An external-caption warning alone does not invalidate known internal table cells;
the raw warning remains visible. Surrounding prose and Main Question stay intact.
For example, 2012 Q19 displays its introduction plus table once; Q38 retains its
already-correct raw body image and now has source-backed clean placement.

### Prompt tails and structured blocks

Existing unambiguous prompts retain their selection. The sentence-aware fallback
requires stored, distinct answer labels, question grammar, a completed tail and
no competing request. It handles prepositional/conditional openings, prompts
embedded after a setup sentence, and balanced parenthetical notes after `?`.
Period-ended requests additionally require imperative/interrogative grammar.
Data introductions, repeated table rows, quoted/reported questions, unbalanced
notes and incomplete answer-completion stems are not promoted just for ending
with punctuation. The raw text and uncertainty stay available.

Body/question text gains a blank line before an introduced block only when
at least two consecutive rows have compatible list, price, numeric or data
structure. Short table headings may precede those rows; ordinary intervening
prose blocks the rule. Recognized rows retain their line breaks. A colon alone
does not trigger spacing; existing blank lines are retained, and this rule does
not change answer-option or subpoint formatting.

The original Body / Prompt issue group supplied 65 resolved analogues out of
75 cases: trailing notes (2011 Q43/Q44, 2012 Q19/Q26, 2017 Q14/Q44), embedded
requests (2008 Q34, 2009 Q32, 2016 Q31/Q38), and qualified/conditional openings.
Detached notes in 2013 Q12 and 2016 Q50 also now stay with the prompt. Formatting
controls include 2011 Q37, 2010 Q8/Q31, 2020 Q7 and specimen Q19; compare the
stored Original Screenshot. Ten incomplete/corrupt/implicit stems remain flagged.

```powershell
$cleanHtml = 'inspections_clean\TSA_2011_q43-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA Oxford 2011.pdf' --year 2011 --question 43 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

Use `--question 37` and a new output filename for the price-block comparison.

## Traceability and limitations

Raw→clean alignment uses the stored body/visual associations, not the legacy
graphics detection note. A standalone initial question-number block is metadata;
only that exact anchor is skipped during alignment. An equal number elsewhere
in the body is retained. Older raw JSON containing interleaved page footers must
be reparsed first; cleaning does not silently skip unmatched structured text.
Q25/Q36 from 2020 retain body images and text choices, rather than becoming
image-answer questions. Test these alongside 2017 Q13, 2019 Q14/Q42 and 2021 Q38.
CID mapping/count mismatches and genuinely unknown visuals remain separate issues.

```powershell
& $parserPython -m parsers.blackstone 'acquisition\local\TSA Oxford 2020.pdf' --output-dir 'data\raw\blackstone' --overwrite --issues-report 'docs\RAW_PARSING_ISSUES.md'
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\CLEANING_ISSUES.md' --overwrite
$cleanHtml = 'inspections_clean\TSA_2020_q25-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA Oxford 2020.pdf' --year 2020 --question 25 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

Use question 36 with a new output filename for the patio comparison. Regression
coverage for these cases lives in `tests/test_blackstone_body_alignment.py`.

`*.clean.json` is separate, deterministic schema v1. Each record stores the
unchanged question ID/source key/page mapping, complete `raw_record` snapshot,
raw JSON absolute path/SHA-256/JSON pointer, warnings, text transformation hashes,
and line-level `content_accounting`. Body blocks retain raw block IDs/spans/page
coordinates. Assets retain their original paths, IDs, order, associations,
coordinates, and warnings; paths resolve relative to the **raw JSON**, not clean
JSON. Keep the original raw JSON/assets available; HTML embeds the images it
successfully reads and remains standalone after export.
An embedded prompt may partition one original line into two accounting entries
with the same line index and disjoint, contiguous structured spans. Each keeps
the original source-block evidence; every supplied line remains fully accounted
for, without deleting its contextual prefix.

### Derived answer crops

Cleaning uses existing raw option anchors, crop bounds, page size and render DPI;
it does not reopen PDFs or infer new option associations. A verified, left-side
letter is removed only in a bounded glyph window with a white isolation ring.
Small font-overhang expansion must not intersect graph primitives, axis labels,
captions or other stored text. Only fully white outer margins are then trimmed;
all remaining answer pixels are preserved, including labels to the letter's left.
If the letter was already outside the raw crop, its pixels are copied unchanged.
Raw CID glyph strings are retained; the already associated anchor's exact bounds
identify its glyph without performing a new text-decoding rule in cleaning.

Derived files live in `data/clean/blackstone/assets/<source-hash>/`, with raw asset
ID and derived-content hash in the filename. `options[].images[].path` remains the
raw reference; optional `clean_asset` adds the clean-relative path, both hashes,
raw asset ID/path, removed glyph rectangle, and pixel crop bounds. Original
screenshots and body graphics still use raw assets. Inspection never creates
assets; regenerate cleaning first. Missing derived files are reported, not
silently replaced. An unsafe derivation shows the explicitly labelled raw
fallback and `clean_option_crop_unresolved` in **Clean Answer Image Derivation**.

Foreign letters, multiple visuals/ambiguous associations, raw crop warnings,
overlapping text, non-white/touching glyphs, inconsistent scale or unsupported PNG
formats remain unresolved. No raw warning is suppressed by clean derivation.

`CLEANING_ISSUES.md` groups only clean-stage discoveries by category and counts
unique records. It does not copy raw warnings or claim they are solved. Missing
assets and changed/missing raw references are checked again during inspection
and report regeneration. Neither operation modifies raw or clean JSON.

Review unresolved implicit/multiple/corrupt prompts, unaligned layouts,
displaced punctuation (2020 Q12), and the remaining CID token (2021 Q7).
Unknown/shared raw visuals remain unresolved; cleaning cannot restore missing
content, fix crop boundaries, repair equations, or rerender missing screenshots.
Compare 2017 Q20, 2022 Q8, 2021 Q32/Q37 and decoded 2012 Q3 with their original
screenshots. No issue row is proof that the representation is faithful.
