"""Reusable website-like preview from pre-final JSON only, with opt-in reporting."""

from html import escape

from .preview_content import QuestionContent, text
from .preview_layout import CSS, WIDTHS, answer_option, document, simulation_frame
from .preview_report import report
from .selection import assert_renderable, load, select, select_many
from .storage import ROOT


def simulation(question, categories, content, *, report_prefix="", position=1, count=1):
    """One question-taking component. No data loading, scoring or interpretation."""
    return simulation_frame(
        content.body(caption=False) or text("No separate passage."),
        escape(question["main_question"]),
        "".join(
            answer_option(a["label"], content.answer(a, caption=False), position)
            for a in question["main_answers"]
        ),
        source=question["source"],
        heading="Rendering preview · " + str(question["year"]),
        badge=categories[question["category"]]["name"],
        question_number=question["question_number"],
        report_prefix=report_prefix,
        position=position,
        count=count,
    )


def build_report(questions, categories, *, root=ROOT, width=1166):
    if width not in WIDTHS:
        raise ValueError("Supported preview widths: 1166 or 1350")
    if not questions:
        raise ValueError("No selected questions to render")
    parts = []
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
    return document(parts, width=width)


def render_html(question, categories, *, root=ROOT, width=1166):
    return build_report([question], categories, root=root, width=width)


def inspect(path, *, root=ROOT, width=1166, **selectors):
    data = load(path)
    return build_report(
        select_many(data, **selectors), data["categories"], root=root, width=width
    )


__all__ = ["CSS", "WIDTHS", "build_report", "inspect", "render_html", "select", "simulation"]
