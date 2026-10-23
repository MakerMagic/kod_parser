# Mathematics: RAW source ingestion

Active domain: mathematics. Sources are the twelve local `math_1.pdf` through
`math_12.pdf` in `acquisition/local/mathematics/matdev`. A parser accepts arbitrary
local paths; acquisition location is provenance, not a parsing requirement.
The additional eight trial PDFs are in `acquisition/local/mathematics/sky (trial)`.

## Independent stages

Current work: categorize issue-free mathematics CLEAN records using the official
NUET specification; see `CATEGORIZATION.md`. RAW, cleaning and matching remain
independent, unchanged dependencies. The trial RAW sources are `Test_1.pdf`–`Test_8.pdf` in
`acquisition/local/mathematics/sky (trial)`; their page 1 is always excluded.

`python -m parsers.mathematics <PDF paths>` writes `data/raw/mathematics`.
It opens each source version once, preserving question-page text, character/font
geometry, question/option bounds, immutable source crops and any source answer
key. Page one is a cover; the final page is excluded only when it is an answer
key. Repeated URL/NUFYPET Math version
headers are excluded only from projections; original page content stays in RAW.

For trial sources, cover text `Trial SET #n (math)` provides the source identity
together with the PDF hash. The last page is excluded only when it actually has
an answer-key heading; Tests 1–7 end with questions, while Test 8 has a partial
native key. No external answer file is read by RAW parsing. Pass the eight
`Test_n.pdf` paths explicitly, or the trial directory, to the same parser CLI.

Trial numbered anchors use printed punctuation, a coherent left margin and
increasing source numbers rather than a font name. Completed preceding options
and the nearest visual cluster determine a leading image's ownership by the next
question; its original position is retained in the ordered body. Connected vector
hook/riser/vinculum paths with enclosed glyphs are recognized as radicals and
passed through the existing LaTeX reconstruction. White PDF background rectangles
are not figures. Legacy mathematical objects use source coordinates and text
matrix baselines because their PDF stream order/font boxes differ from reading
order. Unsupported layouts remain explicit RAW findings.

The existing local label OCR is used only to observe embedded question numbers
or option labels; it never supplies mathematical text. Where available, the
already-installed bundled Node/Tesseract runtime is selected ahead of an
incompatible system Node. Raster-only question/formula content retains diagnostic
assets and `raster_math_unverified`; no formula is guessed from ordinary OCR.
RAW backtesting: `python -m parsers.mathematics.backtest` (see `BACKTEST.md`).

`python -m processors.matching.mathematics run <RAW JSON paths>` writes the separate
`data/merged/mathematics/questions.json`. Matching uses document SHA-256 and
question number, validates duplicate keys/labels, and never reads a PDF. Answers
come only from the extracted key. No mathematical solving or categorization runs.

`python -m processors.normalization.mathematics --raw-json data/raw/mathematics`
writes `data/clean/mathematics/questions.json` and `validation.json`. It accepts
only `extraction_status: extracted` records without RAW findings. Existing valid
CLEAN rows are reused after source-content comparison; only their document-level
RAW reference is refreshed when another question changed the source JSON hash.
New rows include a per-question RAW hash for subsequent reuse. Execution counts
are printed by the CLI, not stored as run-dependent canonical data.

The ordered block schema is preserved. CLEAN version 5 reconstructs prose wraps
using stored glyph geometry and request grammar, reusing the TSA/BMAT whitespace
normalizer. Paragraph gaps, lists, aligned rows and mathematical blocks remain
structural boundaries. It removes a physical `break_before` only when the block
continues unfinished prose; display mathematics and separate equations remain
intact. LaTeX strings, assets, lists, geometry, IDs and RAW evidence remain intact.
`content` retains the full stream; `main_body`/`main_question` are lossless context
and task projections. A task is an ordered block array; genuine absence is null.
The cleaner recognizes interrogative, imperative and answer-completed requests;
math is opaque during grammar detection. A non-whitespace token ledger verifies
no content loss, duplication or mathematical rewriting. Versioned caching reruns
older CLEAN projections after this shared structural correction. Version 5 also
capitalizes recognized prose starts in Main Question, closes terminal prose
commas at component boundaries, and applies the same conservative reflow to
answer text. Inline commas, variables, LaTeX, lists and equations are preserved.
The full content stream receives the same verified one-character prose edits as
the body/task projections. Existing category and explanation decisions may be
rebound only after proving these exact formatting edits, unchanged mathematics,
unchanged answers/assets/identity, and unchanged classifications/explanation text.
`CLEANING_BACKTESTING.md` and `CLEANING_ISSUES.md` are generated by the CLI.
No formula fragments or
duplicate-looking content are merged without source evidence. Encoding artifacts
are retained and reported with their block path. `cleaning_issues` is separate
from RAW issues; failed input validation is retained for review, not marked clean.
Excluded questions and exact reasons appear in the compact validation JSON.
This stage does not read PDFs or modify RAW or existing matching data.
Consumers must distinguish `cleaning.status: cleaned` from `review`; review
records are retained with `cleaning_issues` and are not approved clean output.
The cleaning CLI exits 1 when review records exist, after writing both outputs.

Historical incremental CLEAN snapshot before the structural correction:
600 RAW questions, 557 eligible, 556 cleaned,
1 review and 43 excluded for upstream findings. The run reused 350 valid CLEAN
rows and cleaned 206 new rows. The existing review remains `math_9.pdf` Q1:
`empty_content` at `content` (RAW contains no main-content blocks). No new
cleaning issue was introduced. A repeated run preserves both output files
byte-for-byte and leaves RAW unchanged. Current counts and exact findings are
generated in `CLEANING_BACKTESTING.md` / `CLEANING_ISSUES.md`.

`python -m processors.matching.mathematics retry` uses existing merged records and
their stored RAW/key references. It invokes the existing matcher only for records
without a validated matched answer and writes `retry_validation.json` beside the
merged output. Already valid matches are preserved verbatim. A known key letter
does not become a validated answer while extracted options are missing; such a
record retains its precise matching issue. Cleaning eligibility is independent of
matching, and retrying matching does not admit RAW-issue questions into cleaning.

The second set uses the supplied `acquisition/local/mathematics/sky (trial)/Answers 1-8.txt`
answer key. Apply it by source filename and question number with
`.venv\\Scripts\\python.exe -m processors.matching.mathematics.supplied`. This
rebuilds only Test 1–8 rows from their current RAW records in the existing merged
projection, validates each key label against the extracted options, preserves
agreeing valid answers, and retains
unverifiable labels as candidates with matching issues. The source key is
deterministically represented in `data/merged/mathematics/second_set_answer_key.json`;
scoped validation and generated `MATCHING_BACKTESTING.md` / `MATCHING_ISSUES.md`
are under `docs/mathematics/second_set/`.

For an explicitly authorized repair of stale matching records, use
`python -m processors.matching.mathematics.refresh --raw <RAW.json>
--answer-key <supplied-key.json> --question N --validation <validation.json>
--docs-dir <scoped-docs-directory>` (repeat `--question`). It verifies the supplied
key's document identity and image hash, checks every transcribed answer against
the native key, and rebuilds selected rows with the existing RAW matcher. It
preserves every unselected row and stops on key/identity/option conflicts. The
scoped validation records the selection and key evidence and generates its own
MATCHING Markdown pair. It does not reparse RAW or modify CLEAN/categorization.

## Formula fidelity and schema

Ordered content blocks use `type: text` with exact prose, `type: math` with a
delimiter-free `latex` string plus `display` boolean, or `type: visual` referring
to a genuine source image/diagram asset. `display: true` on a visual makes it a
separate body block; `break_before: true` preserves evidenced source block breaks.
Schema version 2 also supports `type: list`, `ordered` and `items[].content` with
the same inline content types. Bullet-marker glyphs remain in the list's source
evidence. `type: unresolved_math` retains `raw_text` (when native), source geometry
and `diagnostic_asset_id`, with an explicit RAW issue; the diagnostic crop is not
an accepted image answer or a substitute for transcribed mathematical content.
This is the sole mathematics format. The inspection adapter
renders this supported LaTeX subset as native MathML, not exposed delimiters or
plain LaTeX. Inline and display math remain distinct.

Native PDF glyphs/fonts and geometry are preferred. Fractions require evidence of
a rule separating numerator/denominator; scripts require measured baselines.
Fraction-slash operands use raised-left/lowered-right source glyph geometry;
inequalities retain their source operators. Radical extents use the complete
vinculum and radicand, not ordinary font line height. Enclosing fraction separators
prevent a radical from borrowing a bar from a different numerator/denominator.
Stored formula bounds and source crops include supported rules above glyph boxes.
Uncertain delimiter scope remains an issue rather than an accepted transcription.
Literal unbarred `√` notation uses explicit balanced parentheses or an adjacent
same-baseline numeric operand; nested parentheses are preserved. This does not
override ambiguous drawn-vinculum evidence or infer missing mathematical scope.

Unknown glyphs, uncertain grouping or unsupported structures retain diagnostic
source evidence with an explicit issue rather than a guessed expression. Mathematical equivalence
is not permission to rewrite the source. Syntax validation is separate from source
fidelity; valid LaTeX alone does not certify correct extraction.

RAW envelope: domain/source, source identity/hash/path/metadata, page records,
questions, answer_key and issues. A question has deterministic `id`, source
document ID, number, page regions, ordered `content`, labelled `options`, assets,
method/evidence and issues. The matched projection adds a validated nullable
`correct_answer`, key reference and matching status/issues. No TSA/BMAT categories
or difficulty are introduced. IDs use source content identity and question number,
not filesystem order or mutable output position.

Issues use `code`, `reason`, question/page/field and method/evidence when applicable.
Start with structural, formula, visual and key/matching uncertainty supported by
actual findings. JSON is authoritative; a concise issue summary derives from it.
Source crops are immutable evidence and user comparison assets, not a substitute
for structured extraction. Formula fallbacks stay visibly unresolved.

## Local extraction methods and limits

Uses existing pdfplumber/PDFium/Pillow, not a new PDF or ML framework. Native
Cambria Math/Symbol glyphs, fraction bars, radical overbars and measured script
sizes/baselines support fractions (including fractional exponents), powers,
subscripts and indexed/nested roots. Unknown layouts, including unsupported
multi-baseline structures, are explicit `uncertain_formula` fallbacks. The
`geometry_checked` label means glyph/layout and syntax checks, not a mathematical
proof or a promise of perfect recognition. Original glyphs and crops stay available.

Options use actual observed labels, including A–D, A–F and A–H, multirow grids and
native-text tables. Inline raster formula pictures above their letters stay owned
by the corresponding option. Native table borders do not displace cell text.

Optional raster-caption OCR uses the already bundled Tesseract.js runtime and a
locally saved English model, or Windows OCR. It is **not** mathematical OCR and
never supplies formula text. Model provenance/hash is in
`../../parsers/mathematics/ocr_model.json`; the local model is
`data/input/mathematics_ocr/eng.traineddata` (or `MATHEMATICS_OCR_MODEL_DIR`). No
parser or matcher downloads anything. Absent or uncertain OCR leaves explicit
issues, full visual evidence and an unvalidated option set, never invented letters.
OCR evidence is cached against the source asset hash. RAW caching also checks
the source SHA and extraction implementation fingerprint; use `--overwrite` for
intentional regeneration.

For bounded corrections, pass `--overwrite --question N` (repeat `--question` for
each affected record). This requires an existing RAW source, re-extracts only those
questions, and preserves all other records plus original page/key data. Per-question
implementation provenance is stored in `extraction.question_updates`; the original
envelope fingerprint is not falsely changed to imply a complete source reparse.

## Reproducible stages

```powershell
python -m parsers.mathematics acquisition/local/mathematics/matdev
python -m processors.matching.mathematics run data/raw/mathematics
python -m processors.matching.mathematics validate
```

### Earlier baseline and stored downstream snapshots

The original twelve-source matdev baseline contained 360 questions and 360 key rows, 358 validated
answer matches, no duplicate identities and no orphan keys. Header-filtered native
question-page glyph coverage has no gaps or duplicated ownership. There are 2,246
accepted LaTeX blocks and 12 uncertain formula blocks across 6 questions; their
diagnostic source crops remain unresolved. Six compact raster formulas in the explicitly
formula-based `math_6` Q27 also remain untranscribed, with `raster_math_unverified`
findings; ordinary English OCR is not presented as mathematical recognition.
Two additional graph questions (`math_2` Q7,
`math_3` Q27) retain raster options but lack reliable separate option labels, so
their answers remain unmatched. Thus 9 unique questions retain 20 RAW findings, not 360
fully approved questions. `validate` intentionally exits nonzero for the two
unresolved option structures. Canonical per-source metrics and findings are in
`data/merged/mathematics/validation.json`. RAW-stage findings are listed in
`RAW_ISSUES.md`, generated directly from `data/raw/mathematics/*.raw.json` with
`python -m parsers.mathematics.raw_issues`. It includes only question-linked RAW
issues; matching findings remain in the merged structured data and are not mixed
into this RAW report.

The earlier matdev cleaning projection considered all 360 records: 351 eligible, 350
successfully cleaned, 1 review and 9 excluded due to RAW findings. The review is
`math_9.pdf` Q1 (`empty_content`, field `content`): the stored RAW main content
contains no blocks. Its source data is preserved for a separate RAW correction.
The unmatched-only retry processed math_2 Q7 and math_3 Q27; both remain unresolved
because extracted options are absent, despite unique stored key rows A and B.
All 358 existing valid matched records remain unchanged.

The trial RAW run adds 240 questions (30 per PDF). The canonical matched
projection now contains all 600 questions from the twelve matdev and eight trial
sources. The trial sources contribute 24 embedded answer-key rows; 5 answers
validate against complete options, while 235 questions remain unmatched. The
existing 358 matdev matches are preserved. The initial trial RAW findings
totalled 130 across 66 questions: 60 `uncertain_formula`,
31 `option_boundary`, 28 `raster_math_unverified`, 3 `ocr_question_number`,
1 `content_assignment`, 1 `unmapped_glyph`, and 6 `answer_key_structure` findings
for blank native key rows. All are question-linked with page, field and reason.
The initial combined RAW index included the original 20 findings as well (150 total).
All 21 supplied leading-image regressions pass; Test 3 Q12 remains a single body
image. No formula is supplied by raster English OCR. Unsupported native layouts
and raster mathematical payloads remain explicitly unresolved for later RAW work.

## Native formula-region corrections

Current RAW: 33 issue-bearing questions corrected, 59 findings resolved. The
generated index now contains 91 findings on 43 questions: 19 matdev findings on
8 questions and 72 trial findings on 35 questions. No issue-free question was
selected for regeneration; existing cleaning/matching JSON files were preserved.

The diagnostic image is generated **after** native formula recovery; it is not
input to OCR. A missing numerator in that crop can originate earlier: an answer
boundary cut through a fraction, or PDF stream/font runs split one expression.
Fixed padding and higher rendering resolution cannot restore that ownership.
Native glyph/rule unions were selected over those approaches and raster math OCR:
the source already contains the exact characters and separator geometry.

Option regions expand to evidenced numerator/denominator extents around their
own separator. Native text-matrix baselines and horizontal advances determine
fraction/script membership when skewed font boxes overhang the separator; full
original glyph boxes and supported rules still determine source crops. Optional
glyph evidence `pdf_text_x0`/`pdf_text_x1` preserves those advances. Targeted RAW
updates add this evidence only for selected questions, preserving other records.
Repeated spaces inside mathematical font runs do not split expressions; source
line breaks are measured from the last visible glyph rather than blank font boxes.

Systems use complete native brace pieces and observed relation baselines to emit
one `\begin{cases}` expression. This preserves grouping that separate prose lines
would lose, without recognizing an unbraced ambiguous matrix. Stretched Adobe
Symbol parentheses are assembled only from complete, aligned source pieces;
scripts stay attached using text-matrix geometry rather than substitutions.
Duplicate vector outlines of an already recognized radical are not image answers.

For side-by-side condition diagrams, a contiguous punctuated answer-label run is
stronger evidence than bare letters inside the drawing. Condition text overlap
and complete figure geometry determine body ownership, rather than the nearest
option. Independent unsupported summations, wrapped layouts or integral limits
retain RAW issues. RAW corrections do not refresh downstream matching references;
regenerate dependent projections only in a separately authorized stage task.

## Raster-backed RAW recovery

Raster-only questions are recovered only from the existing source-preview crop.
The local Pix2Text worker segments the crop into body, option, formula and visual
regions, isolating a printed question number only when its source glyph pixels do
not touch adjacent content. Option labels must form one directly observed A–E
sequence. Candidate text is independently reread from its source crop; formulas
are compared with the separate local PP-FormulaNet model. LaTeX is syntax-checked
and locally rendered back for diagnostic comparison. Model confidence or valid
LaTeX alone never verifies source fidelity. Unmatched, unsupported or clipped
components remain RAW issues with source traceability; detected genuine visuals
remain separate assets. Neither source pages nor question crops leave the local
machine.

The optional verifier uses an isolated environment (`requirements-mathematics-
formula-verification.txt`) and public PP-FormulaNet model weights:

```powershell
python -m venv .venv-math-formula
.venv-math-formula/Scripts/python.exe -m pip install -r requirements-mathematics-formula-verification.txt
.venv-math-ocr/Scripts/python.exe parsers/mathematics/raster_formula_setup.py --download
```

Run only selected RAW issue files; omit `--apply` for a dry run. `--apply` writes
only a fully verified, issue-free candidate. A candidate requiring review is
withheld from canonical RAW, and its existing issue remains authoritative.

```powershell
python -m parsers.mathematics.raster --raw-json <RAW JSON paths> `
  --ocr-python .venv-math-ocr/Scripts/python.exe `
  --secondary-python .venv-math-formula/Scripts/python.exe `
  --formulanet-model-dir data/input/mathematics_ocr/formulanet_plus_s
```

## Running the relevant tests

The existing `.venv` uses the installed Python 3.13 interpreter and already contains
the dependencies pinned in `requirements.txt`, including pytest. A sandbox denial
of its base interpreter is not evidence that the environment needs recreation;
use the permitted external-process execution mode. Existing system pytest-temp and
cache directories may have incompatible permissions. Use disposable workspace paths:

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null
& .venv/Scripts/python.exe -m pytest tests/test_mathematics_formula_regions.py tests/test_mathematics_radicals.py tests/test_mathematics_corrections.py tests/test_mathematics_trial_raw.py tests/test_mathematics_raw_issues.py -q --basetemp tmp/pytest-mathematics -p no:cacheprovider
```

The general RAW checks in `test_mathematics.py` can be added with
`-k 'not persisted_full_corpus_coverage_and_honest_unresolved_cases'` while the
matching snapshot is stale. That excluded check verifies the downstream merged
projection and belongs to its authorized refresh, not to RAW-only correction.
