"""Official 2020 layout: complete question, A-E options, wider-margin explanation.

This profile never uses older sources' question/answer declaration headers.
All extraction lines survive independently of the derived readable projection.
"""

import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import median

import pdfplumber
import pypdfium2 as pdfium

from parsers.blackstone.visuals import _save_crop

from .inference import infer_answer

PROFILE = "tsa_official_2020_full_explanations"


def reference(line):
    return {key: line[key] for key in ("page", "line_id", "start", "end", "bbox")}


def extract_pages(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        metadata = dict(pdf.metadata or {})
        for page in pdf.pages:
            lines, offset = [], 0
            for i, row in enumerate(
                page.extract_text_lines(x_tolerance=1, y_tolerance=3), 1
            ):
                text = row["text"]
                lines.append(
                    {
                        "page": page.page_number,
                        "line_id": i,
                        "text": text,
                        "start": offset,
                        "end": offset + len(text),
                        "bbox": [row["x0"], row["top"], row["x1"], row["bottom"]],
                    }
                )
                offset += len(text) + 1
            pages.append(
                {
                    "page": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "raw_text": page.extract_text() or "",
                    "layout_text": "\n".join(l["text"] for l in lines),
                    "lines": lines,
                    "words": [
                        {k: w[k] for k in ("text", "x0", "top", "x1", "bottom")}
                        for w in page.extract_words(x_tolerance=1, y_tolerance=3)
                    ],
                }
            )
            page.close()
    return pages, metadata


def find_boundary(page):
    """Require top question number, ordered label gutter, margin reset and gap."""
    lines = page["lines"]
    if not lines:
        return None
    header = re.match(r"^(\d{1,2})(?:\s+|$)", lines[0]["text"])
    if (
        not header
        or not 1 <= int(header[1]) <= 50
        or lines[0]["bbox"][1] > page["height"] * 0.2
    ):
        return None
    number = int(header[1])
    h = median(l["bbox"][3] - l["bbox"][1] for l in lines)
    gutter = None
    anchors = []
    for i, line in enumerate(lines[1:], 1):
        # Multi-column image options have label-only rows (A B C / D E).
        grid = re.fullmatch(r"[A-E](?:\s+[A-E])*", line["text"].strip())
        label = re.match(r"^([A-E])(?:\s+|$)", line["text"])
        if not label:
            continue
        if gutter is None:
            if (
                label[1] != "A"
                or not lines[0]["bbox"][0] + h < line["bbox"][0] < page["width"] * 0.22
            ):
                continue
            gutter = line["bbox"][0]
        if abs(line["bbox"][0] - gutter) > h:
            continue
        words = [w for w in page["words"] if abs(w["top"] - line["bbox"][1]) < h * 0.5]
        selected = (
            [w for w in words if re.fullmatch(r"[A-E]", w["text"])]
            if grid
            else words[:1]
        )
        for word in selected:
            # An article 'A' in the setup is not the A option. A later A in
            # the same gutter restarts an as-yet incomplete label sequence.
            if word["text"] == "A" and len(anchors) == 1:
                anchors = []
            if word["text"] != "ABCDE"[len(anchors)]:
                continue
            anchors.append(
                {
                    "label": word["text"],
                    "line_index": i,
                    "page": page["page"],
                    "bbox": [word["x0"], word["top"], word["x1"], word["bottom"]],
                }
            )
            if len(anchors) == 5:
                break
        if len(anchors) == 5:
            break
    if len(anchors) != 5:
        return {
            "number": number,
            "anchors": anchors,
            "error": "option_anchors_incomplete",
        }
    last = anchors[-1]["line_index"]
    candidates = [
        i
        for i in range(last + 1, len(lines))
        if lines[i]["bbox"][0] < gutter - h * 1.25
        and lines[i]["bbox"][1] - lines[i - 1]["bbox"][3] > h * 1.2
    ]
    if not candidates:
        return {
            "number": number,
            "anchors": anchors,
            "error": "margin_reset_or_whitespace_missing",
        }
    start = candidates[0]
    return {
        "number": number,
        "anchors": anchors,
        "start": start,
        "method": "ordered_option_gutter_then_wider_margin_and_whitespace",
        "gap_in_line_heights": (lines[start]["bbox"][1] - lines[start - 1]["bbox"][3])
        / h,
    }


def full_explanation(lines):
    """One complete block, retaining line breaks and geometry-backed paragraphs."""
    parts = []
    h = median(l["bbox"][3] - l["bbox"][1] for l in lines) if lines else 0
    for i, line in enumerate(lines):
        if i:
            gap = line["bbox"][1] - lines[i - 1]["bbox"][3]
            parts.append("\n\n" if gap > h * 0.7 else "\n")
        parts.append(line["text"])
    text = "".join(parts)
    block = {
        "type": "paragraph",
        "role": "main",
        "order": 1,
        "text": text,
        "line_refs": [reference(l) for l in lines],
    }
    return {
        "presentation": "full_explanation",
        "main_explanation": text,
        "blocks": [block] if lines else [],
        "paragraphs": [block] if lines else [],
        "bulleted_blocks": [],
        "choice_analysis": [],
        "other_lists": [],
        "visual_assets": [],
    }


def parse_pdf(path, *, asset_dir, overwrite=False):
    path, asset_dir = Path(path).resolve(), Path(asset_dir).resolve()
    pages, metadata = extract_pages(path)
    identification = (
        " ".join(str(metadata.get(k, "")) for k in ("Title", "Subject"))
        + " "
        + pages[0]["raw_text"]
    )
    if set(re.findall(r"\b20\d{2}\b", identification)) != {"2020"} or not re.search(
        r"section\s*1", identification, re.IGNORECASE
    ):
        raise ValueError(
            "Official 2020 profile requires 2020 / Section 1 source evidence"
        )
    digest = sha256(path.read_bytes()).hexdigest()
    source = {
        "path": str(path),
        "filename": path.name,
        "sha256": digest,
        "metadata": metadata,
        "document_role": "question_paper_with_explanations",
    }
    data = {
        "stage": "answer_raw",
        "schema_version": "1",
        "parser": {"profile": PROFILE, "version": "1"},
        "source_document": source,
        "pages": pages,
        "boundaries": [],
        "answers": [],
        "issues": [],
    }
    for page in pages:
        boundary = find_boundary(page)
        if not boundary:
            # Cover/end material stays in page extraction, not an explanation.
            content = page["raw_text"]
            administration = (
                not content.strip()
                or (
                    page["page"] == 1
                    and re.search(
                        r"\b(?:TSA|Thinking Skills Assessment)\b",
                        content,
                        re.IGNORECASE,
                    )
                    and re.search(
                        r"2020\b.*?explained\s+answers",
                        content,
                        re.IGNORECASE | re.DOTALL,
                    )
                )
                or (
                    "accessibility" in content.casefold()
                    and "admissionstesting" in content.casefold()
                )
            )
            if not administration:
                data["issues"].append(
                    {
                        "code": "explanation_boundary_unresolved",
                        "year": 2020,
                        "page": page["page"],
                        "manual_review_required": True,
                        "reason": "Unexpected non-question content retained in page text; possible continuation requires review",
                    }
                )
                if data["answers"]:
                    data["answers"][-1]["warnings"].append(
                        "explanation_boundary_unresolved:possible_continuation_page"
                    )
                    data["answers"][-1]["correct_answer"] = None
            data["boundaries"].append(
                {"type": "non_question_page", "page": page["page"]}
            )
            continue
        number, lines = boundary["number"], page["lines"]
        start = boundary.get("start", len(lines))
        body = lines[start:]
        first_option = (
            boundary["anchors"][0]["line_index"] if boundary["anchors"] else len(lines)
        )
        question_text = "\n".join(l["text"] for l in lines[:first_option])
        question_text = re.sub(r"^\d{1,2}\s*", "", question_text, count=1)
        options = []
        for i, anchor in enumerate(boundary["anchors"]):
            a = anchor["line_index"]
            b = (
                boundary["anchors"][i + 1]["line_index"]
                if i + 1 < len(boundary["anchors"])
                else start
            )
            option_lines = lines[a:b]
            text = "\n".join(l["text"] for l in option_lines)
            # Shared label-only grid rows are visuals, never fabricated option prose.
            text = (
                ""
                if re.fullmatch(r"[A-E](?:\s+[A-E])*", lines[a]["text"])
                else re.sub(r"^[A-E]\s*", "", text, count=1)
            )
            options.append(
                {"label": anchor["label"], "text": text, "label_bbox": anchor["bbox"]}
            )
        explanation = full_explanation(body)
        inference = infer_answer(explanation["main_explanation"], question_text)
        warnings = []
        if "error" in boundary:
            warnings.append("explanation_boundary_unresolved:" + boundary["error"])
        if not body:
            warnings.append("explanation_boundary_unresolved:explanation_missing")
        if inference["status"] != "resolved":
            warnings.append(
                "correct_answer_candidates_conflict"
                if len(inference["candidates"]) > 1
                else "correct_answer_not_inferable"
            )
        if any("(cid:" in l["text"] or "\ufffd" in l["text"] for l in body):
            warnings.append("explanation_boundary_unresolved:source_text_malformed")
        span = {
            "page": page["page"],
            "start": body[0]["start"] if body else len(page["layout_text"]),
            "end": body[-1]["end"] if body else len(page["layout_text"]),
            "bbox": [
                0,
                body[0]["bbox"][1] if body else 0,
                page["width"],
                page["height"],
            ],
        }
        answer = {
            "answer_id": f"{digest[:20]}_2020_section_1_q{number}_r{len(data['answers']) + 1}",
            "year": 2020,
            "section": "section_1",
            "question_number": number,
            "correct_answer": inference["correct_answer"] if not warnings else None,
            "paper": None,
            "variant": None,
            "source_document": source.copy(),
            "page_reference": {"start_page": page["page"], "end_page": page["page"]},
            "answer_inference": inference,
            "warnings": warnings,
            "visual_previews": [],
            "question_evidence": {
                "question_text": question_text,
                "options": options,
                "line_refs": [reference(l) for l in lines[:start]],
            },
            "explanation": explanation,
            "raw": {
                "header": lines[0].copy(),
                "span_base": "pages.layout_text",
                "page_spans": [span],
                "source_excerpt": page["layout_text"][span["start"] : span["end"]],
                "explanation_line_refs": [reference(l) for l in body],
                "question_and_options_text": "\n".join(
                    l["text"] for l in lines[:start]
                ),
                "boundary_evidence": boundary,
                "boundary": "end_of_question_page",
            },
        }
        data["answers"].append(answer)
        data["boundaries"].append(
            {"type": "question", "page": page["page"], **boundary}
        )
    counts = Counter(a["question_number"] for a in data["answers"])
    for a in data["answers"]:
        if counts[a["question_number"]] > 1:
            a["warnings"].append("duplicate_answer_identity")
            a["correct_answer"] = None
        for warning in a["warnings"]:
            data["issues"].append(
                {
                    "code": warning.split(":")[0],
                    "reason": warning,
                    "year": 2020,
                    "section": "section_1",
                    "question_number": a["question_number"],
                    "page": a["page_reference"]["start_page"],
                    "manual_review_required": True,
                }
            )
    for n in sorted(set(range(1, 51)) - counts.keys()):
        data["issues"].append(
            {
                "code": "answer_header_missing",
                "reason": "No supported question/options/explanation layout",
                "year": 2020,
                "section": "section_1",
                "question_number": n,
                "manual_review_required": True,
            }
        )
    folder = asset_dir / digest[:20]
    with pdfium.PdfDocument(str(path)) as pdf:
        for a in data["answers"]:
            number = a["page_reference"]["start_page"]
            page = pdf[number - 1]
            bitmap = page.render(scale=1.5, rev_byteorder=True)
            try:
                bbox = [0, 0, page.get_width(), page.get_height()]
                target = folder / f"2020_q{a['question_number']:03}_p{number:03}.png"
                size = _save_crop(
                    bitmap, bytes(bitmap.buffer), bbox, bbox[2:], target, overwrite
                )
                a["visual_previews"].append(
                    {
                        "path": target.relative_to(asset_dir.parent).as_posix(),
                        "page": number,
                        "bbox": bbox,
                        "pixel_size": size,
                        "sha256": sha256(target.read_bytes()).hexdigest(),
                    }
                )
            finally:
                bitmap.close()
                page.close()
    validate_answers(data)
    return data


def validate_answers(data):
    for answer in data["answers"]:
        page = data["pages"][answer["page_reference"]["start_page"] - 1]
        raw = answer["raw"]
        span = raw["page_spans"][0]
        if raw["source_excerpt"] != page["layout_text"][span["start"] : span["end"]]:
            raise ValueError("Raw explanation span changed")
        blocks = answer["explanation"]["blocks"]
        if len(blocks) > 1 or (
            blocks and blocks[0]["text"].replace("\n\n", "\n") != raw["source_excerpt"]
        ):
            raise ValueError("Full explanation content changed or fragmented")
        refs = blocks[0]["line_refs"] if blocks else []
        if refs != raw["explanation_line_refs"]:
            raise ValueError("Explanation lines lost or reordered")
        if (
            "\n".join(page["layout_text"][r["start"] : r["end"]] for r in refs)
            != raw["source_excerpt"]
        ):
            raise ValueError("Explanation content not fully accounted for")
        if answer["correct_answer"] is not None and (
            answer["warnings"]
            or answer["answer_inference"]["correct_answer"] != answer["correct_answer"]
        ):
            raise ValueError("Unverified inference marked resolved")
