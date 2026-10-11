## Skill: Processing Rules and Raw Data Preservation

**Path:** `.codex/skills/processing-raw-preservation/SKILL.md`

**Description:**  
Protects raw extraction quality and prevents Codex from cleaning, deleting, or normalizing important information too early.

**Use when:**  
Working on PDF extraction, raw question parsing, text block detection, options A–E, subpoints, image handling, cleaning rules, or normalization logic.

**Do not use when:**  
Only changing acquisition code, Git setup, README wording, or dependency installation.

**Summarizes:**  
- `docs/PROCESSING_RULES.md`
- relevant raw-data rules from `docs/DATA_SCHEMA.md`
- relevant pipeline boundaries from `docs/ARCHITECTURE.md`

**Read original docs instead when:**  
Adding new processing rules, changing extraction assumptions, changing cleaning strategy, or introducing source-specific behavior not covered by the skill.

**File content:**
```markdown
# Processing Rules and Raw Data Preservation Skill

## Purpose

Use this skill when extracting, cleaning, or transforming document content.

The goal is to preserve raw extracted information before any normalization, cleaning, matching, or categorization happens.

## Main Rule

Raw extraction must preserve information.

Cleaning and normalization must happen later and write to a separate layer.

## Raw Extraction Responsibilities

A parser should extract and preserve:

- full raw question block;
- question number;
- question text;
- subpoints;
- answer options A–E;
- image references;
- page references;
- original file reference;
- extraction notes;
- uncertainty or warnings.

A parser should not silently discard content just because it is messy.

## Question Blocks

Prefer detecting whole question blocks before splitting into final fields.

A question block may include:

- context text;
- stem;
- numbered statements;
- option labels;
- image references;
- multi-line options.

Do not assume every question has the same structure.

## Question Text

`question_text` should contain the actual question content.

If the question has context before the final interrogative sentence, preserve the context.

Do not reduce the question to only the final sentence if that removes necessary meaning.

## Subpoints

If the question contains numbered statements or subparts, preserve them separately when possible.

Examples include:

```text
1.
2.
3.

or similar structures.
Subpoints may vary in number and length.
Do not hard-code one fixed number of subpoints.
Options
Options should preserve labels:
A
B
C
D
E

Options may be:
- single-line text;
- multi-line text;
- image-only;
- text + image;
- partially uncertain.
Do not drop an option because text extraction is incomplete.
If an option cannot be confidently extracted, preserve a warning.
Images
Images should be handled as first-class extraction elements.
When possible, preserve:
- image file or reference;
- page number;
- relation to question, subpoint, or option;
- location or bounding information, if available;
- extraction notes.
Do not ignore images if they carry question meaning.
Cleaning Rules
Cleaning may include:
- whitespace normalization;
- line break cleanup;
- known PDF artifact removal;
- encoding artifact fixes;
- option formatting standardization.
Cleaning must not:
- paraphrase question text;
- rewrite question meaning;
- delete uncertain content;
- overwrite raw extraction;
- merge unrelated records;
- perform categorization.
Normalization Rules
Normalization should operate on structured raw data, not directly on PDFs.
It should produce separate cleaned output.
Suggested layer:
data/raw/   → original extraction
data/clean/ → cleaned structured output

Matching Rules
Matching questions with answers/explanations should happen after raw extraction and cleaning.
Do not match during raw PDF parsing unless the source document itself already combines questions and answers.
Categorization Rules
Categorization should operate only on structured data.
Do not categorize directly from PDF text extraction.
Do not mix categorization logic into parsers.
Warnings and Uncertainty
If extraction is uncertain, preserve that uncertainty.
Use warnings or notes for cases such as:
- missing option;
- unclear question number;
- broken text extraction;
- image-only content;
- unexpected layout;
- missing metadata.
Do not invent missing information.
Forbidden Patterns
Do not:
- clean raw text destructively;
- delete messy extraction output;
- assume all questions have A–E if the source proves otherwise;
- assume every option is text-only;
- categorize questions inside parser code;
- match answers inside question parser code;
- treat PDF extraction order as final dataset identity;
- silently skip problematic questions.
When to Read Original Docs
This skill is enough for ordinary parser and cleaning tasks.
Read original docs when:
- adding source-specific processing rules;
- changing the raw/clean separation;
- changing how question blocks are detected;
- changing image handling;
- changing option/subpoint logic;
- resolving extraction ambiguity.