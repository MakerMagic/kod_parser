"""Opt-in source-linked mathematics rendering with native offline MathML."""

import base64
import json
import random
from hashlib import sha256
from html import escape
from pathlib import Path

from parsers.mathematics.latex import mathml
from processors.pre_final.preview_layout import (
    answer_option,
    document,
    simulation_frame,
)
from processors.pre_final.preview_report import report_section


def select(
    data,
    *,
    source=None,
    question=None,
    identifier=None,
    issues=False,
    issue_code=None,
    sample=None,
    seed=0,
):
    if not any(
        (
            source,
            question is not None,
            identifier,
            issues,
            issue_code,
            sample is not None,
        )
    ):
        raise ValueError(
            "An explicit source/question/ID/issue/sample selection is required"
        )
    rows = []
    for q in data["questions"]:
        s = data["sources"][q["source_document_id"]]
        if source and source not in {s["id"], s["filename"], Path(s["filename"]).stem}:
            continue
        if question is not None and q["question_number"] != question:
            continue
        if identifier and q["id"] != identifier:
            continue
        if issues and not q["issues"]:
            continue
        if issue_code and not any(i["code"] == issue_code for i in q["issues"]):
            continue
        rows.append(q)
    rows.sort(key=lambda q: q["id"])
    if sample is not None:
        if sample <= 0:
            raise ValueError("Positive sample size required")
        rows = sorted(
            random.Random(seed).sample(rows, min(sample, len(rows))),
            key=lambda q: q["id"],
        )
    if not rows:
        raise ValueError("No mathematics records match the selection")
    return rows


def render_question(q, source, *, position=1, count=1):
    registry = {a["id"]: a for a in q["assets"]}

    def figure(identifier):
        a = registry[identifier]
        path = Path(a["path"])
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != a["sha256"]:
            raise ValueError("Source asset missing/changed: " + identifier)
        return (
            "<img alt='"
            + escape(
                a["role"] + (" " + a["option_label"] if a.get("option_label") else ""),
                quote=True,
            )
            + "' src='data:image/png;base64,"
            + base64.b64encode(raw).decode()
            + "'>"
        )

    def blocks(items):
        rendered = []
        for b in items:
            if b["type"] == "text":
                value = "<span class='prose'>" + escape(b["text"]) + "</span>"
            elif b["type"] == "math":
                value = (
                    "<span class='formula' data-latex='"
                    + escape(b["latex"], quote=True)
                    + "'>"
                    + mathml(b["latex"], display=b["display"])
                    + "</span>"
                )
            elif b["type"] == "list":
                tag = "ol" if b["ordered"] else "ul"
                value = (
                    "<"
                    + tag
                    + ">"
                    + "".join(
                        "<li>" + blocks(i["content"]) + "</li>" for i in b["items"]
                    )
                    + "</"
                    + tag
                    + ">"
                )
            elif b["type"] == "unresolved_math":
                value = (
                    "<div class='unresolved-formula'>Formula extraction unresolved.<details><summary>Source evidence (not transcribed)</summary>"
                    + figure(b["diagnostic_asset_id"])
                    + "</details></div>"
                )
            elif b["type"] == "visual":
                tag = "figure" if b.get("display", False) else "span"
                value = (
                    "<"
                    + tag
                    + " class='visual'>"
                    + figure(b["asset_id"])
                    + "</"
                    + tag
                    + ">"
                )
            else:
                raise ValueError("Unsupported RAW content block: " + b["type"])
            if b.get("break_before"):
                value = "<div class='source-block'>" + value + "</div>"
            rendered.append(value)
        return "".join(rendered)

    choices = "".join(
        answer_option(o["label"], blocks(o["content"]), position) for o in q["options"]
    )
    previews = "".join(
        figure(a["id"]) for a in q["assets"] if a["role"] == "source_preview"
    )
    issues = (
        "<ul>"
        + "".join(
            "<li>" + escape(i["code"] + ": " + i["reason"]) + "</li>"
            for i in q["issues"]
        )
        + "</ul>"
        if q["issues"]
        else "<p>No recorded RAW issues.</p>"
    )
    prefix = f"math-{position}-"

    def section(key, title, value):
        return report_section(key, title, value, prefix=prefix)

    return (
        "<article class='question-preview' data-question-id='"
        + escape(q["id"], quote=True)
        + "'>"
        + simulation_frame(
            blocks(q["content"]),
            "",
            choices,
            source=source["filename"],
            heading="Mathematics · "
            + source.get("source", "matdev")
            + " "
            + source["version"],
            question_number=q["question_number"],
            report_prefix=prefix,
            position=position,
            count=count,
            body_label="QUESTION",
        )
        + "<section class='detailed-report' aria-label='Detailed question report'><h2>Detailed report</h2>"
        + section(
            "source", "Source", "<p class='text'>" + escape(source["filename"]) + "</p>"
        )
        + section("main-question", "Main Question", blocks(q["content"]))
        + section(
            "main-answers",
            "Main Answers",
            "".join(
                "<div class='report-answer' data-option='"
                + escape(o["label"], quote=True)
                + "'><strong>"
                + escape(o["label"])
                + ": </strong>"
                + blocks(o["content"])
                + "</div>"
                for o in q["options"]
            ),
        )
        + (
            section(
                "correct-answer",
                "Correct Answer",
                escape(q["correct_answer"] or "Unresolved"),
            )
            if "correct_answer" in q
            else ""
        )
        + section(
            "explanation",
            "Explanation",
            "<p class='text'>Not supplied by the source.</p>",
        )
        + section(
            "issues",
            "RAW issues / matching status" if q.get("matching") else "RAW issues",
            issues,
        )
        + "<details class='original-context'><summary>Original question screenshot</summary>"
        + previews
        + "</details>"
        + "<details><summary>Identity / source metadata</summary><pre>"
        + escape(
            json.dumps(
                {
                    "id": q["id"],
                    "question_number": q["question_number"],
                    "source_sha256": source["sha256"],
                    "raw_reference": q.get("raw_reference"),
                    "matching": q.get("matching"),
                    "issues": q["issues"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        + "</pre></details></section></article>"
    )


def render_report(data, rows, *, width=1166):
    return document(
        [
            render_question(
                q, data["sources"][q["source_document_id"]], position=i, count=len(rows)
            )
            for i, q in enumerate(rows, 1)
        ],
        width=width,
        extra_css=".prose{white-space:pre-wrap}.formula{display:inline-block;vertical-align:middle;padding:0 .12em}math{font-family:'Cambria Math',serif}math[display=block]{margin:12px 0}.visual img,.detailed-report>img{display:block;max-width:100%;width:auto;height:auto;object-fit:contain}",
    )
