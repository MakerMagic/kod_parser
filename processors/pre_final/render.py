"""Reusable website-like preview from pre-final JSON only, with opt-in reporting."""

from html import escape
from pathlib import Path

from .preview_content import QuestionContent, text
from .preview_report import report
from .selection import assert_renderable, load, select, select_many
from .storage import ROOT

WIDTHS = (1166, 1350)
CSS = Path(__file__).with_name("preview.css")


def simulation(question, categories, content, *, report_prefix="", position=1, count=1):
    """One question-taking component. No data loading, scoring or interpretation."""
    label = escape(categories[question["category"]]["name"])
    answers = []
    for answer in question["main_answers"]:
        answers.append(
            "<label class='answer-option' data-option='"
            + escape(answer["label"], quote=True)
            + "'>"
            "<input type='radio' name='answer-"
            + str(position)
            + "' value='"
            + escape(answer["label"], quote=True)
            + "' aria-label='Option "
            + escape(answer["label"], quote=True)
            + "'>"
            "<span class='option-badge' aria-hidden='true'>"
            + escape(answer["label"])
            + "</span>"
            "<span class='option-content'>"
            + content.answer(answer, caption=False)
            + "</span></label>"
        )
    return (
        "<div class='preview-scroll'><section class='website' aria-label='Question simulation'>"
        "<header class='exam-header'><span class='exam-source'>"
        + escape(question["source"])
        + "</span>"
        "<span class='preview-pill'>Rendering preview · "
        + str(question["year"])
        + "</span>"
        "<span class='category-badge'>" + label + "</span></header>"
        "<div class='simulation-grid'><section class='body-pane' tabindex='0' aria-label='Passage'>"
        "<h2 class='eyebrow'>PASSAGE</h2>"
        + (content.body(caption=False) or text("No separate passage."))
        + "</section>"
        "<section class='question-pane' tabindex='0' aria-label='Question and answers'>"
        "<div class='question-stem text'>"
        + escape(question["main_question"])
        + "</div>"
        "<fieldset class='answer-options'><legend class='sr-only'>Select an answer for preview</legend>"
        + "".join(answers)
        + "</fieldset></section></div>"
        "<footer class='exam-footer'><a class='explanation-link' href='#"
        + report_prefix
        + "explanation'>Explanation</a>"
        "<span class='question-counter'>Question "
        + str(question["question_number"])
        + " · Preview "
        + str(position)
        + "/"
        + str(count)
        + "</span>"
        "<button class='check-button' type='button' disabled title='Rendering preview only; no scoring'>Check</button>"
        "</footer></section></div>"
    )


def build_report(questions, categories, *, root=ROOT, width=1166):
    if width not in WIDTHS:
        raise ValueError("Supported preview widths: 1166 or 1350")
    if not questions:
        raise ValueError("No selected questions to render")
    parts = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:; style-src 'unsafe-inline'\">",
        "<title>Question rendering preview</title><style>"
        + CSS.read_text(encoding="utf-8")
        + "</style></head>",
        "<body style='--preview-width:"
        + str(width)
        + "px'><main><p class='preview-note'>"
        + str(width)
        + " px preview · rendering only · answers are selectable, not scored</p>",
    ]
    for index, question in enumerate(questions):
        assert_renderable(question, categories)
        prefix = "" if len(questions) == 1 else f"q{index}-"
        content = QuestionContent(question, root=root)
        parts.append(
            "<article class='question-preview' data-question-id='"
            + escape(question["id"], quote=True)
            + "'>"
        )
        parts.append(
            simulation(
                question,
                categories,
                content,
                report_prefix=prefix,
                position=index + 1,
                count=len(questions),
            )
        )
        parts.append(report(question, categories, content, prefix=prefix))
        parts.append("</article>")
    parts.append("</main></body></html>")
    return "".join(parts)


def render_html(question, categories, *, root=ROOT, width=1166):
    return build_report([question], categories, root=root, width=width)


def inspect(path, *, root=ROOT, width=1166, **selectors):
    data = load(path)
    return build_report(
        select_many(data, **selectors), data["categories"], root=root, width=width
    )


__all__ = ["WIDTHS", "build_report", "inspect", "render_html", "select", "simulation"]
