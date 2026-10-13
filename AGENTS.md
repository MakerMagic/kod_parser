## Editing Rules for Codex

Before editing, inspect only the files relevant to the task.

Do not modify multiple pipeline stages in one task unless explicitly instructed.

Do not rename folders, move modules, change public schema fields, or add new dependencies without explicit approval.

If extraction logic changes, update or add tests for question numbering, option extraction, required fields, and raw text preservation.

## Forbidden Patterns

Do not:

- make one script that downloads, parses, cleans, matches, categorizes, and exports everything;
- make parsers depend on URLs, scraping logic, or acquisition method;
- clean or normalize text inside the raw extraction stage;
- delete uncertain or messy extracted content silently;
- use filename alone as the stable identity of a question;
- read all documentation before every small task;
- add libraries “just in case”;
- perform repo-wide refactors for small parser tasks.

# Project Instructions

This repository implements a modular document-processing pipeline for TSA and related examination materials.

The project is **not** a single PDF scraper. It is a general pipeline that can acquire or receive source files, identify them, parse source-specific formats, preserve raw extracted information, normalize data, match questions with answers/explanations, categorize questions, and produce a structured final dataset.

## Core Pipeline

```text
acquisition
↓
input files
↓
identification / metadata
↓
source parser
↓
raw structured data
↓
normalization
↓
matching / merging
↓
categorization
↓
final dataset
```

## Critical Architecture Rules

File acquisition and document parsing are separate concerns.

A parser must **not** depend on how its input file was obtained. A PDF may come from an automatic downloader, website scraper, manual upload, local folder, ZIP/archive, future API, external source, or previously generated dataset.

Do not combine downloading, scraping, parsing, cleaning, matching, categorization, and final export into one script.

Each stage must remain independently replaceable and testable.

Raw extracted data must be preserved before cleaning or normalization. Cleaning must happen later and write to a separate output layer.

## Code Navigation and Token Efficiency

Do not reread the entire codebase before each task.

Before editing, inspect only:

- the target file or folder;
- directly related test files;
- directly related schema/model files, if needed;
- the relevant skill or short project status file.

When useful, maintain short navigation notes in `docs/CURRENT_WORK.md` under `Code navigation`.

Keep navigation notes brief and practical, for example:

- where the current parser entry point is;
- where tests for the current module are located;
- where output files are expected;
- which files were recently modified.

Do not write long implementation explanations.

Do not scan unrelated folders unless the task requires it.

## Current Development Milestone

Current milestone:

```text
Blackstone raw structured JSON → Blackstone clean structured JSON
```

Cleaning lives in `processors/normalization/blackstone/` and writes only to `data/clean/blackstone/`. Keep raw JSON immutable; unresolved raw issues remain in `docs/RAW_PARSING_ISSUES.md`. Do not reopen PDFs or redesign the parser during cleaning work.

Do not implement answer matching, categorization, final dataset generation, or new acquisition mechanisms unless explicitly requested.

## Context and Skill Usage

Before reading long documentation, classify the task and load only the relevant context.

For ordinary implementation tasks, use only `AGENTS.md` plus the relevant skill.

Recommended minimum skills:

```text
architecture / folders / pipeline boundaries
→ .codex/skills/project-architecture-guardrails/SKILL.md

PDF extraction / raw parsing / cleaning boundaries
→ .codex/skills/processing-raw-preservation/SKILL.md

tests / validators / pytest
→ .codex/skills/testing-validation-expectations/SKILL.md
```

Do not read every `.md` file or every skill before each task.

## Current Work Tracking

Use `docs/CURRENT_WORK.md` to understand the current milestone, current focus, completed work, and next task.

At the end of a completed task, update `docs/CURRENT_WORK.md` briefly if the task changed project progress.

Keep updates short. Do not write long explanations.

Update only relevant sections:

- `Already completed`
- `In progress`
- `Next task`
- `Do not work on yet`

Do not rewrite the whole file unless explicitly requested.

## When to Read Full Documentation

Read full project documentation only when changing architecture, schema, processing rules, development rules, or resolving ambiguity that the skills do not cover.

Reference docs:

- `docs/PROJECT_CONTEXT.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_SCHEMA.md`
- `docs/PROCESSING_RULES.md`
- `docs/DEVELOPMENT_RULES.md`

