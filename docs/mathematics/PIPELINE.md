# Mathematics: matdev source ingestion

Active domain: mathematics. Sources are the twelve local `math_1.pdf` through
`math_12.pdf` in `acquisition/local/mathematics/matdev`. A parser accepts arbitrary
local paths; acquisition location is provenance, not a parsing requirement.

## Independent stages

`python -m parsers.mathematics <PDF paths>` writes `data/raw/mathematics`.
It opens each source version once, preserving question-page text, character/font
geometry, question/option bounds, immutable source crops and the last-page answer
key. Page one is a cover; the last page is a key. Repeated URL/NUFYPET Math version
headers are excluded only from projections; original page content stays in RAW.

`python -m processors.matching.mathematics run <RAW JSON paths>` writes the separate
`data/merged/mathematics/questions.json`. Matching uses document SHA-256 and
question number, validates duplicate keys/labels, and never reads a PDF. Answers
come only from the extracted key. No mathematical solving or categorization runs.

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

The twelve-source run contains 360 questions and 360 key rows, 358 validated
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

## Running the relevant tests

The existing `.venv` uses the installed Python 3.13 interpreter and already contains
the dependencies pinned in `requirements.txt`, including pytest. A sandbox denial
of its base interpreter is not evidence that the environment needs recreation;
use the permitted external-process execution mode. Existing system pytest-temp and
cache directories may have incompatible permissions. Use disposable workspace paths:

```powershell
New-Item -ItemType Directory -Force tmp | Out-Null
& .venv/Scripts/python.exe -m pytest tests/test_mathematics.py tests/test_mathematics_radicals.py tests/test_mathematics_corrections.py tests/test_mathematics_raw_issues.py tests/test_question_rendering.py -q --basetemp tmp/pytest-mathematics -o cache_dir=tmp/pytest-cache
```
