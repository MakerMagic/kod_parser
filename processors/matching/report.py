"""Deterministic matching-only issue groups; upstream presentation stays separate."""

from collections import defaultdict
from pathlib import Path

MARKER = "<!-- tsa-matching-issues-report -->"


def write_report(data, output):
    groups = defaultdict(dict)
    for issue in data["issues"]:
        key = (
            issue.get("year"),
            issue.get("section"),
            issue.get("question_number"),
            issue.get("source_json"),
            issue.get("clean_json"),
        )
        groups[issue["code"]].setdefault(key, [])
        if issue not in groups[issue["code"]][key]:
            groups[issue["code"]][key].append(issue)
    years = data.get("matching", {}).get("years")
    if not years:
        years = sorted(
            {
                r["identity"]["year"]
                for r in data["records"]
                if r.get("identity", {}).get("year") is not None
            }
        )
    scope = (
        str(years[0])
        if len(years) == 1
        else f"{min(years)}–{max(years)}"
        if years and sorted(years) == list(range(min(years), max(years) + 1))
        else ", ".join(map(str, years))
        if years
        else "scope unavailable"
    )
    lines = [
        MARKER,
        f"# Matching {scope} issues",
        "",
        f"Records: {len(data['records'])}. Readiness: {data['readiness']['ready']}. Matching issues only; raw/clean warnings are preserved in merged snapshots and shown during inspection, not silently resolved.",
        "",
    ]
    if not groups:
        lines.append(
            "No matching-specific issues detected. This is not proof of explanation or upstream visual fidelity."
        )
    for category, rows in sorted(groups.items()):
        lines += [
            f"## {category.replace('_', ' ').title()} ({len(rows)} records)",
            "",
            "| Year | Section | Question | Question source | Answer source / pages | Reason / upstream cause | Review |",
            "|---|---|---|---|---|---|---|",
        ]
        for key, findings in sorted(
            rows.items(),
            key=lambda item: (
                item[0][0] or 0,
                item[0][1] or "",
                item[0][2] or 0,
                str(item[0][3:]),
            ),
        ):
            reason = (
                "; ".join(
                    i["reason"]
                    + (
                        "; upstream: " + str(i["upstream_cause"])
                        if i.get("upstream_cause")
                        else ""
                    )
                    for i in findings
                )
                .replace("|", "\\|")
                .replace("\n", " ")
            )
            first = findings[0]
            question_source = str(
                (first.get("question_source") or {}).get(
                    "filename", first.get("clean_json", "unavailable")
                )
            ).replace("|", "\\|")
            answer_source = str(
                (first.get("answer_source") or {}).get(
                    "filename", first.get("source_json", "unavailable")
                )
            ).replace("|", "\\|")
            lines.append(
                f"| {key[0]} | {key[1]} | {key[2]} | {question_source} | {answer_source}; {first.get('answer_pages', 'unavailable')} | {reason} | yes |"
            )
        lines.append("")
    path = Path(output)
    if path.suffix.lower() != ".md":
        raise ValueError("Matching report must be Markdown")
    if path.exists() and not path.read_text(encoding="utf-8").startswith(MARKER):
        raise ValueError("Refusing to replace unrelated Markdown")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
