# Text-only AI explanations for TSA 2017–2019

This is a separate matching overlay. It never rewrites the answer-key-only
snapshot, clean questions, raw records, or source assets. Only exact matched,
complete text-only questions are eligible. Questions with a visual asset,
visual answer option, visual reference, unresolved clean/raw structure, or an
uncertain answer remain excluded.

Run from the repository root in PowerShell.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $matchingPython -m processors.matching.ai_explanations audit `
  --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' `
  --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\MATCHING_2017-2019_AI_EXPLANATIONS_ISSUES.md'
```

The candidate JSON is a reviewed generation result with this shape:

```json
{
  "format": "text_only_explanation_v2",
  "candidates": [{
    "identity": {"year": 2017, "section": "section_1", "question_number": 1},
    "main_reasoning": "...",
    "incorrect_options": [{"label": "A", "reason": "..."}]
  }]
}
```

Apply only validated candidates to a separate snapshot:

```powershell
& $matchingPython -m processors.matching.ai_explanations apply `
  --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' `
  --candidates-json 'data\reviewed\tsa_2017-2019_text_only.json' `
  --output 'data\ai_explanations\blackstone\tsa_2017-2019.ai-explained.matched.json' `
  --report 'docs\critical_thinking_problem_solving\tsa\ai_explanations\MATCHING_2017-2019_AI_EXPLANATIONS_ISSUES.md' `
  --overwrite
```

Validation requires a unique correct answer, a substantive main reasoning block,
one substantive and non-duplicated reason for every incorrect option, exact
option labels, and at most 2,000 characters. Invalid/unlisted candidates stay
unexplained and appear in the report.

Inspect the generated overlay without modifying it:

```powershell
& $matchingPython -m processors.matching.backtest inspect `
  --matched-json 'data\ai_explanations\blackstone\tsa_2017-2019.ai-explained.matched.json' `
  --year 2017 --question 1
```

HTML inspection includes `Final Explanation` and `Explanation Provenance` with
`Explanation by AI: True` for validated generated content. Source/manual
explanations always show `False`.
