## Skill: Safe Development Workflow

**Path:** `.codex/skills/safe-development-workflow/SKILL.md`

**Description:**  
Defines how Codex should edit the repository safely, avoid broad refactors, and keep changes limited to the requested task.

**Use when:**  
Starting a coding task, refactoring, editing multiple files, adding dependencies, changing project structure, or preparing a pull-request-sized change.

**Do not use when:**  
Only answering conceptual questions outside the repository or explaining Python/VS Code usage.

**Summarizes:**  
- `docs/general/DEVELOPMENT_RULES.md`
- relevant architecture safety rules from `docs/general/ARCHITECTURE.md`

**Read original docs instead when:**  
Changing development policy, adding new repo-wide conventions, changing dependency rules, or modifying core architecture.

**File content:**
```markdown
# Safe Development Workflow Skill

## Purpose

Use this skill to keep Codex edits safe, focused, and architecture-compliant.

The goal is to prevent unnecessary large edits, accidental refactors, dependency bloat, and repeated reading of long documentation files.

## Default Workflow

For each task, Codex should:

1. Identify the pipeline stage involved.
2. Load only the relevant skill.
3. Inspect only the directly relevant files.
4. Make the smallest safe change.
5. Preserve architecture boundaries.
6. Update or add tests if behavior changes.
7. Avoid unrelated cleanup.
8. Summarize what changed.

## Task Scope Rule

One task should usually target one stage only:

- acquisition;
- identification;
- parsing;
- raw output;
- normalization;
- matching;
- categorization;
- validation;
- final export.

Do not modify several stages in one task unless explicitly requested.

## Read-Before-Edit Rule

Before editing, Codex should inspect:

- the target file;
- the directly related test file, if it exists;
- the relevant skill;
- the relevant doc only if the skill is insufficient.

Codex should not scan the whole repository by default.

## No Broad Refactor Rule

Do not rename folders, move modules, rewrite architecture, or change public data schema unless the user explicitly asks.

Small parser tasks should not trigger repo-wide restructuring.

## Dependency Discipline

Do not add a new dependency unless:

1. the standard library is insufficient;
2. existing dependencies are insufficient;
3. the dependency directly supports the requested task;
4. the reason is explained;
5. `requirements.txt` is updated only after approval or explicit instruction.

Avoid installing packages “just in case.”

## File Editing Rules

Codex should avoid:

- unrelated formatting changes;
- rewriting entire files unnecessarily;
- changing files outside the requested scope;
- modifying generated data unless requested;
- editing multiple pipeline stages together;
- deleting raw outputs or test fixtures casually.

## Generated Data Rule

Do not manually edit generated JSON datasets unless the task is specifically about fixtures or examples.

If output format changes, update the generator or parser, not only the generated file.

## Documentation Rule

Do not rewrite all documentation for a small implementation task.

Update docs only when:

- architecture changes;
- schema changes;
- processing rules change;
- setup steps change;
- the user asks for documentation updates.

## Milestone Discipline

Current minimum milestone:

```text
Blackstone PDF → raw structured JSON

Do not implement future stages unless explicitly requested.
Future stages include:
- answer parsing;
- explanation parsing;
- matching;
- merging;
- categorization;
- final dataset generation;
- multi-source expansion.
Commit/PR Discipline
Each change should be easy to review.
Prefer small changes such as:
- one parser improvement;
- one validator;
- one test file;
- one schema update;
- one acquisition module.
Avoid mixed changes.
Safety Checklist Before Finalizing
Before finishing, Codex should check:
1. Did I modify only the requested stage?
2. Did I preserve raw data?
3. Did I avoid coupling acquisition and parsing?
4. Did I avoid changing schema casually?
5. Did I update tests if behavior changed?
6. Did I avoid unnecessary dependencies?
7. Did I avoid unrelated refactors?
When to Read Original Docs
This skill is enough for ordinary coding workflow.
Read original docs when:
- changing development rules;
- changing architecture;
- changing schema;
- adding a new major stage;
- resolving conflict between task and existing documentation.