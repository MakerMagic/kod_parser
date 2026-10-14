# TSA 2008–2016 matching inspection

Run from the repository root in PowerShell. No acquisition, question reparsing,
cleaning, categorization, or final export is performed by these commands.
Use a working Python with the installed dependencies; this checkout uses:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

## Separate stages

First parse the local worked-solutions source into an answer intermediate:

```powershell
& $matchingPython -m parsers.explained_answers 'acquisition\local\TSA-2008-2016-Explained-Answers.pdf' --output-dir 'data\raw\explained_answers' --overwrite
```

Then match the existing clean questions to that intermediate:

```powershell
& $matchingPython -m processors.matching --clean-json 'data\clean\blackstone' --answers-json 'data\raw\explained_answers' --question-source blackstone --output 'data\merged\blackstone\tsa_2008-2016.matched.json' --issues-report 'docs\MATCHING_2008-2016_ISSUES.md' --overwrite
```

Omit `--overwrite` on first runs if desired. Answer JSON names include a PDF
content hash; previews are under `data/raw/explained_answers/assets/<hash>/`.
Matching checks clean schema, unique-key candidates, raw snapshots/hashes,
source PDF hashes, and existing raw/clean/answer image references first. A failed
readiness check produces a blocking report and **no matched records**.
Existing upstream review warnings do not imply unreliable identity; they remain
visible. A missing correct-answer label, identity conflict, or duplicate candidate
does block a successful match.

## Inspect one question

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2008-2016.matched.json' --year 2016 --question 1
$matchingHtml = 'inspections_matching\TSA_2016_q01-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2008-2016.matched.json' --year 2016 --question 1 --format html --output $matchingHtml
Invoke-Item -LiteralPath $matchingHtml
```

`--format json` returns the complete stored record, including both snapshots,
all warnings, exact input hashes and JSON pointers. Selectors also include
`--source`, `--section`, `--paper`, and `--variant`; an ambiguous selection fails.
Inspection does not modify input JSON or assets. HTML embeds saved PNGs and
works offline; missing/changed references appear as live inspection issues.
Inspection exports require a new filename; reports may replace only generated
matching reports.

The universal HTML view contains question identity, Main Body, Main Question,
Main Answers, Correct Answer, Main Explanation, Incorrect Answer Explanations,
Other Explanation Lists, Original Question Screenshot, Answer/Explanation Source,
Matching Metadata, and Issues. Original explanation block order and question field
availability are also retained. Question presentation reuses the clean renderer
including its derived answer crops; answer-source previews show full explanation
context, including diagrams or text without an extractable text layer.

## Reports and regression tests

```powershell
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2008-2016.matched.json' --output 'docs\MATCHING_2008-2016_ISSUES.md'
& $matchingPython -m pytest -q tests/test_explained_answers.py tests/test_matching.py
& $matchingPython -m pytest -q
```

Reports group matching-specific findings with unique-record counts. Upstream
issues are referenced only when they block matching; all raw/clean warnings stay
in the merged snapshots and inspection. Regenerating a report uses stored
matching findings; rebuild matching if an input changes. Live inspection checks
current file hashes rather than silently substituting changed content.

## Source profile and limitations

The worked-solutions parser uses standalone year pages, explicit SECTION/END
markers, and `Question N: LETTER` headers—not fonts or hard-coded page numbers.
Only SECTION 1 is parsed. Geometric row extraction restores readable word order
and spaces; default extracted page text is preserved separately. Every explanation
line has a source-page/line/span reference; paragraphs, hanging list continuations,
and cross-page content remain structured. Repeated lettered list items plus an
elimination transition support incorrect-option analysis. Ordinary lists remain
ordinary; absent/conflicting option labels stay unmapped with a warning.

Generic matching uses `(year, section, question_number)` within the explicitly
selected Blackstone question collection. Known paper/variant/exam conflicts are
rejected; absent answer-side paper/variant metadata is null and not claimed verified.
Another source-specific parser can supply the same intermediate contract without
changing generic matching. This is not fuzzy matching or proof of source accuracy.

Verified first run: 450 SECTION 1 answer records across nine years; 449 matched
and 2014 Q50 blocked by missing clean answer labels (only A/C available).
2008 Q12 has an image-only explanation: its preview is preserved but readable
explanation text remains unavailable. 2016 Q9/Q21/Q33 elimination bullets lack
extractable individual labels; their text/lists are preserved separately without
inventing option mapping. 2016 Q38 contains corrupted PDF list markers; their
original text is preserved and reported for review against its source preview.
Existing clean prompt/visual issues remain unresolved.
Compare screenshots, formulas, paragraphs, list boundaries, and both source PDFs
before treating a matched record as fidelity-approved.
