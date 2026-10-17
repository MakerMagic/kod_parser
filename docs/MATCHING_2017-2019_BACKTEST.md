# TSA 2017–2019 answer-key matching

The universal [Final Explanation](MATCHING_2008-2016_BACKTEST.md#final-explanation-all-matching-source-formats)
section now includes the explicitly imported 2017–2019 text explanations and
reviewed visual explanations. The original PDFs remain answer-only sources;
their row screenshots are not explanation visuals. See the
[explanation workspace](2017-2019_questions_images_with_explanation_ai_generated/README.md)
for provenance, counts and unresolved cases.

Run from the repository root in PowerShell. These sources supply **answers only**:
empty explanation fields mean unavailable in this format, not failed extraction.
Parsing and matching are separate commands; no source files are acquired.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
foreach ($answerYear in 2017..2019) {
    & $matchingPython -m parsers.blackstone_answer_keys "acquisition\local\TSA-$answerYear-Answers-blackstone.pdf" --output-dir "data\raw\blackstone_answer_keys\$answerYear" --overwrite
    if ($LASTEXITCODE -ne 0) { throw "Answer-key parsing failed: $answerYear" }
}
& $matchingPython -m processors.matching --clean-json 'data\clean\blackstone' --answers-json 'data\raw\blackstone_answer_keys' --years 2017 2018 2019 --explanation-imports 'docs\2017-2019_questions_text_with_explanation_ai_generated' --visual-explanations 'docs\2017-2019_questions_images_with_explanation_ai_generated' --output 'data\merged\blackstone\tsa_2017-2019.matched.json' --issues-report 'docs\MATCHING_2017-2019_ISSUES.md' --overwrite
```

## Inspect one question

```powershell
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --year 2017 --question 20
$matchingHtml = 'inspections_matching\TSA_2017_q20-' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.html'
& $matchingPython -m processors.matching.backtest inspect --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --year 2017 --question 20 --format html --output $matchingHtml
Invoke-Item -LiteralPath $matchingHtml
```

Change year/question as needed. `--format json` includes the complete stored record.
HTML is self-contained and read-only. It shows Main Body, Main Question, Main
Answers, Correct Answer, source-format explanation availability and the imported/
generated Final Explanation, original question
screenshots, Answer-Key Source (PDF/page/cells/raw row and saved row screenshot),
matching metadata and preserved upstream issues. HTML exports require new filenames.

## Extraction, identity and uncertainty

The independent `parsers/blackstone_answer_keys/` profile requires a ruled table
with Question/Answer columns and corroborating section/year/Answer Key headings.
Cell bounds and contained PDF words corroborate each row; font identity is not
used. Number sequence, expected 1–50 coverage, A–E letters, duplicate rows and
column/text agreement are checked. Unsupported headers or uncertain rows never
yield an accepted correct answer. Original page text, layout lines/spans, table
cells/bounds and row previews remain preserved. Missing grid/header support is
an explicit source parsing failure, not a guessed text-only fallback.

The generic matcher uses year + section + question number, checks known metadata
conflicts, and preserves both input snapshots/hashes/pointers and raw/clean assets.
Duplicate candidates and invalid clean option labels are not force-matched.

Actual source validation: 50 answers per year; all 150 pairs agree with independent
PDFium text extraction, including rows 1/25/50. Matching currently yields **148
matches and two upstream conflicts**: 2018 Q20 and 2019 Q32 have malformed/missing
clean option labels. Their extracted key answers remain stored; the issues report
references the raw/clean cause. The answer-key parser does not fabricate
explanations or issue missing-explanation warnings for this answer-only format;
the explicit explanation overlay is applied after exact-key matching.

User-confirmed answers (2026-10-15): **2018 Q20 = B**, **2019 Q32 = C**.
Both agree with the parsed answer keys and are explicitly shown in the issues
report's source-answer column. Their option-structure conflicts remain unresolved;
knowing the correct letter does not repair missing/incorrect question options.

## Report and tests

```powershell
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --output 'docs\MATCHING_2017-2019_ISSUES.md'
& $matchingPython -m pytest -q tests/test_blackstone_answer_keys.py tests/test_matching.py tests/test_blackstone_explained_answers.py tests/test_explained_answers.py
```

Report headings count unique affected records per nonempty issue category.
Synthetic tests exercise missing, duplicate, malformed, out-of-order and SECTION 2
rows, plus non-mutating inspection. Real-source checks cover every answer pair.
This profile intentionally does not guess unruled or differently headed formats.
