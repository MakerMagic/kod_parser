"""Validate reviewed semantic assessments; consume CLEAN only, never infer labels.

Assessments are classifier output bound to complete content, not question-ID rules.
The single final subcategory determines its official parent.
"""

from collections import Counter
from copy import deepcopy
from pathlib import Path

from categorization.core import digest, file_ref, read

ROOT = Path(__file__).parent
OTHER = {"id": "Other", "name": "Other"}
OTHER_TOPICS = ("Probability", "Statistics", "Calculus", "Logarithms")


def taxonomy():
    data = read(ROOT / "taxonomy.json")
    parents = {c["id"]: c for c in data["categories"]}
    children = {s["id"]: s for s in data["subcategories"]}
    if len(parents) != 5 or len(children) != 65:
        raise ValueError(
            "Official taxonomy must have 5 categories and 65 subcategories"
        )
    if any(s["category_id"] not in parents for s in children.values()):
        raise ValueError("Invalid official parent")
    return data, parents, children


def semantic_content(question):
    assets = {a["id"]: a for a in question["assets"]}

    def blocks(values):
        result = []
        for b in values:
            row = {
                k: b[k]
                for k in ("type", "text", "latex", "display", "break_before", "ordered")
                if k in b
            }
            if b["type"] == "visual":
                a = assets[b["asset_id"]]
                row["asset_sha256"] = a["sha256"]
            elif b["type"] == "list":
                row["items"] = [blocks(i["content"]) for i in b["items"]]
            result.append(row)
        return result

    return {
        "content": blocks(question["content"]),
        "options": [
            {"label": o["label"], "content": blocks(o["content"])}
            for o in question["options"]
        ],
    }


def eligible(q):
    return (
        q.get("cleaning", {}).get("status") == "cleaned"
        and q.get("extraction_status") == "extracted"
        and not q.get("issues")
        and not q.get("cleaning_issues")
    )


def validate_assessment(value, children):
    if not isinstance(value, dict):
        raise TypeError("Classifier output must be one assessment object")
    if value.get("status") == "needs_review":
        if any(
            value.get(k) is not None
            for k in ("category_id", "subcategory_id", "categories", "subcategories")
        ):
            raise ValueError("Unresolved assessment cannot store a guessed category")
        if any(
            not isinstance(value.get(k), str) or not value[k].strip()
            for k in ("reason", "issue_code")
        ):
            raise ValueError("Uncertainty requires an exact reason and issue code")
        return
    if value.get("status") != "categorized":
        raise ValueError("Unknown categorization status")
    if value.get("category_id") == "Other":
        if value.get("subcategory_id") is not None:
            raise ValueError("Other has no subcategories")
        if any(k in value for k in ("categories", "subcategories")):
            raise ValueError("Multiple final classifications are forbidden")
        if (
            value.get("topic") not in OTHER_TOPICS
            or value.get("certainty") != "confirmed"
        ):
            raise ValueError("Other requires one confirmed approved topic")
        for key in ("dominant_operation", "evidence"):
            if not isinstance(value.get(key), str) or not value[key].strip():
                raise ValueError(
                    "Other requires semantic reasoning and source evidence"
                )
        return
    child = value.get("subcategory_id")
    if not isinstance(child, str) or child not in children:
        raise ValueError("Exactly one official subcategory is required")
    parent = children[child]["category_id"]
    if "category_id" in value and value["category_id"] != parent:
        raise ValueError("Subcategory does not belong to supplied parent")
    if "categories" in value or "subcategories" in value:
        raise ValueError("Multiple final classifications are forbidden")
    alternative = value.get("alternative_subcategory_id")
    if (
        not isinstance(alternative, str)
        or alternative not in children
        or alternative == child
    ):
        raise ValueError("Provide the nearest distinct official alternative")
    for key in ("dominant_operation", "why_not_alternative"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(
                "Semantic reasoning and alternative comparison are required"
            )


def build(clean_path, assessments, previous=None):
    source = read(clean_path)
    if (
        source.get("domain") != "mathematics"
        or source.get("stage") != "mathematics_clean"
    ):
        raise ValueError("Only canonical mathematics CLEAN is accepted")
    catalog, parents, children = taxonomy()
    reference = file_ref(clean_path)
    previous = previous or {"questions": []}
    if previous.get("stage", "mathematics_categorized") != "mathematics_categorized":
        raise ValueError("Unrelated previous output")
    old = {q["id"]: q for q in previous["questions"]}
    rows, exclusions, seen = [], [], set()
    for index, q in enumerate(source["questions"]):
        if q["id"] in seen:
            raise ValueError("Duplicate stable question ID")
        seen.add(q["id"])
        if not eligible(q):
            exclusions.append(
                {
                    "id": q["id"],
                    "reason": "Not an issue-free successfully cleaned record",
                }
            )
            continue
        content_hash = digest(semantic_content(q))
        cached = old.get(q["id"])
        if (
            cached
            and cached["content_sha256"] == content_hash
            and cached["assessment"]["status"] == "categorized"
        ):
            decision = deepcopy(cached["assessment"])
        else:
            decision = deepcopy(
                assessments.get(
                    content_hash,
                    {
                        "status": "needs_review",
                        "issue_code": "missing_assessment",
                        "reason": "Complete cleaned content has no content-bound semantic assessment.",
                    },
                )
            )
        validate_assessment(decision, children)
        category = subcategory = None
        issues = []
        if decision["status"] == "categorized":
            if decision.get("category_id") == "Other":
                category = deepcopy(OTHER)
            else:
                subcategory = children[decision["subcategory_id"]]
                category = parents[subcategory["category_id"]]
        else:
            issues.append(
                {
                    "code": decision["issue_code"],
                    "reason": decision["reason"],
                    **(
                        {"candidate_topic": decision["candidate_topic"]}
                        if "candidate_topic" in decision
                        else {}
                    ),
                }
            )
        rows.append(
            {
                "id": q["id"],
                "source_document_id": q["source_document_id"],
                "source_pdf": source["sources"][q["source_document_id"]]["filename"],
                "question_number": q["question_number"],
                "clean_reference": {**reference, "json_pointer": f"/questions/{index}"},
                "content_sha256": content_hash,
                "category": category,
                "subcategory": subcategory,
                "assessment": decision,
                "categorization_issues": issues,
            }
        )
    summary = {
        "eligible": len(rows),
        "categorized": sum(r["category"] is not None for r in rows),
        "unresolved": sum(bool(r["categorization_issues"]) for r in rows),
        "excluded": len(exclusions),
        "category_distribution": {
            k: sum(r["category"] is not None and r["category"]["id"] == k for r in rows)
            for k in (*parents, "Other")
        },
        "other_topic_distribution": {
            topic: sum(
                r["category"] == OTHER and r["assessment"].get("topic") == topic
                for r in rows
            )
            for topic in OTHER_TOPICS
        },
        "subcategory_distribution": dict(
            sorted(
                Counter(
                    r["subcategory"]["id"] for r in rows if r["subcategory"]
                ).items()
            )
        ),
    }
    data = {
        "domain": "mathematics",
        "stage": "mathematics_categorized",
        "schema_version": "2",
        "fallback_policy": {
            "category": OTHER,
            "approved_topics": list(OTHER_TOPICS),
            "subcategory": None,
            "certainty": "confirmed",
        },
        "taxonomy_reference": {
            **file_ref(ROOT / "taxonomy.json"),
            "official_source": catalog["source"],
        },
        "input": reference,
        "questions": rows,
        "summary": summary,
    }
    validation = {
        "domain": "mathematics",
        "stage": "mathematics_categorization_validation",
        "summary": summary,
        "excluded": exclusions,
        "unresolved": [
            {
                k: r[k]
                for k in (
                    "id",
                    "source_pdf",
                    "question_number",
                    "categorization_issues",
                )
            }
            for r in rows
            if r["categorization_issues"]
        ],
    }
    return data, validation
