"""Generate categorization Markdown views from existing canonical JSON only."""

import argparse
from collections import Counter
from html import escape
from pathlib import Path

from categorization.core import read
from processors.stage_artifacts import validate_stage_pairs, write_stage_pair

from .core import OTHER_TOPICS, taxonomy

PROJECT = Path(__file__).resolve().parents[2]
CANONICAL = PROJECT / "data/categorized/mathematics/questions.json"
STAGE = "CATEGORIZATION"


def default_docs_dir(path):
    return (
        PROJECT / "docs/mathematics"
        if Path(path).resolve() == CANONICAL
        else Path(path).parent / "inspection"
    )


def md(value):
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    return escape(str(value), quote=False).replace("|", "&#124;").replace("\n", "<br>")


def cause(code):
    return {
        "outside_official_taxonomy": "taxonomy boundary; outside approved Other topics",
        "insufficient_cleaned_structure": "insufficient/ambiguous cleaned content",
        "uncertain_topic": "uncertain Other assignment / unclear topic",
        "missing_assessment": "missing content-bound semantic assessment",
    }.get(code, f"stage finding: {code}")


def render(path):
    data = read(path)
    if (
        data.get("stage") != "mathematics_categorized"
        or data.get("domain") != "mathematics"
    ):
        raise ValueError("Expected canonical mathematics categorization JSON")
    rows, summary = data["questions"], data["summary"]
    categorized = [q for q in rows if q["category"] is not None]
    unresolved = [q for q in rows if q["categorization_issues"]]
    if len({q["id"] for q in rows}) != len(rows):
        raise ValueError("Duplicate stable question IDs")
    if (
        len(rows) != summary["eligible"]
        or len(categorized) != summary["categorized"]
        or len(unresolved) != summary["unresolved"]
    ):
        raise ValueError("Structured categorization counts disagree")
    if any(bool(q["category"]) == bool(q["categorization_issues"]) for q in rows):
        raise ValueError("Every question must be categorized or have explicit issues")
    categories = Counter(q["category"]["id"] for q in categorized)
    children = Counter(q["subcategory"]["id"] for q in categorized if q["subcategory"])
    topics = Counter(
        q["assessment"]["topic"] for q in categorized if q["category"]["id"] == "Other"
    )
    for actual, field in (
        (categories, "category_distribution"),
        (children, "subcategory_distribution"),
        (topics, "other_topic_distribution"),
    ):
        if dict(+Counter(summary[field])) != dict(actual):
            raise ValueError(f"Structured {field} disagrees with records")
    _, parents, official_children = taxonomy()
    findings = [
        (index, q, issue)
        for index, q in enumerate(rows)
        for issue in q["categorization_issues"]
    ]
    intro = [
        "Generated from canonical structured data; do not edit manually.",
        f"Canonical input: `{Path(path).resolve().as_posix()}`.",
        "",
    ]
    back = [
        "# Mathematics CATEGORIZATION backtesting",
        "",
        *intro,
        (
            f"Eligible questions: {len(rows)}; categorized: {len(categorized)}; "
            f"unresolved questions: {len(unresolved)}; total issues: {len(findings)}."
        ),
        "",
        "## Category distribution",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for key, label in [(k, v["name"]) for k, v in parents.items()] + [
        ("Other", "Other")
    ]:
        back.append(f"| {key} — {label} | {categories[key]} |")
    back += [
        "",
        "## Subcategory distribution",
        "",
        "| Subcategory | Count |",
        "|---|---:|",
    ]
    for key in official_children:
        back.append(f"| {key} | {children[key]} |")
    back += [
        "",
        "Other has no subcategories. Topic metadata is diagnostic, not taxonomy.",
        "",
        "## Other distribution",
        "",
        "| Topic | Count |",
        "|---|---:|",
    ]
    back += [f"| {t} | {topics[t]} |" for t in OTHER_TOPICS]
    back += [
        "",
        "## Inspect selected records",
        "",
        "Read `questions[]` in the canonical JSON by stable `id`, or by",
        "`source_pdf` and `question_number`. Each record's `clean_reference`",
        "contains the CLEAN JSON path and JSON pointer for the actual content.",
        "Inspect `assessment.dominant_operation` and `why_not_alternative`",
        "for official decisions; Other uses `topic`, `certainty` and `evidence`.",
        "Open referenced CLEAN assets directly. Do not regenerate upstream stages.",
        "Regenerate this pair only: `python -m categorization.mathematics.artifacts`.",
        "Normal categorization runs also regenerate both files automatically.",
        "",
        "## Unresolved record index",
        "",
        "Full current reasons/candidates/causes: [CATEGORIZATION_ISSUES.md](CATEGORIZATION_ISSUES.md).",
        "",
        "| Stable ID | Source | Question | State |",
        "|---|---|---:|---|",
    ]
    back += [
        f"| {md(q['id'])} | {md(q['source_pdf'])} | {q['question_number']} | "
        f"{md(q['assessment']['status'])} |"
        for q in unresolved
    ]
    if not unresolved:
        back += ["", "No unresolved categorization cases currently exist."]
    issues = [
        "# Mathematics CATEGORIZATION issues",
        "",
        *intro,
        f"Total issues: {len(findings)}",
        f"Affected questions: {len(unresolved)}",
        "",
    ]
    if not findings:
        issues += ["No unresolved categorization issues currently exist.", ""]
    else:
        issues += ["## Counts by exact issue type", ""]
        issues += [
            f"- {md(code)}: {count}"
            for code, count in sorted(
                Counter(i["code"] for _, _, i in findings).items()
            )
        ]
        for index, q, issue in findings:
            if (
                not q["id"]
                or not q["source_pdf"]
                or not issue.get("code")
                or not issue.get("reason", "").strip()
            ):
                raise ValueError(
                    "Every finding needs identity, source, type and exact reason"
                )
            assessment = q["assessment"]
            candidates = assessment.get(
                "candidate_topic", "Not specified; no category guessed"
            )
            issues += [
                "",
                f"## {md(q['source_pdf'])} — Q{q['question_number']} — {md(q['id'])}",
                "",
                f"- Stable question ID: `{md(q['id'])}`",
                f"- State: {md(assessment['status'])}; category/subcategory: unassigned.",
                f"- Candidate topic: {md(candidates)}.",
                (
                    f"- Candidate category/subcategory: {md(assessment.get('candidate_category_id', 'unassigned'))} / "
                    f"{md(assessment.get('candidate_subcategory_id', 'unassigned'))}."
                ),
                f"- Exact issue type: `{md(issue['code'])}`.",
                f"- Cause: {md(cause(issue['code']))}.",
                f"- Exact reason: {md(issue['reason'])}",
                (
                    f"- Canonical record: `/questions/{index}`; CLEAN content: "
                    f"`{md(q['clean_reference']['json_pointer'])}` in "
                    f"`{md(q['clean_reference']['path'])}`."
                ),
            ]
    return "\n".join(back).rstrip() + "\n", "\n".join(issues).rstrip() + "\n"


def generate(path=CANONICAL, docs_dir=None):
    directory = Path(docs_dir) if docs_dir is not None else default_docs_dir(path)
    paths = write_stage_pair(directory, STAGE, render(path))
    validate_stage_pairs([(directory, STAGE, render(path))])
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions-json", type=Path, default=CANONICAL)
    parser.add_argument("--docs-dir", type=Path)
    args = parser.parse_args(argv)
    for path in generate(args.questions_json, args.docs_dir):
        print(path)


if __name__ == "__main__":
    main()
