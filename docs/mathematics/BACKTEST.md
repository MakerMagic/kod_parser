# Mathematics inspections

Read canonical JSON directly during development. Generate HTML only on request or
for the small representative acceptance sample required by the mathematics task.

## RAW-only inspection

The RAW entry point reads stored `mathematics_raw` JSON directly and reuses the
same report adapter and shared HTML components. It does not invoke matching.

```powershell
python -m parsers.mathematics.backtest --test 3 --question 12 --output inspections/mathematics/raw-chain.html
python -m parsers.mathematics.backtest --test 1 --question 24 --width 1350 --output inspections/mathematics/raw-roots.html
python -m parsers.mathematics.backtest --issues --sample 3 --seed 7 --output inspections/mathematics/raw-review.html
python -m parsers.mathematics.backtest --id <stable-id> --output inspections/mathematics/raw-selected.html
```

`--raw-json` accepts stored RAW files/directories (default `data/raw/mathematics`).
`--test` selects the content-derived trial-set number; `--source`, `--question`,
`--id`, `--issues`, `--issue-code`, `--sample`, `--seed` and the existing width
presets are available. At least one selector is required. A test-only selection
previews that test, not the full corpus. Output is disposable and must be a fresh
path outside canonical data. Raster text/formulas without verified transcription
appear as unresolved diagnostic evidence, rather than accepted image answers.

## Existing matched-data inspection

```powershell
python -m processors.matching.mathematics inspect --source math_1 --question 4 --output inspections/mathematics/example.html
python -m processors.matching.mathematics inspect --id <stable-id> --output inspections/mathematics/selected.html
python -m processors.matching.mathematics inspect --issues --sample 3 --output inspections/mathematics/review.html
python -m processors.matching.mathematics inspect --issue-code uncertain_formula --sample 2 --seed 7 --output inspections/mathematics/formulas.html
```

Selectors intersect; sampling is deterministic with a configurable seed. No
selector means no export. One disposable HTML contains only the selection. It
shows structured prose/formulas/options, source crops, key answer and relevant
extraction/matching evidence. Formula syntax errors and uncertain source recovery
are displayed separately. Images preserve aspect ratio. No TSA/BMAT taxonomy
fields appear. Output must be a fresh path outside canonical data; an inspection
never changes the stored records or opens a PDF.

Mathematics uses the shared TSA/BMAT preview shell, answer cards, detailed-report
sections and `processors/pre_final/preview.css`; its adapter supplies RAW ordered
blocks without inventing categorization or AI-explanation fields. Use `--width 1166`
or `--width 1350`. Lists and standalone visual blocks are rendered from canonical
structure, not question-specific HTML corrections. Unresolved mathematical source
is labelled and its crop appears only as diagnostic evidence, never as an accepted
image answer. Matching remains the existing exact-key projection.

The supported LaTeX subset is converted to native MathML (fractions, superscripts,
subscripts and radicals), with no CDN, external font or JavaScript requirement.
Use a current MathML-capable browser such as Edge. Unsupported extraction remains
an explicit unresolved block with diagnostic source evidence. Syntax validity and
source fidelity are distinct. Text is escaped, line breaks retained, and images
use `max-width:100%; width:auto; height:auto; object-fit:contain`.

One disposable nine-question acceptance preview covers prose, fractions, powers,
indexed/nested roots, a fractional exponent, a formula fallback, graph options and
an eight-choice table and unresolved raster formulas. Its MathML/image layout was tested in headless Edge at
1166 and 1350 px; no external requests, distortion or horizontal page overflow.
The optional `tests/browser_mathematics.cjs <selected.html>` smoke uses the existing
Playwright runtime and installed Edge. It can also accept a loopback HTTP URL.
If that runtime is outside Node's search path, set `NODE_PATH` to its existing
`node_modules` directory before running the smoke test. The HTML itself needs
neither Node nor Playwright. No browser package is installed by the project.
Local HTTP transfer was interrupted
in the execution environment; direct HTML DOM rendering passed. User previews can
be opened directly or served locally on demand:

```powershell
python -m http.server 8766 --bind 127.0.0.1 --directory inspections/mathematics
```
python -m processors.matching.mathematics inspect --source math_11 --question 27 --output inspections/mathematics/m_11_q27.html; Start-Process .\inspections\mathematics\m_11_q27.html
