# System Architecture



## 1. Purpose

This repository implements a modular document-processing pipeline for TSA and related examination materials.

The project is **not** a single PDF scraper. It is a pipeline where each stage is independently replaceable and testable.

## 2. Core Pipeline

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
normalization / cleaning
↓
matching / merging
↓
categorization
↓
pre-final assembly (issue-free, categorized TSA/BMAT)
↓
question-rendering backtesting
↓
later database import
```

Question data and answer/explanation data are processed independently before matching.

The mathematics source-family branch is documented in
`../mathematics/PIPELINE.md`. Its combined local papers contain both questions and
a final-page key, extracted during the same source pass into separate RAW fields.
Matching consumes those saved fields without reopening the PDF. Domain folders
apply only to docs, inspections and acquisition/local; this is not a code-tree
reorganization and does not change historical TSA/BMAT processing behavior.

```text
question input
↓
question parser
↓
question raw
↓
question clean
       \
        \
         → matcher → merged data
        /
       /
answer/explanation input
↓
answer parser
↓
answer raw
↓
answer clean

Matching must not parse PDFs directly.
Answer Parser Is Source-Specific
The current 2008–2016 explained-answer parser may rely on structural markers specific to that document, including:
- year headings;
- SECTION 1;
- END OF SECTION;
- END OF PAPER;
- Question {number}: {answer} headers.
These rules must remain isolated from future answer parsers.
Do not design a universal answer parser around this single document format.
Matching Layer
The matching layer consumes structured question data and structured answer/explanation data.
It must:
- match using examination identity;
- preserve unmatched records;
- detect ambiguity;
- preserve question and answer traceability;
- preserve explanation structure;
- report conflicts rather than guess.
Matching output belongs under:
data/merged/

## 3. Main Architecture Rule

File acquisition and document parsing are separate concerns.

A parser must **not** depend on how its input file was obtained.

A source file may come from:

- automatic download;
- website scraper;
- manual download;
- local folder;
- ZIP/archive;
- future API;
- cloud storage;
- previously generated dataset.

All of these should be able to feed the same downstream parsing pipeline.

## 4. Layer Responsibilities

### 4.1 Acquisition

Responsible for obtaining or receiving source files.

Examples:

- website downloader;
- scraper;
- local importer;
- archive importer;
- future API importer.

Acquisition must not parse questions, identify answer options, clean question text, match answers, categorize questions, or export final datasets.

### 4.2 Input Identification

Responsible for identifying and registering source files.

It may determine:

- source;
- year;
- section;
- paper or variant;
- document role;
- file type;
- acquisition origin.

Possible document roles:

- question paper;
- answer key;
- explanation/solution;
- combined question and answer;
- unknown.

If metadata cannot be determined reliably, preserve uncertainty instead of inventing values.

### 4.3 Source Parsing

Responsible for extracting raw structured data from already available input files.

A parser may be source-specific, such as:

- Blackstone parser;
- Cambridge parser;
- BMAT parser;
- answer/explanation parser.

The parser should only need the document itself and relevant metadata. It must not download files or inspect websites.

### 4.4 Raw Data

Raw parser output must preserve original extracted information.

Raw data should include enough information to debug extraction errors, such as:

- raw question text or block;
- question number;
- answer options;
- subpoints;
- image references;
- page references;
- original file reference;
- extraction warnings.

Raw data must be saved before cleaning or normalization.

### 4.5 Normalization and Cleaning

Responsible for converting raw extracted data into a cleaner, more stable representation.

Cleaning may normalize whitespace, fix known extraction artifacts, and standardize fields.

Cleaning must not overwrite raw data.

### 4.6 Matching and Merging

Responsible for combining structured question data with answers or explanations.

Matching should work on structured data, not PDFs or webpages.

### 4.7 Categorization

Responsible for assigning categories and subcategories to already structured questions.

Categorization must not be part of acquisition or parsing.

### 4.8 Pre-final Assembly (completed dependency)

`processors/pre_final/` reads canonical categorization JSON for TSA and BMAT.
Resolve existing structured references only when needed for issue/answer/asset
context. No stage is rerun and no upstream file is written. Accept only successful,
issue-free inputs with one canonical TSA category and required usable content.
BMAT-specific skips and unresolved/multi-primary categories do not enter this view.

Write one schema-versioned JSON to `data/pre_final/questions.json` and a compact
machine-readable validation summary beside it. Preserve upstream content without
recovery, inference or explanation generation. Stable IDs use examination identity;
all difficulty values are null pending a separate future process.

Rendering/backtesting reads only this unified JSON, on explicit user request.
Database import follows rendering/backtesting and is not part of this milestone.

### 4.9 TSA/BMAT Question Rendering / Backtesting (completed domain milestone)

Flow: pre-final JSON → selector/filter → single-question simulation → report
builder → disposable browser HTML. Reuse `processors/pre_final/render.py` and
keep loading/selection/rendering/output separate. Only selected records receive
lightweight rendering-field assertions; there is no new issue/eligibility review.
The same normalized record supplies the website-like two-column simulation and
the structured report below it. No source-specific content rules or alternate
question schema. Use proportional saved images and independent passage scrolling;
the question/answers column and option cards must grow without internal scrolling.
Presets are 1166px and 1350px. Do not modify data to fit the renderer.

Raw/clean/matching/categorization/pre-final are read-only and are not rerun.
Questions/answers/explanations/categories are not reassessed. Import follows
rendering review, not this task. Preview output is opt-in, never a full catalogue.

### 4.10 Later Validation and Export

Responsible for checking data quality and producing final outputs.

Export may produce JSON, CSV, database records, or future API-ready formats.

Export must not contain parsing logic.

## 5. Required Project Structure

```text
project/
├── acquisition/
│   ├── blackstone/
│   ├── cambridge/
│   ├── local/
│   └── archive/
│
├── identification/
│
├── parsers/
│   ├── blackstone/
│   ├── cambridge/
│   └── bmat/
│
├── processors/
│   ├── normalization/
│   ├── matching/
│   └── merging/
│
├── categorization/
│
├── validation/
│
├── models/
│
├── utils/
│
├── tests/
│
└── data/
    ├── input/
    ├── raw/
    ├── clean/
    ├── merged/
    └── final/
```

The exact structure may evolve, but the separation of responsibilities must not.

## 6. Correct Boundary Example

Bad architecture:

```text
blackstone_parser
↓
find website
↓
download PDF
↓
parse PDF
↓
clean text
↓
categorize
```

Good architecture:

```text
Blackstone acquisition or local import
↓
registered input file
↓
Blackstone parser
↓
raw structured data
↓
normalization
↓
later pipeline stages
```

## 7. Current Development Milestone

Active milestone: mathematics source extraction → stored question/formula/key
records → deterministic answer matching → selected mathematical HTML inspections.
See [mathematics](../mathematics/PIPELINE.md). TSA/BMAT remain a separate completed
domain; their algorithms/content are not reopened. Only documentation, inspection
artifacts and local acquisition files use domain folders. Code/tests retain their
existing module layout. A combined question/key PDF is extracted in one source
pass; the matching module still consumes stored JSON and never opens the PDF.

## 8. Architecture Safeguards

Do not:

- combine downloading, parsing, cleaning, matching, categorization, and export into one script;
- make parsers depend on URLs, scraping logic, or acquisition methods;
- clean or normalize text inside the raw extraction stage;
- delete uncertain extracted content silently;
- use filename alone as stable question identity;
- add future pipeline stages before the current milestone requires them.

## 9. Future-Proofing

The architecture must tolerate future changes in:

- acquisition methods;
- website structure;
- filenames;
- directory structure;
- PDF layouts;
- document types;
- source metadata;
- question formats.

Temporary assumptions should stay inside source-specific modules, not shared architecture.
