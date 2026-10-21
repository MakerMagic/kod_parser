# Blackstone raw → clean inspection

Answer-completed colon prompts are recognised only with final-clause grammar,
parallel textual answer completions and no intervening aligned body visual.
2010 Q32 and 2012 Q16 recover Main Question; table/list/data lead-ins remain body
context. 2014 Q50's separate RAW option-boundary defect is now repaired upstream.
Raw text/options/assets stay unchanged by cleaning.

Unpunctuated conditional completion prompts also require an unfinished request,
parallel substantive text options and no intervening body visual. A final line or
copula alone is insufficient. 2016 Q12's complete scheduling request is retained
as Main Question without inventing punctuation or moving preceding constraints.

Known prompt word joins are repaired conservatively in CLEAN: a modal joined to
an impact verb immediately targeting an argument (`wouldweaken`), or an auxiliary
joined to `not` before a truth/possibility predicate (`isnot true`). An interrogative
prompt context is required; this is not a general dictionary word splitter.
2009 Q17/Q14 retain the exact original tokens in their raw snapshots and source.

Run from the repository root. Cleaning reads stored raw JSON/PNG assets only;
it never opens PDFs, acquires files, matches answers, or categorizes questions.

Read canonical CLEAN/RAW records directly during development. The HTML commands
below are optional user-requested exports, not a way to reconstruct question data.

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
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\critical_thinking_problem_solving\tsa\CLEANING_ISSUES.md'
```

For a repeat run, add `--overwrite`; it replaces only clean JSON belonging to
the same raw input. Output inside a raw input directory is rejected. Input
may be one or more explicit raw JSON files or directories of `*.raw.json`.

Regenerate clean JSON and derived answer PNGs after upgrading the cleaner:

```powershell
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\critical_thinking_problem_solving\tsa\CLEANING_ISSUES.md' --overwrite
$cleanHtml = 'inspections/critical_thinking_problem_solving/tsa/clean\TSA_2017_q20-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA Oxford 2017.pdf' --year 2017 --question 20 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

```powershell
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 8
$cleanHtml = 'inspections/critical_thinking_problem_solving/tsa/clean\TSA_2022_q08-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 8 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
```

HTML is universal, self-contained, offline, and contains embedded PNGs. Exports
require a new filename. `--format json` exports the full clean/raw comparison.
Selectors include `--session`, `--paper`, `--variant`, `--section`, and
`--question-id`. Ambiguous matches fail instead of picking a record silently.

```powershell
& $parserPython -m processors.normalization.blackstone.backtest report --clean-json 'data\clean\blackstone' --output 'docs\critical_thinking_problem_solving\tsa\CLEANING_ISSUES.md'
& $parserPython -m pytest -q tests/test_blackstone_cleaning.py tests/test_blackstone_clean_structure.py tests/test_blackstone_option_asset_crops.py tests/test_blackstone_backtest.py
```

Raw workflows retain their existing module/commands. The raw report is now
`docs/critical_thinking_problem_solving/tsa/RAW_PARSING_ISSUES.md` (parser default: `OUTPUT_DIR/RAW_PARSING_ISSUES.md`).
Existing raw QA exports moved to `inspections/critical_thinking_problem_solving/tsa/raw/`; the raw guide already had
a clear name, [RAW_PARSER_BACKTEST.md](RAW_PARSER_BACKTEST.md). Explicit legacy
report paths still work. Cleaning never edits raw JSON or referenced raw PNGs.

The RAW grouping upgrade for 2019 Q36 / 2016 Q37 needs regeneration, not a clean
merging rule. Inspect these with the same CLI selectors (`--year 2019 --question
36` / `--year 2016 --question 37`, and the corresponding source filename). Main
Body contains one complete pattern plus a separate table for Q36, and two
complete mushroom diagrams for Q37. RAW correctly places the sentence between
Q37's diagrams; an independent, pre-existing CLEAN split still places "When I
looked..." in Main Question rather than between those diagrams. That presentation
issue remains unresolved, not a successful grouping fix. Old unreferenced raw
PNGs remain for traceability; regenerated JSON determines the displayed assets.

## Initial rules and evidence

### Explicit pinned body visual: 2022 Q44

The user's original combined sixteen-card PNG is versioned under
`processors/normalization/blackstone/pinned_sources/`, with an explicit mapping
in `body_visuals.json`. It is bound to the source PDF SHA-256, full question key,
page and approved source asset indices. This is one approved exception, not a
general graphics-merging rule. Cleaning writes an exact PNG copy under
`data/clean/blackstone/assets/pinned/` and replaces only those sixteen consecutive
body blocks with one combined visual. The separate game-history table remains.
Original raw assets, original raw snapshot, warnings and source-block references
remain unchanged. `body_visual_overrides` and asset `provenance` record the
approval, mapping/image hashes and all replaced raw references. Pinned paths use
`path_base="clean_json_parent"`; original asset paths still resolve from raw JSON.

The mapping is applied on every clean write, so raw reparse followed by cleaning
and matching regeneration retains the composite. Missing/changed images, source
hash mismatch or changed body grouping keep the original structure and report
`pinned_body_visual_unresolved`; inspection also checks live pinned references.
Do not edit one generated JSON file or delete the preserved source-derived assets.

```powershell
& $parserPython -m parsers.blackstone 'acquisition\local\critical_thinking_problem_solving\tsa\TSA_2022.pdf' --output-dir 'data\raw\blackstone' --issues-report 'docs\critical_thinking_problem_solving\tsa\RAW_PARSING_ISSUES.md' --overwrite
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone\TSA_2022-aeb958e80a18.raw.json' --output-dir 'data\clean\blackstone' --issues-report 'docs\critical_thinking_problem_solving\tsa\CLEANING_ISSUES.md' --overwrite
$cleanHtml = 'inspections/critical_thinking_problem_solving/tsa/clean\TSA_2022_q44-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $parserPython -m processors.normalization.blackstone.backtest inspect --clean-json 'data\clean\blackstone' --source 'TSA_2022.pdf' --year 2022 --question 44 --format html --output $cleanHtml
Invoke-Item -LiteralPath $cleanHtml
& $parserPython -m pytest -q tests/test_blackstone_pinned_body.py
```

After a clean rerun, rebuild the dependent 2022 matched output using both answer
inputs in [MATCHING_2022_BACKTEST.md](MATCHING_2022_BACKTEST.md), then inspect Q44.
The raw parser deliberately retains its original sixteen source-derived crops.
The pinned composite is a clean-stage effective representation only.

### Conservative text rules

- NFC composes canonical Unicode equivalents; it does not apply NFKC, replace
  mathematical symbols, guess CID maps, or remove hyphens. Accents/composed
  controls and valid `½`, `×`, `−`, and currency characters are regression tested.
- Strip line-edge whitespace and collapse common spaces/tabs/NBSP. Repeated
  trailing whitespace was inspected across 2012 Q3/Q4/Q5, with unaffected
  2010/2022 controls.
- Retain established lowercase wrap rules. In question/body/prompt prose only,
  also join capitalized continuations when exact raw-span alignment, same-page
  consecutive text blocks, component continuity, normal relative line spacing,
  indentation and compatible text heights support a wrap. An unfinished phrase
  plus a grammatical connector or a filled source line is required; neither
  capitalization nor missing punctuation alone authorizes joining. No country/
  name dictionary is used. Options/subpoints retain their existing rules.
- Preserve blank paragraphs, list/data rows, graphics, question boundaries and
  hyphen-ended lines. A newly joined name cannot enable an additional lowercase
  join that the previous rules would have rejected. Potential continuations
  without verified text/geometry remain unchanged, with
  `prose_line_wrap_unresolved` when syntactic evidence warrants review.
- The declared `geometry_backed_capitalized_prose_wraps` rule is reproducible
  from raw JSON alone; older clean rule sets remain readable. Regenerate clean
  JSON using the repeat command above, not by reparsing PDFs. Check 2019 Q33
  (`into the Netherlands and Switzerland`), 2012 Q16, 2016 Q12 and specimen Q18;
  their unrelated missing-prompt warnings are not resolved by text joining.
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
$cleanHtml = 'inspections/critical_thinking_problem_solving/tsa/clean\TSA_2011_q43-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
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
& $parserPython -m parsers.blackstone 'acquisition\local\critical_thinking_problem_solving\tsa\TSA Oxford 2020.pdf' --output-dir 'data\raw\blackstone' --overwrite --issues-report 'docs\critical_thinking_problem_solving\tsa\RAW_PARSING_ISSUES.md'
& $parserPython -m processors.normalization.blackstone --raw-json 'data\raw\blackstone' --output-dir 'data\clean\blackstone' --issues-report 'docs\critical_thinking_problem_solving\tsa\CLEANING_ISSUES.md' --overwrite
$cleanHtml = 'inspections/critical_thinking_problem_solving/tsa/clean\TSA_2020_q25-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
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
