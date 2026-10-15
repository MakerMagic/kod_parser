"""Parse local ruled question/answer tables, without matching or acquisition."""

import re
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

from parsers.blackstone.visuals import _save_crop

PROFILE = "blackstone_ruled_answer_key"


def parse_pdf(path, *, asset_dir, overwrite=False):
    path, asset_dir = Path(path).resolve(), Path(asset_dir).resolve()
    if asset_dir.is_relative_to(path.parent):
        raise ValueError("Answer output must be separate from the source directory")
    digest = sha256(path.read_bytes()).hexdigest()
    data = {
        "stage": "answer_raw",
        "schema_version": "1",
        "parser": {"profile": PROFILE, "version": "1"},
        "source_document": {
            "path": str(path),
            "filename": path.name,
            "sha256": digest,
            "document_role": "answer_key",
            "explanations_supplied": False,
        },
        "pages": [],
        "boundaries": [],
        "answers": [],
        "issues": [],
    }
    headers, candidates = [], []
    with pdfplumber.open(path) as pdf:
        data["source_document"]["metadata"] = dict(pdf.metadata or {})
        for page in pdf.pages:
            lines, offset = [], 0
            for index, row in enumerate(page.extract_text_lines()):
                value = row["text"]
                lines.append(
                    {
                        "line_id": index + 1,
                        "page": page.page_number,
                        "text": value,
                        "start": offset,
                        "end": offset + len(value),
                        "bbox": [row["x0"], row["top"], row["x1"], row["bottom"]],
                    }
                )
                offset += len(value) + 1
            stored = {
                "page": page.page_number,
                "width": page.width,
                "height": page.height,
                "raw_text": page.extract_text() or "",
                "layout_text": "\n".join(line["text"] for line in lines),
                "lines": lines,
                "tables": [],
            }
            data["pages"].append(stored)
            tables = page.find_tables()
            words = page.extract_words()
            for table in tables:
                cells = table.extract()
                if not cells or [str(c or "").strip().lower() for c in cells[0]] != [
                    "question",
                    "answer",
                ]:
                    continue
                above = [line for line in lines if line["bbox"][3] <= table.bbox[1]]
                title = "\n".join(line["text"] for line in above)
                years = set(map(int, re.findall(r"\b20\d{2}\b", title)))
                sections = set(re.findall(r"\bSECTION\s+(\d+)\b", title, re.IGNORECASE))
                supported = (
                    len(years) == 1
                    and years <= {2017, 2018, 2019}
                    and sections == {"1"}
                    and re.search(r"\bAnswer\s+key\b", title, re.IGNORECASE) is not None
                )
                year = next(iter(years)) if len(years) == 1 else None
                headers.append((year, supported))
                stored["tables"].append({"bbox": list(table.bbox), "cells": cells})
                data["boundaries"].append(
                    {
                        "type": "answer_key_table",
                        "year": year,
                        "section": "section_1" if sections == {"1"} else None,
                        "page": page.page_number,
                        "bbox": list(table.bbox),
                        "header_line_refs": above,
                    }
                )
                for row_index, (cell_texts, row) in enumerate(
                    zip(cells[1:], table.rows[1:]), 1
                ):
                    box = list(row.bbox)
                    raw_lines = [
                        line
                        for line in lines
                        if box[1] <= (line["bbox"][1] + line["bbox"][3]) / 2 <= box[3]
                        and box[0] <= line["bbox"][0]
                        and line["bbox"][2] <= box[2]
                    ]
                    values = [str(cell or "").strip() for cell in cell_texts]
                    number = (
                        int(values[0])
                        if values and re.fullmatch(r"\d+", values[0])
                        else None
                    )
                    valid = (
                        len(values) == 2
                        and re.fullmatch(r"[A-E]", values[1]) is not None
                        and number is not None
                        and 1 <= number <= 50
                    )
                    # Corroborate extracted cells against the actual PDF words in each cell.
                    aligned = len(row.cells) == 2 and all(
                        cell is not None
                        and " ".join(
                            w["text"]
                            for w in words
                            if cell[0] <= (w["x0"] + w["x1"]) / 2 <= cell[2]
                            and cell[1] <= (w["top"] + w["bottom"]) / 2 <= cell[3]
                        )
                        == value
                        for cell, value in zip(row.cells, values)
                    )
                    candidates.append(
                        {
                            "year": year,
                            "section": f"section_{next(iter(sections))}"
                            if len(sections) == 1
                            else None,
                            "supported": supported,
                            "number": number,
                            "answer": values[1] if valid else None,
                            "valid": bool(valid and aligned),
                            "page": page.page_number,
                            "bbox": box,
                            "cells": cell_texts,
                            "cell_bboxes": row.cells,
                            "lines": raw_lines,
                            "row_index": row_index,
                        }
                    )
            page.close()
    years = {year for year, _ in headers if year is not None}
    if not years:
        raise ValueError(
            "No unambiguous source year in supported answer-key table headers"
        )
    year = next(iter(years)) if len(years) == 1 else None

    def issue(code, reason, number=None, **extra):
        data["issues"].append(
            {
                "code": code,
                "reason": reason,
                "year": year,
                "section": "section_1",
                "question_number": number,
                "manual_review_required": True,
                **extra,
            }
        )

    counts = Counter(
        (row["year"], row["section"], row["number"])
        for row in candidates
        if row["number"] is not None
    )
    previous = {}
    for ordinal, row in enumerate(candidates, 1):
        number = row["number"]
        problems = []
        if len(years) != 1 or row["year"] not in {2017, 2018, 2019}:
            problems.append("year_mismatch")
        if not row["supported"]:
            problems.append("section_header_parsing_issue")
        if not row["valid"]:
            problems.append("malformed_answer_row")
        if number is not None and counts[row["year"], row["section"], number] > 1:
            problems.append("duplicate_answer")
        if number is not None and number <= previous.get(
            (row["year"], row["section"]), 0
        ):
            problems.append("table_extraction_ambiguity")
        if number is not None:
            previous[row["year"], row["section"]] = number
        for code in problems:
            issue(
                code,
                "Uncertain answer-key row retained without forcing a match",
                number,
                year=row["year"],
                section=row["section"],
                answer_pages={"start_page": row["page"], "end_page": row["page"]},
                raw_row=row,
            )
        if number is None:
            continue
        excerpt = "\n".join(line["text"] for line in row["lines"])
        data["answers"].append(
            {
                "answer_id": f"{digest[:20]}_{row['year']}_{row['section']}_q{number}_r{ordinal}",
                "year": row["year"],
                "section": row["section"],
                "question_number": number,
                "correct_answer": row["answer"] if not problems else None,
                "paper": None,
                "variant": None,
                "source_document": data["source_document"].copy(),
                "page_reference": {"start_page": row["page"], "end_page": row["page"]},
                "raw": {
                    "source_excerpt": excerpt,
                    "cells": row["cells"],
                    "cell_bboxes": row["cell_bboxes"],
                    "row_bbox": row["bbox"],
                    "row_index": row["row_index"],
                    "line_refs": row["lines"],
                    "span_base": "pages.layout_text",
                },
                "explanation": {
                    "availability": "not_supplied_by_source_format",
                    "main_explanation": "",
                    "blocks": [],
                    "paragraphs": [],
                    "bulleted_blocks": [],
                    "choice_analysis": [],
                    "other_lists": [],
                },
                "visual_previews": [],
                "warnings": problems,
            }
        )
    for source_year in sorted(years):
        for number in range(1, 51):
            if not counts[source_year, "section_1", number]:
                issue(
                    "missing_answer",
                    "Expected SECTION 1 answer row absent; no answer inferred",
                    number,
                    year=source_year,
                )
    folder = asset_dir / digest[:20]
    folder.mkdir(parents=True, exist_ok=True)
    with pdfium.PdfDocument(str(path)) as pdf:
        for page_number in sorted(
            {a["page_reference"]["start_page"] for a in data["answers"]}
        ):
            page = pdf[page_number - 1]
            bitmap = page.render(scale=3, rev_byteorder=True)
            try:
                for answer in data["answers"]:
                    if answer["page_reference"]["start_page"] != page_number:
                        continue
                    box = answer["raw"]["row_bbox"]
                    target = folder / f"{answer['answer_id']}_row.png"
                    dimensions = _save_crop(
                        bitmap,
                        bytes(bitmap.buffer),
                        box,
                        [page.get_width(), page.get_height()],
                        target,
                        overwrite,
                    )
                    answer["visual_previews"].append(
                        {
                            "page": page_number,
                            "bbox": box,
                            "path": target.relative_to(asset_dir.parent).as_posix(),
                            "sha256": sha256(target.read_bytes()).hexdigest(),
                            "pixel_size": dimensions,
                            "role": "answer_key_row",
                        }
                    )
            finally:
                bitmap.close()
                page.close()
    return data
