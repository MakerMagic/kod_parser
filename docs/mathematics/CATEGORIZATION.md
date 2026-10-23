# Mathematics categorization

Active stage: categorization only. Input is `data/clean/mathematics/questions.json`.
Accept only `cleaning.status: cleaned`, `extraction_status: extracted`, no RAW
issues and no cleaning issues. Do not repair upstream content or run later stages.

## Authoritative taxonomy

`categorization/mathematics/taxonomy.json` transcribes the attached official NUET
Mathematics Specification, with PDF SHA-256 and page references: M1 Units, M2
Number, M3 Ratio and proportion, M4 Algebra, M5 Geometry; 65 official subcategories.
Descriptions, not keywords or desired distributions, decide the classification.
Do not extend the official taxonomy. The user-authorized project fallback `Other`
is separate from the unchanged official five-category/65-subcategory catalog.
Use it only for unambiguous Probability, Statistics, Calculus or Logarithms.
Store `category: {id: Other, name: Other}`, `subcategory: null`; the approved
topic is diagnostic assessment metadata, NOT a new subcategory. Confirmed topic,
dominant operation and direct CLEAN evidence are mandatory. Uncertain recognition
or other out-of-taxonomy subjects stay unresolved with an exact reason and likely
candidate topic. Never use Other as a generic uncertainty bucket.

Read the complete cleaned body, all options and relevant referenced visuals.
Identify the dominant operation, compare the nearest official alternative and
store one final official child and derive its parent, or the approved Other outcome.
Supporting arithmetic/algebra
must not displace the actual geometry/proportion skill. Ambiguous content or a
taxonomy gap outside the four approved Other groups receives a categorization
issue without a guessed label.

## Reproducible decisions and outputs

`data/categorized/mathematics/assessments.json` contains semantic classifier
decisions keyed by SHA-256 of complete ordered body/options and visual hashes,
not by PDF name, question number or ID. It is reviewed classification data, not
an ID-based production rule. Each successful assessment includes dominant
operation, nearest competing subcategory and the reason for rejecting it.
Changed content requires a new review. Existing valid decisions are retained
when their content hash is unchanged. Source IDs and CLEAN pointers are preserved.

Run from the repository root using its Python environment:

```powershell
.venv\Scripts\python.exe -m categorization.mathematics
.venv\Scripts\python.exe -m pytest tests/test_mathematics_categorization.py -q
```

Optional CLI arguments: `--clean-json`, `--assessments`, `--output-dir`.
`--docs-dir` optionally selects the stage Markdown directory. Normal canonical
runs regenerate `docs/mathematics/CATEGORIZATION_BACKTESTING.md` and
`CATEGORIZATION_ISSUES.md` after JSON persistence, including zero-issue runs.
Custom output directories default to their own `inspection/` directory to avoid
overwriting canonical documentation during tests or experiments.
The command validates every classifier output before writing
`data/categorized/mathematics/questions.json` and `validation.json`. The latter
contains eligibility counts, distributions, exclusions and exact unresolved
reasons. Missing assessments remain explicit issues. Both files are deterministic;
no PDF parsing, matching, question reports or upstream mutation occurs. The
categorized layer references CLEAN rather than duplicating question content.

For an explicitly authorized CLEAN structural correction, `bindings.rebind_structure`
can transfer existing reviewed decisions to updated display hashes only after
proving identical non-whitespace text, exact LaTeX/display structure, ordered
options/assets and stable identity. It records old/new hashes in
`assessments.json:structure_rebindings`. It never classifies new content or
accepts changed mathematics. Normal categorization still requires the exact
current CLEAN hash and refreshes all CLEAN references on regeneration.

Regenerate only the two Markdown artifacts from the existing canonical JSON:

```powershell
.venv\Scripts\python.exe -m categorization.mathematics.artifacts
```

This command does not classify questions or modify JSON. It validates record and
distribution counts and projects every current issue with identity, candidate,
state, cause and exact reason. Both files are generated views, never inputs or
manually maintained state. No per-question HTML files are generated.
