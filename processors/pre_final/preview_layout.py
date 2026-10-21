"""Shared inspection shell; content remains supplied by each stage's adapter."""

from html import escape
from pathlib import Path

WIDTHS = (1166, 1350)
CSS = Path(__file__).with_name("preview.css")


def answer_option(label, content, position=1):
    label = escape(label, quote=True)
    return (
        f"<label class='answer-option' data-option='{label}'>"
        f"<input type='radio' name='answer-{position}' value='{label}' aria-label='Option {label}'>"
        f"<span class='option-badge' aria-hidden='true'>{label}</span>"
        f"<span class='option-content'>{content}</span></label>"
    )


def simulation_frame(
    body,
    stem,
    answers,
    *,
    source,
    heading,
    badge="",
    question_number,
    report_prefix="",
    position=1,
    count=1,
    body_label="PASSAGE",
):
    return (
        "<div class='preview-scroll'><section class='website' aria-label='Question simulation'>"
        "<header class='exam-header'><span class='exam-source'>"
        + escape(source)
        + "</span><span class='preview-pill'>"
        + escape(heading)
        + "</span>"
        + ("<span class='category-badge'>" + escape(badge) + "</span>" if badge else "")
        + "</header><div class='simulation-grid'>"
        "<section class='body-pane' tabindex='0' aria-label='Passage'>"
        "<h2 class='eyebrow'>" + escape(body_label) + "</h2>" + body + "</section>"
        "<section class='question-pane' tabindex='0' aria-label='Question and answers'>"
        + ("<div class='question-stem text'>" + stem + "</div>" if stem else "")
        + "<fieldset class='answer-options'><legend class='sr-only'>Select an answer for preview</legend>"
        + answers
        + "</fieldset></section></div>"
        "<footer class='exam-footer'><a class='explanation-link' href='#"
        + report_prefix
        + "explanation'>Explanation</a>"
        "<span class='question-counter'>Question "
        + str(question_number)
        + " · Preview "
        + str(position)
        + "/"
        + str(count)
        + "</span>"
        "<button class='check-button' type='button' disabled title='Rendering preview only; no scoring'>Check</button>"
        "</footer></section></div>"
    )


def document(articles, *, width=1166, extra_css=""):
    if width not in WIDTHS:
        raise ValueError("Supported preview widths: 1166 or 1350")
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">"
        "<title>Question rendering preview</title><style>"
        + CSS.read_text(encoding="utf-8")
        + extra_css
        + "</style></head>"
        "<body style='--preview-width:"
        + str(width)
        + "px'><main><p class='preview-note'>"
        + str(width)
        + " px preview · rendering only · answers are selectable, not scored</p>"
        + "".join(articles)
        + "</main></body></html>"
    )
