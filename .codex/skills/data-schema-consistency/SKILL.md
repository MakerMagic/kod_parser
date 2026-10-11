## Skill: Data Schema and Dataset Consistency

**Path:** `.codex/skills/data-schema-consistency/SKILL.md`

**Description:**  
Defines the expected structure of extracted question data and protects JSON consistency across raw, clean, merged, and final outputs.

**Use when:**  
Creating or modifying JSON output, schema validation, question IDs, metadata fields, options, subpoints, image references, answer fields, explanation fields, or dataset export.

**Do not use when:**  
Only working on file downloading, folder setup, Git configuration, or unrelated environment setup.

**Summarizes:**  
- `docs/DATA_SCHEMA.md`
- relevant schema rules from `docs/PROCESSING_RULES.md`

**Read original docs instead when:**  
Changing canonical field names, adding/removing required fields, changing final dataset structure, or resolving schema ambiguity.

**File content:**
```markdown
# Data Schema and Dataset Consistency Skill

## Purpose

Use this skill when working with structured data produced by the TSA document-processing pipeline.

The goal is to keep raw JSON, cleaned JSON, merged JSON, and final JSON consistent across sources.

## Main Principle

Every extracted question must remain traceable back to its original source file, page, and raw extracted content.

Do not lose raw information during parsing.

## Core Data Concepts

The project may produce several data layers:

```text
data/raw/      → raw structured extraction
data/clean/    → normalized structured data
data/merged/   → questions matched with answers/explanations
data/final/    → final dataset for use

Each layer should preserve enough metadata to trace back to the original source.
Stable Identity
Do not rely only on:
- filename;
- URL;
- local path;
- download order;
- extraction order.
A stable question identity should be based on a combination of metadata such as:
source + year + paper/variant + section + question_number

If some metadata is missing or uncertain, preserve uncertainty instead of inventing values.
Raw Question Object
A raw question object should preserve:
- source;
- year;
- paper or variant, if known;
- section;
- document role;
- question number;
- raw extracted text;
- question text;
- subpoints, if present;
- answer options;
- image references, if present;
- page reference;
- original file reference;
- extraction metadata;
- uncertainty or warnings.
Recommended Field Categories
Source metadata
Use fields that identify where the question came from:
source
year
paper
variant
section
document_role
original_filename
input_file_path
page_reference

Question identity
Use fields that identify the question:
question_id
question_number
source_question_key

The exact canonical names should follow docs/DATA_SCHEMA.md.
Raw preservation
Always preserve raw extracted content:
raw_text
raw_question_block
raw_options_text
raw_extraction_notes

Do not replace raw text with cleaned text.
Parsed structure
Use structured fields for:
question_text
subpoints
options
images

Options should preserve labels such as A, B, C, D, E.
Answers and explanations
For merged data, include fields such as:
answer
explanation
answer_source
explanation_source
matching_confidence

Do not add answer fields during question-only raw parsing unless the source file contains answers.
Validation and warnings
Include or preserve information about:
missing_options
missing_question_number
uncertain_metadata
extraction_warnings
validation_errors

Do not silently discard problematic records.
Images
Images should be first-class data.
If a question, subpoint, or option contains an image, preserve:
- image reference;
- page number;
- relation to question/subpoint/option;
- extraction location if available;
- original file reference.
Do not replace image-only options with empty text without a warning.
Raw vs Clean Data
Raw data:
- preserves extraction output;
- keeps messy text;
- keeps uncertain content;
- keeps debugging information.
Clean data:
- may normalize whitespace;
- may fix known PDF artifacts;
- may standardize option formatting;
- must not overwrite raw data.
Schema Change Rules
Before changing schema fields, check:
1. Does this break existing raw JSON?
2. Does this affect tests?
3. Does this require updating validators?
4. Does this require updating documentation?
5. Does this preserve traceability?
6. Does this preserve raw extracted data?
Forbidden Patterns
Do not:
- invent missing metadata;
- use filename alone as question identity;
- delete uncertain extracted text;
- collapse raw and clean outputs into one field;
- store final dataset directly from a parser;
- add categorization fields during raw extraction unless the architecture explicitly allows it;
- change field names casually without updating tests and documentation.
When to Read Original Docs
This skill is enough for ordinary schema-related tasks.
Read docs/DATA_SCHEMA.md when:
- adding required fields;
- removing fields;
- changing canonical names;
- changing output layer structure;
- creating final dataset format;
- writing formal validators.