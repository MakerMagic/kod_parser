# Data Schema

## 1. General Principle

The data model must distinguish between:

1. the physical input file;
2. the acquisition/origin of the file;
3. the examination source represented by the file;
4. the structured content extracted from the file.

These must not be conflated.

A parser must not depend on how the file was acquired.

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

## 12. Raw vs Clean Data

Raw data:

- preserves original extracted content;
- may contain messy text;
- may contain extraction artifacts;
- may contain uncertainty warnings.

Clean data:

- may normalize whitespace;
- may standardize fields;
- may fix known extraction artifacts;
- must not overwrite raw data.

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
