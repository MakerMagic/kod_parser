"""Deterministic CLEANING inspection artifacts from canonical structured data."""

from collections import Counter

from processors.stage_artifacts import write_stage_pair


def generate(data, validation, directory):
    rows = data["questions"]
    issues = [
        {
            "id": q["id"],
            "source_pdf": data["sources"][q["source_document_id"]]["filename"],
            "question_number": q["question_number"],
            **issue,
        }
        for q in rows
        for issue in q["cleaning_issues"]
    ]
    reported = [
        {**{k: q[k] for k in ("id", "source_pdf", "question_number")}, **issue}
        for q in validation["issues"]
        for issue in q["issues"]
    ]
    if issues != reported:
        raise ValueError("CLEANING issue coverage differs from validation")
    backtest = [
        "# Mathematics CLEANING backtesting",
        "",
        "Generated from canonical mathematics CLEAN JSON.",
        "",
    ]
    backtest += [
        f"{key}: {value}"
        for key, value in data["summary"].items()
        if not isinstance(value, dict)
    ]
    backtest += ["", "## Context/task boundary decisions", ""]
    backtest += [
        f"- {key}: {value}"
        for key, value in sorted(
            Counter(q["content_structure"]["decision"] for q in rows).items()
        )
    ]
    backtest += [
        "",
        "Canonical records: `data/clean/mathematics/questions.json`.",
        "`main_body` contains context; `main_question` contains ordered task blocks or null.",
        "The full `content` stream preserves source order for traceability and semantic assessment.",
        "",
    ]
    report = [
        "# Mathematics CLEANING issues",
        "",
        "Generated from canonical mathematics CLEAN JSON.",
        "",
        f"Total issues: {len(issues)}",
        f"Affected questions: {len(validation['issues'])}",
        "",
    ]
    for issue in issues:
        report += [
            f"## {issue['source_pdf']} — Q{issue['question_number']} — {issue['id']}",
            f"Type: {issue['code']}",
            f"Affected field: {issue['field']}",
            f"Reason: {issue['reason']}",
            "",
        ]
    if not issues:
        report += ["No unresolved mathematics cleaning issues currently exist.", ""]
    return write_stage_pair(
        directory, "CLEANING", ("\n".join(backtest), "\n".join(report))
    )
