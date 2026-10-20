"""Exact-identity supplied-source overlay; never overwrite existing explanations."""

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from processors.matching.core import file_reference
from processors.matching.explanation import build_final_explanation

from .core import eligibility, key


def apply(data, path, *, previous=None, prefer_text=False):
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    if source.get("stage") != "answer_raw" or source.get("source_family") != "bmat":
        raise ValueError("Supplied explanations must be normalized BMAT answers")
    provenance = source["source_document"]
    if file_reference(provenance["path"])["sha256"] != provenance["sha256"]:
        raise ValueError("Supplied source changed; reparse it")
    ref = file_reference(path)
    data["inputs"].append({"kind": "supplied_answers", **ref})
    by_key = defaultdict(list)
    for i, a in enumerate(source["answers"]):
        by_key[key(a)].append(
            {"record": a, "reference": {**ref, "json_pointer": f"/answers/{i}"}}
        )
    counts, seen = Counter(), set()
    old = {
        tuple(
            r["identity"][f]
            for f in ("source_family", "year", "section", "question_number")
        ): r
        for r in (previous or {}).get("records", [])
    }
    for record in data["records"]:
        ident = record["identity"]
        k = tuple(
            ident[f] for f in ("source_family", "year", "section", "question_number")
        )
        if k not in by_key:
            continue
        seen.add(k)
        items = deepcopy(by_key[k])
        record["supplied_imports"] = items
        q, a = record["question"], items[0]["record"]
        warnings = sorted({w for item in items for w in item["record"]["warnings"]})
        existing = record.get("answer")
        prior = old.get(k, {})
        previous_supplied = (prior.get("answer") or {}).get("source_document", {}).get(
            "source_format"
        ) == "task_supplied_bmat_explanations"
        if previous_supplied and q and eligibility(q) is None:
            for field in (
                "answer",
                "answer_reference",
                "correct_answer",
                "final_explanation",
            ):
                record[field] = deepcopy(prior[field])
            existing = record["answer"]
            if (
                existing["correct_answer"] == a["correct_answer"]
                and existing["explanation"] == a["explanation"]
            ):
                record["answer"] = deepcopy(a)
                record["answer_reference"] = deepcopy(items[0]["reference"])
                record["final_explanation"] = build_final_explanation(
                    a, items[0]["reference"]
                )
                existing = record["answer"]
        # Explicit user authorization only: replace an image-only web explanation
        # with their supplied text, never replace an existing manual/text solution.
        replace_image = bool(
            prefer_text
            and existing
            and existing.get("source_document", {}).get("source_format")
            == "bmat_wordpress_worked_solutions"
            and record["final_explanation"]["blocks"]
            and all(
                b["type"] == "visual" for b in record["final_explanation"]["blocks"]
            )
        )
        if len(items) != 1:
            status = "duplicate_supplied_source"
        elif q is None:
            status = "target_missing"
        elif blocked := eligibility(q):
            status = blocked[0]
        elif a["correct_answer"] not in [o["label"] for o in q["options"]]:
            status = "answer_incompatible"
        elif (
            record.get("correct_answer")
            and record["correct_answer"] != a["correct_answer"]
        ) or any(
            c["record"].get("correct_answer") not in (None, a["correct_answer"])
            for c in record["answer_candidates"]
        ):
            status = "answer_conflict"
        elif previous_supplied and existing["explanation"] != a["explanation"]:
            status = "explanation_conflict"
        elif warnings:
            status = "supplied_review_required"
            if previous_supplied:
                record["status"] = "explanation_review_required"
            if replace_image:
                record["answer_candidates"].append(
                    {
                        "record": deepcopy(existing),
                        "document": deepcopy(existing["source_document"]),
                        "reference": deepcopy(record["answer_reference"]),
                        "superseded_by": "explicit_user_supplied_text",
                    }
                )
                record["answer"] = deepcopy(a)
                record["answer_reference"] = deepcopy(items[0]["reference"])
                record["final_explanation"] = build_final_explanation(
                    a, items[0]["reference"]
                )
                record["status"] = "explanation_review_required"
        elif (
            existing
            and record["final_explanation"]["blocks"]
            and not previous_supplied
            and not replace_image
        ):
            status = "existing_preserved"
        else:
            status = "matched_supplied"
            if replace_image:
                record["answer_candidates"].append(
                    {
                        "record": deepcopy(existing),
                        "document": deepcopy(existing["source_document"]),
                        "reference": deepcopy(record["answer_reference"]),
                        "superseded_by": "explicit_user_supplied_text",
                    }
                )
            record["answer"] = deepcopy(a)
            record["answer_reference"] = deepcopy(items[0]["reference"])
            record["correct_answer"] = a["correct_answer"]
            record["final_explanation"] = build_final_explanation(
                a, items[0]["reference"]
            )
            record["explanation_by_ai"] = False
            record["status"] = "matched"
            record["issues"] = []
            # Historical web candidates remain traceable but are not selected.
            record["matching"]["source_selection"] = "explicit_user_supplied_identity"
            record["matching"]["confidence"] = (
                "exact_source_family_year_section_question"
            )
        for item in items:
            item["import_status"] = status
            item["comparison"] = (
                "same_answer_explanation_variant_preserved_separately"
                if status == "existing_preserved"
                else status
            )
        counts[status] += 1
        if status in {
            "answer_conflict",
            "explanation_conflict",
            "duplicate_supplied_source",
            "supplied_review_required",
            "answer_incompatible",
        }:
            issue = {
                "code": status,
                "reason": "; ".join(warnings)
                or "Supplied source conflicts with existing answer/candidates or identity.",
                "supplied_answer": a["correct_answer"],
                "existing_answer": record.get("correct_answer"),
                "source_reference": items[0]["reference"],
                "manual_review_required": True,
            }
            record["issues"].append(issue)
            # An explicitly uncertain alternative is not accepted. Keep prior
            # content intact, but don't advertise a verified match when its own
            # cited source is identified as needing review.
            same_source = (
                existing
                and a["source_document"].get("source_url")
                and a["source_document"]["source_url"]
                == existing["source_document"].get("source_url")
            )
            if (
                not existing
                or status in {"answer_conflict", "explanation_conflict"}
                or same_source
            ):
                record["status"] = "explanation_review_required" if existing else status
    missing = [k for k in by_key if k not in seen]
    data["source_issues"].extend(source["issues"])
    data["source_issues"].extend(
        {"code": "supplied_target_missing", "identity": list(k)} for k in missing
    )
    data["supplied_import_summary"] = {
        "records": sum(len(v) for v in by_key.values()),
        "by_year": dict(Counter(a["year"] for a in source["answers"])),
        "statuses": dict(counts),
        "target_missing": len(missing),
        "missing_numbers_in_supplied_years": {
            str(y): sorted(
                {
                    r["identity"]["question_number"]
                    for r in data["records"]
                    if r["identity"]["year"] == y
                }
                - {a["question_number"] for a in source["answers"] if a["year"] == y}
            )
            for y in sorted({a["year"] for a in source["answers"]})
        },
    }
    data["summary"]["statuses"] = dict(Counter(r["status"] for r in data["records"]))
    data["issues"] = [
        {**issue, **r["identity"]} for r in data["records"] for issue in r["issues"]
    ]
    return data
