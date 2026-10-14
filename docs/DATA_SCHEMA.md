# Data Schema

## 1. General Principle

The data model must distinguish between:

1. the physical input file;
2. the acquisition/origin of the file;
3. the examination source represented by the file;
4. the structured content extracted from the file.

These must not be conflated.

A parser must not depend on how the file was acquired.

An answer/explanation record should conceptually preserve:

```json
{
  "year": 2012,
  "section": "section_1",
  "question_number": 1,
  "correct_answer": "B",
  "explanation": {
    "paragraphs": [],
    "choice_analysis": [],
    "raw_text": "..."
  },
  "page_start": 1,
  "page_end": 2,
  "warnings": []
}

Exact canonical field names may evolve, but the following must remain separate:
- correct answer;
- explanation;
- explanation structure;
- source metadata;
- warnings.
Explanation Structure
Explanation content should preserve meaningful structure when reliably identifiable.
Possible components include:
- paragraphs;
- bullet lists;
- choice-specific analysis;
- transition text.
Optional analysis of incorrect choices may conceptually be stored as:
[
  {
    "label": "A",
    "text": "..."
  },
  {
    "label": "C",
    "text": "..."
  }
]

Do not invent a choice association when the structure is ambiguous.
Do not flatten meaningful bullet lists or paragraph boundaries unnecessarily.
Matching Metadata
A merged record should explicitly preserve matching state.
Conceptually:
{
  "matching": {
    "status": "matched",
    "question_reference": "...",
    "answer_reference": "...",
    "warnings": []
  }
}

Possible statuses may include:
matched
unmatched_question
unmatched_answer
ambiguous
conflict

Do not silently discard unmatched or ambiguous records.
Merged Data Requirements
A merged record must preserve:
- original question identity;
- question content;
- correct answer;
- explanation;
- explanation structure;
- question-source traceability;
- answer-source traceability;
- matching warnings.
Matching must not destroy the independently processed source records.

## 2. Input File Record

An input file record may contain:

```json
{
  "file": {
    "path": "...",
    "filename": "...",
    "type": "pdf"
  },
  "source": {
    "name": "blackstone",
    "year": 2020,
    "paper": null,
    "variant": null,
    "section": "section_1",
    "document_role": "question_paper"
  },
  "acquisition": {
    "method": "manual",
    "origin": "...",
    "notes": null
  }
}
```

Not every field must always be available. If metadata is uncertain, preserve uncertainty instead of inventing values.

## 3. Acquisition Metadata

Acquisition metadata describes how the file entered the system.

Possible methods:

```text
download
manual
local
archive
api
import
unknown
```

Acquisition metadata is useful for reproducibility and debugging.

It must not determine parsing behavior or question identity.

## 4. Source Metadata

Source metadata describes the document itself.

Examples:

```text
source = blackstone
year = 2020
section = section_1
document_role = question_paper
```

This metadata remains meaningful regardless of how the file was acquired.

## 5. Raw Dataset Structure

Raw parser output should preserve document identity and extraction information.

Example:

```json
{
  "source": "blackstone",
  "year": 2020,
  "paper": null,
  "variant": null,
  "section": "section_1",
  "document_role": "question_paper",
  "input": {
    "filename": "...",
    "path": "..."
  },
  "acquisition": {
    "method": "manual",
    "origin": "..."
  },
  "questions": []
}
```

Raw output belongs in:

```text
data/raw/
```

Raw output must be saved before cleaning, normalization, matching, or categorization.

## 6. Raw Question Object

Each raw question object should contain:

```json
{
  "question_id": "blackstone_2020_section_1_q1",
  "source_question_key": {
    "source": "blackstone",
    "year": 2020,
    "paper": null,
    "variant": null,
    "section": "section_1",
    "question_number": 1
  },
  "question_number": 1,
  "page_reference": {
    "start_page": 1,
    "end_page": 1
  },
  "raw": {
    "question_block": "...",
    "options_block": "...",
    "extraction_notes": []
  },
  "question_text": "...",
  "subpoints": [],
  "options": [
    {
      "label": "A",
      "text": "...",
      "images": []
    },
    {
      "label": "B",
      "text": "...",
      "images": []
    }
  ],
  "images": [],
  "warnings": []
}
```

The exact structure may evolve, but raw extracted text, question number, options, source metadata, and traceability must be preserved.

## 7. Question Identity

Question identity should be based on the examination itself, not acquisition details.

Recommended conceptual key:

```text
source + year + paper/variant + section + question_number
```

The following must not normally define question identity:

- local file path;
- URL;
- downloader;
- acquisition timestamp;
- filename alone.

The same question must remain the same logical question even if the PDF is acquired through a different method.

## 8. Options

Options should be stored as structured objects.

Each option should preserve:

- label;
- text;
- image references, if any;
- uncertainty or warnings, if extraction is incomplete.

Example:

```json
{
  "label": "A",
  "text": "Option text...",
  "images": [],
  "warnings": []
}
```

Options may be text-only, image-only, or text plus image.

Do not silently drop incomplete options.

## 9. Subpoints

If a question contains numbered statements or subparts, preserve them separately when possible.

Example:

```json
[
  {
    "label": "1",
    "text": "First statement..."
  },
  {
    "label": "2",
    "text": "Second statement..."
  }
]
```

Do not assume every question has subpoints.

Do not assume a fixed number of subpoints.

## 10. Images

Images should be first-class extraction elements.

Image records may include:

```json
{
  "image_id": "...",
  "path": "...",
  "page": 1,
  "belongs_to": "question",
  "option_label": null,
  "bbox": null,
  "notes": []
}
```

If exact image extraction is not implemented yet, preserve enough information to show that an image exists or may exist.

Blackstone raw output additionally stores `visual_assets` (ordered graphic crops) and `visual_previews` (ordered question-page layout crops). These are additive; existing raw text and object-level `images` remain preserved. Each saved asset includes `path` relative to the raw JSON directory, `page`, `bbox` in PDF points (top-origin), `asset_type`, `detected_types`, `asset_index`, `order_key`, source SHA/source/year/question number, original `object_ids`, component (`question`, `option`, or `unknown`), optional option label, pixel size, saved SHA, and warnings. Rendered regions use `rendered_crop`, not a claim that vector content was extracted as a standalone raster object. Failed saves retain metadata with null paths and warnings. Page-level assets retain unassigned document graphics. Option image references are added only when geometry supports the association. `raw.page_spans[].bbox` identifies the saved layout region; character spans and text are unchanged.

## 11. Traceability

### Blackstone visual placement (additive)

`layout_blocks` is an optional, ordered question-level list. Text blocks contain `type="text"`, unchanged `text`, `page`, `bbox`, and `raw_span` indexing `raw.question_block`. Visual blocks contain `type="visual"`, `asset_id` referencing `visual_assets[].image_id`, `page`, and the underlying graphic's bounds. Every block has `block_id`, contiguous `order`, `component`, and nullable `label`.

Components are `stimulus`, `question_body`, `subpart`, `option`, `intermediate`, `visual_label`, or `unknown`. Stimulus/stem distinctions are structural estimates, not semantic categorization. `visual_label` text remains in the raw record and is displayed within the saved crop; `asset_ids` identifies the crops containing it. An intermediate graphic is explicitly located between differing components rather than assigned to a passage or option without evidence.

Assets retain existing coarse `belongs_to` values and add `placement` with component/label and neighboring `after_raw_span` / `before_raw_span`. Crop evidence adds `graphic_bbox`, `crop_method`, and full-line `included_text_spans` / `excluded_text_spans`; these evidence spans do not assert that every word on a shared diagram-label row belongs to one crop. Label-only options keep empty text plus saved `options[].images`; confidently saved images resolve only the corresponding empty-image warnings. A contiguous option sequence may extend beyond E. Existing raw fields remain unchanged, and legacy JSON without layout blocks is still inspectable.

For strongly evidenced repeated image choices, `options[].content_type="image"`
and `text=""`; `images` holds the associated asset (including order, page, bounds,
label, path, and warnings). Options also retain `page`, `label_bbox`, and
`association_method`. `raw.text_option_candidates` preserves the initial textual
interpretation before visual association; `raw.question_block`, `options_block`,
and page text/spans are unchanged. Chart/axis text is not ordinary answer text.
Each asset's `visual_text` retains contained extracted tokens, spatial bounds,
and `source_line_span` into the original question block. Rotated glyph bounds
may cover a complete baseline label even when extraction splits its text over
several lines. Legacy records without these additive fields remain supported.

Detected graph crops additionally use `visual_kind="graph"` and optional
`axis_labels` entries (`axis`, correctly ordered `text`, `bbox`, `page`,
`orientation`, `source_line_spans`). Vertical label text follows the PDF glyph
stream and transformation matrix, while the original reversed extraction stays
in `raw.question_block`. If graph-owned extracted lines are removed from the
derived `question_text`, its unmodified former value is saved as
`raw.text_question_candidate`; `layout_blocks` still preserve the exact raw
lines and mark them `visual_label`. No original page/question block is deleted.

A final question should be traceable through the pipeline:

```text
final question
↓
merged record
↓
clean record
↓
raw record
↓
source document
↓
input file
↓
acquisition information
```

Acquisition metadata supports debugging but must not become semantic question identity.

## Clean Data

Clean data is a normalized representation derived from raw structured data.

A clean record should preserve the same logical question identity as its corresponding raw record.

Conceptually:

```json
{
  "question_id": "blackstone_2020_section_1_q1",
  "source": "blackstone",
  "year": 2020,
  "section": "section_1",
  "question_number": 1,

  "raw_reference": "...",

  "question_text": "...",
  "subpoints": [],
  "options": [],
  "images": [],

  "warnings": []
}

```

The exact schema may evolve, but clean data must remain traceable to raw data.
Raw vs Clean
Raw data preserves:
- original extracted text;
- extraction layout/artifacts;
- parser warnings;
- uncertain content;
- debugging information.
Clean data may contain:
- normalized whitespace;
- normalized line breaks;
- standardized option/subpoint structure;
- standardized metadata values;
- normalized image references;
- reliably removed extraction artifacts.
Clean data must not:
- replace or delete the raw record;
- change semantic meaning;
- invent missing information;
- remove unresolved uncertainty;
- contain matching or categorization results unless the pipeline has reached those stages.

## 13. Forbidden Schema Patterns

Do not:

- use filename alone as `question_id`;
- use URL as semantic question identity;
- delete raw question blocks after cleaning;
- replace raw text with cleaned text;
- store final output directly from parser output;
- invent missing metadata;
- silently drop uncertain fields;
- add answer, explanation, or category fields during question-only raw parsing unless the source document contains them.

## Blackstone clean schema v1

`processors/normalization/blackstone/` writes `*.clean.json` to
`data/clean/blackstone/`. It does not modify the raw schema or raw files.

Dataset fields: `stage="clean"`, `schema_version="1"`, `cleaning` (processor,
version and declared rules), `raw_reference` (absolute JSON path/SHA-256),
`document` (unchanged source/input/acquisition/extraction metadata), `questions`.

Each clean question retains its original identity/source key/page mapping and:

- `question_text`: conservative normalization of the whole structured raw text;
- `main_body`: ordered text/visual blocks with raw block IDs/spans/page/bounds;
- `main_question`: one evidenced prompt, or null with a cleaning issue;
- `options` / `subpoints`: original order/labels/associations with normalized text;
- `visual_assets`, `visual_previews`, `images`: original visual references;
- `raw_reference`: raw path/hash, `/questions/N` pointer, original question ID;
- `raw_record`: complete unchanged raw question snapshot, including unknown fields;
- `raw_warnings`, `warnings`, `raw_document_warnings`: unchanged upstream warnings;
- `availability`: separate raw/clean/metadata and option missing/null/empty states;
- `content_accounting`: every nonempty structured text line maps to body, prompt,
  or a visual, with original structured-field offsets and available raw evidence;
- `transformations`: changed field names and before/after hashes;
- `cleaning_issues`: only clean-stage uncertainty or detected reference conflicts.

Original asset paths resolve relative to `raw_reference.path`'s parent.
Image-only options may additionally store `options[].images[].clean_asset`:
derived PNG path (`path_base="clean_json_parent"`), SHA-256, original raw asset
ID/path/SHA-256, page/option label, removal operation, removed letter rectangle,
and pixel crop bounds/size. Only this derived path resolves relative to the
clean JSON folder. Raw references, `visual_assets` and `raw_record` stay unchanged.
`cleaning.asset_rules` declares the independent derived-asset rule. Unsafe or
unavailable derivation remains a cleaning issue; no original image is overwritten.
A missing reference remains an issue, not an invented asset.
Raw-provided answers/explanations remain preserved; none are generated/matched.
Inspecting/reporting checks live raw hashes and saved PNGs without writing JSON.

## Explained-answer intermediate and matched schema v1

The independent source parser in `parsers/explained_answers/` writes
`*.answers.json` under `data/raw/explained_answers/`. This is a common structured
intermediate for matching, not an extension of question-only raw records.

Dataset: `stage="answer_raw"`, `schema_version="1"`, source parser profile/version,
`source_document` (path, filename, SHA-256, PDF metadata), preserved `pages`
(default extraction, geometric layout text/lines/bounds), structural `boundaries`,
`answers`, and `issues`. Each answer retains its content-hash-backed ID,
year/section/question number/correct answer, source document/page range, warnings,
and `raw` header/source excerpt/exact spans into `pages.layout_text`. Absent
paper/variant metadata is null. `visual_previews` retain page/bounds/PNG hash/path,
relative to the answer JSON parent, including graphical/image-only explanations.

`explanation` contains ordered `blocks`, `main_explanation`, main `paragraphs`,
`bulleted_blocks`, `choice_analysis`, and `other_lists`. All paragraphs/items keep
ordered page/line/span/bbox references. List roles distinguish ordinary lists,
incorrect choices with explicit option labels, and incorrect choices whose labels
remain unmapped. Unavailable text is empty plus a warning, never guessed from an
image. Default raw extraction and readable geometric extraction are both retained.

`processors/matching/` consumes intermediates independently of their PDF format.
It writes separate `*.matched.json` in `data/merged/blackstone/` with
`stage="matched"`, `schema_version="1"`, matching method/scope, readiness results,
hashed input references, `records`, and matching-specific `issues`.

Each merged record preserves exact identity, status (`matched`, `conflict`,
`ambiguous`, `unmatched_question`, or `unmatched_answer`), selected correct answer
only for a successful match, complete clean-question/raw-question and answer
snapshots, question document metadata, both input JSON paths/hashes/pointers, and
candidate snapshots when ambiguous. Matching metadata distinguishes exact core
identity from unverified paper/variant metadata and retained upstream review.
Conflicting/unmatched explanations are preserved even when no answer is assigned.
Raw/clean JSON and PNGs remain immutable. Inspection validates live references;
reports group only matching findings with unique-record counts and direct upstream
causes. See `MATCHING_2008-2016_BACKTEST.md` for commands and limitations.
