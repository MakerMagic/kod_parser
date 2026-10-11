# Project Architecture Guardrails Skill

## Purpose

Use this skill to preserve the architecture of the TSA document-processing pipeline.

This repository is not a single PDF scraper. It is a modular document-processing system for TSA and related examination materials.

The main architectural rule is:

**File acquisition and document parsing are separate concerns.**

A parser must not depend on how the input file was obtained.

## Canonical Pipeline

The intended pipeline is:

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

Each stage must remain independently replaceable and testable.
Stage Responsibilities
acquisition/
Responsible for obtaining or importing files.
Allowed sources include:
- website scraper;
- automatic URL download;
- manually downloaded files;
- local directories;
- ZIP/archive imports;
- future APIs;
- external sources;
- previously generated datasets.
Acquisition code may place files or file records into data/input/.
Acquisition code must not parse questions, clean extracted text, match answers, categorize questions, or create final datasets.
data/input/
Stores source files before parsing.
This may include PDFs, archives, or other source files prepared for the pipeline.
identification / metadata
Responsible for determining:
- source;
- year;
- paper or variant;
- section;
- document role;
- document type;
- confidence or uncertainty.
Identification must preserve uncertainty instead of inventing missing metadata.
parsers/
Responsible for extracting raw structured data from already-available input files.
A parser may be source-specific, for example:
- Blackstone parser;
- Cambridge parser;
- BMAT parser;
- answer/explanation parser.
A parser must not download files or depend on URLs, website layout, scraping logic, or acquisition method.
data/raw/
Stores raw structured extraction outputs.
Raw outputs must preserve original extracted text, page references, metadata, image references, and uncertain content.
normalization / cleaning
Responsible for cleaning already-extracted structured data.
Normalization must not replace raw extraction.
Cleaning should write to a separate output layer, such as data/clean/.
matching / merging
Responsible for matching questions with answers and explanations.
Matching must use stable identifiers and metadata, not only local filenames or URLs.
categorization/
Responsible for assigning categories and subcategories to already-structured question data.
Categorization must not read PDFs directly.
data/final/
Stores final structured datasets after extraction, cleaning, matching, validation, and categorization.
Strict Boundaries
Do not combine these responsibilities:
- downloading + parsing;
- parsing + cleaning;
- parsing + categorization;
- acquisition + final export;
- raw extraction + final dataset generation;
- matching + PDF extraction.
Allowed Current Milestone
The first practical milestone is:
Blackstone PDF → raw structured JSON

Do not implement matching, categorization, final export, or new acquisition methods unless explicitly requested.
Required Safeguards
When editing architecture or pipeline code, check:
1. Does this change keep acquisition separate from parsing?
2. Does the parser accept files that already exist?
3. Does raw extraction preserve original extracted data?
4. Does cleaning happen after raw output, not during it?
5. Does matching use stable metadata?
6. Does categorization operate on structured data, not PDFs?
7. Is the change limited to the requested stage?
Forbidden Patterns
Do not create a single script that:
- downloads PDFs;
- parses questions;
- cleans text;
- extracts answers;
- matches answers;
- categorizes questions;
- exports final JSON.
Do not make parser logic depend on:
- URL structure;
- scraper output format only;
- local path names only;
- current folder layout only;
- acquisition method.
Do not modify multiple pipeline stages unless the task explicitly requires it.
When to Read Original Docs
This skill is enough for ordinary development tasks.
Read the original docs when:
- changing the architecture;
- adding a new stage;
- changing folder responsibilities;
- changing milestone scope;
- resolving unclear or conflicting rules;
- updating project documentation.