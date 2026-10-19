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
clean JSON folder. Raw references, `visual_assets` and `raw_record` stay unchanged
by option crop derivation.
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
An ordered paragraph block may have role `list_marker_artifact` when a standalone
marker is verified between a lead-in and a genuine list. Its text and source-line
references remain intact; only the readable paragraph/list projections exclude
that marker. Unknown symbols and encoded meaningful item text are not discarded.

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

### Derived Final Explanation

Each merged record adds `final_explanation` without changing its original
`answer.explanation` snapshot or any raw/clean inputs. It contains `status`
(`available`, `uncertain`, `unavailable`), `ordering`, ordered `blocks`,
`source_reference`, `source_warnings`, `issues`, `unplaced_components`,
`omitted_artifacts` and `deduplicated_blocks`. `reason` explains unavailable
content. Availability describes reconstruction, not verification of the source's
reasoning; existing source warnings keep the view uncertain.

Blocks retain original paragraph/list/visual types, roles, text, option labels,
line/page references and asset indices. Added `source_pointer` values are relative
to the answer snapshot; `source_reference` identifies its original JSON/hash/record
pointer. Visual paths still resolve relative to the original answer JSON, never
the merged output. Manual-source provenance remains in the unchanged answer.

Unique original block ordinals determine reading order, with source-span conflict
checks. Non-overlapping source spans are the fallback when ordinals are absent;
a single block needs no inferred order. Component projections are checked for
coverage, not concatenated. Exact block aliases are represented once; repeated
text at different source positions remains. Transition metadata is used only if
that transition is not already represented by an earlier paragraph. Verified
`list_marker_artifact` blocks are omitted from readable flow but retained with
their pointers. No other text or symbols are removed.

Ambiguous order produces no invented combined sequence: original pieces stay in
`unplaced_components`, with `final_explanation_order_uncertain`. Missing/conflicting
projection content and unplaced/missing visual references produce
`final_explanation_content_unplaced` / `final_explanation_visual_unresolved`.
These findings enter matching reports without changing exact-key match status.
Answer-only sources explicitly remain unavailable; source previews alone are not
silently promoted to decoded explanation content. Older matched files can be
inspected with an in-memory derived view, without changing their stored JSON.

### Blackstone 2021/2022 answer-source profile

`parsers/blackstone_explained_answers/` produces the same `answer_raw` v1 contract,
independently of the legacy layout. Additive page fields retain `header_line_refs`,
`content_top`, `section` and raster/vector `objects`. Raw `header_line_refs` and
`explanation_line_refs` account for paired headers and complete explanation text.
Original default/geometric page extraction remains preserved.

`explanation.visual_assets` stores ordered rendered crops with source PDF/hash,
year/question, page/bbox/graphic bbox, object IDs/types, asset index/ID, relative
path/hash/dimensions and warnings. Ordered `type="visual"` blocks reference
`asset_index` and retain contained text's raw line references. Wider previews
keep their existing meaning. Unassigned regions are saved as `issues[].visual_asset`
without inventing ownership. Legacy records without these fields remain supported.
Matching accepts explicit `--years` with unchanged legacy defaults and separate
new-year outputs/reports. Source issues remain traceable in merged QA; missing or
conflicting saved assets fail readiness.

### Explicit manual explanation supplement

`parsers.manual_explanations` imports one user-approved structured JSON source
only when explicitly invoked. It writes a separate `answer_raw` v1 intermediate;
it does not patch PDF-derived answers. Approved definitions live under
`processors/matching/manual_sources/`: the missing Q46 2022 supplement (2022,
not the corrected 2026 typo), and explicit 2008 Q12 / 2016 Q38 replacements.
`provenance` records manual origin, approval, text JSON pointer/hash
and answer origin; `source_document.related_sources` retains the associated PDF
reference/hash. Raw text is exact user text, with no invented PDF spans or pages.
Optional `target_question_key` must equal the matched clean source key. Missing
questions are never auto-filled, and ordinary duplicate answer candidates remain ambiguous.
Manual origin is shown explicitly in HTML inspection and source metadata.

Optional `explanation_blocks` preserves manually specified paragraphs/lists;
coverage validation checks all supplied text and list `raw_text` markers. Optional
hashed `evidence` files become related sources. An explicit
`provenance.replaces_explanation` pins an original answer ID, PDF hash and SHA-256
of its canonical sorted-key explanation JSON. Matching can select exactly one
approved replacement over exactly one pinned original, only with a unique clean
question, exact target key, consistent metadata and an unchanged correct answer.
Unverified/duplicate replacements do not resolve ambiguity. The original complete
candidate, warnings, references and previews stay in
`superseded_answer_candidates`; it is not deleted or rewritten. Optional
`preserved_source_fragments` must match original block text exactly and remain
present in the replacement. The selected manual snapshot drives the component
sections and Final Explanation; the original stays visible in a separate audit
section. Superseded source findings remain in a separate report history table,
not falsely labelled as parser fixes.

### Answer-only ruled key profile (2017–2019)

`parsers/blackstone_answer_keys/` independently produces `answer_raw` v1.
`source_document.document_role="answer_key"` and `explanations_supplied=false`
declare the actual source content. Explanation text is empty, structural lists
are empty and `explanation.availability="not_supplied_by_source_format"`;
this is distinct from failed explanation extraction. Generic validation rejects
contradictory populated explanation fields. `raw.cells`, `cell_bboxes`, `row_bbox`,
`row_index`, `line_refs` and exact `source_excerpt` preserve the table row.
`visual_previews[].role="answer_key_row"` identifies saved row screenshots,
not explanation images. Invalid/ambiguous rows retain raw content but have null
correct answers; duplicate identities remain candidates, never force-matched.

### Official 2020 full-explanation profile

`parsers/official_2020_answers/` independently produces the same `answer_raw` v1
contract from question/options/explanation pages. `explanation.presentation` is
`full_explanation`: one paragraph-type block contains the complete explanation,
including its paragraph/newline spacing; choice/list projections stay empty.
`raw` retains exact explanation spans, question/options text, all source line
references and geometric boundary evidence. Complete source-page previews are
saved separately; original source and question RAW/CLEAN inputs are immutable.

`answer_inference` retains status, method (`explicit_phrase`, `semantic_pattern`
or `unresolved`), all positive candidate evidence and normalized comparison spans.
Conflicting or unsupported candidates leave `correct_answer` null. No answer
lookup table is used. Optional `question_evidence` contains extracted question
prose and labelled options; generic matching checks the opening source line and
every supplied textual option against the clean question before accepting the
numeric-key match. `matching.source_question_verified` records that check.
HTML presents one Full Explanation and an explicit inference-evidence section,
without separate incorrect-answer/other-list presentation for this profile.

### Explicit pinned clean body visuals

The single approved 2022 Q44 mapping and supplied PNG live in the clean module's
`pinned_sources/`. The raw parser/schema remain unchanged. Clean `visual_assets`
retains every original asset and adds a manual composite with
`path_base="clean_json_parent"`, `provenance.origin="user_supplied_pinned_body_visual"`,
source PDF/hash/question key, mapping/image file references/hashes and complete
`replaced_raw_assets`. `main_body` uses one composite visual block in place of
the approved sixteen consecutive blocks, preserving all other content and order.
`body_visual_overrides` records the explicit approval/provenance; original raw
snapshots, warnings and source block references remain. `cleaning.body_asset_rules`
declares the rule. Group/source/image conflicts keep original body blocks and a
cleaning issue; readiness and inspection validate both pinned source and saved copy.

## Categorization schema v1

The independent `categorization/` layer consumes existing `matched` v1 files.
It writes to `data/categorized/blackstone/`, never into raw/clean/merged inputs.
`matching_handoff.json` is a hash lock over canonical inputs, per-record pointers/
content hashes, and source/asset dependencies; it detects drift, not an archive
copy. Explicit refresh is required after an intentional upstream change.

`*.categorized.json` contains `stage="categorized"`, `schema_version="1"`, owner,
handoff/model references, logic/version/code hashes, records and checked summary.
Each record has a stable identity/source key and hashed `matched_reference`
(`path`, `sha256`, `json_pointer`, `record_sha256`); an unchanged readable
`question_view` (body/prompt/options/visual references); correct answer; Final
Explanation; question/answer/AI provenance references; preserved upstream context;
and an independent `categorization` object. Raw snapshots are referenced, not
copied into yet another full question extraction layer.

Categorization fields: nullable `category` (currently Problem-Solving / Critical Thinking),
`subcategories` array, `status` (`classified`, `multi_label`, `needs_review`,
`ambiguous`, `unclassified`), candidate patterns/support/examples, active pattern
IDs, evidence/rationale, confidence semantics and review issues. Multi-label
Problem-Solving may include Relevant Selection + Finding Procedures. Conflicting
Critical Thinking intents remain ambiguous, not a forced multi-label result.
An accepted label is model-supported, not manually approved. Unresolved rows
retain candidates and issues; a supported top-level category alone is not counted
as successful complete categorization. Summary counts use successful rows only,
with unresolved rows reported separately. No upstream warning is cleared.

The versioned pattern catalogue stores definitions, positive/counter indicators
and cognitive tasks. Reviewed examples are training evidence, never runtime ID
exceptions. Model/version references preserve reproducibility as patterns evolve.
Inspection layers categorization onto matching HTML without changing its input.

Pattern catalogue v2 also stores category metadata (`engine`, supported
`modalities`, `multi_label`). Eligibility and output validation use this metadata;
current Critical Thinking excludes meaningful question visuals, not source
screenshots, decorative objects or explanation images. New profile-based
families can share the existing evidence/status/report schema. Spatial
representation equivalence joins method equivalence under Identifying Similarity;
material filtering can coexist with similarity when separately supported.
Optional `comparison` and per-row `previous_categorization` / `previous_main_question`
are QA-only before/after evidence, never runtime classification inputs.

Catalogue v3 stores `semantic_families` with lexical indicators, semantic intent,
required context, counter-evidence, modality and confidence-contribution meaning.
The trained model freezes these families; active family evidence is exposed in
each categorization result. Comparison counts distinguish resolutions by previous
status (unclassified/needs_review/ambiguous) without counting status-only moves as
resolved. No confidence thresholds were lowered for this refinement.

## BMAT RAW / CLEAN projections

BMAT RAW retains immutable page strings, question blocks, source keys, page spans
and native object metadata. Additive `raw_components` contains `main_body`,
`main_question`, `body_equals_question`, method and normalization flag.
No separate textual passage uses `Equals question` plus the explicit boolean;
the actual prompt remains in `main_question`. Exact-span
`raw.visual_text_exclusions` / `raw.structural_exclusions` explain ownership.
Readable layout interpretations do not replace exact `text` / `raw_span`.
Prior crop candidates remain traceable; source assets are not overwritten.

BMAT CLEAN follows the existing clean-document shape: `stage`, `schema_version`,
`cleaning`, `document`, `raw_reference`, `questions`. Each item preserves identity,
an exact `raw_record` snapshot, SHA/pointer reference, ordered `main_body`
text/visual blocks, `main_question`, `options`, unchanged assets and complete
`bmat_filter`. Asset paths resolve relative to `raw_reference.path`, not CLEAN.
No PDF parsing, answer inference or matching occurs in cleaning.

`cleaning_issues[].origin` distinguishes `raw` propagation from actual `cleaning`
defects. `pipeline_status` is `clean_ready`, `upstream_review`, `cleaning_review`
or `intentional_skip`; `pipeline_eligible` requires no skip and no issues.
Skipped records remain inspectable without becoming genuine parser failures.

BMAT exclusion rule v2 adds `Subpoints` and `Drawing Inferences`, with all
applicable tags retained. `options[].glyph_layout` records native line/point
and exact nearby glyph geometry, without normalizing RAW mathematical content.
CLEAN may add `fraction_normalization` evidence and `render_text_only` while
retaining the original text/crops in `raw_record` and unchanged image references.
Verified table-row false choices remain under `raw.rejected_option_candidates`
with structural rejection evidence; no separate answer set is invented.

Independent BMAT categorization currently consumes CLEAN directly for targeted
task-intent attribution: `owner: bmat_categorization_v1`, `input_stage: clean`,
hashed sources, stable identities, question snapshots and `categorization`.
It reuses TSA category names, not matching success. `matching_status: not_run`
is explicit. Statuses distinguish `supported`, `intentional_skip`, `needs_review`
and `not_evaluated` (normal attribution outside the targeted pass). No correct
answer/explanation or completed normal dataset is claimed by this layer.
