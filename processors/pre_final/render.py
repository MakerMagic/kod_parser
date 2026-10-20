"""Opt-in unified question view: read pre-final JSON and its saved assets only."""

import base64
import json
import mimetypes
from html import escape
from pathlib import Path

from .core import validate
from .storage import ROOT, Store


def select(data, *, identifier=None, source=None, year=None, question=None):
    validate(data)
    if identifier is None and (source is None or year is None or question is None):
        raise ValueError("Select an exact ID or source/year/question")
    rows = [
        q
        for q in data["questions"]
        if (
            (identifier is None or q["id"] == identifier)
            and (source is None or q["source"] == source)
            and (year is None or q["year"] == year)
            and (question is None or q["question_number"] == question)
        )
    ]
    if len(rows) != 1:
        raise ValueError("No unique pre-final question; refine identity")
    return rows[0]


def render_html(question, categories, *, root=ROOT):
    """Keep the established readable section order, without an upstream renderer."""
    store = Store(root)
    assets = {a["id"]: a for a in question["assets"]}

    def text(value):
        return "<p class='text'>" + escape(str(value)) + "</p>"

    def figure(identifier):
        asset = assets[identifier]
        path = store.check(asset)
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("Unsupported saved inspection asset")
        return (
            "<figure><img alt='"
            + escape(asset["role"], quote=True)
            + "' src='data:"
            + mime
            + ";base64,"
            + base64.b64encode(path.read_bytes()).decode("ascii")
            + "'><figcaption>"
            + escape(asset["role"])
            + " · page "
            + escape(str(asset["page"]))
            + "</figcaption></figure>"
        )

    def section(identifier, heading, content):
        return (
            f"<section id='{identifier}'><h2>{escape(heading)}</h2>{content}</section>"
        )

    title = f"{question['source']} {question['year']} — Question {question['question_number']}"
    category = categories[question["category"]]
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">",
        "<title>" + escape(title) + "</title>",
        "<style>body{font:16px/1.55 system-ui,sans-serif;background:#eef2f6;color:#192535}main{max-width:1000px;margin:24px auto;background:white;padding:28px}h2{color:#235586;border-bottom:1px solid #dbe2e8}.text{white-space:pre-wrap}img{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{margin-bottom:28px}</style></head><body><main>",
        section("source", "Source", text(question["source"])),
        section(
            "explanation-by-ai",
            "Explanation by AI",
            text(str(question["explanation_by_ai"]).lower()),
        ),
        section(
            "category", "Category", text(category["family"] + " → " + category["name"])
        ),
        "<h1>" + escape(title) + "</h1>",
        section(
            "main-body",
            "Main Body",
            "".join(
                text(b["text"]) if b["type"] == "text" else figure(b["asset_id"])
                for b in question["main_body"]
            ),
        ),
        section("main-question", "Main Question", text(question["main_question"])),
        section(
            "main-answers",
            "Main Answers",
            "".join(
                "<div data-option='"
                + escape(a["label"], quote=True)
                + "'>"
                + text(a["label"] + ": " + a["text"])
                + (
                    ""
                    if a.get("render_text_only")
                    else "".join(figure(i) for i in a["asset_ids"])
                )
                + "</div>"
                for a in question["main_answers"]
            ),
        ),
        section("correct-answer", "Correct Answer", text(question["correct_answer"])),
    ]
    explanation = question["explanation"]
    blocks = []
    for block in (explanation or {}).get("blocks", []):
        if block["type"] == "paragraph":
            blocks.append(text(block["text"]))
        elif block["type"] == "visual":
            blocks.append(figure(block["asset_id"]))
        elif block["type"] == "list":
            tag = "ol" if block.get("ordered") else "ul"
            blocks.append(
                "<"
                + tag
                + ">"
                + "".join(
                    "<li class='text'>"
                    + escape(
                        ((i.get("label") + ": ") if i.get("label") else "") + i["text"]
                    )
                    + "</li>"
                    for i in block["items"]
                )
                + "</"
                + tag
                + ">"
            )
            if block.get("transition"):
                transition = block["transition"]
                blocks.append(
                    text(
                        transition["text"]
                        if isinstance(transition, dict)
                        else transition
                    )
                )
    parts.append(
        section(
            "explanation",
            "Explanation",
            "".join(blocks)
            if explanation
            else text("Not supplied by the accepted upstream source."),
        )
    )
    parts.append(
        section(
            "original-question",
            "Original question screenshot",
            "".join(
                figure(a["id"])
                for a in question["assets"]
                if a["role"] == "source_preview"
            ),
        )
    )
    parts.append(
        "<details><summary>Provenance</summary><pre>"
        + escape(
            json.dumps(
                {
                    "id": question["id"],
                    **question["provenance"],
                    "explanation": (explanation or {}).get("provenance"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        + "</pre></details></main></body></html>"
    )
    return "".join(parts)


def inspect(path, *, root=ROOT, **selectors):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return render_html(select(data, **selectors), data["categories"], root=root)
