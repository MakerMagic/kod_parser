"""Canonical TSA pattern IDs and existing BMAT exclusion names, not new labels."""

import json
import re
from pathlib import Path

from parsers.bmat.skip_rules import ORDER

CATALOG = Path(__file__).parents[1] / "patterns.json"
FAMILY = "BMAT-specific"


def categories():
    tsa = json.loads(CATALOG.read_text(encoding="utf-8"))["patterns"]
    return {
        p["id"]: {
            "category": p["category"],
            "subcategory": p["subcategory"],
            "description": p["description"],
        }
        for p in tsa
    } | {
        name: {
            "category": FAMILY,
            "subcategory": name,
            "description": "Existing BMAT exclusion definition; preserve its stored evidence and precedence.",
        }
        for name in ORDER
    }


def special(question):
    """Read existing exclusions; recognize the same answer frameworks in CLEAN.

    No extraction/skip metadata is mutated or recomputed. An explicit multiple-
    response instruction differs from one pair-valued multiple-choice answer.
    """
    evidence = question["bmat_filter"]
    if evidence["skip_from_pipeline"]:
        name = evidence["primary_type"]
        if name not in ORDER:
            raise ValueError("Unknown stored BMAT-specific category")
        return name, evidence["skip_reason"], "stored_bmat_filter"
    stem = question.get("main_question") or ""
    choices = [o.get("text", "").strip() for o in question.get("options", [])]
    combinations = len(choices) >= 3 and all(
        re.fullmatch(
            r"(?:(?:all|none)(?: of (?:the (?:above|statements)|them))?|[1-9](?:\s*(?:,\s*(?:and\s+)?|and|&)\s*[1-9])*(?: only)?)\.?",
            t,
            re.IGNORECASE,
        )
        for t in choices
    )
    if not combinations and (
        re.search(
            r"\b(?:shade|select|choose)\s+all\s+that\s+apply\b", stem, re.IGNORECASE
        )
        or re.search(
            r"\bwhich\s+(?:two|three)\s+of\s+the\s+following\s+(?:apply|are correct|are true)\b",
            stem,
            re.IGNORECASE,
        )
    ):
        return (
            "Several correct answers",
            "The stem explicitly requires multiple separately labelled responses; the options are not single combination-valued choices.",
            "clean_response_framework",
        )
    text = question.get("question_text", "")
    entries = list(re.finditer(r"(?m)^\s*([1-9])[.)]?\s+([^\n]+)", text))
    series = []
    for m in entries:
        if m[1] == "1":
            series = [m]
        elif series:
            series.append(m)
    proposition_request = re.search(
        r"\b(?:which|identify|select|deduce)\b", stem, re.IGNORECASE
    ) and re.search(
        r"\b(?:statements?|claims?|propositions?|why|challenges?|infer\w*|conclu\w*|flaw\w*|weak\w*|strength\w*|support\w*|assum\w*|principl\w*|reason\w*)\b",
        stem,
        re.IGNORECASE,
    )
    if (
        combinations
        and proposition_request
        and [m[1] for m in series] == ["1", "2", "3"]
        and all(
            len(m[2].split()) >= 5
            and len(re.findall(r"\b[a-z]{3,}\b", m[2], re.IGNORECASE)) >= 3
            for m in series
        )
    ):
        return (
            "Subpoints",
            "Exactly three full propositions must be evaluated and one combination-valued answer selected; not a numerical list or three unrelated data values.",
            "clean_proposition_framework",
        )
    return None


def assign(
    result, identifier, rationale, *, status="supported", method="semantic_attribution"
):
    if identifier not in categories():
        raise ValueError("Unknown canonical category")
    definition = categories()[identifier]
    result.update(
        category=definition["category"],
        subcategories=[definition["subcategory"]],
        patterns=[identifier],
        status=status,
        confidence="supported",
        rationale=rationale,
        issues=[],
    )
    result["decision_method"] = method
    return result


def validate(result):
    if result["status"] in {"supported", "intentional_skip"}:
        if len(result["patterns"]) != 1 or len(result["subcategories"]) != 1:
            raise ValueError("BMAT requires exactly one canonical category")
        definition = categories().get(result["patterns"][0])
        if not definition or (result["category"], result["subcategories"][0]) != (
            definition["category"],
            definition["subcategory"],
        ):
            raise ValueError("Noncanonical BMAT category ID/name")
        if result["issues"]:
            raise ValueError("Unresolved categorization cannot be accepted")
    elif (
        result["category"] is not None or result["subcategories"] or result["patterns"]
    ):
        raise ValueError(
            "Unresolved BMAT record must not pretend to have an accepted category"
        )
