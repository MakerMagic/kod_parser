"""Clean stored, issue-free mathematics without changing mathematical content."""

import json
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from parsers.mathematics.latex import validate as validate_latex
from parsers.mathematics.structure import walk


def clean_question(raw, reference):
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
    for field, blocks in components:
        if not blocks:
            issue("empty_content", "Required component contains no blocks", field)
        for block in walk(blocks):
            kind = block["type"]
            if kind == "text":
                # Preserve meaningful lines, internal spacing and adjacent math
                # boundaries. Never join separate blocks or rewrite symbols.
                block["text"] = block["text"].replace("\r\n", "\n").replace("\r", "\n")
                if len(blocks) == 1 and block is blocks[0]:
                    block["text"] = block["text"].strip()
                if not block["text"].strip():
                    issue(
                        "empty_text",
                        "Source text block contains only whitespace",
                        field,
                    )
            elif kind == "math":
                errors = validate_latex(block["latex"])
                if errors:
                    issue("malformed_latex", "; ".join(errors), field)
            elif kind == "visual":
                if block["asset_id"] not in assets:
                    issue(
                        "missing_asset", "Visual references an absent asset ID", field
                    )
            elif kind == "list":
                if not block["items"]:
                    issue("empty_list", "Source list contains no items", field)
            else:
                issue(
                    "unsupported_block",
                    "Unresolved or unsupported block: " + kind,
                    field,
                )
    row["cleaning_issues"] = findings
    row["cleaning"] = {
        "processor": "mathematics",
        "version": "1",
        "status": "review" if findings else "cleaned",
    }
    return row


def clean_dataset(paths):
    questions, excluded, inputs, sources = [], [], [], {}
    ids = set()
    for path in sorted({Path(p).resolve() for p in paths}):
        raw = json.loads(path.read_text(encoding="utf8"))
        if raw.get("domain") != "mathematics" or raw.get("stage") != "mathematics_raw":
            raise ValueError("Mathematics cleaning requires mathematics RAW JSON")
        ref = {"path": path.as_posix(), "sha256": sha256(path.read_bytes()).hexdigest()}
        inputs.append(ref)
        source = raw["source_document"]
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
            questions.append(
                clean_question(q, {**ref, "json_pointer": f"/questions/{index}"})
            )
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
    }
    data = {
        "domain": "mathematics",
        "stage": "mathematics_clean",
        "schema_version": "2",
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
    return data, validation
