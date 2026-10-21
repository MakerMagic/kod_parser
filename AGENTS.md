# Project instructions

Use this file as a short project router. Read only one relevant domain/stage guide
after it; consult schemas/taxonomies only when the task needs them.

## Editing and architecture safeguards

- Inspect only relevant files and tests. Do not change multiple stages, public
  schema, module paths or dependencies unless the task explicitly requires it.
- Keep acquisition, identification, source parsing, raw extraction, cleaning,
  matching, categorization, pre-final assembly and rendering independently
  replaceable. Detailed architecture: `docs/general/ARCHITECTURE.md`.
- Parsers consume available source files and do not acquire/download them. Preserve
  original raw information; clean into a separate layer. Do not silently discard
  uncertain extraction or use filenames alone as stable question identity.
- When extraction changes, test question numbering, option boundaries, required
  fields and raw-text preservation.
- Use canonical structured data as the source of truth. Open referenced assets
  directly. Generate inspection output only on user request or for a concrete,
  evidenced diagnostic need that source data/assets cannot resolve.
- Preserve user changes. Do not use destructive repository-wide recovery commands.

## Current domain and stage

The active domain is mathematics: RAW extraction is followed by issue-free
cleaning and stored answer-key matching. Cleaning consumes only completed,
RAW-issue-free records and writes a separate `data/clean/mathematics` projection.
Retry matching only for records without a validated matched answer; preserve all
existing valid matches. Twelve local `matdev` papers have RAW extraction.
RAW-stage findings are listed in the generated
`docs/mathematics/RAW_ISSUES.md`; inspect only relevant records/assets. Extraction and
matching commands, method limits and schema are in `docs/mathematics/PIPELINE.md`;
selected-output guidance is in `docs/mathematics/BACKTEST.md`. Do not solve
questions or guess formulas from unresolved visuals. Do not start cleaning,
categorization, difficulty or database import without an explicit task.

TSA/BMAT processing is a completed dependency. Keep its shared pre-final and
question-rendering system available at `processors/pre_final`; canonical input is
`data/pre_final/questions.json`. Its selected-preview instructions are in
`docs/critical_thinking_problem_solving/PRE_FINAL_BACKTEST.md`. Do not reopen
upstream TSA/BMAT content or processing unless the user asks.

Domain folders apply only to `docs`, `inspections` and `acquisition/local`.
Processors, parsers, scripts, tests and shared utilities remain in shared module
trees.

## Context and validation

- Consult `docs/general/CURRENT_WORK.md` when work depends on current project
  progress; do not reread it when the task is self-contained or its status is
  already in context. Keep its status brief and current.
- For a task, read the relevant domain/stage guide and its direct tests. Load the
  schema/taxonomy only when needed; do not scan all docs or the whole repository.
- Use a task-matched skill when it is present in the active Codex skill catalog;
  do not assume uninstalled repository skill paths. The repository-local skill is
  `.agents/skills/token-saver-codex/SKILL.md`.
- Run focused tests and validators for changed behavior. Do not regenerate
  unrelated datasets or reports.

## Reference guides

- `docs/general/ARCHITECTURE.md` — full stage responsibilities and boundaries.
- `docs/general/DEVELOPMENT_RULES.md` and
  `docs/general/PROCESSING_RULES.md` — development and preservation rules.
- `docs/critical_thinking_problem_solving/DATA_SCHEMA.md` — TSA/BMAT fields.
- `docs/mathematics/PIPELINE.md` — mathematics extraction/matching contract.
