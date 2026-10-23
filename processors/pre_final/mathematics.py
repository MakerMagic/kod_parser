"""Read-only mathematics assembly. Blocking findings prohibit rendering."""

import argparse
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from categorization.mathematics.core import (
    OTHER,
    eligible,
    semantic_content,
    taxonomy,
    validate_assessment,
)
from parsers.mathematics.latex import validate as latex_errors
from parsers.mathematics.structure import walk
from processors.normalization.mathematics.structure import projection_is_lossless

from .storage import OWNER, ROOT, InvalidInput, Store, digest, write_owned

SCHEMA = json.loads(
    Path(__file__).with_name("mathematics_schema.json").read_text(encoding="utf8")
)


def assert_ready(data):
    if not data.get("summary", {}).get("ready_for_rendering") or data["summary"].get(
        "blocking_issues"
    ):
        raise InvalidInput(
            "pre_final_blocked",
            "Unresolved pre-final findings prohibit Question Rendering",
        )


def structural_issues(row, store):
    issues = []

    def finding(code, field, reason):
        issues.append({"code": code, "field": field, "reason": reason})

    if row["id"] != f"{row['source_document_id']}_q{row['question_number']:03d}":
        finding(
            "invalid_identity",
            "id",
            "ID does not match existing intrinsic source-document/question identity",
        )
    options = row["main_answers"]
    labels = [o["label"] for o in options]
    if len(labels) < 2 or labels != [chr(65 + n) for n in range(len(labels))]:
        finding(
            "invalid_options",
            "main_answers",
            "Options must be complete, unique and in consecutive source-label order",
        )
    if row["correct_answer"] not in labels:
        finding(
            "invalid_correct_answer",
            "correct_answer",
            "Stored correct answer does not reference a supplied option",
        )
    assets = {a["id"]: a for a in row["assets"]}
    if len(assets) != len(row["assets"]):
        finding("duplicate_asset", "assets", "Asset IDs are not unique")
    for asset in assets.values():
        try:
            store.check(asset)
        except (InvalidInput, OSError) as error:
            finding("invalid_asset", "assets." + asset["id"], str(error))
    groups = [("main_body", row["main_body"]), ("main_question", row["main_question"])]
    groups += [("option." + o["label"], o["content"]) for o in options]
    for field, blocks in groups:
        if field.startswith("option.") and not blocks:
            finding("empty_content", field, "Required ordered content is empty")
        for index, block in enumerate(walk(blocks or [])):
            kind = block.get("type")
            component = f"{field}.blocks[{index}]"
            if kind == "math":
                for reason in latex_errors(block.get("latex", "")):
                    finding("invalid_latex", component, reason)
                if not block.get("latex", "").strip():
                    finding("invalid_latex", component, "Empty mathematical expression")
            elif kind == "visual":
                if field == "main_question":
                    finding(
                        "image_in_main_question",
                        component,
                        "Question visuals must be owned by main_body; main_question is text/LaTeX only",
                    )
                asset = assets.get(block.get("asset_id"))
                if not asset:
                    finding(
                        "missing_asset_reference",
                        component,
                        "Visual block does not resolve to an asset",
                    )
                elif field.startswith("option.") and (
                    asset["role"] != "option" or asset.get("option_label") != field[-1]
                ):
                    finding(
                        "asset_association",
                        component,
                        "Option visual belongs to a different component/label",
                    )
                elif (
                    field in {"main_body", "main_question"} and asset["role"] != "body"
                ):
                    finding(
                        "asset_association",
                        component,
                        "Body visual is not a body asset",
                    )
            elif kind == "text":
                if not isinstance(block.get("text"), str):
                    finding("invalid_text", component, "Text block lacks a text string")
            elif kind != "list":
                finding(
                    "unsupported_content",
                    component,
                    f"Unsupported ordered block type: {kind}",
                )
    return issues


def validate_dataset(data, store=None):
    store = store or Store()
    if (
        data.get("stage") != "mathematics_pre_final"
        or data.get("domain") != "mathematics"
    ):
        raise ValueError("Expected mathematics pre-final")
    if any(k not in data for k in SCHEMA["required"]):
        raise ValueError("Missing required mathematics dataset field")
    if data["summary"]["included"] != len(data["questions"]):
        raise ValueError("Included question count disagrees")
    _, parents, children = taxonomy()
    store.check(data["taxonomy_reference"])
    seen, identities, contents = set(), set(), set()
    for q in data["questions"]:
        if any(k not in q for k in SCHEMA["$defs"]["question"]["required"]):
            raise ValueError("Missing required mathematics question field")
        if (
            q["source"] != "Mathematics"
            or q["content_layout"] != "body_and_question"
            or not isinstance(q["main_body"], list)
            or (q["main_question"] is not None and not q["main_question"])
            or not (q["main_body"] or q["main_question"])
        ):
            raise ValueError("Invalid mathematics content contract")
        identity = (q["source_document_id"], q["question_number"])
        if q["id"] in seen or identity in identities or q["content_sha256"] in contents:
            raise ValueError("Duplicate mathematics question")
        seen.add(q["id"])
        identities.add(identity)
        contents.add(q["content_sha256"])
        validate_assessment(q["categorization_evidence"], children)
        if q["category"] == OTHER:
            if (
                q["subcategory"] is not None
                or q["categorization_evidence"].get("category_id") != "Other"
            ):
                raise ValueError("Invalid Other classification")
        elif (
            q["subcategory"] is None
            or q["subcategory"] != children.get(q["subcategory"]["id"])
            or q["category"] != parents.get(q["subcategory"]["category_id"])
        ):
            raise ValueError("Invalid official mathematics parent/child")
        problems = structural_issues(q, store)
        if problems:
            raise ValueError(f"Invalid admitted question {q['id']}: {problems}")
        for reference in q["provenance"].values():
            store.record(reference)
        clean = store.record(q["provenance"]["clean_reference"])
        if (
            q["main_body"] != clean["main_body"]
            or q["main_question"] != clean["main_question"]
            or q["main_answers"] != clean["options"]
            or q["assets"] != clean["assets"]
        ):
            raise ValueError("Pre-final changed upstream content/order/assets")
        if not projection_is_lossless(
            clean["content"], q["main_body"], q["main_question"]
        ):
            raise ValueError("Context/task projection lost or duplicated content")
        if digest(semantic_content(clean)) != q["content_sha256"]:
            raise ValueError("Question content hash differs from reviewed CLEAN")
        matched = store.record(q["provenance"]["matching_reference"])
        key = store.record(q["provenance"]["answer_reference"])
        if (
            matched["id"] != q["id"]
            or key["question_number"] != q["question_number"]
            or q["correct_answer"] != matched["correct_answer"]
            or key["correct_answer"] != q["correct_answer"]
        ):
            raise ValueError(
                "Pre-final answer/identity differs from canonical matching"
            )
        store.check(data["sources"][q["source_document_id"]])
    return data


def build(categorized, clean, matched, *, root=ROOT, source_document_ids=None):
    store = Store(root)
    cat, cleaned, merged = (store.load(p) for p in (categorized, clean, matched))
    for data, stage in (
        (cat, "mathematics_categorized"),
        (cleaned, "mathematics_clean"),
        (merged, "mathematics_matched"),
    ):
        if data.get("stage") != stage or data.get("domain") != "mathematics":
            raise ValueError(f"Expected canonical {stage}")
    clean_rows = {q["id"]: q for q in cleaned["questions"]}
    matches = {q["id"]: (i, q) for i, q in enumerate(merged["questions"])}
    if len(matches) != len(merged["questions"]) or len(clean_rows) != len(
        cleaned["questions"]
    ):
        raise ValueError("Duplicate upstream identity")
    selected_sources = None
    if source_document_ids is not None:
        selected_sources = set(source_document_ids)
        unknown = selected_sources - set(merged["sources"])
        if not selected_sources or unknown:
            raise ValueError(f"Invalid pre-final source selection: {sorted(unknown)}")
    _, parents, children = taxonomy()
    rows, excluded, findings = [], [], []
    categorized_count = matched_count = 0
    for index, r in enumerate(cat["questions"]):
        if (
            selected_sources is not None
            and r["source_document_id"] not in selected_sources
        ):
            continue
        identity = {
            k: r[k]
            for k in ("id", "source_document_id", "source_pdf", "question_number")
        }
        if (
            not r["category"]
            or r["categorization_issues"]
            or r["assessment"]["status"] != "categorized"
        ):
            excluded.append(
                {
                    **identity,
                    "code": "categorization_not_eligible",
                    "reason": "No successful issue-free categorization",
                    "blocking": False,
                }
            )
            continue
        categorized_count += 1
        q = clean_rows.get(r["id"])
        pair = matches.get(r["id"])
        if not q or not eligible(q):
            excluded.append(
                {
                    **identity,
                    "code": "clean_not_eligible",
                    "reason": "No completed issue-free CLEAN record",
                    "blocking": False,
                }
            )
            continue
        if (
            not pair
            or pair[1]["matching"]["status"] != "matched"
            or not pair[1].get("correct_answer")
        ):
            excluded.append(
                {
                    **identity,
                    "code": "matching_not_complete",
                    "reason": "Required validated matched correct answer is missing",
                    "blocking": False,
                }
            )
            continue
        matched_count += 1
        mi, answer = pair
        required = (
            "id",
            "source_document_id",
            "question_number",
            "content",
            "main_body",
            "main_question",
            "options",
            "assets",
            "raw_reference",
        )
        missing = [key for key in required if key not in q]
        if missing:
            findings.append(
                {
                    **identity,
                    "state": "blocked",
                    "issues": [
                        {
                            "code": "required_input_missing",
                            "field": ", ".join(missing),
                            "reason": "Required canonical CLEAN fields are missing; assembly cannot create upstream data",
                        }
                    ],
                }
            )
            continue
        problems = []

        def problem(code, field, reason, *, problems=problems):
            problems.append({"code": code, "field": field, "reason": reason})

        if answer.get("issues") or answer["matching"].get("issues"):
            problem(
                "matching_upstream_issue",
                "matching.issues",
                json.dumps(
                    answer.get("issues") or answer["matching"]["issues"],
                    ensure_ascii=False,
                ),
            )
        stale = []
        for field, reference in (
            ("matching.raw_reference", answer.get("raw_reference")),
            ("matching.key_reference", answer["matching"].get("key_reference")),
        ):
            try:
                if not reference:
                    raise InvalidInput("reference_missing", field)
                store.check(reference)
            except (InvalidInput, OSError) as error:
                stale.append(f"{field}: {error}; stored reference: {reference}")
        if stale:
            problem(
                "matching_reference_changed",
                "matching.provenance",
                "Stored matching provenance cannot be verified against current canonical RAW. "
                + " | ".join(stale),
            )
        try:
            if (
                store.record(r["clean_reference"]) != q
                or digest(semantic_content(q)) != r["content_sha256"]
            ):
                raise InvalidInput("categorization_clean_changed")
            raw_q = store.record(q["raw_reference"])
            if (
                raw_q["id"] != q["id"]
                or raw_q.get("issues")
                or raw_q.get("extraction_status") != "extracted"
            ):
                raise InvalidInput("raw_not_eligible")
            source = cleaned["sources"][q["source_document_id"]]
            store.check(source)
            if any(
                answer[k] != q[k]
                for k in ("id", "source_document_id", "question_number")
            ):
                raise InvalidInput("matching_identity_conflict")
            if not stale:
                key = store.record(answer["matching"]["key_reference"])
                if (
                    key["question_number"] != q["question_number"]
                    or key["correct_answer"] != answer["correct_answer"]
                ):
                    raise InvalidInput("answer_key_conflict")
            validate_assessment(r["assessment"], children)
            if r["category"] == OTHER:
                if (
                    r["subcategory"] is not None
                    or r["assessment"].get("category_id") != "Other"
                ):
                    raise InvalidInput("invalid_other")
            elif r["subcategory"] != children.get(
                r["assessment"]["subcategory_id"]
            ) or r["category"] != parents.get(r["subcategory"]["category_id"]):
                raise InvalidInput("invalid_category")
        except (InvalidInput, ValueError, KeyError, OSError) as error:
            problem(
                getattr(error, "code", "invalid_input"),
                "provenance/classification",
                str(error),
            )
        row = {
            "id": q["id"],
            "source": "Mathematics",
            "source_document_id": q["source_document_id"],
            "source_pdf": r["source_pdf"],
            "question_number": q["question_number"],
            "content_layout": "body_and_question",
            "main_body": deepcopy(q["main_body"]),
            "main_question": deepcopy(q["main_question"]),
            "main_answers": deepcopy(q["options"]),
            "correct_answer": answer["correct_answer"],
            "category": deepcopy(r["category"]),
            "subcategory": deepcopy(r["subcategory"]),
            "categorization_evidence": deepcopy(r["assessment"]),
            "assets": deepcopy(q["assets"]),
            "content_sha256": r["content_sha256"],
            "provenance": {
                "raw_reference": q["raw_reference"],
                "clean_reference": r["clean_reference"],
                "categorization_reference": store.reference(
                    categorized, f"/questions/{index}"
                ),
                "matching_reference": store.reference(matched, f"/questions/{mi}"),
                "answer_reference": answer["matching"]["key_reference"],
            },
        }
        problems.extend(structural_issues(row, store))
        if problems:
            findings.append({**identity, "state": "blocked", "issues": problems})
        else:
            rows.append(row)
    duplicate_ids = Counter(q["id"] for q in rows)
    duplicate_contents = Counter(q["content_sha256"] for q in rows)
    for q in rows[:]:
        if duplicate_ids[q["id"]] > 1 or duplicate_contents[q["content_sha256"]] > 1:
            findings.append(
                {
                    **{k: q[k] for k in ("id", "source_pdf", "question_number")},
                    "state": "blocked",
                    "issues": [
                        {
                            "code": "duplicate_question",
                            "field": "id/content_sha256",
                            "reason": "Duplicate stable identity or identical complete question content",
                        }
                    ],
                }
            )
            rows.remove(q)
    rows.sort(key=lambda q: q["id"])
    summary = {
        "categorized_candidates": categorized_count,
        "matched_candidates": matched_count,
        "included": len(rows),
        "blocked_questions": len(findings),
        "blocking_issues": sum(len(f["issues"]) for f in findings),
        "upstream_exclusions": len(excluded),
        "excluded_by_reason": dict(
            sorted(Counter(e["code"] for e in excluded).items())
        ),
        "by_source": dict(sorted(Counter(q["source_pdf"] for q in rows).items())),
        "ready_for_rendering": not findings,
    }
    if selected_sources is not None:
        summary["source_document_ids"] = sorted(selected_sources)
    data = {
        "owner": OWNER,
        "domain": "mathematics",
        "stage": "mathematics_pre_final",
        "schema_version": "2",
        "inputs": [store.reference(p) for p in (categorized, clean, matched)],
        "taxonomy_reference": cat["taxonomy_reference"],
        "summary": summary,
        "sources": {
            sid: deepcopy(cleaned["sources"][sid])
            for sid in sorted({q["source_document_id"] for q in rows})
        },
        "questions": rows,
    }
    validation = {
        "owner": OWNER,
        "domain": "mathematics",
        "stage": "mathematics_pre_final_validation",
        "schema_version": "1",
        "summary": summary,
        "issues": findings,
        "exclusions": excluded,
    }
    validate_dataset(data, store)
    return data, validation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--categorized",
        type=Path,
        default=ROOT / "data/categorized/mathematics/questions.json",
    )
    parser.add_argument(
        "--clean", type=Path, default=ROOT / "data/clean/mathematics/questions.json"
    )
    parser.add_argument(
        "--matched", type=Path, default=ROOT / "data/merged/mathematics/questions.json"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "data/pre_final/mathematics"
    )
    parser.add_argument("--docs-dir", type=Path, default=ROOT / "docs/mathematics")
    parser.add_argument(
        "--source-prefix",
        action="append",
        help="Restrict this assembly run to source PDF filename prefixes; may be repeated",
    )
    args = parser.parse_args(argv)
    source_ids = None
    if args.source_prefix:
        matched = Store().load(args.matched)
        source_ids = {
            source_id
            for source_id, source in matched["sources"].items()
            if any(
                source["filename"].casefold().startswith(prefix.casefold())
                for prefix in args.source_prefix
            )
        }
        if not source_ids:
            raise ValueError("No source documents match the requested prefix")
    data, validation = build(
        args.categorized,
        args.clean,
        args.matched,
        source_document_ids=source_ids,
    )
    write_owned(args.output_dir / "questions.json", data)
    write_owned(args.output_dir / "validation.json", validation)
    from .mathematics_artifacts import generate

    generate(args.output_dir, args.docs_dir)
    print(json.dumps(data["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if data["summary"]["ready_for_rendering"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
