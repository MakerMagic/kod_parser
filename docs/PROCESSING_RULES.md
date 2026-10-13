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

Cleaning starts only after raw structured data has been successfully produced.

Input:

```text
data/raw/

Output:
data/clean/

Cleaning operates on structured raw records. It must not reopen or reparse the original PDF unless a separate debugging task explicitly requires it.
Cleaning may perform
Text normalization
- normalize repeated spaces;
- normalize unnecessary line breaks;
- normalize leading/trailing whitespace;
- normalize known encoding artifacts;
- normalize consistently identified PDF extraction artifacts;
- standardize equivalent Unicode characters where this does not change meaning.
Question structure normalization
- standardize representation of question text;
- standardize subpoint structure;
- standardize option labels such as A–E;
- normalize multiline options into consistent structured values;
- standardize empty/null representations.
Metadata normalization
- standardize source names;
- standardize section names;
- standardize document-role values;
- standardize year/question-number representations;
- normalize known metadata formats without inventing missing values.
Image/reference normalization
- standardize image-reference structure;
- standardize paths or asset identifiers;
- preserve the relationship between an image and its question, option, or subpoint.
Known extraction artifact removal
Cleaning may remove artifacts only when they are reliably identified as non-content, for example:
- repeated page headers or footers;
- known navigation text such as Turn Over;
- known extraction-only separators;
- duplicated whitespace or layout artifacts.
Do not remove text merely because it appears unusual.
Cleaning must NOT perform
Cleaning must not:
- modify data/raw/;
- overwrite raw text;
- paraphrase question wording;
- simplify question meaning;
- infer missing question content;
- invent missing metadata;
- determine correct answers;
- match questions to answer files;
- categorize questions;
- silently remove uncertain content;
- hide parser failures by making malformed raw output appear valid.
Raw preservation
Every cleaned record must remain traceable to its raw record.
Where practical, retain:
- stable question identity;
- source metadata;
- input/source reference;
- raw-record reference;
- warnings relevant to downstream processing.
If cleaning resolves a formatting issue, the original raw value must still remain available in data/raw/.
Uncertainty
Cleaning may resolve purely representational uncertainty only when there is deterministic evidence.
Example:
"A   text"
→
label = "A"
text = "text"

Cleaning must not convert semantic uncertainty into certainty.
If the parser was genuinely unsure whether content belongs to option A or B, cleaning must preserve that warning rather than guessing.
Determinism
The same raw input should produce the same clean output.
Cleaning rules should be explicit and reproducible.
Avoid heuristic transformations that depend on unrelated files, network access, or acquisition method.

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