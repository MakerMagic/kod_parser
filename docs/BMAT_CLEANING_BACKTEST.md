# BMAT RAW → CLEAN inspection

Cleaning reads stored BMAT RAW JSON only. It reuses the proven pure text
normalizer, but not TSA prompt splitting, categorization or source overrides.
No PDF is opened, no RAW image is changed, no answer is inferred.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv/Lib/site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$bmatPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $bmatPython -m processors.bmat clean --raw-json data/raw/bmat --overwrite
& $bmatPython -m processors.normalization.bmat.backtest report --all-html
& $bmatPython -m processors.normalization.bmat.backtest inspect --year 2014 --question 1
& $bmatPython -m pytest -q tests/test_bmat_cleaning.py
```

- [All RAW/CLEAN inspections](../inspections_bmat_clean/index.html)
- [Current cleaning issues](BMAT_CLEANING_ISSUES.md)
- [Machine-readable clean status](../inspections_bmat_clean/status.json)
- [Cross-category stabilization audit](../inspections_bmat/stabilization/review.json)

Inspection uses the **same renderer and section order as TSA CLEAN**:
Main Body → Main Question → Main Answers → Original Screenshot → metadata →
availability → issues → expandable original record/transformation evidence.
One additional section shows BMAT-specific category/skip evidence. The expandable
evidence includes explicitly named Raw/Clean Main Body, Main Question and Main
Answers for comparison. Unknown ownership remains unresolved in the issues and
source evidence, not silently promoted to Main Body. A stale RAW hash blocks inspection.

Verified native slash/bar and numerator/denominator glyph geometry may become
plain-text `n/d` in CLEAN options. Mixed numbers, signs and surrounding text are
preserved; a character-accounting mismatch prevents conversion. Original RAW
text, glyph positions and source crops remain in the expandable evidence.
Verified regressions: 2004 Q5, 2007 Q7/Q26 and 2010 Q23 (20 fraction answers).
Raised numerators are assigned to their own option at RAW geometry level before
CLEAN renders the fraction; text/slash glyphs and vector separators are supported.

All 664 items, including intentional skips and RAW reviews, remain stored for QA.
Only `pipeline_eligible: true` records may proceed to future normal stages.
Issues distinguish `origin: raw` from `origin: cleaning`. Intentional skips are
not defects and do not erase independent RAW issues.

Stabilization anchors include 2014 Q1/Q7/Q35, 2010 Q12, 2012 Q3/Q14,
2003 Q12/Q36/Q38, 2009 Q3, 2004 Q22 and 2017 Q18. The water-ice colon prompt
is **2004 Q13**, not Q3; Q3's screws question is preserved. 2008 Q22 already
had its prompt; the repaired defect there was a page separator.
All seven caption-review questions were inspected: six boundaries are verified;
2021 Q8's fragmented graph groups remain unresolved.

2014 Q7's Cambria subset lacks Unicode mapping. Complete spatial fractions are
stored as six source-rendered option images, including numerators, denominators
and letters, not guessed Unicode text. 2017 Q28 retains an unknown source-font glyph
for review. 2015 Q18's native bullet outline/list context is verified; its six image
options survive cleaning, but its 75.44% occupied height makes it an intentional
`too long` exclusion. Matching now runs independently over eligible CLEAN records;
see [matching backtesting](BMAT_MATCHING_BACKTEST.md). A separate targeted
BMAT classification pass is documented in [categorization backtesting](BMAT_CATEGORIZATION_BACKTEST.md);
it does not imply that matching or normal Problem-Solving attribution is complete.
