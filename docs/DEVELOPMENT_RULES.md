# Development Rules

## Canonical-data-first inspection

Read question data from canonical structured storage and open its referenced
assets directly. Reports are optional user views, not development inputs. Stage
runs must not implicitly render per-question inspections; backtesting guides
contain commands/selectors/interpretation, not question catalogs. Follow the
bounded diagnostic exception in `AGENTS.md` only when source data cannot resolve
a concrete evidenced uncertainty.

## 1. Current Development Milestone

Active milestone: pre-final assembly of already categorized, issue-free TSA/BMAT.
Earlier stages are read-only dependencies: do not rerun, repair or modify them.
Validate missing/invalid input and exclude it explicitly. Preserve validated text,
answers, explanations and assets, use stable deterministic examination IDs and
set difficulty to null. One unified JSON feeds explicit user rendering/backtesting;
database import and difficulty assignment follow in separate tasks.
