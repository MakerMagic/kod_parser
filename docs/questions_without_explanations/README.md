# Questions with answer keys but without explanations

These read-only Markdown views come from the canonical
[2017–2019 matched dataset](../../data/merged/blackstone/tsa_2017-2019.matched.json),
cross-checked against its three answer-key intermediates. Input hashes are
verified so stale matched input references are not silently exported.
Cleaned question snapshots supply body/prompt/options without rewriting raw,
clean or matched data. Archived AI pilot snapshots are not canonical inputs.

| Year | Question records checked | Known answer-key records | Existing explanations | Exported |
|---|---:|---:|---:|---:|
| 2017 | 50 | 50 | 0 | 50 |
| 2018 | 50 | 50 | 0 | 50 |
| 2019 | 50 | 50 | 0 | 50 |

- [2017 questions](2017_questions_without_explanations.md)
- [2018 questions](2018_questions_without_explanations.md)
- [2019 questions](2019_questions_without_explanations.md)

The exporter excludes existing source/manual/current matched explanation content,
including uncertain/unplaced explanations and accepted AI content. It never uses
generation candidates as explanation text. Missing/conflicting answer keys are
listed as exclusions rather than silently skipped. A source key without a usable
question is retained with explicit unavailable fields.

2018 Q20 (key **B**) and 2019 Q32 (key **C**) remain upstream option-mapping
conflicts. Their source keys are included without claiming a successful match or
inventing missing choices. Existing warnings, available assets and original-layout
references are retained. Other unresolved clean/raw findings also remain visible.
Body visuals remain in order; image options use existing cleaned crops with links
to original raw assets. Unassigned visuals stay explicitly unassigned.

## Reproduce offline (PowerShell, repository root)

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv\Lib\site-packages').Path
$exportPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $exportPython -m processors.matching.export_without_explanations --matched-json 'data\merged\blackstone\tsa_2017-2019.matched.json' --output-dir 'docs\questions_without_explanations'
& $exportPython -m pytest -q tests/test_questions_without_explanations.py
```

This command writes only the three Markdown views and prints exact inclusion /
exclusion counts. It imports no explanation provider and performs no generation
or network requests. Reruns are deterministic for unchanged inputs.

Validation: 70 export/explanation-structure/matching tests passed, plus Ruff,
985 local-link checks and 10 PowerShell-block syntax checks (not execution).
All 150 records were checked for complete stored body/prompt/option text, option
order and correct key. No AI generation was run.
