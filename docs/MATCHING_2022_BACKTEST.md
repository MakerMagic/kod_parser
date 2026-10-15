# TSA 2022 matching inspection

Run from the repository root in PowerShell. Parsing and matching are separate;
question raw/clean files and 2008–2016 outputs stay unchanged.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $matchingPython -m parsers.blackstone_explained_answers 'acquisition\local\TSA-2022-Explained-Answers-blackstone.pdf' --output-dir 'data\raw\blackstone_explained_answers\2022' --overwrite
& $matchingPython -m processors.matching --clean-json 'data\clean\blackstone' --answers-json 'data\raw\blackstone_explained_answers\2022' --years 2022 --output 'data\merged\blackstone\tsa_2022.matched.json' --issues-report 'docs\MATCHING_2022_ISSUES.md' --overwrite
```

## Inspect a cross-page explanation

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --year 2022 --question 18
$matchingHtml = 'inspections_matching\TSA_2022_q18-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --year 2022 --question 18 --format html --output $matchingHtml
Invoke-Item -LiteralPath $matchingHtml
```

Use Q45/Q46 to inspect the unresolved source gap, or `--format json` for the
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

The actual source jumps from header 45 to 47. Intervening sports-points text
has no question number/correct-answer declaration. It remains in Q45's source
block with a blocking boundary warning, **not confidently assigned to Q45**.
Q46 has no answer record; neither its answer nor boundary is inferred from
meaning. Current result: 49 parsed answers, 48 matches, Q45 conflict, Q46
unmatched. Both affected questions remain in categorized issues. A corrected or
independently verified source is needed to resolve the gap. Parsing does not
verify the mathematical/logical correctness of source explanations.

## Issues and tests

```powershell
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2022.matched.json' --output 'docs\MATCHING_2022_ISSUES.md'
& $matchingPython -m pytest -q tests/test_blackstone_explained_answers.py tests/test_explained_answers.py tests/test_explanation_classification.py tests/test_matching.py
```

Categories count unique records and retain source/page/reason/review details;
empty categories are omitted. Rebuild matching if the raw intermediate changes.
Report regeneration alone uses stored findings. Verify equations, list endings,
page continuations and missing headers against saved source screenshots.
