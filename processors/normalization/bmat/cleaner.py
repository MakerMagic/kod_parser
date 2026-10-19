"""Normalize proven BMAT structural projections, without opening source PDFs."""

import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from processors.normalization.blackstone.text import normalize_text


def line_evidence(raw, text):
    """Align readable projected rows to retained exact-span RAW layout blocks."""
    blocks = [b for b in raw.get("layout_blocks", []) if b["type"] == "text"]
    cursor = 0
    result = []
    for value in text.splitlines():
        if not value.strip():
            continue
        line = value.strip()
        found = None
        for i in range(cursor, len(blocks)):
            b = blocks[i]
            readable = b.get("readable_text", b["text"]).strip()
            readable = re.sub(r"^" + str(raw["question_number"]) + r"\s+", "", readable)
            if line in readable:
                found = {
                    "block_id": b["block_id"],
                    "raw_span": b["raw_span"],
                    "page": b["page"],
                    "bbox": b["bbox"],
                    "order": b["order"],
                    "text": line,
                    "component": "question_body",
                }
                cursor = i + 1
                break
        result.append(found)
    return result


def normalized(text, context=None):
    return normalize_text(
        text,
        join_lines=True,
        separate_blocks=True,
        contextual_wraps=True,
        line_context=context,
    )


def body_blocks(raw):
    text = raw["raw_components"]["main_body"]
    if raw["raw_components"].get("body_equals_question"):
        text = ""
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    context = line_evidence(raw, text)
    events = []
    for i, (line, evidence) in enumerate(zip(lines, context)):
        events.append(
            {
                "kind": "text",
                "text": line,
                "source": evidence,
                "key": (evidence["page"], evidence["bbox"][1], evidence["bbox"][0])
                if evidence
                else (raw["page_reference"]["start_page"], float(i), 0),
            }
        )
    for asset in raw["visual_assets"]:
        if asset["belongs_to"] == "question":
            events.append(
                {
                    "kind": "visual",
                    "asset": asset,
                    "key": (asset["page"], asset["bbox"][1], asset["bbox"][0]),
                }
            )
    events.sort(key=lambda e: e["key"])
    blocks = []
    paragraph = []
    sources = []

    def flush():
        if paragraph:
            blocks.append(
                {
                    "type": "text",
                    "text": normalized("\n".join(paragraph), sources),
                    "source_blocks": [s for s in sources if s],
                }
            )
            paragraph.clear()
            sources.clear()

    for event in events:
        if event["kind"] == "visual":
            flush()
            a = event["asset"]
            blocks.append(
                {
                    "type": "visual",
                    "asset_id": a["image_id"],
                    "path": a["path"],
                    "page": a["page"],
                    "bbox": a["bbox"],
                    "raw_asset": deepcopy(a),
                }
            )
            continue
        source = event["source"]
        if sources and sources[-1] and source:
            before = sources[-1]
            a, b = before["bbox"], source["bbox"]
            if (
                before["page"] != source["page"]
                or b[1] - a[3] > max(a[3] - a[1], b[3] - b[1]) * 0.8
            ):
                flush()
        paragraph.append(event["text"])
        sources.append(source)
    flush()
    if not blocks and raw["raw_components"].get("body_equals_question"):
        blocks = [
            {
                "type": "text",
                "text": "Equals question",
                "source_blocks": [],
                "body_equals_question": True,
            }
        ]
    for i, b in enumerate(blocks, 1):
        b["order"] = i
    return blocks, not all(context)


def clean_dataset(dataset, raw_json, *, raw_sha256=None):
    """Pure stored-data transform; no acquisition, matching, parsing or crop writes."""
    if dataset.get("source") != "bmat":
        raise ValueError("BMAT source required")
    path = Path(raw_json).resolve()
    digest = raw_sha256 or sha256(path.read_bytes()).hexdigest()
    result = {
        "stage": "clean",
        "schema_version": "1",
        "cleaning": {
            "processor": "bmat",
            "version": "1",
            "rules": [
                "raw_component_preservation",
                "nfc_whitespace",
                "geometry_backed_prose_wraps",
                "ordered_body_visuals",
                "immutable_option_assets",
                "upstream_issue_propagation",
            ],
        },
        "raw_reference": {"path": str(path), "sha256": digest},
        "document": deepcopy(
            {k: v for k, v in dataset.items() if k not in {"questions", "pages"}}
        ),
        "questions": [],
    }
    for index, raw in enumerate(dataset["questions"]):
        body, unaligned = body_blocks(raw)
        issues = [
            {**deepcopy(i), "origin": "raw", "field": "upstream"}
            for i in raw["parsing_issues"]
        ]
        issues.extend(
            {
                "code": "upstream_document_issue",
                "origin": "raw",
                "field": "document",
                "reason": w,
                "manual_review_required": True,
            }
            for w in dataset["warnings"]
        )
        if unaligned:
            issues.append(
                {
                    "code": "clean_layout_alignment_unresolved",
                    "origin": "cleaning",
                    "field": "main_body",
                    "reason": "Projected source row could not be aligned to a retained RAW layout block; text is preserved, reading order needs review.",
                    "manual_review_required": True,
                }
            )
        stem = raw["raw_components"]["main_question"]
        options = deepcopy(raw["options"])
        for option in options:
            option["text"] = normalized(option["text"])
            from .fractions import recover

            fraction = recover(option)
            if fraction:
                option["text"], option["fraction_normalization"] = fraction
                option["render_text_only"] = True
        q = {
            "question_id": raw["question_id"],
            "question_number": raw["question_number"],
            "source_question_key": deepcopy(raw["source_question_key"]),
            "metadata": {
                k: dataset.get(k)
                for k in (
                    "source",
                    "year",
                    "paper",
                    "variant",
                    "section",
                    "document_role",
                )
            },
            "page_reference": deepcopy(raw["page_reference"]),
            "raw_reference": {
                "path": str(path),
                "sha256": digest,
                "json_pointer": f"/questions/{index}",
                "question_id": raw["question_id"],
            },
            "raw_record": deepcopy(raw),
            "raw_warnings": deepcopy(raw["warnings"]),
            "raw_document_warnings": deepcopy(dataset["warnings"]),
            "question_text": normalized(
                raw["question_text"], line_evidence(raw, raw["question_text"])
            ),
            "main_body": body,
            "main_question": normalized(stem, line_evidence(raw, stem))
            if stem
            else None,
            "options": options,
            "images": deepcopy(raw["images"]),
            "visual_assets": deepcopy(raw["visual_assets"]),
            "visual_previews": deepcopy(raw["visual_previews"]),
            "bmat_filter": deepcopy(raw["bmat_filter"]),
            "cleaning_issues": issues,
            "transformations": [
                "Normalized only stored RAW component projections; original record and asset references retained."
            ],
        }
        text_before = (
            ""
            if raw["raw_components"].get("body_equals_question")
            else raw["raw_components"]["main_body"]
        )
        text_after = "".join(
            b["text"]
            for b in body
            if b["type"] == "text" and not b.get("body_equals_question")
        )
        if re.sub(r"\s+", "", text_before) != re.sub(r"\s+", "", text_after):
            issues.append(
                {
                    "code": "clean_content_accounting_mismatch",
                    "origin": "cleaning",
                    "field": "main_body",
                    "reason": "Whitespace-independent body projection changed; preserve review status.",
                    "manual_review_required": True,
                }
            )
        q["pipeline_eligible"] = (
            not q["bmat_filter"]["skip_from_pipeline"] and not issues
        )
        q["pipeline_status"] = (
            "intentional_skip"
            if q["bmat_filter"]["skip_from_pipeline"]
            else "upstream_review"
            if any(i["origin"] == "raw" for i in issues)
            else "cleaning_review"
            if issues
            else "clean_ready"
        )
        result["questions"].append(q)
    validate_clean(result, dataset)
    return result


def validate_clean(data, raw=None):
    if data["stage"] != "clean" or data["cleaning"]["processor"] != "bmat":
        raise ValueError("Invalid BMAT CLEAN document")
    seen = set()
    for i, q in enumerate(data["questions"]):
        if q["question_id"] in seen:
            raise ValueError("Duplicate clean question identity")
        seen.add(q["question_id"])
        if raw is not None and q["raw_record"] != raw["questions"][i]:
            raise ValueError("RAW snapshot changed")
        if q["pipeline_eligible"] and (
            q["cleaning_issues"] or q["bmat_filter"]["skip_from_pipeline"]
        ):
            raise ValueError("Unresolved/skipped record cannot be eligible")
        assets = {a["image_id"]: a for a in q["visual_assets"]}
        used = set()
        for option in q["options"]:
            for a in option["images"]:
                if assets.get(a["image_id"], {}).get("option_label") != option["label"]:
                    raise ValueError("Option image association changed")
                used.add(a["image_id"])
        if any(b.get("asset_id") in used for b in q["main_body"]):
            raise ValueError("Option visual leaked into body")
        if q["bmat_filter"] != q["raw_record"]["bmat_filter"]:
            raise ValueError("CLEAN changed RAW skip evidence")
