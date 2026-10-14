"""Local worked-solutions parsing: explicit year/section/header state machine."""

import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import median

import pdfplumber
import pypdfium2 as pdfium

from parsers.blackstone.visuals import _save_crop

from .structure import structure

HEADER = re.compile(r"^Question\s*(\d+)\s*:\s*([A-Z])\s*$", re.IGNORECASE)
QUESTION = re.compile(r"^Question\s*(\d+)\b", re.IGNORECASE)
SECTION = re.compile(r"^SECTION\s*([12])\s*$", re.IGNORECASE)
END = re.compile(r"^END\s*OF\s*(SECTION|PAPER)\s*$", re.IGNORECASE)
YEAR = re.compile(r"20(?:0[89]|1[0-6])")


def parse_pdf(path, *, asset_dir, overwrite=False):
    path, asset_dir = Path(path).resolve(), Path(asset_dir).resolve()
    digest = sha256(path.read_bytes()).hexdigest()
    data = {
        "stage": "answer_raw",
        "schema_version": "1",
        "parser": {"profile": "tsa_2008_2016_explained_answers", "version": "1"},
        "source_document": {"path": str(path), "filename": path.name, "sha256": digest},
        "pages": [],
        "boundaries": [],
        "answers": [],
        "issues": [],
    }
    with pdfplumber.open(path) as pdf:
        data["source_document"]["metadata"] = dict(pdf.metadata or {})
        for page in pdf.pages:
            heights = [c["bottom"] - c["top"] for c in page.chars if c["text"].strip()]
            tolerance = min(8, max(2, median(heights) * 0.65)) if heights else 3
            extracted = page.extract_text_lines(
                x_tolerance=1, y_tolerance=tolerance, return_chars=False
            )
            lines, offset = [], 0
            for i, line in enumerate(extracted):
                text = line["text"]
                lines.append(
                    {
                        "page": page.page_number,
                        "line_id": i + 1,
                        "text": text,
                        "start": offset,
                        "end": offset + len(text),
                        "bbox": [line["x0"], line["top"], line["x1"], line["bottom"]],
                    }
                )
                offset += len(text) + 1
            data["pages"].append(
                {
                    "page": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "raw_text": page.extract_text() or "",
                    "layout_text": "\n".join(l["text"] for l in lines),
                    "lines": lines,
                    "images": [
                        {"bbox": [o["x0"], o["top"], o["x1"], o["bottom"]]}
                        for o in page.images
                    ],
                }
            )
            page.close()
    active_year = active_section = pending = None

    def finish(boundary, page_number, y):
        nonlocal pending
        if pending is None:
            return
        if pending["segments"][-1]["page"] == page_number:
            pending["segments"][-1]["bbox"][3] = max(
                pending["segments"][-1]["bbox"][1] + 1, y
            )
        explanation, notes = structure(pending.pop("lines"), pending["correct_answer"])
        pending["explanation"] = explanation
        pending["warnings"].extend(notes)
        pending["raw"] = {
            "header": pending.pop("header"),
            "span_base": "pages.layout_text",
            "page_spans": pending.pop("segments"),
            "boundary": boundary,
        }
        pending["raw"]["source_excerpt"] = "\n".join(
            data["pages"][s["page"] - 1]["layout_text"][s["start"] : s["end"]]
            for s in pending["raw"]["page_spans"]
        )
        pages = [s["page"] for s in pending["raw"]["page_spans"]]
        pending["page_reference"] = {"start_page": min(pages), "end_page": max(pages)}
        if not explanation["blocks"]:
            pending["warnings"].append(
                "explanation_text_unavailable:source_preview_requires_review"
            )
        data["answers"].append(pending)
        pending = None

    for page in data["pages"]:
        compact = re.sub(r"\s+", "", page["layout_text"])
        if YEAR.fullmatch(compact):
            if pending:
                pending["warnings"].append(
                    "explanation_boundary_unresolved:year_before_section_end"
                )
            finish("year", page["page"], 0)
            active_year, active_section = int(compact), None
            data["boundaries"].append(
                {"page": page["page"], "type": "year", "year": active_year}
            )
            continue
        # A continuation page may contain only a worked diagram, not text.
        if pending:
            pending["segments"].append(
                {
                    "page": page["page"],
                    "start": 0,
                    "end": 0,
                    "bbox": [0, 0, page["width"], page["height"]],
                }
            )
        for line in page["lines"]:
            text = line["text"].strip()
            section, end = SECTION.fullmatch(text), END.fullmatch(text)
            if section:
                if pending and active_section == "section_1":
                    pending["warnings"].append(
                        "explanation_boundary_unresolved:section_without_end_marker"
                    )
                finish("section", page["page"], line["bbox"][1] - 1)
                active_section = (
                    f"section_{section[1]}" if active_year is not None else None
                )
                data["boundaries"].append(
                    {
                        "page": page["page"],
                        "type": "section",
                        "year": active_year,
                        "section": active_section,
                    }
                )
                continue
            if end:
                finish("end_" + end[1].lower(), page["page"], line["bbox"][1] - 1)
                data["boundaries"].append(
                    {
                        "page": page["page"],
                        "type": "end_" + end[1].lower(),
                        "year": active_year,
                        "section": active_section,
                    }
                )
                active_section = None
                if end[1].upper() == "PAPER":
                    active_year = None
                continue
            if active_year is None or active_section != "section_1":
                continue
            header, question = HEADER.fullmatch(text), QUESTION.match(text)
            if question:
                finish("next_question", page["page"], line["bbox"][1] - 1)
                pending = {
                    "answer_id": f"{digest[:20]}_{active_year}_section_1_q{question[1]}_r{len(data['answers']) + 1}",
                    "year": active_year,
                    "section": active_section,
                    "question_number": int(question[1]),
                    "correct_answer": header[2].upper() if header else None,
                    "paper": None,
                    "variant": None,
                    "source_document": data["source_document"].copy(),
                    "header": line.copy(),
                    "lines": [],
                    "segments": [],
                    "visual_previews": [],
                    "warnings": []
                    if header
                    else ["malformed_question_header:correct_answer_unavailable"],
                }
            if pending:
                if (
                    not pending["segments"]
                    or pending["segments"][-1]["page"] != page["page"]
                ):
                    pending["segments"].append(
                        {
                            "page": page["page"],
                            "start": line["start"],
                            "end": line["end"],
                            "bbox": [
                                0,
                                max(0, line["bbox"][1] - 3) if question else 0,
                                page["width"],
                                page["height"],
                            ],
                        }
                    )
                pending["segments"][-1]["end"] = line["end"]
                if not question:
                    pending["lines"].append(line.copy())
    if pending:
        pending["warnings"].append("explanation_boundary_unresolved:end_of_file")
    finish("end_of_file", len(data["pages"]), data["pages"][-1]["height"])
    # Preserve every graphical explanation, including entries with no text layer.
    folder = asset_dir / digest[:20]
    folder.mkdir(parents=True, exist_ok=True)
    with pdfium.PdfDocument(str(path)) as document:
        requests = {}
        for answer in data["answers"]:
            for segment in answer["raw"]["page_spans"]:
                requests.setdefault(segment["page"], []).append((answer, segment))
        for number, requests_on_page in requests.items():
            page = document[number - 1]
            bitmap = page.render(scale=1.5, rev_byteorder=True)
            try:
                pixels = bytes(bitmap.buffer)
                size = [page.get_width(), page.get_height()]
                for answer, segment in requests_on_page:
                    shape = sha256(repr(segment["bbox"]).encode()).hexdigest()[:10]
                    target = (
                        folder
                        / f"{answer['year']}_q{answer['question_number']:03}_p{number:03}_{shape}.png"
                    )
                    dimensions = _save_crop(
                        bitmap, pixels, segment["bbox"], size, target, overwrite
                    )
                    answer["visual_previews"].append(
                        {
                            "path": target.relative_to(asset_dir.parent).as_posix(),
                            "page": number,
                            "bbox": segment["bbox"],
                            "sha256": sha256(target.read_bytes()).hexdigest(),
                            "pixel_size": dimensions,
                        }
                    )
            finally:
                bitmap.close()
                page.close()
    counts = Counter(
        (a["year"], a["section"], a["question_number"]) for a in data["answers"]
    )
    for answer in data["answers"]:
        if counts[(answer["year"], answer["section"], answer["question_number"])] > 1:
            answer["warnings"].append("duplicate_answer_identity")
    validate_answers(data)
    return data


def validate_answers(data):
    if data.get("stage") != "answer_raw" or data.get("schema_version") != "1":
        raise ValueError("Unsupported answer intermediate schema")
    pages = {p["page"]: p for p in data["pages"]}
    for answer in data["answers"]:
        if answer["section"] != "section_1":
            raise ValueError("SECTION 2 leaked into answer records")
        for span in answer["raw"]["page_spans"]:
            if (
                not 0
                <= span["start"]
                <= span["end"]
                <= len(pages[span["page"]]["layout_text"])
            ):
                raise ValueError("Invalid answer source span")
        excerpt = "\n".join(
            pages[s["page"]]["layout_text"][s["start"] : s["end"]]
            for s in answer["raw"]["page_spans"]
        )
        if excerpt != answer["raw"]["source_excerpt"]:
            raise ValueError("Answer excerpt lost original layout text")
        expected = []
        for span in answer["raw"]["page_spans"]:
            expected.extend(
                (span["page"], l["line_id"])
                for l in pages[span["page"]]["lines"]
                if span["start"] <= l["start"] < span["end"]
            )
        header = answer["raw"]["header"]
        expected.remove((header["page"], header["line_id"]))
        actual = []
        for block in answer["explanation"]["blocks"]:
            groups = block["items"] if block["type"] == "list" else [block]
            actual.extend(
                (r["page"], r["line_id"])
                for group in groups
                for r in group["line_refs"]
            )
        if expected != actual:
            raise ValueError("Explanation lines were lost, reordered or duplicated")
