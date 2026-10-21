# Development Rules

## Canonical-data-first inspection

Read question data from canonical structured storage and open its referenced
assets directly. Reports are optional user views, not development inputs. Stage
runs must not implicitly render per-question inspections; backtesting guides
contain commands/selectors/interpretation, not question catalogs. Follow the
bounded diagnostic exception in `AGENTS.md` only when source data cannot resolve
a concrete evidenced uncertainty.

## 1. Current Development Milestone

Active milestone: question-rendering backtesting from completed pre-final JSON.
Raw/cleaning/matching/categorization/pre-final assembly are out of scope: do not
rerun, repair or modify them. Do not reassess question/answer/explanation/category
quality or reopen excluded issues. Only lightweight assertions for selected
rendering fields/assets are allowed. Report malformed pre-final input rather than
repair it. Use one reusable simulation/report builder with opt-in selectors and
1166/1350px layouts, not default bulk exports or static catalogues. Database import
follows rendering review; difficulty assignment is separate later work.
