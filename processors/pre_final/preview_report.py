"""Readable structured report below the simulation, never a second data model."""

import json
from functools import partial
from html import escape

from .preview_content import text


def report_section(identifier, title, value, *, prefix=""):
    return (
        f"<section id='{prefix}{identifier}'><h3>{escape(title)}</h3>{value}</section>"
    )


def report(question, categories, content, *, prefix=""):
    section = partial(report_section, prefix=prefix)

    category = categories[question["category"]]
    parts = [
        "<section class='detailed-report' aria-label='Detailed question report'><h2>Detailed report</h2>"
    ]
    parts += [
        section("source", "Source", text(question["source"])),
        section(
            "explanation-by-ai",
            "Explanation by AI",
            text(str(question["explanation_by_ai"]).lower()),
        ),
        section(
            "category", "Category", text(category["family"] + " → " + category["name"])
        ),
        section("main-body", "Main Body", content.body()),
        section("main-question", "Main Question", text(question["main_question"])),
        section(
            "main-answers",
            "Main Answers",
            "".join(
                "<div class='report-answer' data-option='"
                + escape(a["label"], quote=True)
                + "'>"
                + text(a["label"] + ": " + a["text"])
                + (
                    ""
                    if a.get("render_text_only")
                    else "".join(content.figure(i) for i in a["asset_ids"])
                )
                + "</div>"
                for a in question["main_answers"]
            ),
        ),
        section("correct-answer", "Correct Answer", text(question["correct_answer"])),
        section("explanation", "Explanation", content.explanation()),
    ]
    previews = [a for a in question["assets"] if a["role"] == "source_preview"]
    if previews:
        parts.append(
            "<details class='original-context'><summary>Original question screenshot</summary>"
            + "".join(content.figure(a["id"]) for a in previews)
            + "</details>"
        )
    provenance = question["provenance"]
    explanation_provenance = (question["explanation"] or {}).get("provenance", {})
    metadata = {
        "id": question["id"],
        "year": question["year"],
        "question_number": question["question_number"],
        "section": question.get("section"),
        "question_source": provenance.get("question_source"),
        "explanation_source": {
            k: explanation_provenance[k]
            for k in ("source_type", "source_document", "source_reference")
            if k in explanation_provenance
        },
    }
    parts.append(
        "<details><summary>Identity / source metadata</summary><pre>"
        + escape(json.dumps(metadata, ensure_ascii=False, indent=2))
        + "</pre></details></section>"
    )
    return "".join(parts)
