# Categorization backtesting

Categorization is now a read-only upstream dependency of pre-final assembly.
Unified question rendering follows pre-final JSON; the commands below remain
available for explicit stage-specific user inspection, not normal pre-final runs.

Canonical TSA categorization is `data/categorized/blackstone/tsa.categorized.json`. Read its structured records directly by stable identity and issue filters. The report is not the source of question text, answers, explanations, categories or evidence.

## User-requested inspection

Run from the repository root using the existing Python environment:

```powershell
python -m categorization inspect --categorized-json data/categorized/blackstone/tsa.categorized.json --year 2020 --question 31 --format html --output inspections_categorization/selected-review.html
python -m categorization report --categorized-json data/categorized/blackstone/tsa.categorized.json --output docs/categorization_issues.md
```

Use a new export filename; `--overwrite` is permitted only for an owned inspection. Select with `--year` and `--question`. JSON inspection is available with `--format json`, but direct canonical JSON access needs no export.

The `report` command refreshes the issue index without exporting question HTML. `--review-inspections-dir` explicitly requests a batch of reviewed-question inspections; use it only when the user requests that batch. `--backtest-guide` maintains instructions, not a question catalog.

## Interpretation and safeguards

- Categorization never reparses, cleans, matches answers or generates explanations.
- Frozen matching input/model/source/asset hashes must agree. Investigate changes before refreshing dependent categorization; do not bypass stale references.
- Canonical category definitions and semantic evidence are in `categorization/patterns.json`; the supplied Problem-Solving rulebook remains in `categorization/ps_attribution_rulebook.txt`.
- An assistant review is not human approval. Complete assessments, previous categories, rationale, confidence, candidate patterns and unresolved reasons remain in structured categorization/review records.
- Requested reasoning operation, body, options and required visual evidence take precedence over keyword resemblance. Explanations support but do not override the question.
- RAW/CLEAN/matching issues remain independent of category confidence.
- TSA's existing valid multi-label representation is retained. BMAT's one-primary-category policy is separate; see `BMAT_CATEGORIZATION_BACKTEST.md`.
- The selected user view preserves Main Body, Main Question, Main Answers, Correct Answer, Main/Final Explanation, visuals, original screenshot, provenance and categorization evidence.
- RS selects applicable supplied information; FP constructs/executes a material procedure; IS recognizes preserved structure across representations. Routine arithmetic alone does not settle the distinction.

## Relevant regression checks

```powershell
python -m pytest -q tests/test_categorization.py tests/test_categorization_review.py tests/test_categorization_representation_refinement.py
```
