# Development Rules

## Canonical-data-first inspection

Read question data from canonical structured storage and open its referenced
assets directly. Reports are optional user views, not development inputs. Stage
runs must not implicitly render per-question inspections; backtesting guides
contain commands/selectors/interpretation, not question catalogs. Follow the
bounded diagnostic exception in `AGENTS.md` only when source data cannot resolve
a concrete evidenced uncertainty.

## 1. Current Development Milestone

Active milestone: mathematics source ingestion and stored-key answer matching.
Follow `../mathematics/PIPELINE.md`. Extract source mathematics without solving,
guessing or rewriting it. Test representative native/layout cases before the full
twelve-source run. Uncertain formulas remain visible as issues with source assets.
TSA/BMAT logic/content remain closed; relocation may update paths/hash references.
Do not mirror domain folders in code/tests/scripts or implement categorization,
difficulty or database import. Inspections remain small and explicitly selected.
