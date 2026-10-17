# Questions with answer keys but without explanations

These read-only Markdown views come from the canonical
[2017–2019 matched dataset](../../data/merged/blackstone/tsa_2017-2019.matched.json),
cross-checked against its three answer-key intermediates. Input hashes are
verified so stale matched input references are not silently exported.
Cleaned question snapshots supply body/prompt/options without rewriting raw,
clean or matched data. Archived AI pilot snapshots are not canonical inputs.

| Year | Question records checked | Known answer-key records | Existing explanations | Exported |
|---|---:|---:|---:|---:|
| 2017 | 50 | 50 | 46 | 4 |
| 2018 | 50 | 50 | 45 | 5 |
| 2019 | 50 | 50 | 45 | 5 |

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
inventing missing choices. Existing warnings and available assets are retained.
Other unresolved clean/raw findings also remain visible. Each question retains
its question record identifier, while other source references are omitted. Body
visuals remain in order; image options use existing cleaned crops. Unassigned
visuals stay explicitly unassigned.

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

The canonical records now include 97 imported text explanations and 39 reviewed
visual explanations; these are excluded from this missing-explanation view.
See the [explanation workspace](../2017-2019_questions_images_with_explanation_ai_generated/README.md)
for per-question outcomes and unresolved cases. Export regeneration itself is
offline and never generates explanations. Two source-listed image skips (2018 Q14
and 2019 Q6) were found to be text-sufficient; their illustrations do not justify
including them in image-only generation, so they remain listed here.
