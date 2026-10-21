# Current work

## Current milestone

Mathematics: stored RAW → issue-free cleaning and bounded stored-key matching.

## Already completed

- TSA/BMAT pre-final/rendering; historical work is preserved at
  `../critical_thinking_problem_solving/CURRENT_WORK.md`.
- Recovery verified that pre-final/renderer code was never moved or deleted:
  `processors/pre_final`, input `data/pre_final/questions.json` (700 TSA, 304 BMAT).
- Removed the shared fixed-height/scroll constraint from question/answers; passage
  alone remains a bounded reading viewport. Four Edge layout fixtures pass at
  1166/1350 px. Generate fresh selected HTML; older snapshots embed older CSS.
- All 70 relocation targets exist. Canonical categorized/pre-final comparison
  found no question-content differences beyond authorized paths/hash metadata.
- Recovery regression suite: 338 passed (pre-final, renderer including opt-in
  Edge fixtures, stored matching/categorization reference checks and mathematics).
  Pre-final read-only rebuild is byte-identical; validate and selected inspect
  CLI commands work. Ruff checks pass. No upstream outputs were regenerated.
- Domain folders established only for docs, inspections and acquisition/local.
- Independent mathematics extraction, stored-key matching and selected MathML
  inspections implemented: 12 papers, 360 questions/key rows, 358 answer matches.
- Mathematics regressions pass; selected nine-question Edge layout passes at
  1166/1350 px. Native text/glyph coverage has no unassigned or duplicate glyphs.
- Mathematics RAW structure corrections were bounded to 33 previously issue-bearing
  questions; 327 other records, original page/key data and stable IDs were preserved.
  The user-approved merged projection/validation synchronization is complete;
  all answers and matching statuses stayed unchanged. Regression suite: 72 passed,
  including real Edge checks; selected corrected records pass at 1166/1350 px.
  Pytest uses the existing `.venv` with writable workspace temp/cache paths.

## In progress

- Cleaning processed all 351 eligible mathematics RAW records: 350 cleaned and
  1 review (math_9 Q1: empty stored main content); 9 RAW-issue questions excluded.
  Canonical output: `data/clean/mathematics/questions.json`, with separate
  cleaning/exclusion findings in its `validation.json`. RAW remains unchanged.
- Unmatched-only key retry processed math_2 Q7 and math_3 Q27: both retain their
  missing-option validation issues. All 358 existing valid matches were preserved.
  Retry details: `data/merged/mathematics/retry_validation.json`. Focused cleaning,
  stored matching and RAW-issue regressions: 13 passed; Ruff checks pass.
- 9 mathematics questions retain explicit RAW findings: 12 uncertain native
  formula blocks, 6 unverified raster formulas in one question, and two graph
  option sets without reliable separate labels. See `../mathematics/RAW_ISSUES.md`.
- Native inequality/fraction and stretched-radical corrections updated 10 bounded
  issue-bearing records; 350 others, source glyphs, IDs and answers were preserved.
  Nine questions lost all RAW issues. One ambiguous radical keeps its explicit
  issue with improved source geometry. Existing view/projection files are in sync.
  Latest relevant suite: 84 passed; selected Edge previews pass at 1166/1350 px.
- Literal unbarred radical recovery corrected math_4 Q7/Q10 from explicit source
  parentheses/numeric operands; original glyphs and the genuine diagram remain.
  The one analogous issue-bearing radical (math_12 Q13) has incompatible drawn
  vinculum/delimiter scope and remains unresolved rather than guessed.
  Targeted RAW/projection synchronization and canonical-to-MathML checks pass;
  latest focused regression suite: 86 passed, including opt-in browser tests.

## Next task

- Resolve recorded mathematics source/layout limitations with verified extraction;
  do not solve questions, guess formulas or silently approve image fallbacks.

## Do not work on yet

- Categorization, pre-final, rendering changes, difficulty, database import;
  TSA/BMAT content changes and further mathematics processing.
