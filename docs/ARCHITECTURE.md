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
validation / export
```

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

### 4.8 Validation and Export

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

Current milestone:

```text
Blackstone raw structured JSON → Blackstone clean structured JSON

The current work is normalization/cleaning of already parsed raw data.
Cleaning must:
- consume structured raw data, not PDFs;
- preserve raw data unchanged;
- write cleaned data to a separate output layer;
- remain deterministic and independently testable;
- preserve uncertainty instead of hiding extraction problems.
Do not implement answer matching, categorization, or final dataset generation unless explicitly requested.

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