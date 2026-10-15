"""2021/2022 layout: anchored number + correct-answer statement, not legacy headers."""

import re
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pdfplumber

from .structure import ITEM, reference, structure
from .visuals import attach_visuals, objects_on_page, save_visuals

PAGE_HEADER = re.compile(r"TSA\s*SECTION\s*([12])\s*[-–—]?\s*(20\d{2})", re.IGNORECASE)
INLINE = re.compile(
    r"(\d{1,2})[.)]?\s+(The\s+correct\s+answer\s+is\b.*)", re.IGNORECASE
)
NUMBER = re.compile(r"(\d{1,2})[.)]?")
ANSWER = re.compile(r"The\s+correct\s+answer\s+is\b(.*)", re.IGNORECASE)


def extract_pages(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        metadata = dict(pdf.metadata or {})
        for page in pdf.pages:
            rows = page.extract_text_lines(
                x_tolerance=1, y_tolerance=3, return_chars=True
            )
            lines, offset = [], 0
            for index, row in enumerate(rows, 1):
                value = row["text"]
                lines.append(
                    {
                        "page": page.page_number,
                        "line_id": index,
                        "text": value,
                        "start": offset,
                        "end": offset + len(value),
                        "bbox": [row["x0"], row["top"], row["x1"], row["bottom"]],
                    }
                )
                marker = ITEM.match(value)
                if marker:
                    chars = sorted(
                        (c for c in row["chars"] if c["text"].strip()),
                        key=lambda c: c["x0"],
                    )
                    prefix_length = len(marker[1].strip())
                    if len(chars) > prefix_length:
                        lines[-1]["content_x"] = chars[prefix_length]["x0"]
                offset += len(value) + 1
            headers = [
                line
                for line in lines
                if PAGE_HEADER.fullmatch(line["text"].strip())
                and line["bbox"][3] <= page.height * 0.16
            ]
            pages.append(
                {
                    "page": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "raw_text": page.extract_text() or "",
                    "layout_text": "\n".join(line["text"] for line in lines),
                    "lines": lines,
                    "header_line_refs": [reference(line) for line in headers],
                    "content_top": max(
                        (line["bbox"][3] for line in headers), default=0
                    ),
                    "objects": objects_on_page(page),
                }
            )
            page.close()
    return pages, metadata


def boundary_at(rows, index, pages):
    """Require a left-side anchor and an adjacent correct-answer declaration."""
    line = rows[index]
    page = pages[line["page"] - 1]
    if line["bbox"][0] > page["width"] * 0.18:
        return None
    inline = INLINE.fullmatch(line["text"].strip())
    number = NUMBER.fullmatch(line["text"].strip())
    if inline:
        value, answer_text, count = int(inline[1]), inline[2], 1
    elif number and index + 1 < len(rows):
        following = rows[index + 1]
        answer = ANSWER.fullmatch(following["text"].strip())
        height = line["bbox"][3] - line["bbox"][1]
        if (
            answer is None
            or abs(following["bbox"][0] - line["bbox"][0]) > height * 2
            or following["page"] == line["page"]
            and not 0 <= following["bbox"][1] - line["bbox"][3] <= height * 3
        ):
            return None
        value, answer_text, count = int(number[1]), following["text"], 2
    else:
        return None
    if not 1 <= value <= 50:
        return None
    tail = ANSWER.fullmatch(answer_text)[1].strip()
    letter = re.fullmatch(r"([A-E])[.]?", tail, re.IGNORECASE)
    return {
        "index": index,
        "count": count,
        "number": value,
        "correct_answer": letter[1].upper() if letter else None,
    }


def parse_pdf(path, *, asset_dir, overwrite=False):
    path, asset_dir = Path(path).resolve(), Path(asset_dir).resolve()
    pages, metadata = extract_pages(path)
    digest = sha256(path.read_bytes()).hexdigest()
    headers = [
        (page, line, PAGE_HEADER.fullmatch(line["text"].strip()))
        for page in pages
        for line in page["lines"]
        if any(line["line_id"] == ref["line_id"] for ref in page["header_line_refs"])
    ]
    years = {int(match[2]) for _, _, match in headers}
    if len(years) != 1 or not years <= {2021, 2022}:
        raise ValueError(
            "New Blackstone profile requires one unambiguous 2021/2022 header year"
        )
    year = years.pop()
    source = {
        "path": str(path),
        "filename": path.name,
        "sha256": digest,
        "metadata": metadata,
    }
    data = {
        "stage": "answer_raw",
        "schema_version": "1",
        "parser": {"profile": "blackstone_section1_explained_answers", "version": "2"},
        "source_document": source,
        "pages": pages,
        "boundaries": [
            {
                "type": "page_header",
                "year": year,
                "section": f"section_{match[1]}",
                **reference(line),
            }
            for _, line, match in headers
        ],
        "answers": [],
        "issues": [],
    }
    rows = []
    active_section = None
    for page in pages:
        page_headers = [match for p, _, match in headers if p["page"] == page["page"]]
        if page_headers:
            sections = {match[1] for match in page_headers}
            if len(sections) != 1:
                raise ValueError("Conflicting section headers on one source page")
            active_section = next(iter(sections))
        page["section"] = f"section_{active_section}"
        if active_section != "1":
            data["issues"].append(
                {
                    "code": "section_excluded",
                    "reason": "Non-SECTION-1 page retained but not parsed",
                    "year": year,
                    "section": f"section_{active_section}",
                    "page": page["page"],
                }
            )
            continue
        excluded = {ref["line_id"] for ref in page["header_line_refs"]}
        rows.extend(line for line in page["lines"] if line["line_id"] not in excluded)
    boundaries, index = [], 0
    while index < len(rows):
        candidate = boundary_at(rows, index, pages)
        if candidate:
            boundaries.append(candidate)
            index += candidate["count"]
        else:
            index += 1
    if not boundaries:
        raise ValueError(
            "No supported number/correct-answer boundaries; source not parsed"
        )
    if boundaries[0]["index"]:
        data["issues"].append(
            {
                "code": "source_content_unassigned",
                "year": year,
                "reason": "Content precedes the first supported question header; preserved in page text",
                "line_refs": [reference(l) for l in rows[: boundaries[0]["index"]]],
            }
        )
    for position, boundary in enumerate(boundaries):
        start = boundary["index"]
        end = (
            boundaries[position + 1]["index"]
            if position + 1 < len(boundaries)
            else len(rows)
        )
        selected = rows[start:end]
        header_rows = selected[: boundary["count"]]
        body = selected[boundary["count"] :]
        number = boundary["number"]
        answer = {
            "answer_id": f"{digest[:20]}_{year}_section_1_q{number}_r{position + 1}",
            "year": year,
            "section": "section_1",
            "question_number": number,
            "correct_answer": boundary["correct_answer"],
            "paper": None,
            "variant": None,
            "source_document": source.copy(),
            "visual_previews": [],
            "warnings": []
            if boundary["correct_answer"]
            else ["malformed_question_header:correct_answer_unavailable"],
        }
        # A skipped ordinal is a missing-record issue, not itself evidence that
        # this explanation's confirmed boundaries or list continuation failed.
        # Actual orphan answer declarations still make ownership ambiguous.
        for line in body:
            if ANSWER.fullmatch(line["text"].strip()):
                answer["warnings"].append(
                    f"explanation_boundary_unresolved:orphan_correct_answer_declaration:page_{line['page']}_line_{line['line_id']}"
                )
        next_line = rows[end] if end < len(rows) else None
        first_page = header_rows[0]["page"]
        last_page = next_line["page"] if next_line else pages[-1]["page"]
        segments = []
        for page_number in range(first_page, last_page + 1):
            page = pages[page_number - 1]
            if page["section"] != "section_1":
                continue
            on_page = [line for line in selected if line["page"] == page_number]
            y0 = (
                header_rows[0]["bbox"][1] - 2
                if page_number == first_page
                else page["content_top"] + 2
            )
            y1 = (
                next_line["bbox"][1] - 2
                if next_line and next_line["page"] == page_number
                else page["height"]
            )
            if y1 <= y0:
                continue
            # A next-page header is not evidence of an empty continuation page.
            objects = [
                o for o in page["objects"] if o["bbox"][1] >= y0 and o["bbox"][3] <= y1
            ]
            if not on_page and not objects:
                continue
            segments.append(
                {
                    "page": page_number,
                    "start": on_page[0]["start"] if on_page else 0,
                    "end": on_page[-1]["end"] if on_page else 0,
                    "bbox": [0, max(y0, 0), page["width"], y1],
                }
            )
        answer["raw"] = {
            "header": header_rows[0].copy(),
            "header_line_refs": [reference(line) for line in header_rows],
            "explanation_line_refs": [reference(line) for line in body],
            "span_base": "pages.layout_text",
            "page_spans": segments,
            "boundary": "next_question" if next_line else "end_of_file",
            "source_excerpt": "\n".join(
                pages[s["page"] - 1]["layout_text"][s["start"] : s["end"]]
                for s in segments
            ),
        }
        answer["page_reference"] = {
            "start_page": min(s["page"] for s in segments),
            "end_page": max(s["page"] for s in segments),
        }
        attach_visuals(answer, body, pages, structure)
        data["answers"].append(answer)
        data["boundaries"].append(
            {
                "type": "question",
                "year": year,
                "question_number": number,
                "header_line_refs": answer["raw"]["header_line_refs"],
            }
        )
    counts = Counter(a["question_number"] for a in data["answers"])
    for previous, current in zip(data["answers"], data["answers"][1:]):
        if current["question_number"] > previous["question_number"] + 1:
            missing = list(
                range(previous["question_number"] + 1, current["question_number"])
            )
            for number in missing:
                data["issues"].append(
                    {
                        "code": "answer_header_missing",
                        "year": year,
                        "section": "section_1",
                        "question_number": number,
                        "reason": "Source jumps between confirmed question headers; no number/answer inferred",
                        "answer_pages": previous["page_reference"],
                    }
                )
        elif current["question_number"] <= previous["question_number"]:
            current["warnings"].append(
                "explanation_boundary_unresolved:non_increasing_question_order"
            )
    for answer in data["answers"]:
        if counts[answer["question_number"]] > 1:
            answer["warnings"].append("duplicate_answer_identity")
    save_visuals(data, path, asset_dir, overwrite=overwrite)
    validate_answers(data)
    return data


def validate_answers(data):
    """All original body lines remain accounted for, including visual-contained text."""
    pages = {p["page"]: p for p in data["pages"]}
    for answer in data["answers"]:
        if answer["section"] != "section_1":
            raise ValueError("SECTION 2 leaked into answers")
        raw = answer["raw"]
        for span in raw["page_spans"]:
            if (
                not 0
                <= span["start"]
                <= span["end"]
                <= len(pages[span["page"]]["layout_text"])
            ):
                raise ValueError("Invalid answer source span")
        if raw["source_excerpt"] != "\n".join(
            pages[s["page"]]["layout_text"][s["start"] : s["end"]]
            for s in raw["page_spans"]
        ):
            raise ValueError("Source excerpt changed")
        expected = [(r["page"], r["line_id"]) for r in raw["explanation_line_refs"]]
        actual = []
        for block in answer["explanation"]["blocks"]:
            groups = block["items"] if block["type"] == "list" else [block]
            actual.extend(
                (r["page"], r["line_id"])
                for group in groups
                for r in group["line_refs"]
            )
        if Counter(expected) != Counter(actual) or len(actual) != len(set(actual)):
            raise ValueError("Explanation source lines lost or duplicated")
        headers = {
            (r["page"], r["line_id"])
            for page in data["pages"]
            for r in page["header_line_refs"]
        }
        if headers.intersection(actual):
            raise ValueError("Repeated page header leaked into explanation")
