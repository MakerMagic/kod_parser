# TSA 2022 matching inspection

All inspections include the derived [Final Explanation](MATCHING_2008-2016_BACKTEST.md#final-explanation-all-matching-source-formats)
alongside original components. Q45 preserves prose → bullets → concluding prose;
Q46 keeps its manual-origin notice. Re-run matching only to persist the new field.

Run from the repository root in PowerShell. Parsing and matching are separate;
question raw/clean files and 2008–2016 outputs stay unchanged.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $matchingPython -m parsers.blackstone_explained_answers 'acquisition\local\critical_thinking_problem_solving\tsa\TSA-2022-Explained-Answers-blackstone.pdf' --output-dir 'data\raw\blackstone_explained_answers\2022' --overwrite
& $matchingPython -m parsers.manual_explanations 'processors\matching\manual_sources\tsa_2022_q046.json' --output 'data\raw\manual_explanations\2022\tsa_2022_q046.answers.json' --overwrite
& $matchingPython -m processors.matching --clean-json 'data\clean\blackstone' --answers-json 'data\raw\blackstone_explained_answers\2022' 'data\raw\manual_explanations\2022' --years 2022 --output 'data\merged\blackstone\tsa_2022.matched.json' --issues-report 'docs\critical_thinking_problem_solving\tsa\MATCHING_2022_ISSUES.md' --overwrite
```

## Inspect a cross-page explanation

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --year 2022 --question 18
$matchingHtml = 'inspections/critical_thinking_problem_solving/tsa/matching\TSA_2022_q18-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --year 2022 --question 18 --format html --output $matchingHtml
Invoke-Item -LiteralPath $matchingHtml
```

Use Q45/Q46 to inspect the complete PDF explanation/manual supplement, or `--format json` for the
complete record. Inspection is read-only; HTML requires a new filename. Offline
HTML shows cleaned question structure, correct answer, ordered explanation,
Explanation Visuals, original screenshots, source metadata and issues.

## Profile and actual coverage

The independent new profile handles the actual `N) The correct answer is X`
layout and separate number/answer lines. Left-side anchors, adjacent declaration,
plausible number range and sequence checks support boundaries—not fonts or
arbitrary numbers. Repeated top-of-page headers stay outside explanations but
remain in raw page text. Geometric word gaps restore spaces absent from default
2022 extraction; both original extraction versions are retained.

All six pages were checked: vector objects are header decorations/backgrounds;
no meaningful explanation images were found. The same visual support as 2021
is available; see [visual storage/traceability](MATCHING_2021_BACKTEST.md).
Cross-page controls: Q18 pages 2–3, Q27 pages 3–4, Q37 pages 4–5. Q6/Q37 test
real lists followed by ordinary explanation prose/equations.

The source jumps from header 45 to 47. The user confirmed Q45's complete expected
content, including the sports-points paragraphs/list. No text was lost: the former
blocking warning incorrectly inferred a broken explanation boundary from the
ordinal gap alone. Missing ordinals now remain missing-record issues; actual
orphan answer declarations, malformed headers and duplicate order still require
review. A standalone list lead-in is separated only when real aligned items
follow; a colon alone does not create a list. Prose after a list remains prose.

Q46 is supplied **manually for 2022**, after the user corrected the initial 2026
typo. Its exact text and explicit C answer live in the versioned
`processors/matching/manual_sources/tsa_2022_q046.json`. The explicit import command
writes a separate one-record intermediate, never patches PDF-derived JSON and
never fills another missing question automatically. Matching validates its exact
target question key; duplicate candidates are not overridden. The manual source,
its hash, related PDF hash and origin/approval remain in provenance. No PDF pages
or extraction coordinates are fabricated; manual page references are null. HTML
labels the explanation as manually supplied and shows provenance in Source.

Current result: 49 PDF answers plus one approved manual answer, **50 matches**.
The PDF's missing Q46 header remains truthfully documented in `MATCHING_2022_ISSUES.md`;
it is not a failed manual import. Parsing does not verify source reasoning.

## Issues and tests

```powershell
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --output 'docs\critical_thinking_problem_solving\tsa\MATCHING_2022_ISSUES.md'
& $matchingPython -m pytest -q tests/test_blackstone_explanation_continuation.py tests/test_blackstone_explained_answers.py tests/test_explained_answers.py tests/test_explanation_classification.py tests/test_matching.py
```

Categories count unique records and retain source/page/reason/review details;
empty categories are omitted. Rebuild matching if the raw intermediate changes.
Report regeneration alone uses stored findings. Verify equations, list endings,
page continuations and missing headers against saved source screenshots.
