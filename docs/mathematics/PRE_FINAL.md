# Mathematics pre-final

This stage assembles existing CLEAN, categorization and stored matching outputs.
It does not parse, clean, match, reclassify or repair upstream records.
This stage is completed for the current source sets. Existing TSA/BMAT `Store`, hash-checked references, owned JSON persistence and deterministic
identity conventions are reused; its ten-category schema is not imposed on math.

Run `.venv\Scripts\python.exe -m processors.pre_final.mathematics`.
Inputs: `data/categorized/mathematics/questions.json`,
`data/clean/mathematics/questions.json`, `data/merged/mathematics/questions.json`.
Output: `data/pre_final/mathematics/questions.json` and `validation.json`.
Generated inspection views: `PRE_FINAL_BACKTESTING.md` and `PRE_FINAL_ISSUES.md`.

Require completed issue-free RAW/CLEAN, successful categorization, validated
matching and a correct answer supported by existing options. Known upstream
non-eligible records are exclusions, not admitted records. Newly detected stale
provenance, structural, formula, asset or integrity failures are blocking pre-final
findings. No record with any finding is admitted. If any blocking finding remains,
the partial dataset is explicitly NOT ready and Question Rendering must not run.
When ready, rendering consumes the all-source `data/pre_final/mathematics/questions.json`
directly without modifying it; see `QUESTION_RENDERING.md`.

Preserve existing source-document/hash-based IDs and ordered blocks unchanged.
CLEAN owns context/task separation. Copy its `main_body` and `main_question`
without making boundary decisions in assembly. The task is an ordered block
array, or null only for a source without a separate task statement. Context may
be empty when the source consists entirely of a task. `content_layout` is
`body_and_question`; `main_answers` retains original labeled block arrays.
LaTeX and genuine assets remain structured, with their original source ordering.
Official parent/child classifications and the confirmed Other/null-subcategory
exception are validated without reclassification. No TSA-only year, section,
explanation or AI-origin fields are invented. No difficulty assignment occurs.

All required references, source PDFs, assets and stored answer-key pointers are
hash checked. RAW/CLEAN/merged/categorization files are immutable here. Missing
matching, stale hashes or broken fields require a separate upstream correction.
Validation contains per-question exclusions and exact blocking reasons. The JSON
schema is `processors/pre_final/mathematics_schema.json`; structural validation is
also executed directly by the generator. No HTML is produced by this stage.

For a bounded source subset, pass `--source-prefix` (repeatable). The second
mathematics set is assembled with `--source-prefix Test_`; its separate canonical
projection and stage artifacts are stored in `data/pre_final/mathematics/second_set/`
and `docs/mathematics/second_set/`. This leaves the all-source pre-final snapshot
independent and still subject to its own validation gate.
