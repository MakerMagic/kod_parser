# Mathematics Question Rendering

This stage reads only `data/pre_final/mathematics/questions.json`. It requires
`ready_for_rendering: true` and zero blocking pre-final issues. It never modifies
pre-final records or invokes raw parsing, cleaning, matching or categorization.
It creates an offline HTML inspection preview, derived rendering validation JSON,
and `QUESTION_RENDERING_BACKTESTING.md` / `QUESTION_RENDERING_ISSUES.md`.

Run the all-record rendering audit and write one representative sample preview:

```powershell
.venv\Scripts\python.exe -m processors.pre_final.mathematics_render run
```

Select an individual question, source/test, canonical category, issue-bearing case
or deterministic sample on demand:

```powershell
.venv\Scripts\python.exe -m processors.pre_final.mathematics_render inspect --id <stable-id> --output inspections/mathematics/question_rendering/selected.html
.venv\Scripts\python.exe -m processors.pre_final.mathematics_render inspect --source Test_3.pdf --question 12 --width 1350 --output inspections/mathematics/question_rendering/test-3-q12.html
.venv\Scripts\python.exe -m processors.pre_final.mathematics_render inspect --category M4 --sample 5 --output inspections/mathematics/question_rendering/algebra-sample.html
.venv\Scripts\python.exe -m processors.pre_final.mathematics_render inspect --issues --output inspections/mathematics/question_rendering/issues.html
```

Supported desktop widths are 1166 and 1350 px. A selected sample produces one
disposable HTML document; no per-question report catalog is maintained. Serve
only the inspection directory on loopback if the browser blocks `file://`:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory inspections/mathematics/question_rendering
```

The reusable TSA/BMAT layout shell, answer cards, shared report sections, CSS,
asset hash checks and selectors are reused. Mathematics content remains in source
order within the CLEAN-derived Main Body and Main Question fields. The renderer
does not infer their boundary; null Main Question means no separate source task.
LaTeX is
converted offline to native MathML. Genuine images keep their asset identity and
aspect ratio. The body pane can scroll independently; answer options and cards
grow naturally and have no internal scrolling. Mathematics has no explanation or
AI-explanation field, so the report omits those TSA/BMAT-only sections. Correct
answer and official mathematics category come directly from the same pre-final
record.
