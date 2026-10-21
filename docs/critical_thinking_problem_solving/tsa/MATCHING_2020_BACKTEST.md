# Official 2020 matching backtesting

This source has the original question and A–E options above a complete explanation
on each question page. Its independent profile is `parsers.official_2020_answers`;
it does not use the legacy or Blackstone explanation header/classifier rules.

## Reproduce in PowerShell

Run from the repository root with the existing project Python environment.

```powershell
python -m parsers.official_2020_answers 'acquisition/local/critical_thinking_problem_solving/tsa/TSA-2020-Explained-Answers-official.pdf' --output-dir data/raw/official_2020_answers --overwrite
$answers2020 = Get-ChildItem -LiteralPath data/raw/official_2020_answers -Filter '*.answers.json' | Select-Object -ExpandProperty FullName
python -m processors.matching --clean-json 'data/clean/blackstone/TSA Oxford 2020-ca4ee526afb0.clean.json' --answers-json $answers2020 --years 2020 --output data/merged/blackstone/tsa_2020.matched.json --issues-report docs/critical_thinking_problem_solving/tsa/MATCHING_2020_ISSUES.md --overwrite
```

Inspect one question (omit `--output` to print text/JSON/HTML; a saved inspection
uses exclusive creation, so choose a fresh filename when rerunning):

```powershell
python -m processors.matching.backtest inspect --matched-json data/merged/blackstone/tsa_2020.matched.json --year 2020 --question 23 --format html --output inspections/critical_thinking_problem_solving/tsa/matching/2020/q023-review.html
python -m processors.matching.backtest inspect --matched-json data/merged/blackstone/tsa_2020.matched.json --year 2020 --question 23 --format json
python -m processors.matching.backtest report --matched-json data/merged/blackstone/tsa_2020.matched.json --output docs/critical_thinking_problem_solving/tsa/MATCHING_2020_ISSUES.md
python -m pytest -q tests/test_official_2020_answers.py tests/test_matching.py tests/test_blackstone_explained_answers.py tests/test_final_explanation.py
```

## Inspection and interpretation

- [Generated matching issues](MATCHING_2020_ISSUES.md).
- HTML shows Main Body, Main Question, Main Answers, Correct Answer, one **Full
  Explanation**, answer-inference method/evidence, original question screenshot,
  complete official source-page preview, provenance and upstream/live issues.
- The explanation remains one ordered block with meaningful paragraph and line
  breaks. Incorrect-option discussion is not separately classified.
- Source identity includes PDF hash, page/line/bounding-box references, exact
  explanation spans/raw text, extracted question/options, and inference evidence.
- Matching additionally verifies opening question prose and every textual answer
  against the cleaned record. Unresolved inference has no selected answer;
  conflicts or duplicate candidates are not force-matched.
- Inference methods distinguish `explicit_phrase`, `semantic_pattern` and
  `unresolved`; no manual answer lookup/fallback is used. Repeated mentions of
  rejected alternatives are not positive evidence.
- Existing RAW/CLEAN warnings remain inspectable. A successful match is not a
  claim that all upstream question issues or the source author's reasoning were
  manually proved correct.

## Regression anchors

Verified source result: 50 explanations and 50 matches; 26 answers come from
explicit assertions and 24 from supported semantic assertions. No source-specific
inference/boundary conflicts remain in this PDF. Existing upstream reviews are
separate: Q12 retains `isolated_symbol_ordering_unresolved` in cleaning and Q25
retains its RAW caption-boundary review. Neither warning was removed or solved
by this answer-source task.

Use the inspection command above with the requested year/question; do not
pre-generate a question catalog. Regression fixtures retain answer assertions.
Tests compare all complete explanation text and inferred assertion evidence
against independent PDFium extraction, check A–E geometry and exact raw spans,
and exercise missing explanation, conflicting answers and mismatched questions.

2008-2016 matching:
$matchingHtml = 'inspections/critical_thinking_problem_solving/tsa/matching\TSA_2020_q20-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'; & $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2020.matched.json' --year 2020 --question 20 --format html --output $matchingHtml; if (Test-Path $matchingHtml) { Invoke-Item -LiteralPath $matchingHtml }
