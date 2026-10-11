# Processing Rules

## 1. General Rule

Processing starts only after a document is available as an input.

A parser must operate on the document content and relevant metadata. It must not depend on how the file was acquired.

## 2. File Identification

Before parsing, the system may identify:

- source;
- year;
- paper;
- variant;
- section;
- document role.

Identification may use:

- trusted acquisition metadata;
- filename;
- directory structure;
- PDF metadata;
- document content.

If identification is ambiguous, preserve uncertainty instead of inventing values.

## 3. Raw Parsing

Raw parsing extracts structured information from an already available input file.

For a Blackstone question PDF, the parser should extract:

- source;
- year;
- paper or variant, if available;
- section;
- filename/input reference;
- question number;
- raw question block;
- question text;
- numbered subpoints;
- options A–E;
- images or image references;
- page information;
- extraction warnings.

Raw parsing must preserve messy or uncertain extracted content.

Do not clean destructively during raw parsing.

## 4. Answers and Explanations

Answer and explanation files are separate input types.

They may be acquired through the same or different mechanisms as question PDFs.

Answer/explanation parsing should depend on document format, not acquisition method.

## 5. Cleaning

Cleaning occurs after raw extraction.

Cleaning may normalize:

- whitespace;
- line breaks;
- known PDF artifacts;
- option formatting;
- encoding issues;
- image references.

Cleaning must write to a separate cleaned output and must not overwrite raw data.

## 6. Matching

Matching operates on structured data, not PDFs, URLs, or websites.

Preferred conceptual key:

```text id="rhpdku"
source + year + paper/variant + section + question_number
```

Do not match based on:

- filename alone;
- URL;
- local path;
- acquisition method.

## 7. Categorization

Categorization operates only on structured merged content.

It must not inspect:

- source website;
- download URL;
- local file path;
- acquisition method.

Initial main categories:

- Critical Thinking;
- Problem Solving;
- Math.

Problem Solving rules may initially use case-insensitive keyword detection involving:

```text id="tzuizs"
during
which
how
many
much
long
must
should
what
how many
how much
how long
```

Questions involving:

```text id="2q7n7u"
inferences
what if true
what if false
```

are initially assigned to `other` unless explicitly overridden by a later rule.

Categorization rules must remain isolated from parsing and acquisition.

## 8. Forbidden Processing Patterns

Do not:

- use URL structure as parser logic;
- use downloader-specific filenames as parser logic;
- clean or normalize before raw output exists;
- delete uncertain raw content silently;
- match records by filename alone;
- categorize directly from PDFs;
- mix acquisition, parsing, cleaning, matching, and categorization in one script.