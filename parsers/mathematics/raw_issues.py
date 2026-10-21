"""Generate the Mathematics RAW-stage issue index from canonical RAW JSON."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def collect(raw_paths):
    """Return validated, question-linked raw issue records from RAW JSON files."""
    findings = []
    for path in sorted(map(Path, raw_paths), key=lambda item: item.name):
        data = json.loads(path.read_text(encoding="utf8"))
        if (
            data.get("domain") != "mathematics"
            or data.get("stage") != "mathematics_raw"
        ):
            raise ValueError(f"Not mathematics RAW JSON: {path}")
        source_pdf = data.get("source_document", {}).get("filename")
        if not source_pdf:
            raise ValueError(f"Missing source PDF filename: {path}")
        questions = {q["question_number"]: q for q in data.get("questions", [])}

        # RAW question issues are the report's intended source. Keep a guard for
        # future file-/key-level findings: they must still identify a question.
        issue_groups = [(q, q.get("issues", [])) for q in questions.values()]
        issue_groups.extend((None, data.get("issues", [])) for _ in [0])
        issue_groups.extend(
            (None, data.get("answer_key", {}).get("issues", [])) for _ in [0]
        )
        for owner, issues in issue_groups:
            for issue in issues or []:
                number = issue.get("question_number") or (owner or {}).get(
                    "question_number"
                )
                question = questions.get(number)
                if question is None:
                    raise ValueError(
                        f"RAW issue in {source_pdf} is not linked to a question: {issue}"
                    )
                reason = issue.get("reason")
                if not reason or not str(reason).strip():
                    raise ValueError(
                        f"RAW issue lacks a concrete reason in {source_pdf} Q{number}: {issue}"
                    )
                findings.append(
                    {
                        "question_id": question.get("id"),
                        "question_number": number,
                        "source_pdf": source_pdf,
                        "page": issue.get("page"),
                        "category": issue.get("code") or issue.get("category"),
                        "reason": str(reason).strip(),
                        "field": issue.get("field") or issue.get("component"),
                        "option_label": issue.get("option_label"),
                        "method": issue.get("method"),
                        "asset_id": issue.get("asset_id"),
                    }
                )
    if any(not item["question_id"] or not item["category"] for item in findings):
        raise ValueError(
            "Every RAW finding must have a stable question ID and category"
        )
    return sorted(
        findings,
        key=lambda item: (
            item["source_pdf"],
            item["question_number"],
            item["category"],
            item["page"] or 0,
            item["field"] or "",
            item["asset_id"] or "",
        ),
    )


def render(findings):
    counts = Counter(item["category"] for item in findings)
    questions_by_category = defaultdict(set)
    for item in findings:
        questions_by_category[item["category"]].add(item["question_id"])
    affected = len({item["question_id"] for item in findings})
    rows = [
        "# Mathematics RAW Issues",
        "",
        "Generated from `data/raw/mathematics/*.raw.json`; this file contains RAW-stage findings only.",
        "",
        f"Total raw issues: **{len(findings)}** across **{affected}** questions.",
        "",
        "| Raw issue category | Findings | Questions |",
        "|---|---:|---:|",
    ]
    for category in sorted(counts):
        rows.append(
            f"| `{category}` | {counts[category]} | {len(questions_by_category[category])} |"
        )
    rows.extend(["", "## Per-question findings", ""])
    for item in findings:
        page = f" — page {item['page']}" if item["page"] is not None else ""
        field = f"; affected field: `{item['field']}`" if item["field"] else ""
        if item.get("option_label"):
            field += f" `{item['option_label']}`"
        details = []
        if item["method"]:
            details.append(f"method `{item['method']}`")
        if item["asset_id"]:
            details.append(f"asset `{item['asset_id']}`")
        suffix = f"; diagnostic: {', '.join(details)}" if details else ""
        rows.extend(
            [
                f"- **{item['source_pdf']} — Q{item['question_number']}** (`{item['question_id']}`){page} — `{item['category']}`",
                f"  Reason: {item['reason']}{field}{suffix}.",
            ]
        )
    if not findings:
        rows.append("No raw issues recorded.")
    return "\n".join(rows) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", nargs="?", type=Path, default=Path("data/raw/mathematics")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("docs/mathematics/RAW_ISSUES.md")
    )
    args = parser.parse_args(argv)
    paths = (
        sorted(args.input.glob("*.raw.json")) if args.input.is_dir() else [args.input]
    )
    if not paths:
        parser.error(f"No RAW JSON files found in {args.input}")
    output = render(collect(paths))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf8", newline="\n")
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
