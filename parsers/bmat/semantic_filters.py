"""BMAT exclusion evidence from requested operation and source proposition structure.

This is not normal TSA categorization. No question identity participates in a rule.
"""

import re


def search(pattern, text):
    return re.search(pattern, text, re.IGNORECASE)


def proposition_structure(question, *, expected_count=3):
    """Verify full propositions AND combination choices (three for exclusion).

    Normal categorization may inspect other lengths without making them BMAT
    exclusions; that does not weaken the exactly-three RAW filter.
    """
    stem = question["raw_components"].get("main_question") or ""
    body = question["raw_components"].get("main_body", "")
    # Read the final proposition series, not isolated CO2 subscripts or table rows.
    text = body + "\n" + stem
    entries = list(re.finditer(r"(?m)^\s*([1-9])[.)]?\s+([^\n]+)", text))
    series = []
    for item in entries:
        if item[1] == "1":
            series = [item]
        elif series:
            series.append(item)
    if (
        not series
        or [m[1] for m in series] != [str(i) for i in range(1, len(series) + 1)]
        or (expected_count is not None and len(series) != expected_count)
    ):
        return None
    statements = []
    for i, match in enumerate(series):
        end = series[i + 1].start() if i + 1 < len(series) else len(text)
        value = text[match.start(2) : end].strip()
        if len(value.split()) < 5 or not search(r"[a-z]{3}", value):
            return None
        statements.append(value)
    options = [o["text"].strip() for o in question["options"]]
    option_pattern = (
        r"^(?:(?:none|all)(?: of the (?:above(?: statements)?|statements|claims|conclusions|assumptions))?|"
        r"(?:both |neither )?[123I](?:(?:\s*(?:,\s*(?:and\s+)?|&|and|nor)\s*|\s+)[123])*(?: only)?)\.?$"
    )
    if expected_count is None:
        option_pattern = option_pattern.replace("[123I]", "[1-9I]").replace(
            "[123]", "[1-9]"
        )
    combination = re.compile(option_pattern, re.IGNORECASE)
    if len(options) < 3 or not all(combination.fullmatch(t) for t in options):
        return None
    if any(int(n) > len(series) for t in options for n in re.findall(r"\d+", t)):
        return None
    request = re.split(r"(?m)^\s*1[.)]?\s+", stem, maxsplit=1)[0]
    if not (
        search(r"\b(?:which|identify|select)\b", request)
        and search(
            r"\b(?:conclu\w*|infer\w*|flaw\w*|weak\w*|strength\w*|support\w*|assum\w*|principl\w*|reason\w*)\b",
            request,
        )
    ):
        return None
    return {
        "statements": statements,
        "combination_options": options,
        "request": request,
    }


def inference_evidence(question):
    stem = " ".join((question["raw_components"].get("main_question") or "").split())
    options = [o["text"].strip() for o in question["options"]]
    # Claim alternatives, not numerical/diagram choices in a constrained puzzle.
    claims = sum(
        len(t.split()) >= 4 and len(re.findall(r"\b[a-z]{2,}\b", t, re.IGNORECASE)) >= 3
        for t in options
    )
    if claims < 3 or not search(r"\b(?:which|what)\b", stem):
        return None
    counters = search(
        r"\b(?:conclusion|assum\w*|flaw\w*|weak\w*|strengthen\w*|challenge|"
        r"principle|same reasoning|explain\w*|arrangements?|configurations?)\b",
        stem,
    )
    if counters:
        return None
    patterns = {
        "supported_inference": r"\binference\b.{0,80}\b(?:drawn|supported|justified|follows)\b|\b(?:draw|support|justify)\w*\b.{0,50}\binference\b",
        "finding_justifies_claim": r"\b(?:finding|evidence|information|passage|result)\b.{0,40}\bjustif\w*\b|\bjustif\w*\b.{0,40}\b(?:finding|evidence|passage)\b",
        "implication_of_passage": r"\b(?:issue|passage|finding|statement|evidence|information|argument)\b.{0,60}\bimpl(?:ies|y)\b.{0,35}\bwhich\b",
        "definite_claim_about_evidence": r"\bcan\s+(?:definitely|reliably|certainly)\s+be\s+(?:said|inferred|deduced)\s+(?:about|from)\b",
    }
    for name, pattern in patterns.items():
        match = search(pattern, stem)
        if match:
            return {
                "pattern": name,
                "request_evidence": match[0],
                "claim_options": claims,
                "distinction": "Evidence entails a requested inference/justified claim; no explicit conclusion task. This is a source-set routing distinction, not a claim that inference and conclusion are philosophically disjoint.",
            }
    categorical = (
        len(
            re.findall(
                r"\b(?:all|some|no)\s+\w+\s+are\s+\w+",
                question["question_text"],
                re.IGNORECASE,
            )
        )
        >= 2
    )
    definite_statement = search(
        r"\bstatements?\b.{0,25}\b(?:definitely|necessarily)\s+true\b", stem
    )
    if categorical and definite_statement:
        return {
            "pattern": "necessary_implication_of_categorical_premises",
            "request_evidence": definite_statement[0],
            "claim_options": claims,
            "premise_evidence": "at least two explicit all/some/no class-membership propositions",
        }
    return None


def tags(question):
    found = []
    for name, evidence in [
        ("Subpoints", proposition_structure(question)),
        ("Drawing Inferences", inference_evidence(question)),
    ]:
        if evidence:
            found.append(
                {
                    "type": name,
                    "reason": (
                        "Exactly three full propositions are evaluated through single combination-valued answers."
                        if name == "Subpoints"
                        else "The requested operation derives an evidence-supported inference, rather than identifies an explicit conclusion/assumption/flaw."
                    ),
                    "evidence": evidence,
                    "positive_signals": list(evidence),
                    "counter_signals_checked": [
                        "incidental word in passage",
                        "unrelated numbered data",
                        "normal explicit conclusion task",
                    ],
                    "confidence": "high",
                    "status": "intentional_skip",
                }
            )
    return found
