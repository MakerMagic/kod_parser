## Skill: Testing and Validation Expectations

**Path:** `.codex/skills/testing-validation-expectations/SKILL.md`

**Description:**  
Defines minimum testing and validation expectations for parsers, schema outputs, and pipeline stages.

**Use when:**  
Adding or modifying parser tests, validators, schema checks, extraction checks, pytest files, fixtures, or quality gates.

**Do not use when:**  
Only editing documentation, installing VS Code extensions, or asking conceptual project questions.

**Summarizes:**  
- `docs/general/DEVELOPMENT_RULES.md`
- `docs/critical_thinking_problem_solving/DATA_SCHEMA.md`
- `docs/general/PROCESSING_RULES.md`

**Read original docs instead when:**  
Changing validation strategy, adding new formal schemas, changing required fields, or introducing source-specific test rules.

**File content:**
```markdown
# Testing and Validation Expectations Skill

## Purpose

Use this skill when creating or modifying tests and validators.

The goal is to prevent silent extraction errors and keep every pipeline stage independently testable.

## Main Principle

Every stage should be testable independently.

A parser should be testable without downloading files.

Acquisition should be testable without parsing questions.

Categorization should be testable without reading PDFs.

## Parser Test Priorities

When parser behavior changes, tests should check:

- question count, if expected count is known;
- question numbering;
- option labels A–E;
- multiline option handling;
- subpoint extraction;
- raw text preservation;
- page references;
- image references, if present;
- warnings for uncertain extraction;
- required metadata fields.

## Raw Output Validation

Raw output validation should check that each record preserves:

- source;
- original file reference;
- question number;
- raw extracted text or raw question block;
- structured question text;
- options, if expected;
- page reference;
- extraction warnings when needed.

Do not accept a parser that only returns cleaned text without raw preservation.

## Schema Validation

Schema validation should check:

- required fields exist;
- field types are consistent;
- options are structured consistently;
- image references are structured consistently;
- metadata is preserved;
- IDs are stable and not based only on local filenames.

## Stage-Specific Validation

### Acquisition

Check that acquisition outputs input files or file records.

Do not test acquisition by requiring parser output.

### Identification

Check that identification detects or preserves:

- source;
- year;
- section;
- document role;
- uncertainty.

### Parsing

Check that parsing extracts raw structured data from existing files.

Parsing tests should not depend on network access.

### Normalization

Check that normalization writes separate clean output and does not overwrite raw output.

### Matching

Check that matching uses stable identifiers and metadata.

### Categorization

Check that categorization operates on structured data, not PDFs.

### Final export

Check that final output is consistent with the schema and traceable to source records.

## Test Fixture Rules

Use small, focused fixtures where possible.

Do not require large real PDF files for every unit test unless integration testing needs them.

Keep tests stage-specific.

## Regression Test Rule

If fixing a parsing bug, add a test that would fail before the fix.

## Do Not Over-Test Future Stages

Do not create tests for matching, categorization, or final export before those stages are implemented unless the task explicitly asks.

## Quality Tools

Recommended tools:

- `pytest` for tests;
- `ruff` for linting and simple code quality checks.

Do not add heavier testing tools unless necessary.

## Forbidden Patterns

Do not:

- rely on live website downloads in parser tests;
- validate only final output while ignoring raw output;
- skip tests after changing extraction logic;
- silently accept missing question numbers;
- silently accept missing options when options are expected;
- overwrite raw data during normalization tests;
- mix tests for unrelated pipeline stages.

## When to Read Original Docs

This skill is enough for ordinary testing work.

Read original docs when:

- changing required schema fields;
- designing formal validators;
- changing test strategy;
- adding a new source-specific parser;
- introducing new output layers.