# Project Context

## 1. What This Project Is

This project is a modular data-processing system for examination materials, initially focused on TSA.

The goal is to transform heterogeneous examination files into a reliable structured question dataset.

The system may eventually process:

- question papers;
- answer keys;
- explanation/solution documents;
- documents containing images;
- future supporting files.

Planned or possible sources include:

- Blackstone Tutors;
- Cambridge TSA;
- BMAT-related materials;
- future examination sources.

This project must be treated as a general processing system, not a one-off PDF scraper.

## 2. Core Pipeline

```text
acquisition
↓
input files
↓
identification / metadata
↓
source-specific parser
↓
raw structured data
↓
normalization / cleaning
↓
matching / merging
↓
categorization
↓
final dataset
```

Each stage should remain independently replaceable and testable.

## 3. Acquisition vs Processing

Input acquisition means how a file enters the project.

Examples:

- automatic download;
- website scraper;
- manual file placement;
- local directory import;
- ZIP/archive import;
- future API;
- previously downloaded file.

Input processing means what happens after the file is available.

Examples:

- identify source, year, section, and document role;
- extract PDF text or images;
- identify questions and options;
- parse answers/explanations;
- normalize extracted content;
- match, merge, categorize, and export.

A change in acquisition must not require rewriting the parser unless the actual document format changes.

## 4. Source vs Acquisition Method

Do not confuse source with acquisition method.

Example:

```text
source = blackstone
acquisition_method = manual
```

or:

```text
source = blackstone
acquisition_method = website_download
```

Both should feed the same Blackstone parser if the document format is the same.

A parser should receive an already available file plus relevant metadata. It should not depend on the original URL, website HTML, downloader, or folder convention.

## 5. Source-Specific Processing

Different sources may require different parsers:

```text
Blackstone PDF → blackstone parser
Cambridge PDF → cambridge parser
BMAT PDF → bmat parser
```

Different parser implementations are acceptable, but downstream outputs should remain compatible.

## 6. First Development Milestone

Current milestone:

```text
Blackstone input PDF → blackstone_raw.json
```

Here, “Blackstone input PDF” means an already available document.

The existing Blackstone downloader may remain as acquisition utility, but it must stay separate from parser logic.

Do not implement cleaning, answer matching, categorization, final export, or additional sources unless explicitly requested.

## 7. Main Design Principles

The project prioritizes:

1. correctness;
2. raw data preservation;
3. modularity;
4. replaceability;
5. traceability;
6. reproducibility;
7. deterministic processing;
8. maintainability.

The system should not be optimized around the current website, URL pattern, filename convention, downloader, or temporary PDF layout.