# 2017–2019 imported and visual explanations

The supplied text explanation files live in
[`../2017-2019_questions_text_with_explanation_ai_generated/`](../2017-2019_questions_text_with_explanation_ai_generated).
Their original bytes are preserved. All three have malformed pasted containers;
the importer recovers only complete, individually valid question objects, rejects
unaccounted content, and stores the original file hash and character range.

Text imports use year + SECTION 1 + question number + exact question record ID.
They must agree with the stored answer and option labels. Existing explanations
are preserved; conflicting imports remain issues. The 97 supplied explanations
are imported, not regenerated or claimed independently authored in this task.

Visual explanations were written by the Codex assistant after inspecting the
stored question crops and effective body/answer assets. No Gemini API call was
made. The existing provider-independent prompt is copied verbatim in
[`prompt.txt`](prompt.txt); the prompt and existing validator remain unchanged.

| Year | Imported text explanations | Source-listed candidates | Verified visual-dependent | Accepted visual explanations | Unresolved visual cases | Text-sufficient illustrations skipped |
|---|---:|---:|---:|---:|---:|---:|
| 2017 | 37 | 13 | 13 | 9 | 4 | 0 |
| 2018 | 32 | 18 | 17 | 13 | 4 | 1 |
| 2019 | 28 | 22 | 21 | 17 | 4 | 1 |

Each year contains:

- `candidates.json`: question context, ordered assets with ownership and hashes,
  full-question preview references, structural findings and prompt fingerprint.
- `explanations.json`: accepted candidates or explicit unresolved reasoning
  results, question IDs, context fingerprints and visual review evidence.
- `ISSUES.md`: categorized import/visual outcomes with unique-question counts.
- `BACKTEST.md`: year-specific inspection links and command.

Accepted explanations appear in the canonical matched record's `final_explanation`
and have `explanation_by_ai: true`. Source type distinguishes imported text from
new visual explanations. Original question and answer-key snapshots/references
are unchanged. Visual review is by the assistant, not an assertion of human
approval or proof that all historical upstream issues have been fixed.

Five cases remain structurally unsafe: 2017 Q38, 2018 Q20/Q50 and 2019 Q32/Q44.
Seven need a stronger independent geometric proof: 2017 Q14/Q44/Q50,
2018 Q32/Q44 and 2019 Q20/Q50. These retain unavailable Final Explanation and
explicit review reasons; known answers do not resolve missing options or prove
a proposed spatial explanation.

2018 Q14 and 2019 Q6 have illustrations but all necessary information is present
in prose. They are excluded from this image-only phase. Their text explanation
drafts are preserved in the workspace but are not attached or counted as accepted;
they remain in the missing-explanation exports for a subsequent text-only review.

## Reapply imports and rebuild all 150 HTML inspections

Run in PowerShell from the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$env:PYTHONIOENCODING = 'utf-8'
$matchingPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $matchingPython -m processors.matching.explanation_imports apply --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --output 'data\merged\blackstone\tsa_2017-2019.matched.json' --backtests
& $matchingPython -m processors.matching.backtest report --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --output 'docs\critical_thinking_problem_solving\tsa\MATCHING_2017-2019_ISSUES.md'
& $matchingPython -m processors.matching.export_without_explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --output-dir 'docs\critical_thinking_problem_solving\tsa\questions_without_explanations'
```

This reuses stored explanation files. It does not call an explanation provider.
If raw/clean matching is rebuilt first, use the explicit import arguments in
[`MATCHING_2017-2019_BACKTEST.md`](../MATCHING_2017-2019_BACKTEST.md).
Changed question context or assets invalidate a visual candidate instead of
silently rebinding its explanation.

[All-question HTML index](../../../../inspections/critical_thinking_problem_solving/tsa/matching/explanation_imports/index.html)
and [live inspection findings](../../../../inspections/critical_thinking_problem_solving/tsa/matching/explanation_imports/validation.json).
Per-year reports: [2017](2017/ISSUES.md), [2018](2018/ISSUES.md), [2019](2019/ISSUES.md).

## Validation

98 targeted matching, Final Explanation, source/manual replacement and import/
export regressions passed. Independent calculation checks cover ticket-package
optimization, parking charges, card-game guarantees, clock segments, ratios and
other numerical results. All 150 prior question/answer snapshots, matching
statuses/issues and 15 referenced input hashes remain unchanged. Rebuilding the
matcher with both explicit import arguments reproduces the explanation records.
The 150 HTML views retain upstream warnings and validate explanation-file hashes.
Representative imported, visual and unresolved views were checked in the browser.

```powershell
& $matchingPython -m pytest -q tests/test_explanation_imports.py tests/test_questions_without_explanations.py tests/test_matching.py tests/test_final_explanation.py tests/test_manual_explanation_replacements.py
```
