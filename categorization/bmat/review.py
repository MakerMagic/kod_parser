"""Content-bound review using the existing TSA hashing/asset-review primitives.

Year/number are authoring navigation only. Runtime reuse requires the exact full
question digest and verified visual evidence; changed questions need new review.
"""

import csv
import json
from copy import deepcopy
from pathlib import Path

from categorization.core import digest, file_ref, verify_refs
from categorization.review import visual_references

from .taxonomy import ORDER, assign, categories


def visual_row(record):
    return {
        "question_view": record["question"],
        "provenance": {"question_reference": record["question_reference"]},
    }


def freeze_baseline(source, output):
    """Small persistent review scope, not another copy of the question corpus."""
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = [
        {k: r[k] for k in ("identity", "question_reference", "categorization")}
        | {"question_sha256": digest(r["question"])}
        for r in data["records"]
        if r["categorization"]["status"] == "not_evaluated"
    ]
    Path(output).write_text(
        json.dumps(
            {"owner": "bmat_review_baseline_v1", "records": rows},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def bind(baseline_path, decisions_path, output):
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    eligible = {
        (r["identity"]["year"], r["identity"]["question_number"]): r
        for r in baseline["records"]
        if r["categorization"]["status"] == "not_evaluated"
    }
    decisions, seen = [], set()
    with Path(decisions_path).open(encoding="utf-8", newline="") as stream:
        for item in csv.DictReader(stream, delimiter="\t"):
            navigation = int(item["year"]), int(item["question"])
            if navigation not in eligible or navigation in seen:
                raise ValueError("Duplicate/out-of-scope BMAT authored review")
            seen.add(navigation)
            if (
                item["category_id"] not in categories()
                or len(item["evidence"].strip()) < 60
            ):
                raise ValueError(
                    "Canonical label and substantive semantic assessment required"
                )
            row = eligible[navigation]
            if "question" not in row:
                ref = row["question_reference"]
                verify_refs([ref])
                source = json.loads(Path(ref["path"]).read_text(encoding="utf-8"))
                row["question"] = source["questions"][
                    int(ref["json_pointer"].rsplit("/", 1)[1])
                ]
                if digest(row["question"]) != row["question_sha256"]:
                    raise ValueError("Review baseline content changed")
            refs, missing = visual_references(visual_row(row))
            if missing:
                raise ValueError("Required review visual is missing")
            decisions.append(
                {
                    "identity": row["identity"],
                    "question_sha256": digest(row["question"]),
                    "category_id": item["category_id"],
                    "evidence": item["evidence"],
                    "input_issue": item.get("input_issue") or None,
                    "evaluated_categories": [
                        "ps_select",
                        "ps_procedure",
                        "ps_similarity",
                    ]
                    if item["category_id"].startswith("ps_")
                    else [
                        "ps_select",
                        "ps_procedure",
                        "ps_similarity",
                        item["category_id"],
                    ],
                    "visual_references": refs,
                    "previous_categorization": row["categorization"],
                }
            )
    if seen != eligible.keys():
        raise ValueError(
            "Every pending BMAT question needs an actual reviewed decision"
        )
    bound = {
        "owner": "bmat_content_bound_review_v1",
        "reviewer": "assistant_semantic_rulebook_review",
        "baseline_reference": file_ref(baseline_path),
        "decision_source_reference": file_ref(decisions_path),
        "rulebook_reference": file_ref(
            Path(__file__).parents[1] / "ps_attribution_rulebook.txt"
        ),
        "single_dominant_category_policy": "Current BMAT request supersedes multi-label output only for BMAT; TSA remains unchanged.",
        "decisions": decisions,
    }
    Path(output).write_text(
        json.dumps(bound, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return bound


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("owner") != "bmat_content_bound_review_v1":
        raise ValueError("Not a bound BMAT review")
    verify_refs(
        [
            data[k]
            for k in (
                "baseline_reference",
                "decision_source_reference",
                "rulebook_reference",
            )
        ]
    )
    keys = [d["question_sha256"] for d in data["decisions"]]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate content-bound review")
    return {d["question_sha256"]: d for d in data["decisions"]}


def apply(result, record, decisions):
    decision = decisions.get(digest(record["question"]))
    if decision is None:
        return result
    if record["question"]["cleaning_issues"]:
        raise ValueError("Review cannot clear upstream defects")
    refs, missing = visual_references(visual_row(record))
    if missing or refs != decision["visual_references"]:
        raise ValueError("Question visual context changed; review again")
    verify_refs(refs)
    previous = deepcopy(result)
    if decision.get("input_issue"):
        result.update(
            category=None,
            subcategories=[],
            patterns=[],
            status="needs_review",
            confidence="unresolved",
            rationale=decision["evidence"],
            issues=[
                {
                    "code": "input_representation_review",
                    "reason": decision["input_issue"],
                }
            ],
        )
    else:
        assign(
            result,
            decision["category_id"],
            decision["evidence"],
            status="intentional_skip"
            if decision["category_id"] in ORDER
            else "supported",
            method="content_bound_rulebook_review",
        )
    result["review"] = {
        "previous": previous,
        "baseline": decision["previous_categorization"],
        "proposed_category": decision["category_id"],
        "input_issue": decision.get("input_issue"),
        "evaluated_categories": decision["evaluated_categories"],
        "question_sha256": decision["question_sha256"],
        "visual_references": refs,
    }
    return result
