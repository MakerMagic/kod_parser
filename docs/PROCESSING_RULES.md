# Processing Rules

## Active pre-final boundary

Current development assembles only successfully categorized, issue-free TSA/BMAT
canonical records into one pre-final JSON. Earlier-stage rules below describe their
own historical processing responsibilities, not work to rerun here. Pre-final does
not parse, clean, match, categorize, repair input or generate explanations. Missing
required data is recorded as a validation exclusion. Preserve validated content;
use deterministic examination IDs and difficulty=null. Question rendering follows
assembly; database import and difficulty assignment are separate later tasks.
The authoritative ten-category catalogue is `categorization/patterns.json`; historical
category proposals below do not add pre-final labels or BMAT-to-TSA mappings.

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

## Answer / Explanation Matching 2008-2016 Parsing

Before matching, parse:

```text
TSA-2008-2016-Explained-Answers.pdf

The parser must treat the document as a multi-year, multi-section source.
Year handling
A year heading appears before the corresponding material.
The active year should remain in effect until a new valid year heading is encountered.
Do not hard-code page numbers.
Section handling
Parse only:
SECTION 1

END OF SECTION marks the end of the relevant Section 1 content.
Section 2 must be skipped completely.
END OF PAPER may be used as a structural signal before transition to the next year.
Do not depend on font family, font size, or visual styling as the primary semantic signal.
Answer Entry Structure
A new answer entry begins from a structure conceptually equivalent to:
Question {question_number}: {correct_answer}

The explanation continues until the next valid question entry or structural section/year boundary.
The parser must support explanations that continue across page boundaries.
Explanation Preservation
Explanation parsing should preserve:
- paragraph boundaries;
- multi-paragraph explanations;
- bullet lists;
- optional incorrect-choice analysis;
- original ordering.
Common transition phrases may help detect incorrect-choice analysis, for example:
Let us look at why the other answer choices are wrong:

or:
In this case, it is also useful to arrive at the answer by eliminating the other answers:

These phrases may be useful signals but must not become the only supported structure.
Do not assume every explanation contains incorrect-choice analysis.
Matching Rules
Matching starts only after both sides exist as structured data.
Preferred conceptual matching key:
source + year + paper/variant + section + question_number

Matching must:
- validate identity fields;
- detect missing candidates;
- detect multiple candidates;
- preserve unmatched records;
- preserve warnings;
- attach both correct answer and explanation when matched.
Do not:
- match directly from PDF text;
- match by filename alone;
- silently select one ambiguous candidate;
- repair parser errors inside the matcher;
- suppress unresolved warnings.
Matching Backtesting
Matching backtesting must allow inspection of:
1. question identity;
2. question text/options;
3. correct answer;
4. explanation;
5. incorrect-choice analysis, if present;
6. question source metadata;
7. answer source metadata;
8. matching status;
9. matching warnings.
The correct answer and explanation must appear in separate inspection sections.

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
