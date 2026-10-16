"""Local structural/quality checks; semantic correctness still needs backtesting."""

import re
from difflib import SequenceMatcher

MAX_CHARACTERS = 2000
_RELATIONSHIPS = re.compile(
    r"\b(?:contradict\w*|incompatible|necess\w*|sufficien\w*|irrelevan\w*|"
    r"weaken\w*|strengthen\w*|unsupported|alternative explanation|revers\w*)\b",
    re.IGNORECASE,
)
_CONTRADICTION = re.compile(r"\b(?:contradict\w*|incompatible)\b", re.IGNORECASE)
_META = re.compile(
    r"\b(?:as an ai|language model|my confidence|confidence score|generation process|let us carefully|to begin with)\b",
    re.IGNORECASE,
)
_GENERIC = re.compile(
    r"^(?:option [A-Z] |it |this option )?(?:is incorrect|is irrelevant|does not fit(?: the pattern)?|contradicts the passage)[.!]?$",
    re.IGNORECASE,
)


def render_text(candidate):
    """Count exactly the human-readable form, including labels and whitespace."""
    return (
        candidate["main_reasoning"]
        + "\n\n"
        + "\n\n".join(
            f"{item['label']}: {item['reason']}"
            for item in candidate["incorrect_options"]
        )
    )


def semantic_review(candidate):
    """Triage, NOT entailment checking. Even unflagged prose requires review.

    Lexical signals identify claims a reviewer should inspect; they cannot tell
    whether a relationship is asserted, negated, or logically justified.
    """
    parts = {"main_reasoning": candidate["main_reasoning"]}
    parts.update(
        {item["label"]: item["reason"] for item in candidate["incorrect_options"]}
    )
    return {
        "status": "pending",
        "method": "local_triage_then_documented_reasoning_review",
        "limitations": "Local checks do not prove entailment, coexistence, arithmetic, or necessity.",
        "parts": parts,
        "relationship_mentions": {
            part: sorted(
                {match.group().lower() for match in _RELATIONSHIPS.finditer(text)}
            )
            for part, text in parts.items()
            if _RELATIONSHIPS.search(text)
        },
        "coexistence_review_required": [
            part for part, text in parts.items() if _CONTRADICTION.search(text)
        ],
    }


def validate_semantic_review(candidate, checks, coexistence_checks):
    """Validate review evidence, not the truth of the reviewer's conclusions."""
    review = semantic_review(candidate)
    if set(checks) != set(review["parts"]) or any(
        not isinstance(reason, str) or len(reason.split()) < 8
        for reason in checks.values()
    ):
        raise ValueError(
            "Review requires substantive main and individual option checks"
        )
    if set(coexistence_checks) != set(review["coexistence_review_required"]):
        raise ValueError(
            "Every contradiction mention requires an explicit coexistence review"
        )
    for evidence in coexistence_checks.values():
        if (
            not isinstance(evidence, dict)
            or type(evidence.get("contradiction_asserted")) is not bool
            or type(evidence.get("can_coexist")) is not bool
            or not isinstance(evidence.get("reason"), str)
            or len(evidence["reason"].split()) < 8
        ):
            raise ValueError("Incomplete coexistence review evidence")
        if evidence["contradiction_asserted"] and evidence["can_coexist"]:
            raise ValueError(
                "False contradiction: compatible claims cannot be approved"
            )
    return review


def validate(candidate, *, options, correct_answer):
    errors = []
    if not isinstance(candidate, dict):
        return ["malformed_explanation"]
    if "error" in candidate:
        return ["provider_could_not_explain_reliably"]
    if set(candidate) != {"correct_answer", "main_reasoning", "incorrect_options"}:
        errors.append("unsupported_structure")
    if candidate.get("correct_answer") != correct_answer:
        errors.append("correct_answer_mismatch")
    labels = [o["label"] for o in options]
    main, items = candidate.get("main_reasoning"), candidate.get("incorrect_options")
    if not isinstance(main, str) or len(main.split()) < 12:
        errors.append("main_reasoning_insubstantial")
    if not isinstance(items, list) or any(
        not isinstance(i, dict)
        or set(i) != {"label", "reason"}
        or not isinstance(i.get("label"), str)
        or not isinstance(i.get("reason"), str)
        for i in (items if isinstance(items, list) else [])
    ):
        return sorted({*errors, "malformed_incorrect_options"})
    expected = [label for label in labels if label != correct_answer]
    received = [i["label"] for i in items]
    if expected != received:
        errors.append("incorrect_option_coverage")
    for item in items:
        reason = item["reason"].strip()
        if len(reason.split()) < 5 or _GENERIC.fullmatch(reason):
            errors.append("incorrect_option_reason_insubstantial")
    normalized = [" ".join(i["reason"].lower().split()) for i in items]
    if any(
        SequenceMatcher(None, left, right).ratio() >= 0.90
        for index, left in enumerate(normalized)
        for right in normalized[index + 1 :]
    ):
        errors.append("duplicated_incorrect_option_reasons")
    if isinstance(main, str):
        text = render_text(candidate)
        if len(text) > MAX_CHARACTERS:
            errors.append("explanation_too_long")
        if _META.search(text) or "```" in text:
            errors.append("meta_commentary_or_extra_structure")
        for label in re.findall(r"\b(?:option|choice|answer)\s+([A-Z])\b", text):
            if label not in labels:
                errors.append("unknown_option_reference")
        for label in re.findall(
            r"\b(?:option|choice|answer)\s+([A-Z])\s+is\s+(?:the\s+)?correct\b",
            text,
            re.IGNORECASE,
        ):
            if label.upper() != correct_answer:
                errors.append("contradictory_correct_answer_claim")
        for label in re.findall(r"\b([A-Z])\s+is\s+(?:the\s+)?correct\b", text):
            if label != correct_answer:
                errors.append("contradictory_correct_answer_claim")
        if re.search(
            r"\b"
            + re.escape(correct_answer)
            + r"\s+is\s+(?:incorrect|wrong|not correct|ruled out)\b",
            text,
        ):
            errors.append("contradictory_correct_answer_claim")
    return sorted(set(errors))
