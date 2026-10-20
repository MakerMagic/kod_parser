"""Assemble categorized, issue-free inputs only; all earlier stages are read-only."""

import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote

from .content import Content
from .storage import OWNER, ROOT, InvalidInput, Store, write_owned

DEFAULT_INPUTS = {
    "TSA": "data/categorized/blackstone/tsa.categorized.json",
    "BMAT": "data/categorized/bmat/questions.categorized.json",
}
CATALOG = "categorization/patterns.json"
# Existing RAW informational codes (parsers/blackstone/backtest.py), not issue suppression.
INFORMATIONAL = {
    "graphics_present:option_association_not_resolved",
    "no_extractable_text:blank_or_scanned_page",
}
ACCEPTED = {"TSA": {"classified"}, "BMAT": {"supported"}}
SCHEMA = json.loads(Path(__file__).with_name("schema.json").read_text(encoding="utf-8"))
TSA_IDS = set(SCHEMA["$defs"]["question"]["properties"]["category"]["enum"])


def canonical_identity(source, identity):
    original = identity.get("source_question_key") or identity
    if (
        source not in DEFAULT_INPUTS
        or original.get("source")
        not in {"TSA": {"blackstone", "tsa", "TSA"}, "BMAT": {"bmat", "BMAT"}}[source]
    ):
        raise InvalidInput("source_identity_invalid")
    result = {"source": source}
    for key in ("year", "question_number"):
        value = original.get(key)
        if type(value) is not int or value <= 0:
            raise InvalidInput("identity_missing", key)
        result[key] = value
        if identity.get(key) != value:
            raise InvalidInput("identity_conflict", key)
    for key in ("section", "paper", "variant"):
        value = original.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise InvalidInput("identity_invalid", key)
        if key in identity and identity[key] != value:
            raise InvalidInput("identity_conflict", key)
        result[key] = value
    if not result["section"]:
        raise InvalidInput("identity_missing", "section")
    return result


def stable_id(identity):
    """Reuse proven parser IDs for current identities; escape future variants."""

    # Existing IDs are already intrinsic; do not replace them just to align labels.
    paper = identity["paper"]
    if (
        identity["section"] == "section_1"
        and identity["variant"] is None
        and (
            isinstance(paper, str)
            and re.fullmatch(r"[A-Z0-9]{4}/[0-9]{2}", paper)
            or identity["source"] == "BMAT"
            and paper is None
        )
    ):
        family = "blackstone" if identity["source"] == "TSA" else "bmat"
        return f"{family}_{identity['year']}_{paper or 'unspecified'}_section_1_q{identity['question_number']}"

    def part(value):
        return "null" if value is None else "v" + quote(str(value), safe="")

    return ":".join(
        [
            identity["source"].lower(),
            str(identity["year"]),
            part(identity["section"]),
            "paper=" + part(identity["paper"]),
            "variant=" + part(identity["variant"]),
            "q" + str(identity["question_number"]),
        ]
    )


def issue_reasons(record, question=None, matched=None):
    reasons = []
    if record["categorization"].get("issues"):
        reasons.append("categorization_issue")
    upstream = record.get("upstream", {})
    for field in ("matching_issues", "cleaning_issues"):
        if upstream.get(field):
            reasons.append(field)
    if any(w not in INFORMATIONAL for w in upstream.get("raw_warnings", [])):
        reasons.append("raw_issue")
    if question is not None:
        if question.get("cleaning_issues"):
            reasons.append("cleaning_issues")
        raw = question.get("raw_record", {})
        if raw.get("parsing_issues") or any(
            w not in INFORMATIONAL for w in question.get("raw_warnings", [])
        ):
            reasons.append("raw_issue")
        if question.get("bmat_filter", {}).get("skip_from_pipeline"):
            reasons.append("intentional_skip")
        if (
            question.get("pipeline_eligible") is False
            or question.get("pipeline_status", "clean_ready") != "clean_ready"
        ):
            reasons.append("upstream_not_eligible")
        if any(o.get("warnings") for o in question.get("options", [])):
            reasons.append("option_issue")
    if matched is not None:
        if matched.get("status") != "matched":
            reasons.append("matching_not_complete")
        if matched.get("issues"):
            reasons.append("matching_issues")
        if matched.get("matching", {}).get("upstream_review_required"):
            # Legacy matching sets this on the literal 'not_resolved' in the
            # informational graphics-presence notice too (matching/core.py).
            # Only that evidenced informational-only case is not a real issue.
            informational_only = (
                question is not None
                and bool(question.get("raw_warnings"))
                and all(w in INFORMATIONAL for w in question["raw_warnings"])
                and not question.get("cleaning_issues")
                and not any(
                    a.get("warnings") for a in question.get("visual_assets", [])
                )
            )
            if not informational_only:
                reasons.append("upstream_review_required")
        final = matched.get("final_explanation") or {}
        if (
            final.get("issues")
            or final.get("source_warnings")
            or final.get("status") == "uncertain"
            or final.get("unplaced_components")
        ):
            reasons.append("explanation_issue")
        if (matched.get("answer") or {}).get("warnings"):
            reasons.append("answer_issue")
    return sorted(set(reasons))


def gate(record, source, categories):
    cat = record["categorization"]
    reasons = issue_reasons(record)
    if (
        cat.get("status") == "intentional_skip"
        or cat.get("category") == "BMAT-specific"
    ):
        reasons.append("intentional_skip")
    if cat.get("status") not in ACCEPTED[source]:
        reasons.append("categorization_not_complete")
    assigned = cat.get("patterns", [])
    if (
        len(assigned) != 1
        or assigned[0] not in categories
        or (cat.get("category"), cat.get("subcategories"))
        != (categories[assigned[0]]["family"], [categories[assigned[0]]["name"]])
    ):
        reasons.append("invalid_or_missing_category")
    return sorted(set(reasons))


def assemble(record, source, identity, ref, categories, store):
    match_ref = record.get("matched_reference") or record.get("matching_reference")
    if not match_ref:
        raise InvalidInput("matching_reference_missing")
    matched = store.record(match_ref)
    q = matched.get("question")
    if not q:
        raise InvalidInput("question_missing")
    key = q.get("source_question_key") or {}
    if canonical_identity(source, key) != identity:
        raise InvalidInput("matching_identity_conflict")
    match_identity = matched.get("identity", {})
    if any(
        match_identity.get(k) != identity[k]
        for k in ("year", "section", "question_number")
    ):
        raise InvalidInput("matching_identity_conflict")
    if source == "BMAT" and match_identity.get("source_family") != "bmat":
        raise InvalidInput("matching_identity_conflict")
    if "question" in record:
        if record["question"] != q or record["matching_status"] != matched["status"]:
            raise InvalidInput("categorization_snapshot_changed")
    else:
        view = record["question_view"]
        if any(q.get(k) != v for k, v in view.items()):
            raise InvalidInput("categorization_snapshot_changed")
        if record.get("correct_answer") != matched.get("correct_answer") or record.get(
            "final_explanation"
        ) != matched.get("final_explanation"):
            raise InvalidInput("categorization_snapshot_changed")
    if (
        record.get("upstream", {}).get("matching_status", matched["status"])
        != matched["status"]
    ):
        raise InvalidInput("categorization_snapshot_changed")
    reasons = issue_reasons(record, q, matched)
    if reasons:
        return None, reasons
    # Verify only referenced canonical records; do not enumerate raw/clean directories.
    for reference in (matched.get("question_reference"), q.get("raw_reference")):
        if not reference:
            raise InvalidInput("question_reference_missing")
        store.check(reference)
    if store.record(matched["question_reference"]) != q:
        raise InvalidInput("clean_snapshot_changed")
    for reference in (
        matched.get("answer_reference"),
        (matched.get("final_explanation") or {}).get("source_reference"),
    ):
        if reference:
            store.check(reference)
    options = q.get("options") or []
    labels = [o.get("label") for o in options]
    if (
        not isinstance(q.get("main_question"), str)
        or not q["main_question"].strip()
        or not isinstance(q.get("main_body"), list)
    ):
        raise InvalidInput("required_question_content_missing")
    if (
        len(labels) < 2
        or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)])
        or any(
            not (str(o.get("text") or "").strip() or o.get("images")) for o in options
        )
    ):
        raise InvalidInput("answer_options_invalid")
    if matched.get("correct_answer") not in labels:
        raise InvalidInput("correct_answer_missing_or_invalid")
    final = matched.get("final_explanation")
    if not final:
        raise InvalidInput("explanation_state_missing")
    ai = final.get("explanation_by_ai", matched.get("explanation_by_ai"))
    if type(ai) is not bool:
        raise InvalidInput("explanation_ai_flag_missing")
    if "explanation_by_ai" in matched and matched["explanation_by_ai"] != ai:
        raise InvalidInput("explanation_ai_flag_conflict")
    content = Content(store, q, matched)
    body, answers = content.question_content()
    explanation = content.explanation(final)
    document = matched.get("question_document") or {}
    pdf = document.get("input") or {}
    result = {
        "id": stable_id(identity),
        **identity,
        "category": record["categorization"]["patterns"][0],
        "difficulty": None,
        "main_body": body,
        "main_question": q["main_question"],
        "main_answers": answers,
        "correct_answer": matched["correct_answer"],
        "explanation": explanation,
        "explanation_by_ai": ai,
        "assets": content.assets,
        "provenance": {
            "categorized_reference": ref,
            "upstream_question_id": q.get("question_id"),
            "question_source": {
                "filename": pdf.get("filename"),
                "sha256": pdf.get("sha256"),
                "pages": deepcopy(q.get("page_reference")),
            },
            "source_metadata_notices": deepcopy(document.get("warnings", [])),
        },
    }
    validate_question(result, categories)
    return result, []


def validate_question(q, categories):
    """Strict output invariants independent of source-specific upstream models."""
    required = {
        "id",
        "source",
        "year",
        "question_number",
        "section",
        "paper",
        "variant",
        "category",
        "difficulty",
        "main_body",
        "main_question",
        "main_answers",
        "correct_answer",
        "explanation",
        "explanation_by_ai",
        "assets",
        "provenance",
    }
    if set(q) != required:
        raise ValueError("Pre-final question fields do not match unified schema")
    identity = {
        k: q[k]
        for k in ("source", "year", "section", "paper", "variant", "question_number")
    }
    for field in ("section", "paper", "variant"):
        if q[field] is not None and (
            not isinstance(q[field], str) or not q[field].strip()
        ):
            raise ValueError("Invalid identity component")
    if not q["section"]:
        raise ValueError("Missing section")
    if q["source"] not in DEFAULT_INPUTS or q["id"] != stable_id(identity):
        raise ValueError("Invalid stable question identity")
    if (
        type(q["year"]) is not int
        or type(q["question_number"]) is not int
        or q["year"] <= 0
        or q["question_number"] <= 0
    ):
        raise ValueError("Invalid numeric identity")
    if (
        q["category"] not in TSA_IDS
        or q["category"] not in categories
        or q["difficulty"] is not None
        or type(q["explanation_by_ai"]) is not bool
    ):
        raise ValueError("Invalid category/difficulty/AI metadata")
    labels = [a["label"] for a in q["main_answers"]]
    if (
        len(labels) < 2
        or labels != list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(labels)])
        or q["correct_answer"] not in labels
        or not q["main_question"].strip()
    ):
        raise ValueError("Invalid required content")
    assets = {a["id"]: a for a in q["assets"]}
    if len(assets) != len(q["assets"]) or [a["order"] for a in q["assets"]] != list(
        range(1, len(assets) + 1)
    ):
        raise ValueError("Invalid asset identities/order")
    for a in q["assets"]:
        if (
            a["role"] not in {"body", "option", "explanation", "source_preview"}
            or not isinstance(a["path"], str)
            or not a["path"]
            or "://" in a["path"]
        ):
            raise ValueError("Invalid asset role/path")
        if len(a["sha256"]) != 64 or any(
            c not in "0123456789abcdef" for c in a["sha256"]
        ):
            raise ValueError("Invalid asset hash")
        if (
            a["role"] == "option"
            and a["option_label"] not in labels
            or a["role"] != "option"
            and a["option_label"] is not None
        ):
            raise ValueError("Invalid asset option label")

    def asset(identifier, role, label=None):
        if identifier not in assets or (
            assets[identifier]["role"],
            assets[identifier]["option_label"],
        ) != (role, label):
            raise ValueError("Invalid asset association")

    for b in q["main_body"]:
        if b["type"] == "visual":
            asset(b["asset_id"], "body")
        elif b["type"] != "text" or not isinstance(b.get("text"), str):
            raise ValueError("Invalid body block")
    for answer in q["main_answers"]:
        if not isinstance(answer["text"], str) or not (
            answer["text"].strip() or answer["asset_ids"]
        ):
            raise ValueError("Empty answer")
        for identifier in answer["asset_ids"]:
            asset(identifier, "option", answer["label"])
    if q["explanation"] is not None:
        for block in q["explanation"]["blocks"]:
            if block["type"] == "visual":
                asset(block["asset_id"], "explanation")
            elif block["type"] == "paragraph":
                if not isinstance(block.get("text"), str):
                    raise ValueError("Invalid paragraph")
            elif block["type"] == "list":
                if not all(isinstance(i.get("text"), str) for i in block["items"]):
                    raise ValueError("Invalid list")
            else:
                raise ValueError("Unsupported explanation block")


def validate(data):
    if (
        data.get("stage") != "pre_final"
        or data.get("schema_version") != "1"
        or data.get("owner") != OWNER
    ):
        raise ValueError("Not a unified pre-final dataset")
    if set(data["categories"]) != TSA_IDS:
        raise ValueError("Pre-final requires exactly the ten canonical TSA categories")
    ids = set()
    for q in data["questions"]:
        validate_question(q, data["categories"])
        if q["id"] in ids:
            raise ValueError("Duplicate pre-final ID")
        ids.add(q["id"])
    expected = dict(sorted(Counter(q["source"] for q in data["questions"]).items()))
    if data["summary"] != {"total": len(ids), "by_source": expected}:
        raise ValueError("Pre-final summary mismatch")
    return data


def build(inputs=None, *, root=ROOT):
    store = Store(root)
    catalogue = store.load(CATALOG)
    categories = {
        p["id"]: {"name": p["subcategory"], "family": p["category"]}
        for p in catalogue["patterns"]
    }
    if set(categories) != TSA_IDS:
        raise ValueError("Canonical category catalogue differs from pre-final schema")
    records, excludes, seen, source_refs = [], [], {}, []
    for source, path in (inputs or DEFAULT_INPUTS).items():
        if source not in DEFAULT_INPUTS:
            raise ValueError("Only TSA and BMAT categorized inputs are accepted")
        data = store.load(path)
        if data.get("stage") not in ("categorized", "categorization"):
            raise ValueError("Pre-final requires canonical categorization output")
        source_refs.append(store.reference(path))
        for index, record in enumerate(data["records"]):
            ref = {"path": store.relative(path), "json_pointer": f"/records/{index}"}
            identity, identifier = None, None
            reasons = gate(record, source, categories)
            try:
                identity = canonical_identity(source, record["identity"])
                identifier = stable_id(identity)
                if identifier in seen:
                    reasons.append("duplicate_identity")
                seen.setdefault(identifier, []).append(ref)
                if not reasons:
                    question, reasons = assemble(
                        record, source, identity, ref, categories, store
                    )
                    if question is not None:
                        records.append(question)
            except InvalidInput as error:
                reasons.append(error.code)
            except (KeyError, TypeError, IndexError) as error:
                reasons.append("malformed_input:" + type(error).__name__)
            if reasons:
                excludes.append(
                    {
                        "source": source,
                        "identity": identity or record.get("identity"),
                        "reference": ref,
                        "reasons": sorted(set(reasons)),
                    }
                )
    # Reject *all* occurrences, never retain whichever duplicate was traversed first.
    duplicates = {k for k, refs in seen.items() if len(refs) > 1}
    for q in records[:]:
        if q["id"] in duplicates:
            excludes.append(
                {
                    "source": q["source"],
                    "identity": {
                        k: q[k]
                        for k in (
                            "year",
                            "section",
                            "paper",
                            "variant",
                            "question_number",
                        )
                    },
                    "reference": q["provenance"]["categorized_reference"],
                    "reasons": ["duplicate_identity"],
                }
            )
            records.remove(q)
    records.sort(key=lambda q: q["id"])
    source_refs.sort(key=lambda r: r["path"])
    excludes.sort(
        key=lambda e: (
            e["source"],
            e["reference"]["path"],
            e["reference"]["json_pointer"],
        )
    )
    result = {
        "owner": OWNER,
        "stage": "pre_final",
        "schema_version": "1",
        "categories": categories,
        "inputs": source_refs,
        "taxonomy_reference": store.reference(CATALOG),
        "questions": records,
        "summary": {
            "total": len(records),
            "by_source": dict(sorted(Counter(q["source"] for q in records).items())),
        },
    }
    validation = {
        "owner": OWNER,
        "stage": "pre_final_validation",
        "schema_version": "1",
        "inputs": source_refs,
        "included": result["summary"],
        "excluded_total": len(excludes),
        "excluded_by_source": dict(
            sorted(Counter(e["source"] for e in excludes).items())
        ),
        "excluded_by_primary_reason": dict(
            sorted(Counter(primary_reason(e["reasons"]) for e in excludes).items())
        ),
        "reason_counts_overlapping": dict(
            sorted(Counter(r for e in excludes for r in e["reasons"]).items())
        ),
        "exclusions": excludes,
    }
    return validate(result), validation


def primary_reason(reasons):
    """Disjoint counts; detailed reason counts deliberately retain overlaps."""
    if "intentional_skip" in reasons:
        return "intentional_skip"
    if any(
        r
        in {
            "categorization_issue",
            "raw_issue",
            "cleaning_issues",
            "matching_issues",
            "matching_not_complete",
            "explanation_issue",
            "answer_issue",
            "option_issue",
            "upstream_review_required",
            "upstream_not_eligible",
            "asset_issue",
        }
        for r in reasons
    ):
        return "unresolved_issues"
    if "invalid_or_missing_category" in reasons:
        return "invalid_or_missing_category"
    return "input_validation"


def run(inputs=None, *, root=ROOT, output=None, validation_output=None):
    result, findings = build(inputs, root=root)
    output = output or root / "data/pre_final/questions.json"
    validation_output = validation_output or root / "data/pre_final/validation.json"
    if str(output) == str(validation_output):
        raise ValueError("Dataset and validation paths must differ")
    write_owned(output, result, root)
    write_owned(validation_output, findings, root)
    return result, findings
