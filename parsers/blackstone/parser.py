"""Lossless page extraction with conservative TSA question segmentation."""

import re
from collections import Counter
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

import pdfplumber

from .visual_structure import add_layout
from .visuals import save_visuals

PARSER_VERSION = "3"
SOURCE_FIELDS = ("source", "year", "paper", "variant", "section", "document_role")
NUMBER = re.compile(r"^(\d{1,3})(?:[ \t]+|$)")
OPTION = re.compile(r"^([A-Z])(?:[ \t]+|$)")
# These markers occur in the local papers with missing ToUnicode font maps.
# Interpret only structural glyphs; keep every CID token in the extracted text.
CID_NUMBER = re.compile(r"^((?:\(cid:(?:19|2[0-8])\))+)(?:\(cid:3\))*[ \t]*")
CID_OPTION = re.compile(r"^\(cid:(3[6-9]|40)\)(?:\(cid:3\))*[ \t]*")
ADMIN = re.compile(
    r"^(?:BLANK PAGE|END OF (?:PAPER|QUESTIONS)|Copyright|©|\[Turn)", re.IGNORECASE
)


def _marker(text, kind):
    """Return the label, content offset, and whether it was CID-encoded."""
    match = (NUMBER if kind == "number" else OPTION).match(text)
    if match:
        label = int(match[1]) if kind == "number" else match[1]
        return label, match.end(), False
    match = (CID_NUMBER if kind == "number" else CID_OPTION).match(text)
    if not match:
        return None
    if kind == "number":
        label = int("".join(str(int(cid) - 19) for cid in re.findall(r"\d+", match[1])))
    else:
        label = chr(int(match[1]) + 29)
    return label, match.end(), True


def _metadata(pages, pdf_metadata, supplied):
    cover = pages[0]["raw_text"] if pages else ""
    title = str(pdf_metadata.get("Title", ""))
    header = "\n".join(cover.splitlines()[:10])
    warnings = []
    year_matches = re.findall(r"\b(?:19|20)\d{2}\b", header + "\n" + title)
    years = set(map(int, year_matches))
    year = next(iter(years)) if len(years) == 1 else None
    # A cover can mention the next section in its instructions. Use headings only.
    sections = set(re.findall(r"\bsection\s+(\d+)\b", title, re.IGNORECASE))
    for line in cover.splitlines():
        if re.match(
            r"(?:SECTION\s+\d+\b|Thinking Skills Assessment)", line, re.IGNORECASE
        ):
            sections.update(re.findall(r"\bsection\s+(\d+)\b", line, re.IGNORECASE))
    section = "section_" + next(iter(sections)) if len(sections) == 1 else None
    recognized = bool(
        re.search(r"Thinking Skills Assessment|\bTSA\b", cover + title, re.IGNORECASE)
    )
    role = (
        "question_paper"
        if recognized
        and re.search(r"instructions? to candidates", cover, re.IGNORECASE)
        else None
    )
    paper_match = re.search(r"\b(?:\d{4}|[A-Z]\d{3})/\d{2}\b", header)
    result = {
        "source": "blackstone",
        "year": year,
        "paper": paper_match[0] if paper_match else None,
        "variant": "specimen"
        if re.search(r"\bspecimen\b", header + title, re.IGNORECASE)
        else None,
        "section": section,
        "document_role": role,
    }
    unknown = set(supplied) - set(SOURCE_FIELDS)
    if unknown:
        raise ValueError(f"Unknown source metadata fields: {sorted(unknown)}")
    if supplied.get("source", "blackstone") != "blackstone":
        raise ValueError("This parser uses the blackstone source profile")
    result.update(supplied)
    for field in ("year", "section", "document_role"):
        if result[field] is None:
            warnings.append(f"uncertain_metadata:{field}")
    if not re.search(r"blackstone", cover + title, re.IGNORECASE):
        warnings.append("source_assigned_by_parser_profile:not_verified_in_document")
    if not recognized:
        warnings.append("unrecognized_document:review_full_page_text")
    return result, recognized, warnings


def _read_page(page):
    raw_text = page.extract_text(layout=False) or ""
    lines = []
    cursor = 0
    warnings = []
    for extracted in page.extract_text_lines(return_chars=True):
        line = {key: value for key, value in extracted.items() if key != "chars"}
        # Spatial word boxes keep adjacent diagram columns out of each other's crops.
        line["word_boxes"] = []
        line["word_texts"] = []
        word = []
        for char in extracted["chars"]:
            separator = char["text"].isspace() or char["text"] == "(cid:3)"
            if word and (separator or char["x0"] > word[-1]["x1"] + 3):
                line["word_boxes"].append(
                    [
                        min(c["x0"] for c in word),
                        min(c["top"] for c in word),
                        max(c["x1"] for c in word),
                        max(c["bottom"] for c in word),
                    ]
                )
                line["word_texts"].append("".join(c["text"] for c in word))
                word = []
            if not separator:
                word.append(char)
        if word:
            line["word_boxes"].append(
                [
                    min(c["x0"] for c in word),
                    min(c["top"] for c in word),
                    max(c["x1"] for c in word),
                    max(c["bottom"] for c in word),
                ]
            )
            line["word_texts"].append("".join(c["text"] for c in word))
        line["label_positions"] = [
            {
                "label": char["text"]
                if len(char["text"]) == 1 and "A" <= char["text"] <= "Z"
                else chr(int(re.search(r"\d+", char["text"])[0]) + 29),
                "bbox": [char["x0"], char["top"], char["x1"], char["bottom"]],
            }
            for char in extracted["chars"]
            if len(char["text"]) == 1
            and "A" <= char["text"] <= "Z"
            or re.fullmatch(r"\(cid:(?:36|37|38|39|40)\)", char["text"])
        ]
        start = raw_text.find(line["text"], cursor)
        if start < 0:
            warnings.append("line_offset_unavailable:full_page_text_preserved")
            continue
        end = start + len(line["text"])
        lines.append({**line, "start": start, "end": end})
        cursor = end
    if "(cid:" in raw_text or "\ufffd" in raw_text:
        warnings.append("font_encoding_artifacts:raw_tokens_preserved")
    if not raw_text:
        warnings.append("no_extractable_text:blank_or_scanned_page")
    images = []
    for kind, objects in (
        ("raster", page.images),
        ("vector", [*page.curves, *page.rects, *page.lines]),
    ):
        for index, obj in enumerate(objects):
            images.append(
                {
                    "image_id": f"p{page.page_number}_{kind}_{index}",
                    "path": None,
                    "page": page.page_number,
                    "belongs_to": None,
                    "option_label": None,
                    "bbox": [obj["x0"], obj["top"], obj["x1"], obj["bottom"]],
                    "kind": kind,
                    "object_type": obj["object_type"],
                    "decorative": kind == "vector"
                    and obj.get("fill")
                    and not obj.get("stroke")
                    and obj.get("non_stroking_color") in [(1, 1, 1), (0, 0, 0, 0), 1]
                    and (obj["x1"] - obj["x0"]) * (obj["bottom"] - obj["top"])
                    > page.width * page.height * 0.3,
                    "notes": ["reference_to_source_pdf:no_image_file_exported"],
                }
            )
    return {
        "page_number": page.page_number,
        "width": page.width,
        "height": page.height,
        "raw_text": raw_text,
        "images": images,
        "warnings": warnings,
    }, lines


def _body_lines(page, lines):
    # Margins affect structural interpretation only. Full text remains in pages[].
    return [
        line
        for line in lines
        if 35 <= line["top"]
        and line["bottom"] <= page["height"] - 35
        and not ADMIN.match(line["text"])
        and not (
            line["text"].isdigit()
            and line["x0"] > page["width"] * 0.4
            and (line["top"] > page["height"] * 0.85 or line["top"] < 50)
        )
    ]


def _split_fields(block, lines):
    """Use raw offsets; never normalize whitespace or rewrite extracted content."""
    first = _marker(lines[0]["text"], "number")
    text_start = lines[0]["block_start"] + first[1]
    grouped_rows = [
        line
        for line in lines[1:]
        if re.fullmatch(r"[A-E](?:[ \t]+[A-E])+", line["text"])
        or re.fullmatch(r"[A-Z](?:[ \t]+[A-Z])+", line["text"])
        and line["text"].split()
        == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(line["text"].split())])
    ]
    if grouped_rows:
        start = grouped_rows[0]["block_start"]
        label_rows = [
            line
            for line in lines
            if line["block_start"] >= start
            and re.fullmatch(r"[A-Z](?:[ \t]+[A-Z])*", line["text"])
        ]
        candidate_labels = [
            label for line in label_rows for label in line["text"].split()
        ]
        if len(candidate_labels) < 5 or candidate_labels != list(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(candidate_labels)]
        ):
            label_rows = [
                line
                for line in label_rows
                if re.fullmatch(r"[A-E](?:[ \t]+[A-E])*", line["text"])
            ]
        labels = [label for line in label_rows for label in line["text"].split()]
        options = [
            {
                "label": label,
                "text": "",
                "images": [],
                "warnings": [
                    "multi_column_option:content_preserved_in_raw_options_block"
                ],
            }
            for label in labels
        ]
        warnings = ["multi_column_options:text_and_image_association_unresolved"]
        if len(labels) < 5 or labels != list(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]
        ):
            warnings.append(f"incomplete_or_ambiguous_options:{','.join(labels)}")
        return block[text_start:start], block[start:], options, [], warnings
    candidates = [
        (line, marker)
        for line in lines[1:]
        if (marker := _marker(line["text"], "option"))
        and (marker[0] <= "E" or re.fullmatch(r"[F-Z]", line["text"]))
    ]
    if candidates:
        left = min(line["x0"] for line, _ in candidates)
        candidates = [
            (line, marker) for line, marker in candidates if line["x0"] <= left + 4
        ]
    # Take the last A-led sequence, avoiding prose starting with "A ...".
    starts = [i for i, (_, marker) in enumerate(candidates) if marker[0] == "A"]
    selected = candidates[starts[-1] :] if starts else candidates
    # F and later labels require a contiguous choice sequence; an "I ..."
    # sentence in an option is not a new choice merely because it is uppercase.
    confirmed = []
    for candidate in selected:
        label = candidate[1][0]
        if label <= "E" or confirmed and ord(label) == ord(confirmed[-1][1][0]) + 1:
            confirmed.append(candidate)
    selected = confirmed
    warnings = []
    options = []
    options_start = selected[0][0]["block_start"] if selected else len(block)
    for index, (line, marker) in enumerate(selected):
        end = (
            selected[index + 1][0]["block_start"]
            if index + 1 < len(selected)
            else len(block)
        )
        text = block[line["block_start"] + marker[1] : end]
        option_warnings = (
            ["empty_option_text:may_be_image_only"] if not text.strip() else []
        )
        options.append(
            {
                "label": marker[0],
                "text": text,
                "images": [],
                "warnings": option_warnings,
            }
        )
    labels = [option["label"] for option in options]
    if len(labels) < 5 or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)]):
        warnings.append(f"incomplete_or_ambiguous_options:{','.join(labels) or 'none'}")
    if first[2] or any(marker[2] for _, marker in selected):
        warnings.append("cid_structural_markers_interpreted:requires_review")
    question_text = block[text_start:options_start]
    subpoints = []
    for match in re.finditer(r"(?m)^([1-9]\d*)[.)][ \t]+([^\n]*)", question_text):
        subpoints.append({"label": match[1], "text": match[2]})
    return question_text, block[options_start:], options, subpoints, warnings


def parse_pdf(
    input_path,
    *,
    metadata=None,
    acquisition=None,
    asset_dir=None,
    overwrite_assets=False,
):
    """Parse an existing PDF path. Metadata never determines extraction behavior."""
    path = Path(input_path).resolve(strict=True)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {path}")
    digest = sha256(path.read_bytes()).hexdigest()
    pages = []
    all_lines = []
    with pdfplumber.open(path) as document:
        pdf_metadata = dict(document.metadata or {})
        for page in document.pages:
            record, lines = _read_page(page)
            pages.append(record)
            all_lines.append(_body_lines(record, lines))
            page.close()
    source, recognized, warnings = _metadata(pages, pdf_metadata, metadata or {})
    dataset = {
        **source,
        "input": {"filename": path.name, "path": str(path), "sha256": digest},
        "acquisition": dict(acquisition)
        if acquisition is not None
        else {"method": "unknown", "origin": None},
        "extraction": {
            "parser": "blackstone",
            "parser_version": PARSER_VERSION,
            "backend": "pdfplumber",
            "backend_version": pdfplumber.__version__,
            "recognized_question_paper": recognized
            and source["document_role"] == "question_paper",
            "pdf_metadata": pdf_metadata,
        },
        "pages": pages,
        "questions": [],
        "warnings": warnings,
    }
    numeric_lines = [
        line
        for page, lines in zip(pages, all_lines)
        for line in lines
        if _marker(line["text"], "number") and line["x0"] < page["width"] * 0.14
    ]
    # The repeated number column distinguishes question labels from tables and subpoints.
    columns = Counter(round(line["x0"] / 4) * 4 for line in numeric_lines)
    margin = columns.most_common(1)[0][0] + 5 if columns else 0
    pending = None
    for page, lines in zip(pages, all_lines):
        if not lines:
            continue
        starts = [
            i
            for i, line in enumerate(lines)
            if line["x0"] <= margin and _marker(line["text"], "number")
        ]
        if not starts and (
            not page["raw_text"].strip() or "BLANK PAGE" in page["raw_text"]
        ):
            continue
        # Encoded pages without a detectable boundary are not appended to a previous question.
        if not starts and "(cid:" in page["raw_text"] and pending is not None:
            pending = None
            dataset["warnings"].append(f"unassigned_encoded_page:{page['page_number']}")
        cuts = [0, *starts, len(lines)]
        for begin, end in pairwise(cuts):
            if begin == end:
                continue
            if begin in starts:
                marker = _marker(lines[begin]["text"], "number")
                pending = {
                    "number": marker[0],
                    "segments": [],
                    "lines": [],
                    "images": [],
                }
                dataset["questions"].append(pending)
            if pending is None:
                continue
            start_offset = lines[begin]["start"]
            end_offset = lines[end - 1]["end"]
            offset = sum(len(segment["text"]) + 1 for segment in pending["segments"])
            segment = {
                "page": page["page_number"],
                "start": start_offset,
                "end": end_offset,
                "text": page["raw_text"][start_offset:end_offset],
                "bbox": [
                    0,
                    max(0, lines[begin]["top"] - 6),
                    page["width"],
                    lines[end]["top"] - 6 if end < len(lines) else page["height"] - 35,
                ],
            }
            pending["segments"].append(segment)
            pending["lines"].extend(
                {
                    **line,
                    "page": page["page_number"],
                    "block_start": offset + line["start"] - start_offset,
                }
                for line in lines[begin:end]
            )
            top = lines[begin]["top"]
            bottom = lines[end]["top"] if end < len(lines) else page["height"] - 35
            pending["images"].extend(
                {**image, "belongs_to": "question"}
                for image in page["images"]
                if image["bbox"][1] < bottom and image["bbox"][3] > top
            )
    questions = []
    for pending in dataset["questions"]:
        block = "\n".join(segment["text"] for segment in pending["segments"])
        text, options_block, options, subpoints, question_warnings = _split_fields(
            block, pending["lines"]
        )
        if "(cid:" in block or "\ufffd" in block:
            question_warnings.append("font_encoding_artifacts:raw_tokens_preserved")
        if pending["images"]:
            question_warnings.append("graphics_present:option_association_not_resolved")
        number = pending["number"]
        key = {
            field: source[field]
            for field in ("source", "year", "paper", "variant", "section")
        }
        key["question_number"] = number
        if source["year"] is None or source["section"] is None:
            identifier = None
            question_warnings.append("question_id_unavailable:uncertain_metadata")
        else:
            identity_parts = [
                source["source"],
                str(source["year"]),
                source["paper"],
                source["variant"],
                source["section"],
                f"q{number}",
            ]
            identifier = "_".join(
                str(part) for part in identity_parts if part is not None
            )
        questions.append(
            {
                "question_id": identifier,
                "source_question_key": key,
                "question_number": number,
                "page_reference": {
                    "start_page": pending["segments"][0]["page"],
                    "end_page": pending["segments"][-1]["page"],
                },
                "raw": {
                    "question_block": block,
                    "options_block": options_block,
                    "extraction_notes": [
                        "Page spans index unmodified pages[].raw_text; page joins use a newline."
                    ],
                    "page_spans": [
                        {k: v for k, v in segment.items() if k != "text"}
                        for segment in pending["segments"]
                    ],
                },
                "question_text": text,
                "subpoints": subpoints,
                "options": options,
                "images": pending["images"],
                "warnings": question_warnings,
            }
        )
    pending_questions = dataset["questions"]
    dataset["questions"] = questions
    save_visuals(
        dataset,
        pending_questions,
        asset_dir or Path("data/raw/blackstone/assets"),
        overwrite=overwrite_assets,
    )
    for question, pending in zip(questions, pending_questions):
        add_layout(question, pending)
    numbers = [question["question_number"] for question in questions]
    if numbers != list(range(1, len(numbers) + 1)):
        dataset["warnings"].append("nonsequential_or_duplicate_question_numbers")
    expected = (
        re.search(
            r"(?:all|attempt)\s+(\d+)\s+questions", pages[0]["raw_text"], re.IGNORECASE
        )
        if pages
        else None
    )
    if expected and len(questions) != int(expected[1]):
        dataset["warnings"].append(
            f"question_count_mismatch:expected_{expected[1]}_extracted_{len(questions)}"
        )
    if not questions:
        dataset["warnings"].append("no_questions_detected:full_page_text_preserved")
    validate_raw(dataset)
    return dataset


def validate_raw(dataset):
    """Lightweight checks for required fields and exact raw-span traceability."""
    required = {
        *SOURCE_FIELDS,
        "input",
        "acquisition",
        "questions",
        "pages",
        "warnings",
    }
    if required - dataset.keys():
        raise ValueError(
            f"Missing raw dataset fields: {sorted(required - dataset.keys())}"
        )
    if not {"filename", "path", "sha256"} <= dataset["input"].keys():
        raise ValueError("Missing input traceability fields")
    if dataset["year"] is not None and type(dataset["year"]) is not int:
        raise ValueError("Source year must be an integer or null")
    for field in ("questions", "pages", "warnings"):
        if not isinstance(dataset[field], list):
            raise TypeError(f"Raw dataset {field} must be a list")
    pages = {page["page_number"]: page["raw_text"] for page in dataset["pages"]}
    for question in dataset["questions"]:
        fields = {
            "question_id",
            "source_question_key",
            "question_number",
            "page_reference",
            "raw",
            "question_text",
            "subpoints",
            "options",
            "images",
            "warnings",
        }
        if fields - question.keys():
            raise ValueError("Missing raw question fields")
        if (
            type(question["question_number"]) is not int
            or question["question_number"] < 1
        ):
            raise ValueError("Question number must be a positive integer")
        for field in ("options", "subpoints", "images", "warnings"):
            if not isinstance(question[field], list):
                raise TypeError(f"Raw question {field} must be a list")
        key = question["source_question_key"]
        for field in ("source", "year", "paper", "variant", "section"):
            if key.get(field) != dataset[field]:
                raise ValueError("Question source key does not match dataset metadata")
        if key.get("question_number") != question["question_number"]:
            raise ValueError("Question source key does not match question number")
        spans = question["raw"]["page_spans"]
        if not spans:
            raise ValueError("Question must reference at least one raw page span")
        for span in spans:
            if span["page"] not in pages or not 0 <= span["start"] <= span[
                "end"
            ] <= len(pages[span["page"]]):
                raise ValueError("Invalid raw page span")
        if question["page_reference"] != {
            "start_page": spans[0]["page"],
            "end_page": spans[-1]["page"],
        }:
            raise ValueError("Page reference does not match raw page spans")
        reconstructed = "\n".join(
            pages[span["page"]][span["start"] : span["end"]] for span in spans
        )
        if reconstructed != question["raw"]["question_block"]:
            raise ValueError("Raw question block does not match source page spans")
        for option in question["options"]:
            if not {"label", "text", "images", "warnings"} <= option.keys():
                raise ValueError("Missing raw option fields")
            if (
                not isinstance(option["text"], str)
                or len(option["label"]) != 1
                or option["label"] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ):
                raise ValueError("Invalid raw option label or text")
        if "layout_blocks" in question:
            blocks = question["layout_blocks"]
            if [b["order"] for b in blocks] != list(range(1, len(blocks) + 1)):
                raise ValueError("Invalid raw layout order")
            asset_ids = {a["image_id"] for a in question["visual_assets"]}
            for layout in blocks:
                if layout["type"] == "text":
                    span = layout["raw_span"]
                    if (
                        not 0 <= span["start"] <= span["end"] <= len(reconstructed)
                        or reconstructed[span["start"] : span["end"]] != layout["text"]
                    ):
                        raise ValueError("Layout text does not match raw question span")
                elif layout["type"] != "visual" or layout["asset_id"] not in asset_ids:
                    raise ValueError("Invalid raw layout visual reference")
