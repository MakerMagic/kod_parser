"""Evidence-bearing BMAT exclusions; never normal TSA subcategory attribution."""

import re
from collections import defaultdict

ORDER = [
    "Shared Information Range",
    "No Question",
    "Necessary and Sufficient Conditions",
    "Several correct answers",
    "Complete the text",
    "Source",
    "Variable-related question",
    "Explanation",
    "too long",
]


def has(pattern, text):
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL)


def semantic_tags(q):
    body = q["question_text"]
    stem = q["raw_components"]["main_question"] or ""
    s = " ".join(stem.split())
    options = [o["text"].strip() for o in q["options"]]
    tags = []

    def add(name, evidence, signals, counter):
        tags.append(
            {
                "type": name,
                "reason": evidence,
                "positive_signals": signals,
                "counter_signals_checked": counter,
                "confidence": "high",
                "status": "intentional_skip",
            }
        )

    necessary = sum(
        bool(has(r"\bnecessary\b", t) and has(r"\bsufficient\b", t)) for t in options
    )
    if (
        necessary >= 3
        and sum(bool(has(r"\b(both|neither|not|but)\b", t)) for t in options) >= 2
    ):
        add(
            "Necessary and Sufficient Conditions",
            "Answer alternatives compare necessity and sufficiency of the same condition.",
            [
                "at least three necessary/sufficient alternatives",
                "logical contrasts in choices",
            ],
            ["not a lone occurrence in passage"],
        )
    combinations = sum(
        bool(
            has(
                r"^(?:[1-9A-H](?:\s*[,/&+]\s*|\s+and\s+|\s+or\s+))+[1-9A-H](?:\s+only)?[.]?$|\b(?:both|neither|only)\b",
                t,
            )
        )
        for t in options
    )
    multi = has(
        r"\b(?:choose|select|identify|give)\s+(?:any\s+)?(?:two|three|all)\s+(?:of\s+)?(?:the\s+)?(?:answers?|options?|statements?|that apply)\b|\bwhich\s+(?:two|three)\s+(?:of\s+)?(?:these\s+|the following\s+)?(?:statements?|conclusions?|options?)\b|\b(?:two|three) answers? (?:are|is) correct\b|\bselect all that apply\b",
        s,
    )
    multi = multi or has(
        r"\b(?:choose|select)\s+the\s+pair\b|\bwhich\s+(?:of the following\s+)?statements\s+(?:are|would|must)\b",
        s,
    )
    if multi and combinations < 2:
        add(
            "Several correct answers",
            "The request selects multiple separate choices, not one combination-valued answer.",
            [multi[0], "no combination-option framework"],
            ["paired contents within a single choice"],
        )
    completion = has(r"\b(?:complet\w*|fill\w*|insert\w*|missing|omitted)\b", s)
    completion_object = has(
        r"\b(?:argument|passage|text|sentence|phrase|word|gap|blank)\b", s
    )
    blank = has(r"_{3,}|-{3,}|\.{4,}", body)
    if (
        completion
        and completion_object
        and (blank or has(r"\b(?:phrase|word|sentence|argument)\b", s))
    ):
        add(
            "Complete the text",
            "Select missing textual/argument content rather than solve a numeric blank.",
            [
                completion[0],
                "textual completion object",
                "blank marker" if blank else "explicit omitted/completing text request",
            ],
            ["underscores alone", "numeric table cell"],
        )
    attribution = has(
        r"[\[(]\s*sources?\s*[:：][^\])]+[\])]|(?:^|\n)\s*(?:sources?|adapted from|extract from)\s*[:：]\s*\S+",
        body,
    )
    if attribution:
        add(
            "Source",
            attribution[0],
            ["attached attribution syntax"],
            ["ordinary prose use of source"],
        )
    explanation = has(
        r"\b(?:explain(?:s|ed|ing)?|explanation|account(?:s)? for|reconcile|incompatib\w*|paradox)\b",
        s,
    )
    evaluation = has(
        r"\b(?:best|possible|could|support|why|how|account|incompatib|explanation offered|explanation given)\w*\b",
        s,
    )
    flaw = has(
        r"\b(?:flaw|reasoning error|erroneous step|main conclusion|assumption)\b", s
    )
    if (
        explanation
        and evaluation
        and not flaw
        and (
            has(
                r"\bexplanation\b|\b(?:best|would|could|can|might)\s+(?:\w+\s+){0,3}explain\b|\bnot incompatible\b|\baccount(?:s)? for\b",
                s,
            )
        )
    ):
        add(
            "Explanation",
            "The requested operation identifies/evaluates a cause or resolves an observed apparent incompatibility.",
            [explanation[0], "explanation-evaluation intent"],
            ["explain a flaw/conclusion", "explanation mentioned only in body"],
        )
    variables = has(
        r"\b(?:variables?|function|equation|algebra|proportional|inversely)\b", body
    )
    symbols = re.findall(r"(?<![A-Za-z])([a-z])(?![A-Za-z])", body)
    relation = has(
        r"(?:\b[a-z]\b\s*[=<>≤≥]|\b[a-z]\b\s*[+−–*/^]\s*(?:\d|[a-z]\b)|\bf\s*\(\s*[a-z]\s*\))",
        body,
    )
    relation = relation or has(
        r"\b[a-z]\b\s+(?:is|varies)\s+(?:(?:directly|inversely)\s+)?(?:proportional to|a function of|dependent on|greater than|less than)\s+[a-z]\b",
        body,
    )
    target = has(
        r"\b(?:value|values|relationship|expression|equation|function|variable|proportional|increase|decrease|equal|greater|less|conditions|represent)\b",
        s,
    )
    if (
        relation
        and target
        and (variables or len(set(symbols)) >= 2)
        and (has(r"\b[a-z]\b|\b(?:variable|function|equation|expression)\b", s))
    ):
        add(
            "Variable-related question",
            "The requested mathematical result depends on an explicit symbolic relation/function.",
            [relation[0], target[0], "variable/function framework"],
            [
                "x as multiplication",
                "object/axis labels only",
                "single table placeholder without symbolic relation",
            ],
        )
    write_in = has(
        r"\b(?:write|give|enter)\s+(?:your|the)\s+answer\b|\bwrite\s+(?:in words|in numbers|a number|one word)\b",
        body,
    )
    audit = q.get("option_audit") or {}
    verified_write_in = (
        audit.get("cover_allows_write_in")
        and audit.get("possible_label_lines") == 0
        and audit.get(
            "answer_region_native_objects", audit.get("meaningful_native_objects")
        )
        == 0
        and audit.get("text_complete")
        and audit.get("bounded_by_numbered_items")
        and (
            re.sub(r"[_\s]+$", "", s).endswith("?")
            or has(r"^(?:Estimate|Express|Calculate|Determine)\b", s)
        )
    )
    if (
        not options
        and (write_in or verified_write_in)
        and not has(
            r"\b(?:which (?:one|two)|following (?:options|statements|answers))\b", s
        )
    ):
        add(
            "No Question",
            "A complete numbered write-in task has no multiple-choice set; source instructions and native layout support a written response.",
            [
                write_in[0]
                if write_in
                else "cover explicitly permits written words/numbers",
                "no extracted option anchors or omitted visual answers",
                "bounded numbered item",
            ],
            ["option detection failure alone is insufficient"],
        )
    return tags


def annotate(dataset):
    for declared in dataset["shared_information_ranges"]:
        declared["affected_question_ids"] = []
    owners = defaultdict(set)
    for q in dataset["questions"]:
        for span in q["raw"]["page_spans"]:
            owners[span["page"]].add(q["question_id"])
    for q in dataset["questions"]:
        tags = semantic_tags(q)
        for r in dataset["shared_information_ranges"]:
            if (
                1
                <= r["start_question"]
                <= q["question_number"]
                <= r["end_question"]
                <= (dataset["extraction"].get("expected_questions") or 100)
            ):
                tags.append(
                    {
                        "type": "Shared Information Range",
                        "reason": f"Question falls in declared shared-information interval {r['start_question']}--{r['end_question']}.",
                        "range": {
                            k: r[k]
                            for k in (
                                "start_question",
                                "end_question",
                                "page",
                                "raw_text",
                                "bbox",
                            )
                        },
                        "confidence": "high",
                        "status": "intentional_skip",
                    }
                )
                r["affected_question_ids"].append(q["question_id"])
        spans = q["raw"]["page_spans"]
        if len(spans) == 1 and len(owners[spans[0]["page"]]) == 1:
            page = dataset["pages"][spans[0]["page"] - 1]
            # Actual content bounds, not the padded question/page preview crop.
            layout = q.get("layout_blocks") or []
            boxes = [b["bbox"] for b in layout if b.get("bbox")]
            if boxes:
                extent = (max(b[3] for b in boxes) - min(b[1] for b in boxes)) / (
                    page["height"] - 80
                )
                if extent >= 0.65:
                    tags.append(
                        {
                            "type": "too long",
                            "reason": "One complete question is the sole question on the page and spans at least 65% of its usable height.",
                            "page": page["page_number"],
                            "content_height_ratio": round(extent, 4),
                            "confidence": "high",
                            "status": "intentional_skip",
                        }
                    )
        unique = {}
        for tag in tags:
            if tag["type"] in unique:
                unique[tag["type"]].setdefault("additional_evidence", []).append(tag)
            else:
                unique[tag["type"]] = tag
        tags = sorted(unique.values(), key=lambda t: ORDER.index(t["type"]))
        q["bmat_filter"] = {
            "rule_version": "1",
            "skip_from_pipeline": bool(tags),
            "primary_type": tags[0]["type"] if tags else None,
            "types": tags,
            "status": "intentional_skip"
            if tags
            else "parser_review"
            if not q["options"]
            else "normal",
            "skip_reason": tags[0]["reason"] if tags else None,
        }
