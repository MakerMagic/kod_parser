# Development Rules

## Canonical-data-first inspection

Read question data from canonical structured storage and open its referenced
assets directly. Per-question reports are optional user views, not development inputs. Stage
runs must not implicitly render per-question inspections; backtesting guides
contain commands/selectors/interpretation, not question catalogs. Follow the
bounded diagnostic exception in `AGENTS.md` only when source data cannot resolve
a concrete evidenced uncertainty.

## Mandatory stage artifacts

Every executed/regenerated pipeline stage must, after saving canonical output,
regenerate BOTH `<STAGE>_BACKTESTING.md` and `<STAGE>_ISSUES.md` in its domain's
documentation/inspection directory. Apply this separately to EACH stage in a
multi-stage command/task, for all existing stages/domains. Do not invent stages.

These generated artifacts are never authoritative inputs. Backtesting summaries
show counts/distributions, inspection guidance and relevant issue identities,
not catalogs of successful questions or static HTML links. Issues contain every
current structured finding: stable ID, source/question, state, candidates if
available, exact type/reason/cause. Zero issues still generates count 0 explicitly.

Use a canonical stage adapter and the shared
`processors.stage_artifacts.write_stage_pair` / `validate_stage_pairs` contract.
Validate ALL executed stages before completion: both files exist; counts and
issue membership match structured data; resolved findings disappear; regeneration
is deterministic; stages cannot overwrite each other. Do not combine stages in
generic files or manually maintain Markdown state.

Wire generation into each stage command when that stage is next executed or
changed; never omit a pair. Do not execute unrelated stages just to backfill
historical artifacts. Mathematics categorization is wired now; its independent
artifact command reads only existing canonical output. The mandatory pair does
not authorize mass per-question HTML generation.

## 1. Current Development Milestone

Active milestone: mathematics source ingestion and stored-key answer matching.
Follow `../mathematics/PIPELINE.md`. Extract source mathematics without solving,
guessing or rewriting it. Test representative native/layout cases before the full
twelve-source run. Uncertain formulas remain visible as issues with source assets.
TSA/BMAT logic/content remain closed; relocation may update paths/hash references.
Do not mirror domain folders in code/tests/scripts or implement categorization,
difficulty or database import. Inspections remain small and explicitly selected.
