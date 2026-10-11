# Codex Skills Usage Guide

## Purpose

Use this file only to decide which Codex skill is relevant for a task. Do not read all skills or all project docs by default.

## Active Skills

| Task type | Use this skill |
|---|---|
| Architecture, folders, pipeline boundaries | `.codex/skills/project-architecture-guardrails/SKILL.md` |
| PDF parsing, raw extraction, cleaning boundaries | `.codex/skills/processing-raw-preservation/SKILL.md` |
| Tests, validation, pytest checks | `.codex/skills/testing-validation-expectations/SKILL.md` |

## Optional Skills

Use these only if they actually exist and the task specifically needs them:

| Task type | Use this skill |
|---|---|
| JSON schema or dataset field consistency | `.codex/skills/data-schema-consistency/SKILL.md` |
| Safe editing, dependencies, task scope | `.codex/skills/safe-development-workflow/SKILL.md` |
| Unsure which skill to load | `.codex/skills/token-efficient-context-routing/SKILL.md` |

## Context Rule

For ordinary tasks, use:

1. `AGENTS.md`
2. one relevant skill
3. directly relevant project files only

Do not read every `.md` file, every skill, or the whole repository unless the task explicitly requires it.

## When to Read Original Docs

Read original docs only when:

- changing architecture;
- changing schema;
- changing processing rules;
- changing development rules;
- adding a new source type;
- adding a new pipeline stage;
- resolving ambiguity not covered by the relevant skill.

For ordinary tasks, use:

1. `AGENTS.md`
2. `docs/CURRENT_WORK.md`
3. one relevant skill
4. directly relevant project files only

## Current Work Updates

After completing a task, update `docs/CURRENT_WORK.md` only if progress changed.

Keep updates short:

- move completed tasks to `Already completed`;
- update `In progress` if something remains unfinished;
- update `Next task` if the next step is clear.

Do not add detailed implementation notes.
Do not duplicate commit messages.
Do not rewrite the full file.

## Good Prompt Examples

```text
Use only AGENTS.md and the Processing Rules and Raw Data Preservation skill.
Modify only parsers/blackstone/ and tests/.
Do not touch acquisition, matching, categorization, or final export.

Use only AGENTS.md and the Testing and Validation Expectations skill.
Add tests for Blackstone raw extraction.
Do not modify parser architecture.

Use only AGENTS.md and the Project Architecture Guardrails skill.
Review folder boundaries only. Do not edit files.

Bad Prompt Examples
Avoid:
Read all docs and improve the project.

Scan the whole repository and refactor everything.

Use all skills before starting.