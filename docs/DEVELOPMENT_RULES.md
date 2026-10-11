# Development Rules

## 1. First Development Milestone

Current milestone:

```text
Blackstone PDF → raw structured JSON
```

Do not implement cleaning, answer matching, categorization, final export, or additional sources unless explicitly requested.

## 2. Inspect Before Editing

Before changing existing code, inspect only the files directly relevant to the task.

For parser work, inspect:

- current Blackstone parsing logic;
- relevant PDF extraction utilities;
- related tests;
- relevant schema expectations.

Do not scan or refactor the whole repository for a small task.

## 3. Preserve Useful Existing Logic

Reuse useful existing Blackstone functionality where possible, including:

- PDF extraction;
- CID decoding;
- question detection;
- option detection;
- validation.

However, do not preserve bad coupling only because it already exists.

Downloader logic may be reused, but it must remain separate from parser logic.

## 4. Keep Parsers Independent

A parser should be executable on a locally available input file.

A parser must not require:

- network access;
- website access;
- downloader execution;
- scraping.

Bad:

```text
parser downloads its own PDFs
```

Good:

```text
acquisition obtains files
↓
parser receives files
```

## 5. Keep Acquisition Replaceable

A source may have multiple acquisition methods:

```text
Blackstone
├── website downloader
├── manual import
├── archive import
└── local test fixture
```

All valid input methods should be able to feed the same parser.

## 6. Preserve Raw Data

Do not perform irreversible transformations before raw output exists.

When uncertain, preserve:

- raw text;
- structured interpretation;
- source metadata;
- extraction warning.

Do not silently delete messy or uncertain content.

## 7. No Silent Failures

If parsing fails, report enough information to debug:

- source;
- input file;
- year, if known;
- question number, if known;
- page, if known;
- failure reason.

Do not silently skip problematic content.

## 8. Testing Rules

Acquisition tests and parser tests are separate.

Parser tests should use fixed local files or fixtures where possible.

Parser tests should check:

- question numbering;
- option extraction;
- raw text preservation;
- required fields;
- multiline questions/options;
- numbered subpoints;
- image-related cases when available;
- visible warnings for uncertain extraction.

Do not make parser tests depend on live websites.

## 9. Stage-by-Stage Development

Develop in this order:

1. Input PDF → Blackstone raw JSON
2. Blackstone raw → Blackstone clean
3. Answer/explanation input → answers raw
4. Answers raw → answers clean
5. Question + answer datasets → merged
6. Merged → categorized/final
7. Additional sources

Do not implement everything simultaneously.

## 10. Adding a New Source

When adding a source:

1. define how files can enter the system;
2. define document identification;
3. implement source parser;
4. produce raw data;
5. normalize data;
6. validate output;
7. integrate matching/categorization only when needed.

Adding one source must not require rewriting unrelated parsers.

## 11. Completion Criteria

A stage is complete only when:

- its input contract is clear;
- its output schema is clear;
- it works independently;
- real examples or fixtures have been tested;
- failures are visible;
- raw/source information is preserved;
- downstream stages can consume its output.

## 12. Core Principle

Design around:

```text
What information does the next stage need?
```

Do not design around temporary website details, URL patterns, filenames, or download methods.

Websites and acquisition mechanisms are replaceable. Structured examination data and processing contracts are the stable core.