# BMAT Section 1 RAW backtesting

BMAT is a separate source family. Acquisition, local PDF parsing, RAW exclusion
annotations, cleaning, matching and categorization remain separate stages.
No answers, explanations or normal TSA-style subcategories are inferred here.

The second refinement adds evidence-bearing `Drawing Inferences` and `Subpoints`
exclusions. Three full numbered propositions **and** combination-valued options
are required for `Subpoints`; a lone keyword or three unrelated bullets is not
enough. Explicit conclusion/assumption/flaw requests remain normal task intents
unless another BMAT-specific exclusion applies. Normal task attribution lives
in the independent [BMAT categorization stage](BMAT_CATEGORIZATION_BACKTEST.md).

## Reproduce (repository root, PowerShell)

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv/Lib/site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$bmatPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $bmatPython -m processors.bmat acquire
& $bmatPython -m processors.bmat raw data/input/bmat --output-dir data/raw/bmat --overwrite
& $bmatPython -m processors.bmat report --output docs/critical_thinking_problem_solving/bmat/BMAT_RAW_ISSUES.md
& $bmatPython -m processors.bmat inspect --year 2017 --question 1 --output inspections/critical_thinking_problem_solving/bmat/raw/2017_q001.html
& $bmatPython -m processors.bmat list --status parser_review
& $bmatPython -m processors.bmat list --type 'Shared Information Range'
& $bmatPython -m pytest -q tests/test_bmat.py
```

Acquisition is independently runnable as `python -m acquisition.bmat`; it obtains
only PMT Past Papers / Section 1 Question Papers, 2003–2021. The acquired
[manifest](../../../data/input/bmat/manifest.json) preserves every requested year,
URL/path/hash/status/error. Matching existing hashes prevents duplicate downloads.
TLS verification stays enabled, using OS trust roots plus the requests trust
bundle. No mark schemes, other sections, mock papers or explanations are fetched.

The parser independently accepts arbitrary existing local PDF filenames through
`python -m parsers.bmat PATH`. Cover content, not acquisition URL, identifies the
BMAT/Section 1/year/count. An explicit API year must not contradict the cover.
`--no-assets` is a diagnostic-only probe, not a completed usable RAW run.

## Inspection

Read canonical RAW JSON and referenced assets directly for development. The
`inspect` command above is an optional user-requested export, not a prerequisite
for reading a question. Add `--all-html` only for an explicitly requested batch;
use `--year`, `--question`, `--status` and `--type` to bound it.

- [All questions: filter by year/status/type](../../../inspections/critical_thinking_problem_solving/bmat/raw/index.html)
- [Machine-readable current status](../../../inspections/critical_thinking_problem_solving/bmat/raw/status.json)
- [Current skip/defect report](BMAT_RAW_ISSUES.md)
- [Cross-layer validation](../../../inspections/critical_thinking_problem_solving/bmat/raw/validation.json)

Each HTML shows RAW body/prompt/options, resolved body and option crops in
separate sections, unresolved ownership separately (never silently in Main Body),
original question previews, exclusion evidence, parser issues and exact raw text.
Shared information retains its declaration/page/bounds, affected identities and
unaltered source page text, including introductory material not owned by one item.
The skip tag counts overlap; the total skipped question count is deduplicated.
Skipped questions may independently retain genuine parsing issues.

## Validated layout families / controls

- Early aptitude papers: 2003 has 40 items and genuine written-response tasks.
- Most aptitude papers have 35 items, variable A–D through A–H choice counts,
  shared-information intervals and occasional cross-page items.
- Mirrored print margins: number-column tolerance follows label glyph width;
  numbered body statements must not replace the actual number column.
- Shifted CID-font pages (e.g. 2013): only the verified map is interpreted;
  unknown glyphs remain a review issue. Literal/CID spaces must not eat words.
- Centred multiline text labels: first lines are reassigned only through aligned
  label geometry, complete sequences and source-line spans; initial candidates stay raw.
- Above-centred picture labels: complete native-object ownership can recover
  options. Shared/crossing objects or touching neighbour crops remain reviewable.
- Alphabetic display/plot ticks (2009 Q3, 2020 Q14, 2021 Q8) are body/internal data,
  not extra choices. Lowercase relative clauses inside answers are not new prompts.
- Thinking Skills (2020–2021): 32 items; kept separate from the older count rules.

Pilot inspection used 2003/2013/2017/2020, then added mirrored-margin and
centred-label cases in 2004/2008/2011. Full-corpus processing follows that pilot;
remaining problems are quarantined, not forced into successful normal records.

## RAW contract and exclusions

The common raw fields/source key/page spans/native objects/layout/crop metadata
follow the existing contracts. BMAT adds:

- `raw_components`: unnormalised body/prompt projection, with method/uncertainty;
- `option_audit`: cover write-in permission, possible label evidence, native
  graphics in the answer area, extraction completeness and boundary evidence;
- `bmat_filter`: rule version, all evidence-bearing types, deterministic primary
  type, reason, confidence and `skip_from_pipeline`;
- `parsing_issues`: independent concrete defects with manual-review requirements;
- `pipeline_status`: `raw_ready`, `parser_review` or `intentional_skip`;
- document `shared_information_ranges`, unassigned source spans and observed
  cover/layout/number-column metadata.

Exclusion families: No Question, Shared Information Range, Variable-related
question, Several correct answers, Explanation, Complete the text, too long,
Source, Necessary and Sufficient Conditions. No normal PS subtype is assigned.
No Question requires source response evidence, not merely missing extraction.
One selected combination-valued option is not several independently selected
choices. Full-page exclusion requires one complete item, actual content-height
coverage >60% (ending at the final option bottom), and no continuation from another page; padded crops/text length
alone supply no proof. X as multiplication/object labels, ordinary mentions of
explanation/source, and lone underscores/necessary are negative controls.

`processors.bmat.contracts.eligible_records` excludes skips, parser defects and
documents with unresolved numbering. Separate [BMAT cleaning](BMAT_CLEANING_BACKTEST.md)
now consumes corrected stored RAW and retains skips/defects for inspection.
The independent matching/categorization entrypoints retain this eligibility and
provenance rather than rediscover tags. Matching consumes only issue-free retained items.

Original question previews now use the union of owned text, body visuals and all
answer-option geometry, with neighbor/shared-range barriers and font-relative padding.
Original preview candidates remain preserved. Compact extracted range declarations
such as `Questions 19–22refer ...` are recognized without swallowing the next shared
stimulus into the preceding question. Native round glyphs become readable bullets
only with outline proof and a repeated aligned list following a colon; raw strings stay exact.

## Reuse and remaining limitations

`parsers.bmat.reuse` narrowly wraps existing page extraction, verified CID map,
native graphics/geometry, rendering/crops, layout, PNG QA and raw validation.
TSA segmentation/metadata/cleaning is not invoked. The shared renderer accepts
an optional asset-name prefix; its default TSA behavior is unchanged. Source
files and previous generated assets are never deleted by these commands.

RAW is not declared complete while structural/encoding/visual issues remain in
the report. Such records stay quarantined for manual source comparison. Existing
TSA raw/clean/matching/categorization data must remain hash-identical.

## Stabilization audit

RAW v2 adds font-scoped embedded-cmap/zero-ink spacing evidence, complete
anchor-to-visual ownership, spatial-math crops, paragraph crop barriers,
PDF-matrix-backed axis bounds, exact-span visual/admin exclusions and contextual
final prompts. Original page strings and old PNGs remain intact.
`layout_blocks[].readable_text` is additive, not a replacement for exact
`text`/`raw_span`. `raw_components.body_equals_question` distinguishes the
`Equals question` sentinel from literal source content.

Full-page detection was refined from 65% to 60% of usable height, still requiring
one complete, non-continuing question on that page. This includes the verified
compact 2017 Q18 layout; text length alone is not evidence.

[Before/after audit](../../../inspections/critical_thinking_problem_solving/bmat/raw/stabilization/review.json) records all
82 initial genuine issue questions. The source's water-ice prompt is 2004 Q13,
not Q3. 2014 Q7 retains faithful fraction images, not guessed text. Residual
2021 Q8 graph fragments and unknown fonts are not declared resolved.
