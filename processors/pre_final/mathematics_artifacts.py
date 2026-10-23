"""PRE_FINAL inspection pair generated only from saved assembly/validation JSON."""

from html import escape
from pathlib import Path

from categorization.core import read
from processors.stage_artifacts import validate_stage_pairs, write_stage_pair


def render(output):
    output = Path(output)
    data, validation = read(output / "questions.json"), read(output / "validation.json")
    if (
        data.get("stage") != "mathematics_pre_final"
        or validation.get("stage") != "mathematics_pre_final_validation"
    ):
        raise ValueError(
            "PRE_FINAL artifacts require canonical mathematics assembly outputs"
        )
    summary = data["summary"]
    issues = validation["issues"]
    if (
        summary != validation["summary"]
        or summary["included"] != len(data["questions"])
        or summary["blocked_questions"] != len(issues)
        or summary["blocking_issues"] != sum(len(q["issues"]) for q in issues)
        or summary["upstream_exclusions"] != len(validation["exclusions"])
    ):
        raise ValueError("PRE_FINAL structured counts disagree")
    intro = [
        "Generated from canonical pre-final JSON; do not edit manually.",
        f"Data: `{(output / 'questions.json').resolve().as_posix()}`.",
        f"Validation: `{(output / 'validation.json').resolve().as_posix()}`.",
        "",
    ]
    back = [
        "# Mathematics PRE_FINAL backtesting",
        "",
        *intro,
        f"Categorized candidates: {summary['categorized_candidates']}",
        f"Matched candidates: {summary['matched_candidates']}",
        f"Included: {summary['included']}",
        f"Blocked questions: {summary['blocked_questions']}",
        f"Blocking issues: {summary['blocking_issues']}",
        f"Ready for rendering: {str(summary['ready_for_rendering']).lower()}",
        "",
        "## Included by source",
        "",
    ]
    back += [f"- {source}: {count}" for source, count in summary["by_source"].items()]
    back += [
        "",
        "## Known upstream eligibility exclusions",
        "",
        "These records are not admitted; no upstream repair or answer inference was performed.",
    ]
    back += [
        f"- {code}: {count}" for code, count in summary["excluded_by_reason"].items()
    ]
    back += [
        "",
        "## Targeted inspection",
        "",
        "Select `questions[]` by stable `id`, `source_pdf` and `question_number`.",
        "Main Body retains the entire original ordered math question stream.",
        "Main Question remains empty because upstream does not split passage/prompt.",
        "Main Answers preserve ordered blocks; correct_answer is an existing matched label.",
        "Use provenance pointers and existing assets directly; do not generate question reports to read data.",
        "",
        "## Rendering gate",
        "",
        "Do not start Question Rendering while ready_for_rendering is false.",
        "See [PRE_FINAL_ISSUES.md](PRE_FINAL_ISSUES.md) for every blocking finding.",
    ]
    out = [
        "# Mathematics PRE_FINAL issues",
        "",
        *intro,
        f"Total issues: {summary['blocking_issues']}",
        f"Affected questions: {len(issues)}",
        "",
    ]
    if not issues:
        out += ["No unresolved pre-final blocking issues currently exist."]
    for q in issues:
        out += [
            f"## {q['source_pdf']} — Q{q['question_number']} — {q['id']}",
            "",
            f"Stable ID: `{q['id']}`; state: blocked; not included.",
            "",
        ]
        for issue in q["issues"]:
            out += [
                f"- Type: `{issue['code']}`; field: `{issue['field']}`.",
                "  Exact reason: "
                + escape(issue["reason"], quote=False).replace("\n", "<br>"),
            ]
        out.append("")
    return "\n".join(back).rstrip() + "\n", "\n".join(out).rstrip() + "\n"


def generate(output, docs):
    paths = write_stage_pair(docs, "PRE_FINAL", render(output))
    validate_stage_pairs([(docs, "PRE_FINAL", render(output))])
    return paths
