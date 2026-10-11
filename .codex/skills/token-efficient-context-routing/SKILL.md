# Token-Efficient Context Routing Skill

## Purpose

Use this skill to avoid wasting tokens during Codex-assisted development.

Codex should not read every `.md` file and every skill before every task.

Instead, Codex should identify the task type and load only the relevant context.

## Context Loading Rule

Before reading documentation, classify the task.

Use this routing:

```text
architecture / folders / boundaries
→ project-architecture-guardrails

JSON fields / schema / output consistency
→ data-schema-consistency

PDF extraction / raw parsing / cleaning
→ processing-raw-preservation

safe editing / dependencies / workflow
→ safe-development-workflow

tests / validators / pytest
→ testing-validation-expectations

Default Context Strategy
For ordinary tasks:
1. Read the task prompt.
2. Identify the pipeline stage.
3. Load only one relevant skill.
4. Inspect only directly relevant project files.
5. Read original docs only if the skill is insufficient.
When to Use Skill Summary Instead of Original Docs
Use a skill summary when:
- the task is ordinary implementation work;
- the architecture is not being changed;
- schema fields are not being changed;
- the task affects one pipeline stage;
- the needed rule is already in the skill;
- the task is small or medium scope.
When to Read Original Docs
Read original .md files when:
- changing architecture;
- changing schema;
- changing processing rules;
- changing development rules;
- adding a new pipeline stage;
- adding a new source type;
- resolving ambiguity;
- resolving conflict between skills and docs;
- updating documentation itself.
Avoid Loading Unrelated Skills
Do not load all skills by default.
Examples:
- If editing parser extraction, do not load acquisition rules unless acquisition is affected.
- If writing tests, do not load categorization rules unless testing categorization.
- If fixing schema fields, do not load full architecture docs unless boundaries are affected.
- If changing dependency setup, do not load processing rules.
Prompt Structure for Low Token Usage
Future prompts should specify:
1. pipeline stage;
2. target files or folders;
3. allowed scope;
4. relevant skill;
5. forbidden changes.
Good example:
Use only the parser-development / raw-preservation skill.
Modify only parsers/blackstone/.
Goal: extract raw question blocks into data/raw/.
Do not change acquisition, categorization, matching, or final export.

Bad example:
Read all docs and improve the whole project.

Persistent Project Summary
Keep a short persistent project summary in AGENTS.md.
It should contain only:
- one-sentence project purpose;
- canonical pipeline;
- strict separation rule;
- current milestone;
- list of available skills;
- rule to load only relevant skill.
Do not copy all docs into AGENTS.md.
What Wastes Tokens
Avoid:
- asking Codex to read all .md files every time;
- asking Codex to inspect the whole repository for small tasks;
- loading all skills for one parser bug;
- duplicating full docs inside prompts;
- giving broad tasks like “improve everything”;
- combining multiple pipeline stages in one request;
- repeatedly pasting long architecture descriptions when a skill exists.
Final Rule
Codex should use the smallest context that is sufficient for the task.
If the task is unclear, Codex should ask for scope or make the smallest safe assumption instead of loading the whole repository.