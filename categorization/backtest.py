"""Categorization QA layered on the existing matching inspection renderer."""

import json
import re
from collections import defaultdict
from html import escape

from processors.matching.backtest import inspect_question as inspect_match
from processors.matching.backtest import render_html as matching_html

from .core import MARKER, digest, load_handoff, read, safe_output, validate_output


def load_categorized(path):
    data = read(path)
    validate_output(data)
    ref = data["handoff_reference"]
    from .core import verify_refs

    verify_refs(
        [
            ref,
            *data["inputs"],
            *([data["model_reference"]] if data.get("model_reference") else []),
            *([data["review_reference"]] if data.get("review_reference") else []),
        ]
    )
    if data.get("review_reference"):
        annotations = read(data["review_reference"]["path"])
        verify_refs(
            [
                annotations[k]
                for k in (
                    "baseline_reference",
                    "rulebook_reference",
                    "decision_source_reference",
                )
            ]
        )
    load_handoff(ref["path"])
    return data


def inspect(data, *, year, question, section="section_1", cache=None):
    selected = [
        r
        for r in data["records"]
        if r["identity"]["year"] == year
        and r["identity"]["question_number"] == question
        and r["identity"]["section"] == section
    ]
    if len(selected) != 1:
        raise ValueError(
            "No unique categorized question; inspect stable identity/source selection"
        )
    row = selected[0]
    ref = row["matched_reference"]
    result = inspect_match(
        ref["path"], year=year, question_number=question, section=section, cache=cache
    )
    if digest(result["record"]) != ref["record_sha256"]:
        raise ValueError("Matched record changed after categorization")
    return {
        "categorization_record": row,
        "logic": data["logic"],
        "matching_inspection": result,
    }


def render_html(result):
    row = result["categorization_record"]
    c = row["categorization"]
    title = (c["category"] or "Unclassified") + (
        " → " + " + ".join(c["subcategories"])
        if c["subcategories"]
        else " → review required"
    )

    def dump(value):
        return (
            "<pre>" + escape(json.dumps(value, ensure_ascii=False, indent=2)) + "</pre>"
        )

    card = (
        "<section id='categorization'><h2>Categorization</h2><h3>"
        + escape(title)
        + "</h3>"
        + "<p>Status: <strong>"
        + escape(c["status"])
        + "</strong>; confidence: "
        + escape(c["confidence"]["level"])
        + " (not a calibrated probability; not human approval).</p>"
        + "<p>"
        + escape(
            c["rationale"] or "No justified complete assignment; see review reasons."
        )
        + "</p>"
        + (
            "<p><strong>Previous categorization:</strong> "
            + escape(str(row["previous_categorization"]))
            + "; previous Main Question: "
            + escape(str(row.get("previous_main_question")))
            + "</p>"
            if row.get("previous_categorization")
            else ""
        )
        + "<details><summary>Evidence / detected patterns</summary>"
        + dump({"patterns": c["patterns"], "evidence": c["evidence"]})
        + "</details>"
        + (
            "<details open><summary>Rulebook review / all three subcategories</summary>"
            + dump(
                {
                    k: row["rulebook_review"][k]
                    for k in (
                        "evaluated_subcategories",
                        "material_subcategories",
                        "evidence",
                        "remaining_review_reason",
                        "previous_categorization",
                    )
                }
            )
            + "</details>"
            if row.get("rulebook_review")
            else ""
        )
        + (
            "<div class='issue'><h3>Categorization issues</h3>"
            + "<ul>"
            + "".join(
                "<li>" + escape(i["code"]) + ": " + escape(i["reason"]) + "</li>"
                for i in c["issues"]
            )
            + "</ul>"
            + "</div>"
            if c["issues"]
            else ""
        )
        + "<details><summary>Candidate attribution, model/version and provenance</summary>"
        + dump(
            {
                "candidates": c["candidates"],
                "matched_reference": row["matched_reference"],
                "logic": result["logic"],
            }
        )
        + "</details></section>"
    )
    html = matching_html(result["matching_inspection"])
    html = html.replace(
        "<title>Matching inspection</title>", "<title>Categorization inspection</title>"
    )
    html = html.replace(
        "<h1>Matched question / explanation inspection</h1>",
        "<h1>Categorization inspection</h1>" + card,
    )
    # Keep debug/source components intact but collapse duplicate technical
    # sections. Main Body/Question/Answers/Final Explanation stay immediately visible.
    for section in (
        "main-explanation",
        "incorrect-explanations",
        "other-lists",
        "explanation-order",
        "matching-metadata",
        "availability",
        "answer-source",
    ):
        html = re.sub(
            r"(<section id='" + section + r"'>)(.*?)(</section>)",
            r"\1<details><summary>Matching/source detail</summary>\2</details>\3",
            html,
            flags=re.DOTALL,
        )
    return html.replace("<!doctype html>", f"<!doctype html><!-- {MARKER} -->", 1)


def report(data, path):
    path = safe_output(path, data["inputs"])
    if path.suffix.lower() != ".md":
        raise ValueError("Issues report must be Markdown, never an input JSON")
    if path.exists() and not path.read_text(encoding="utf-8").startswith(
        f"<!-- {MARKER} -->"
    ):
        raise ValueError("Refusing to overwrite an unrelated report")
    groups = defaultdict(dict)
    for r in data["records"]:
        if r["categorization"]["issues"] and r["categorization"]["status"] in {
            "classified",
            "multi_label",
        }:
            raise ValueError("Accepted categorization still has unresolved issues")
        for issue in r["categorization"]["issues"]:
            groups[issue["code"]].setdefault(r["record_key"], (r, []))[1].append(issue)
    unresolved_keys = {key for records in groups.values() for key in records}
    lines = [
        f"<!-- {MARKER} -->",
        "# Categorization issues",
        "",
        "Counts are unique question records within each group. Accepted multi-label results are not errors. Upstream warnings remain traceable, not copied wholesale or declared fixed.",
        "",
        f"Active unresolved question records: **{len(unresolved_keys)}**. A question may have several distinct issue types; group counts must not be added together.",
        "",
        "## Run summary",
        "",
        "```json",
        json.dumps(data["summary"], indent=2),
        "```",
        "",
    ]
    if not groups:
        lines += [
            "No categorization-specific issues detected; this is not manual validation.",
            "",
        ]
    if data.get("review_summary"):
        lines += [
            "## Complete rulebook review pass",
            "",
            "```json",
            json.dumps(data["review_summary"], indent=2),
            "```",
            "",
            "Every in-scope record, including unresolved decisions, is linked from [categorization backtesting](CATEGORIZATION_BACKTEST.MD). Classifier-only uncertainty is replaced by the recorded diagnosis, not hidden.",
            "",
        ]
    if (data.get("comparison") or {}).get("changes"):
        lines += [
            "Resolved questions are not issue rows. Their complete before/after history remains in [categorization backtesting](CATEGORIZATION_BACKTEST.MD).",
            "",
        ]
    for code, records in sorted(groups.items()):
        lines += [
            f"## {code.replace('_', ' ').title()} ({len(records)} questions)",
            "",
            "| Year | Question | Category / candidates | Reason | Matched record | Review |",
            "|---|---|---|---|---|---|",
        ]
        for r, issues in sorted(
            records.values(),
            key=lambda pair: (
                pair[0]["identity"]["year"],
                pair[0]["identity"]["question_number"],
                pair[0]["record_key"],
            ),
        ):
            c = r["categorization"]
            reason = "; ".join(dict.fromkeys(i["reason"] for i in issues))
            ref = r["matched_reference"]
            cells = [
                r["identity"]["year"],
                r["identity"]["question_number"],
                (c["category"] or "unclassified")
                + "; "
                + ", ".join(
                    x.get("subcategory", x["pattern"]) for x in c["candidates"][:2]
                ),
                reason,
                ref["path"] + ref["json_pointer"],
                "required",
            ]
            lines.append(
                "| "
                + " | ".join(
                    str(x).replace("|", "\\|").replace("\n", " ") for x in cells
                )
                + " |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_inspection(
    data, *, year, question, output, format="html", overwrite=False, cache=None
):
    path = safe_output(output, data["inputs"])
    if path.suffix.lower() != (".html" if format == "html" else ".json"):
        raise ValueError("Inspection filename must match the selected format")
    result = inspect(data, year=year, question=question, cache=cache)
    content = (
        render_html(result)
        if format == "html"
        else json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    if path.exists():
        previous = path.read_text(encoding="utf-8")
        row = result["categorization_record"]
        owned = f"<!-- {MARKER} -->" in previous or (
            format == "html"
            and "<title>Categorization inspection</title>" in previous
            and row["matched_reference"]["record_sha256"] in previous
        )
        if not overwrite or not owned:
            raise FileExistsError(
                "Inspection exists or is not an owned categorization export"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w" if overwrite else "x", encoding="utf-8") as handle:
        handle.write(content)
    return result


def update_guide(data, path):
    """Regenerate the bounded current-run audit, retaining maintained CLI docs."""
    path = safe_output(path, data["inputs"])
    existing = path.read_text(encoding="utf-8")
    if path.suffix.lower() != ".md" or not existing.startswith(
        "# Categorization backtesting"
    ):
        raise ValueError("Not a categorization backtest guide")
    marker = "<!-- categorization-current-audit -->"
    head = existing.split(marker)[0].rstrip()
    lines = [
        head,
        "",
        marker,
        "## Current refinement audit",
        "",
        "Generated from the categorized output; assignments are not human approval.",
        "",
        "```json",
        json.dumps(data["summary"], indent=2),
        "```",
        "",
        "Before/after counts: "
        + json.dumps(data.get("comparison", {}).get("counts", {})),
        "",
        "| Year | Question | Previous → current | Inspection |",
        "|---|---|---|---|",
    ]
    for change in data.get("comparison", {}).get("changes", []):
        y, n = change["identity"]["year"], change["identity"]["question_number"]

        def label(c):
            return (
                (c["category"] or "Unclassified")
                + " / "
                + " + ".join(c["subcategories"])
                + " ["
                + c["status"]
                + "]"
            )

        target = path.parent.parent / "inspections_categorization" / f"{y}_q{n:03}.html"
        link = (
            f"[HTML](../inspections_categorization/{target.name})"
            if target.exists()
            else "Not yet rendered"
        )
        lines.append(
            f"| {y} | {n} | {label(change['previous'])} → {label(change['current'])} | {link} |"
        )
    lines += [
        "",
        (
            "Unknown task profiles and concrete upstream conflicts remain in the issues report. "
            "A previous label withdrawn for review is not a completed reclassification."
        ),
        "",
    ]
    if data.get("review_summary"):
        lines += [
            "## Rulebook review — complete audit",
            "",
            (
                "Assistant assessments rebound to current task evidence, not human approval. Refined semantic families are evaluated across all statuses; changed text/asset ownership cannot silently inherit an old assessment."
                if data.get("refinement_summary")
                else "Assistant assessments under the supplied rulebook, not human approval. No classifier retraining or changes outside the frozen review set."
            ),
            "",
            "```json",
            json.dumps(data["review_summary"], indent=2),
            "```",
            "",
            "| Year | Question | Previous → current | Evidence / remaining reason | Inspection |",
            "|---|---|---|---|---|",
        ]
        for row in data["records"]:
            review = row.get("rulebook_review")
            if not review:
                continue
            y, n = row["identity"]["year"], row["identity"]["question_number"]
            c = row["categorization"]
            final = " + ".join(c["subcategories"]) or "review"
            evidence = review["evidence"].replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {y} | {n} | {review['previous_categorization']['status']} → {final} [{c['status']}] | {evidence} | [HTML](../inspections_categorization/{y}_q{n:03}.html) |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
