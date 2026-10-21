"""Deterministic matching-only issue groups; upstream presentation stays separate."""

import os
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
            "| Year | Section | Question | Question source | Answer source / pages | Source answer (not match approval) | Reason / upstream cause | Review |",
            "|---|---|---|---|---|---|---|---|",
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
            source_answers = {
                r["answer"]["correct_answer"]
                for r in data["records"]
                if r.get("identity")
                == {"year": key[0], "section": key[1], "question_number": key[2]}
                and (r.get("answer") or {}).get("correct_answer")
            }
            source_answer = (
                next(iter(source_answers))
                if len(source_answers) == 1
                else "unavailable / ambiguous"
            )
            lines.append(
                f"| {key[0]} | {key[1]} | {key[2]} | {question_source} | {answer_source}; {first.get('answer_pages', 'unavailable')} | {source_answer} | {reason} | yes |"
            )
        lines.append("")
    superseded = [r for r in data["records"] if r.get("superseded_answer_candidates")]
    if data.get("explanation_imports"):
        from .export_without_explanations import has_explanation

        available = [r for r in data["records"] if has_explanation(r)]
        missing = [r for r in data["records"] if not has_explanation(r)]
        links = []
        for year in (2017, 2018, 2019):
            target = (
                Path(__file__).resolve().parents[2]
                / f"docs/critical_thinking_problem_solving/tsa/2017-2019_questions_images_with_explanation_ai_generated/{year}/ISSUES.md"
            )
            relative = Path(
                os.path.relpath(target, Path(output).resolve().parent)
            ).as_posix()
            links.append(f"[{year}](<{relative}>)")
        lines += [
            "## Explanation Availability",
            "",
            f"Available: {len(available)}. Without an accepted explanation: {len(missing)}. Explanation import/generation does not change matching approval.",
            "",
            "Year-specific import/review reports: " + ", ".join(links) + ".",
            "",
        ]
        for year in sorted({r["identity"]["year"] for r in missing}):
            group = [r for r in missing if r["identity"]["year"] == year]
            lines += [f"### {year} Without Explanation ({len(group)} questions)", ""]
            for record in group:
                metadata = record.get("ai_explanation") or {}
                reason = (
                    metadata.get("quality_review_reasons")
                    or metadata.get("validation_errors")
                    or ["No accepted explanation supplied"]
                )
                lines.append(
                    f"- Q{record['identity']['question_number']}: {metadata.get('generation_status', 'unavailable')}; {'; '.join(reason)}"
                )
            lines.append("")
    if superseded:
        lines += [
            f"## Manually Superseded Source Findings ({len(superseded)} records)",
            "",
            "Audit history, not active explanation failures. Explicit pinned manual supplements are selected; the original parser is not claimed fixed. Original records/warnings/previews remain in superseded_answer_candidates and HTML inspection.",
            "",
            "| Year | Question | Original source / pages | Preserved warnings | Manual source |",
            "|---|---|---|---|---|",
        ]
        for record in sorted(
            superseded,
            key=lambda r: (r["identity"]["year"], r["identity"]["question_number"]),
        ):
            original = record["superseded_answer_candidates"][0]["record"]
            warnings = "; ".join(original["warnings"]).replace("|", "\\|")
            lines.append(
                f"| {record['identity']['year']} | {record['identity']['question_number']} | {original['source_document']['filename']}; {original['page_reference']} | {warnings or 'none'} | {record['answer']['source_document']['filename']} |"
            )
        lines.append("")
    path = Path(output)
    if path.suffix.lower() != ".md":
        raise ValueError("Matching report must be Markdown")
    if path.exists() and not path.read_text(encoding="utf-8").startswith(MARKER):
        raise ValueError("Refusing to replace unrelated Markdown")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
