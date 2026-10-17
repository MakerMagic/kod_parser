"""Positive answer assertions, not mere option-letter mentions."""

import re

# Patterns describe assertion families. Negation and conflicting positive
# assertions are checked independently; no question-number lookup is used.
PATTERNS = {
    "explicit_phrase": [
        r"(?:the\s+)?correct\s+answer\s+is\s+(?:option\s+)?(?P<label>[A-E])\b",
        r"\boption\s+(?P<label>[A-E])\s+is\s+(?:the\s+)?correct\b",
    ],
    "semantic_pattern": [
        r"\b(?:this(?:\s+(?:assumption|conclusion))?|the\s+principle)\s+is\s+(?:expressed|illustrated|stated)\s+in\s+option\s+(?P<label>[A-E])\b",
        r"\boption\s+(?P<label>[A-E])\s+(?:expresses|states|identifies)\s+(?:(?:the|this)\s+)?(?:main\s+conclusion|erroneous\s+step\s+in\s+(?:the\s+)?(?:reasoning|argument))\b",
        r"\boption\s+(?P<label>[A-E])\s+is\s+a\s+statement\s+of\s+the\s+main\s+conclusion\b",
        r"\boption\s+(?P<label>[A-E])\s+illustrates\s+(?:the\s+same|this)\s+principle\b",
        r"\bthe\s+passage\s+and\s+option\s+(?P<label>[A-E])\s+(?:both\s+)?share\s+the\s+same\s+underlying\s+structure\b",
        r"\b(?:we\s+can\s+draw|can\s+be\s+drawn\s+from)\s+option\s+(?P<label>[A-E])\s+as\s+a\s+conclusion\b",
        r"\boption\s+(?P<label>[A-E])\s+supplies\s+this\s+connection\b",
        r"\bline\s+of\s+reasoning\s+in\s+option\s+(?P<label>[A-E])\s+is\s+essential\s+for\s+the\s+conclusion\b",
        r"\bwhich\s+is\s+stated\s+in\s+option\s+(?P<label>[A-E])\b",
    ],
}


def infer_answer(text, question_text="", labels="ABCDE"):
    """Return evidence-bearing unique inference or an unresolved result.

    Weakening is only positive evidence when the actual prompt requests it.
    Other positive families identify the answer explicitly in the explanation.
    """
    normalized = " ".join(text.split())
    evidence = []
    patterns = {key: list(values) for key, values in PATTERNS.items()}
    if re.search(
        r"\b(?:weaken|weakens|weakening|undermine)\b", question_text, re.IGNORECASE
    ):
        patterns["semantic_pattern"].append(
            r"\boption\s+(?P<label>[A-E])\s+weakens\s+(?:the\s+argument|the\s+inference)\b"
        )
    for method, family in patterns.items():
        for pattern in family:
            for match in re.finditer(pattern, normalized, re.IGNORECASE):
                # Do not promote a quoted, hypothetical or negated assertion.
                left = normalized[max(0, match.start() - 65) : match.start()]
                clause = re.split(r"[.!?;:]", left)[-1]
                if re.search(
                    r"\b(?:not|never|cannot|can't|if|whether|suppose)\b",
                    clause,
                    re.IGNORECASE,
                ):
                    continue
                label = match["label"].upper()
                if label in labels:
                    evidence.append(
                        {
                            "label": label,
                            "method": method,
                            "text": match[0],
                            "normalized_span": [match.start(), match.end()],
                        }
                    )
    candidates = sorted({item["label"] for item in evidence})
    return {
        "correct_answer": candidates[0] if len(candidates) == 1 else None,
        "method": (
            "explicit_phrase"
            if len(candidates) == 1
            and any(e["method"] == "explicit_phrase" for e in evidence)
            else "semantic_pattern"
            if len(candidates) == 1
            else "unresolved"
        ),
        "candidates": candidates,
        "evidence": evidence,
        "normalization": "whitespace_and_case_for_comparison_only",
        "status": "resolved" if len(candidates) == 1 else "unresolved",
    }
