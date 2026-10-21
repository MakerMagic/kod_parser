# TSA 2021 matching inspection

All inspections include the derived [Final Explanation](MATCHING_2008-2016_BACKTEST.md#final-explanation-all-matching-source-formats)
alongside original components; Q48's table is included at its source-block position.
Re-run matching only to persist the new field; original answer JSON/assets remain unchanged.

Run in PowerShell from the repository root. Parsing and matching are separate;
question raw/clean files and legacy answer outputs are not modified.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $matchingPython -m parsers.blackstone_explained_answers 'acquisition\local\critical_thinking_problem_solving\tsa\TSA-2021-Explained-Answers-blackstone.pdf' --output-dir 'data\raw\blackstone_explained_answers\2021' --overwrite
& $matchingPython -m processors.matching --clean-json 'data\clean\blackstone' --answers-json 'data\raw\blackstone_explained_answers\2021' --years 2021 --output 'data\merged\blackstone\tsa_2021.matched.json' --issues-report 'docs\critical_thinking_problem_solving\tsa\MATCHING_2021_ISSUES.md' --overwrite
```

## Inspect Q48, including its table

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2021.matched.json' --year 2021 --question 48
$matchingHtml = 'inspections/critical_thinking_problem_solving/tsa/matching\TSA_2021_q48-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2021.matched.json' --year 2021 --question 48 --format html --output $matchingHtml
Invoke-Item -LiteralPath $matchingHtml
```

Change `--question` to select another record; `--format json` returns all fields.
Inspection is read-only; exports require a new filename. Offline HTML shows
cleaned Main Body/Question/Answers, correct answer, ordered explanation, a visual
gallery, original question/source screenshots, provenance and issues. Visuals
appear in-place and again in Explanation Visuals for focused comparison.

## Source profile and preservation

The new parser is independent of the 2008–2016 source parser. A left-side number
plus an adjacent correct-answer declaration (separate or combined line) defines
a boundary. Numbers alone do not. Repeated top-of-page SECTION/year headers are
recorded, not emitted as explanation text. Original default/geometric extraction
is retained. Explanations cross pages; lists use marker/content geometry, so
ordinary following prose does not become part of the final item.

JSON/assets live under `data/raw/blackstone_explained_answers/2021/`. PNG names
contain source hash, year, question, record ordinal, page, visual index and bounds
hash. `explanation.visual_assets` stores source/page/bounds/path/hash/type and
warnings; ordered visual blocks reference `asset_index`. Contained table text
keeps raw references instead of duplicating prose. Ambiguous unassigned visuals
are saved in source issues, not force-assigned. Wider `visual_previews` remain.

Q48's complete embedded table is its explanation; no text is invented. The six
source pages contain no other meaningful explanation images/vector regions.
Cross-page controls: Q10 pages 1–2 and Q27 pages 3–4. All 50 identifiers match;
upstream Q7 encoding review remains visible in inspection. Source reasoning is
not verified, and unfamiliar vector/label layouts may require manual review.

## Issues and regression tests

```powershell
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2021.matched.json' --output 'docs\critical_thinking_problem_solving\tsa\MATCHING_2021_ISSUES.md'
& $matchingPython -m pytest -q tests/test_blackstone_explained_answers.py tests/test_explained_answers.py tests/test_explanation_classification.py tests/test_matching.py
```

Reports use nonempty categories with unique-record counts. Rebuild matching if
raw answers change; regeneration alone uses stored findings. Missing/changed
assets fail matching readiness and appear during live inspection. Compare the
table edges, source screenshots, answer letters and paragraph/list boundaries.
