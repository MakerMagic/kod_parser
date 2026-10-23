"""Rendering integration against mathematics PRE-FINAL only."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from html import escape

import pytest

from parsers.mathematics.structure import walk
from processors.pre_final import mathematics_render as renderer
from processors.pre_final.preview_layout import CSS


@pytest.fixture(scope="module")
def prefinal():
    return renderer.load()


def source_blocks(question):
    return list(walk(question["main_body"] + (question["main_question"] or []))) + [
        block
        for answer in question["main_answers"]
        for block in walk(answer["content"])
    ]


def test_renderer_reads_only_authoritative_ready_prefinal():
    data = renderer.load()
    assert data["stage"] == "mathematics_pre_final"
    assert data["summary"]["included"] == 519
    assert data["summary"]["ready_for_rendering"]
    assert len({q["id"] for q in data["questions"]}) == len(data["questions"])
    assert len(
        {(q["source_document_id"], q["question_number"]) for q in data["questions"]}
    ) == len(data["questions"])


def test_all_prefinal_render_audit_and_stage_pair_cover_canonical_ids(prefinal):
    audit_path = renderer.OUTPUT
    assert audit_path.is_file()
    validation = json.loads(audit_path.read_text(encoding="utf-8"))
    assert validation["summary"]["pre_final_questions"] == len(prefinal["questions"])
    assert validation["summary"]["renderable"] == len(prefinal["questions"])
    assert validation["issues"] == []
    assert set(validation["summary"]["questions_by_source"]) == {
        q["source_pdf"] for q in prefinal["questions"]
    }
    assert validation["summary"]["content_blocks_by_type"]["math"] > 0
    back = (renderer.DOCS / "QUESTION_RENDERING_BACKTESTING.md").read_text(
        encoding="utf-8"
    )
    issues = (renderer.DOCS / "QUESTION_RENDERING_ISSUES.md").read_text(
        encoding="utf-8"
    )
    assert "PRE-FINAL questions: 519" in back
    assert "Total issues: 0" in issues
    assert "No unresolved mathematics question-rendering issues" in issues


def test_report_metadata_order_category_and_answer_are_canonical(prefinal):
    q = prefinal["questions"][0]
    original = json.dumps(q, ensure_ascii=False, sort_keys=True)
    html = renderer.build_report([q], prefinal["sources"])
    positions = [
        html.index(f"id='{field}'")
        for field in (
            "source",
            "category",
            "main-body",
            "main-question",
            "main-answers",
            "correct-answer",
        )
    ]
    assert positions == sorted(positions)
    assert "Mathematics · " + q["source_pdf"] in html
    assert q["category"]["name"] in html
    assert f">{q['correct_answer']}</p>" in html
    assert "explanation-by-ai" not in html and "Explanation</h3>" not in html
    assert json.dumps(q, ensure_ascii=False, sort_keys=True) == original


def test_clean_derived_prompt_is_displayed_only_on_question_side(prefinal):
    q = deepcopy(prefinal["questions"][0])
    q["main_body"] = [{"type": "text", "text": "A context-only sentence."}]
    q["main_question"] = [
        {"type": "text", "text": "Find the required value of "},
        {"type": "math", "latex": r"\sqrt{x^{2}+1}", "display": False},
    ]
    html = renderer.build_report([q], prefinal["sources"])
    body = html.split("class='body-pane'", 1)[1].split("class='question-pane'", 1)[0]
    question = html.split("class='question-pane'", 1)[1].split("<fieldset", 1)[0]
    assert "A context-only sentence." in body and "Find the required value" not in body
    assert "Find the required value" in question and "<msqrt" in question
    assert "A context-only sentence." not in question
    q["main_body"], q["main_question"] = q["main_question"], None
    html = renderer.build_report([q], prefinal["sources"])
    assert "null — no separate source task statement" in html
    assert "class='question-stem text'" not in html


def test_renderer_rejects_visual_owned_by_main_question(prefinal):
    q = deepcopy(
        next(
            row
            for row in prefinal["questions"]
            if any(b["type"] == "visual" for b in walk(row["main_body"]))
        )
    )
    visual = next(b for b in walk(q["main_body"]) if b["type"] == "visual")
    q["main_question"] = [deepcopy(visual)]
    with pytest.raises(renderer.RenderingInputError, match="Main Body"):
        renderer.assert_renderable(q, prefinal["sources"])


def test_latex_is_rendered_as_mathml_not_source_and_stays_ordered(prefinal):
    q = next(
        q
        for q in prefinal["questions"]
        if any(b["type"] == "math" for b in source_blocks(q))
    )
    formulas = [b["latex"] for b in source_blocks(q) if b["type"] == "math"]
    html = renderer.build_report([q], prefinal["sources"], width=1350)
    assert html.count("<math ") >= len(formulas) * 2  # simulation and lower report
    assert "data-latex" not in html
    assert "\\frac" not in html and "\\sqrt" not in html
    assert "--preview-width:1350px" in html
    for formula in formulas:
        assert renderer.mathml(formula) in html


def test_rendered_mixed_body_keeps_math_text_and_visual_order(prefinal):
    q = next(
        q
        for q in prefinal["questions"]
        if {b["type"] for b in walk(q["main_body"])} >= {"text", "math", "visual"}
    )
    blocks = list(walk(q["main_body"]))
    html = renderer.build_report([q], prefinal["sources"])
    start = html.index("class='body-pane'")
    end = html.index("class='question-pane'", start)
    simulation = html[start:end]
    offsets = []
    cursor = 0
    for block in blocks:
        if block["type"] == "text" and block["text"].strip():
            token = "<span class='math-text'>" + escape(block["text"]) + "</span>"
            found = simulation.find(token, cursor)
        elif block["type"] == "math":
            found = simulation.find(
                renderer.mathml(block["latex"], display=block["display"]), cursor
            )
        elif block["type"] == "visual":
            asset = next(a for a in q["assets"] if a["id"] == block["asset_id"])
            found = simulation.find("alt='" + asset["role"], cursor)
        else:
            continue
        assert found >= 0
        offsets.append(found)
        cursor = found + 1
    assert offsets == sorted(offsets)


def test_visuals_preserve_assets_and_proportional_css(prefinal):
    q = next(
        q
        for q in prefinal["questions"]
        if any(b["type"] == "visual" for b in source_blocks(q))
    )
    before = {
        a["path"]: sha256((renderer.ROOT / a["path"]).read_bytes()).hexdigest()
        for a in q["assets"]
    }
    html = renderer.build_report([q], prefinal["sources"])
    assert "object-fit:contain" in html
    assert "max-width:100%" in html and "height:auto" in html
    assert "overflow-y:auto" not in renderer.MATH_CSS
    assert "overflow-y:auto" in CSS.read_text(encoding="utf-8")
    assert all(
        sha256((renderer.ROOT / path).read_bytes()).hexdigest() == value
        for path, value in before.items()
    )
    assert re.search(r"<img alt='(?:body|option)(?: [A-Z])?' src='data:image/", html)


def test_system_roots_fractions_and_display_math_have_browser_shapes(prefinal):
    shapes = {
        term: next(
            (
                q
                for q in prefinal["questions"]
                if any(term in b.get("latex", "") for b in source_blocks(q))
            ),
            None,
        )
        for term in (r"\begin{cases}", r"\sqrt", r"\frac")
    }
    assert all(shapes.values())
    system = renderer.build_report(
        [shapes[r"\begin{cases}"][0] if False else shapes[r"\begin{cases}"]],
        prefinal["sources"],
    )
    assert "<mtable" in system and 'columnalign="left"' in system
    assert "<msqrt" in renderer.build_report([shapes[r"\sqrt"]], prefinal["sources"])
    assert "<mfrac" in renderer.build_report([shapes[r"\frac"]], prefinal["sources"])
    display_q = next(
        q
        for q in prefinal["questions"]
        if any(b["type"] == "math" and b["display"] for b in source_blocks(q))
    )
    assert 'display="block"' in renderer.build_report([display_q], prefinal["sources"])


def test_select_by_stable_id_source_test_category_and_sample(prefinal):
    q = next(q for q in prefinal["questions"] if q["source_pdf"] == "Test_3.pdf")
    assert renderer.select_many(prefinal, identifier=q["id"])[0]["id"] == q["id"]
    assert (
        renderer.select_many(
            prefinal, source="Test_3.pdf", question=q["question_number"]
        )[0]["id"]
        == q["id"]
    )
    assert (
        renderer.select_many(prefinal, source="Test_3", question=q["question_number"])[
            0
        ]["id"]
        == q["id"]
    )
    assert renderer.select_many(
        prefinal, category=q["category"]["id"], sample=5
    ) == renderer.select_many(prefinal, category=q["category"]["id"], sample=5)
    with pytest.raises(ValueError, match="Select an ID"):
        renderer.select_many(prefinal)
    with pytest.raises(ValueError, match="No mathematics"):
        renderer.select_many(prefinal, identifier="missing-id")


def test_answers_expand_and_never_get_internal_scrollbars(prefinal):
    css = CSS.read_text(encoding="utf-8")
    rules = {
        s.strip(): d
        for s, d in re.findall(r"([^{}]+)\{([^{}]*)\}", css.split("@media print", 1)[0])
    }
    for selector in (
        ".question-pane",
        ".answer-options",
        ".answer-option",
        ".option-content",
    ):
        assert "overflow" not in rules[selector].replace("overflow-wrap:anywhere", "")
        assert "max-height" not in rules[selector]
    assert "overflow-y:auto" in rules[".body-pane"]
    long_answer = max(
        prefinal["questions"],
        key=lambda q: max(
            len(json.dumps(a["content"], ensure_ascii=False)) for a in q["main_answers"]
        ),
    )
    html = renderer.build_report([long_answer], prefinal["sources"])
    assert len(html) > 1000 and "class='answer-option'" in html


def test_inspect_generates_only_requested_preview_and_guards_canonical_paths(
    prefinal, tmp_path
):
    q = prefinal["questions"][0]
    path = tmp_path / "selected.html"
    assert renderer.write_inspection(prefinal, path, identifier=q["id"]) == path
    assert path.read_text(encoding="utf-8").count("class='question-preview'") == 1
    with pytest.raises(FileExistsError):
        renderer.write_inspection(prefinal, path, identifier=q["id"])
    with pytest.raises(ValueError, match="canonical data"):
        renderer.write_inspection(
            prefinal,
            renderer.ROOT / "data/pre_final/mathematics/unsafe.html",
            identifier=q["id"],
        )
