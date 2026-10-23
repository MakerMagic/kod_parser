"""Clean stored, issue-free mathematics without changing mathematical content."""

import json
import re
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.mathematics.latex import validate as validate_latex
from parsers.mathematics.structure import walk
from processors.normalization.blackstone.text import (
    artifact_reason,
    normalize_text,
    structured_line,
)

from .structure import (
    VERSION,
    body_owns_visuals,
    projection,
    projection_is_lossless,
    prompt_start,
    reflow,
    split,
    token_ledger,
)
from .text_quality import polish, sync_prose


def question_digest(question):
    return sha256(
        json.dumps(question, ensure_ascii=False, sort_keys=True).encode("utf8")
    ).hexdigest()


def clean_text(value, *, standalone):
    """Reuse prose whitespace rules without crossing a math or source-line boundary."""
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    # Aligned numeric/list rows can use horizontal whitespace as structure.
    if any(
        structured_line(line.strip()) and re.search(r"\S[ \t\u00a0]{2,}\S", line)
        for line in value.split("\n")
    ):
        return value.strip() if standalone else value
    normalized = normalize_text(value, join_lines=False)
    if standalone or not normalized:
        return normalized

    def boundary(whitespace):
        return "\n" * min(2, whitespace.count("\n")) if "\n" in whitespace else " "

    leading = re.match(r"\s+", value)
    trailing = re.search(r"\s+$", value)
    if leading:
        normalized = boundary(leading[0]) + normalized
    if trailing:
        normalized += boundary(trailing[0])
    return normalized


def layout_digest(raw, glyphs=None):
    glyphs = glyphs or {}
    ids = {
        g
        for b in walk(raw["content"])
        for g in b.get("source", {}).get("glyph_ids", [])
    }
    return question_digest({g: glyphs[g] for g in sorted(ids) if g in glyphs})


def reusable(previous, raw, *, glyphs=None):
    """Validate a cached result without running the cleaner again."""
    if (
        not previous
        or previous.get("cleaning", {}).get("status") != "cleaned"
        or previous.get("cleaning_issues")
    ):
        return False
    metadata = previous["cleaning"]
    if metadata.get("version") != VERSION or metadata.get(
        "layout_sha256"
    ) != layout_digest(raw, glyphs):
        return False
    return same_input(previous, raw)


def same_input(previous, raw):
    """Verify an earlier CLEAN cache against RAW independently of rule version."""
    metadata = previous["cleaning"]
    if metadata.get("input_sha256"):
        return metadata["input_sha256"] == question_digest(raw)
    if metadata.get("version") != "1":
        return False
    # Legacy records predate per-question hashes. Compare their exact retained
    # fields, allowing only the two documented version-1 text transformations.
    expected = deepcopy(raw)
    for blocks in [expected["content"], *[o["content"] for o in expected["options"]]]:
        for block in walk(blocks):
            if block["type"] == "text":
                block["text"] = block["text"].replace("\r\n", "\n").replace("\r", "\n")
                if len(blocks) == 1 and block is blocks[0]:
                    block["text"] = block["text"].strip()
    return all(previous.get(key) == value for key, value in expected.items())


def clean_question(raw, reference, *, glyphs=None):
    if raw.get("issues") or raw.get("extraction_status") != "extracted":
        raise ValueError("Cleaning requires completed RAW without unresolved issues")
    row = deepcopy(raw)
    row["raw_reference"] = deepcopy(reference)
    findings = []

    def issue(code, reason, field):
        findings.append({"code": code, "reason": reason, "field": field})

    assets = {a["id"] for a in row["assets"]}
    components = [("content", row["content"])] + [
        ("option " + o["label"], o["content"]) for o in row["options"]
    ]
    labels = [o["label"] for o in row["options"]]
    if len(labels) < 2 or len(set(labels)) != len(labels):
        issue(
            "option_structure",
            "Missing or duplicate extracted option labels",
            "options",
        )

    def clean_blocks(blocks, field):
        if not blocks:
            issue("empty_content", "Required component contains no blocks", field)
        for index, block in enumerate(blocks):
            location = f"{field}[{index}]"
            kind = block["type"]
            if kind == "text":
                if not isinstance(block.get("text"), str):
                    issue("invalid_text", "Text block has no string content", location)
                    continue
                reason = artifact_reason(block["text"])
                if reason:
                    issue("encoding_artifact_unresolved", reason, location)
                block["text"] = clean_text(block["text"], standalone=len(blocks) == 1)
                if not block["text"].strip():
                    issue(
                        "empty_text",
                        "Source text block contains only whitespace",
                        location,
                    )
            elif kind == "math":
                errors = validate_latex(block.get("latex"))
                if errors:
                    issue("malformed_latex", "; ".join(errors), location)
            elif kind == "visual":
                if block.get("asset_id") not in assets:
                    issue(
                        "missing_asset",
                        "Visual references an absent asset ID",
                        location,
                    )
            elif kind == "list":
                if not block["items"]:
                    issue("empty_list", "Source list contains no items", location)
                for item_index, item in enumerate(block["items"]):
                    clean_blocks(
                        item["content"], f"{location}.items[{item_index}].content"
                    )
            else:
                issue(
                    "unsupported_block",
                    "Unresolved or unsupported block: " + kind,
                    location,
                )

    for field, blocks in components:
        clean_blocks(blocks, field)
    # RAW retains physical line geometry. CLEAN owns prose reflow and the
    # context/task projection; downstream stages copy these decisions verbatim.
    original = deepcopy(row["content"])
    row["content"] = reflow(row["content"], glyphs)
    if token_ledger(original) != token_ledger(row["content"]):
        raise ValueError("Prose reconstruction changed non-whitespace content")
    if (
        "main_body" in raw
        and "main_question" in raw
        and (
            raw["main_question"] is not None
            or prompt_start(projection(raw["main_body"])[0])[0] is None
        )
    ):
        body = reflow(raw["main_body"], glyphs)
        prompt = reflow(raw["main_question"], glyphs) if raw["main_question"] else None
        body, prompt = body_owns_visuals(body, prompt)
        if not projection_is_lossless(row["content"], body, prompt):
            raise ValueError(
                "Existing context/task fields disagree with source content"
            )
        row["main_body"], row["main_question"] = body, prompt
        reason = "preserved_explicit_boundary"
    else:
        row["main_body"], row["main_question"], reason = split(row["content"])
    body, prompt, prose_edits = polish(row['main_body'], row['main_question'])
    row['content'] = sync_prose(row['content'], body, prompt)
    row['main_body'], row['main_question'] = body, prompt
    for option in row['options']:
        before = deepcopy(option['content'])
        option['content'] = reflow(before, glyphs)
        if token_ledger(before) != token_ledger(option['content']):
            raise ValueError('Answer prose reflow changed source characters')
    if any(block["type"] == "visual" for block in walk(row["main_question"] or [])):
        raise ValueError("CLEAN invariant violated: Main Question contains a visual")
    row["content_structure"] = {
        "method": "source_geometry_and_request_grammar",
        "version": VERSION,
        "decision": reason,
    }
    if (
        row["content"]
        and row["main_question"] is None
        and any(
            b["type"] == "text" and re.search(r"\?\s*[A-Za-z]", b["text"])
            for b in row["content"]
        )
    ):
        issue(
            "question_boundary_ambiguous",
            "A standalone question mark is mixed with fragmented formula/prose; no source-faithful task boundary can be established.",
            "main_question",
        )
    row["cleaning_issues"] = findings
    row["cleaning"] = {
        "processor": "mathematics",
        "version": VERSION,
        "input_sha256": question_digest(raw),
        "layout_sha256": layout_digest(raw, glyphs),
        "status": "review" if findings else "cleaned",
    }
    return row


def clean_dataset(paths, existing=None, *, run_stats=None):
    questions, excluded, inputs, sources = [], [], [], {}
    if existing is not None and (
        existing.get("domain") != "mathematics"
        or existing.get("stage") != "mathematics_clean"
    ):
        raise ValueError("Existing cleaning data must be mathematics CLEAN")
    cached = {q["id"]: q for q in (existing or {}).get("questions", [])}
    stats = {"reused_valid": 0, "processed_new": 0, "retried_review_or_stale": 0}
    ids = set()
    for path in sorted({Path(p).resolve() for p in paths}):
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("domain") != "mathematics" or raw.get("stage") != "mathematics_raw":
            raise ValueError("Mathematics cleaning requires mathematics RAW JSON")
        ref = {"path": path.as_posix(), "sha256": sha256(path.read_bytes()).hexdigest()}
        inputs.append(ref)
        source = raw["source_document"]
        glyphs = {
            glyph["id"]: glyph
            for page in raw.get("pages", [])
            for glyph in page.get("glyphs", [])
        }
        if source["id"] in sources:
            raise ValueError("Duplicate source document")
        sources[source["id"]] = deepcopy(source)
        for index, q in enumerate(raw["questions"]):
            if q["id"] in ids or q["source_document_id"] != source["id"]:
                raise ValueError("Duplicate question ID or mismatched source identity")
            ids.add(q["id"])
            reasons = deepcopy(q.get("issues", []))
            if q.get("extraction_status") != "extracted":
                reasons.append(
                    {
                        "code": "raw_not_complete",
                        "reason": "RAW status is " + str(q.get("extraction_status")),
                    }
                )
            if raw.get("issues"):
                reasons.extend(deepcopy(raw["issues"]))
            if reasons:
                excluded.append(
                    {
                        "id": q["id"],
                        "source_document_id": source["id"],
                        "source_pdf": source["filename"],
                        "question_number": q["question_number"],
                        "reasons": reasons,
                    }
                )
                continue
            reference = {**ref, "json_pointer": f"/questions/{index}"}
            previous = cached.get(q["id"])
            if reusable(previous, q, glyphs=glyphs):
                row = deepcopy(previous)
                row["raw_reference"] = reference
                stats["reused_valid"] += 1
            else:
                row = clean_question(q, reference, glyphs=glyphs)
                if (
                    previous
                    and previous["cleaning"]["status"] == "cleaned"
                    and not previous.get("cleaning_issues")
                    and same_input(previous, q)
                ):
                    # Reflow option prose too; mathematical tokens remain exact.
                    for prior, option in zip(previous['options'], row['options'], strict=True):
                        if token_ledger(prior['content']) != token_ledger(option['content']):
                            raise ValueError('Cleaning upgrade changed answer meaning')
                stats["retried_review_or_stale" if previous else "processed_new"] += 1
            questions.append(row)
    summary = {
        "total": len(ids),
        "eligible": len(questions),
        "cleaned": sum(q["cleaning"]["status"] == "cleaned" for q in questions),
        "review": sum(q["cleaning"]["status"] == "review" for q in questions),
        "excluded": len(excluded),
        "excluded_raw_issues": sum(
            any(i["code"] != "raw_not_complete" for i in e["reasons"]) for e in excluded
        ),
        "issues_by_code": dict(
            Counter(i["code"] for q in questions for i in q["cleaning_issues"])
        ),
        "with_main_question": sum(q["main_question"] is not None for q in questions),
        "without_separate_main_question": sum(
            bool(q["content"])
            and q["main_question"] is None
            and not q["cleaning_issues"]
            for q in questions
        ),
    }
    data = {
        "domain": "mathematics",
        "stage": "mathematics_clean",
        "schema_version": "3",
        "inputs": inputs,
        "sources": sources,
        "questions": questions,
        "summary": summary,
    }
    validation = {
        "domain": "mathematics",
        "stage": "mathematics_clean_validation",
        "summary": summary,
        "excluded": excluded,
        "issues": [
            {
                "id": q["id"],
                "source_pdf": sources[q["source_document_id"]]["filename"],
                "question_number": q["question_number"],
                "issues": q["cleaning_issues"],
            }
            for q in questions
            if q["cleaning_issues"]
        ],
    }
    if run_stats is not None:
        run_stats.update(stats)
    return data, validation
