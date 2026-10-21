"""RAW source structure and shared inspection regressions; no mathematical solving."""

import subprocess
import sys
from pathlib import Path

import pytest

from parsers.mathematics.formulas import recover
from parsers.mathematics.source import option_anchors, parse_pdf, project
from parsers.mathematics.structure import walk
from processors.matching.mathematics.backtest import render_report
from processors.pre_final.preview_layout import CSS

ROOT = Path(__file__).resolve().parents[1]


def char(value, x, y, *, font="Tahoma", size=10, identifier=None):
    return {
        "text": value,
        "x0": x,
        "x1": x + 5,
        "top": y,
        "bottom": y + size,
        "fontname": font,
        "size": size,
        "id": identifier or value + str(x) + str(y),
    }


class Assets:
    def crop(self, page, box, role, question, option=None):
        return {"id": f"asset-{len(str(box))}-{role}", "role": role}


def test_project_python_can_execute_pytest():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "pytest" in result.stdout


def test_source_image_between_lines_is_an_ordered_standalone_block():
    blocks, _, issues = project(
        [char("Before", 0, 0), char("After", 0, 50)],
        [],
        [[0, 20, 50, 40]],
        Assets(),
        2,
        3,
        "question",
    )
    assert [b["type"] for b in blocks] == ["text", "visual", "text"]
    assert blocks[1]["display"] is True
    assert [b["order"] for b in blocks] == [1, 2, 3]
    assert blocks[2]["break_before"]
    assert not issues


def test_list_markers_are_structure_and_continuation_stays_outside_list():
    chars = [
        char("Intro:", 0, 0),
        char("\uf0b7", 10, 30, font="Symbol"),
        char("First", 25, 30),
        char("\uf0b7", 10, 50, font="Symbol"),
        char("Second", 25, 50),
        char("Continuation?", 0, 80),
    ]
    blocks, _, issues = project(chars, [], [], Assets(), 2, 18, "question")
    assert [b["type"] for b in blocks] == ["text", "list", "text"]
    assert [item["content"][0]["text"] for item in blocks[1]["items"]] == [
        "First",
        "Second",
    ]
    assert {g for b in walk(blocks) for g in b["source"]["glyph_ids"]} == {
        c["id"] for c in chars
    }
    assert not issues


def test_separated_option_punctuation_is_structural_but_math_parenthesis_survives():
    words = [{**char(label, i * 50, 0), "page": 2} for i, label in enumerate("ABCD")]
    words.append({**char(")", 157, 0), "page": 2})
    anchors = option_anchors(words)
    assert anchors[-1]["x1"] == 162
    assert (
        recover(
            [
                char("x", 0, 0, font="Cambria Math"),
                char(")", 6, 0, font="Cambria Math"),
            ],
            [],
        )[0]
        == "x)"
    )
    words[-1]["fontname"] = "Cambria Math"
    assert option_anchors(words)[-1]["x1"] == 155


def test_uncertain_formula_is_not_stored_as_an_accepted_image_answer():
    blocks, _, issues = project(
        [char("\ue000", 0, 0, font="Cambria Math")],
        [],
        [],
        Assets(),
        2,
        27,
        "option",
        "D",
    )
    assert blocks[0]["type"] == "unresolved_math"
    assert "asset_id" not in blocks[0]
    assert blocks[0]["diagnostic_asset_id"]
    assert (
        issues[0]["reason"]
        and issues[0]["field"] == "option"
        and issues[0]["option_label"] == "D"
    )


def test_raster_math_requires_real_recognition_not_a_false_diagram_label():
    blocks, _, issues = project(
        [], [], [[0, 0, 100, 20]], Assets(), 2, 1, "option", "A", math_context=True
    )
    assert blocks[0]["type"] == "unresolved_math"
    assert blocks[0]["diagnostic_asset_id"]
    assert issues[0]["code"] == "raster_math_unverified"


@pytest.fixture(scope="module")
def corrected_math11(tmp_path_factory):
    return parse_pdf(
        ROOT / "acquisition/local/mathematics/matdev/math_11.pdf",
        asset_dir=tmp_path_factory.mktemp("corrected-math11") / "assets",
        question_numbers={3, 18, 27, 29},
    )


def test_native_multiline_equations_preserve_separate_source_lines(corrected_math11):
    q = corrected_math11["questions"][0]
    equations = [b for b in q["content"] if b["type"] == "math" and b["display"]]
    assert [b["latex"] for b in equations] == ["a+b=-5", "ab=3"]
    assert all(b["break_before"] for b in equations)
    assert "What is the equation?" in q["content"][-1]["text"]
    assert not q["issues"]


@pytest.mark.parametrize("number", [18, 29])
def test_native_bullet_lists_have_two_separate_items(corrected_math11, number):
    q = next(q for q in corrected_math11["questions"] if q["question_number"] == number)
    lists = [b for b in q["content"] if b["type"] == "list"]
    assert len(lists) == 1 and len(lists[0]["items"]) == 2
    assert q["content"][-1]["type"] == "text"
    assert not any(
        b["type"] in {"visual", "unresolved_math"} for b in walk(q["content"])
    )
    assert not q["issues"]


def test_native_fractional_radicals_and_clean_option_markers(corrected_math11):
    q = next(q for q in corrected_math11["questions"] if q["question_number"] == 27)
    expected = [
        "x",
        r"\frac{x}{\sqrt[3]{2}}",
        r"\sqrt[3]{2}",
        r"\frac{1}{\sqrt[3]{2}}",
        r"\sqrt[3]{2}x",
    ]
    assert [[b.get("latex") for b in o["content"]] for o in q["options"]] == [
        [x] for x in expected
    ]
    assert all(b["type"] == "math" for o in q["options"] for b in o["content"])
    assert not q["issues"]


def test_multiline_answer_keeps_break_even_when_superscript_bbox_overlaps_previous_line(
    tmp_path,
):
    raw = parse_pdf(
        ROOT / "acquisition/local/mathematics/matdev/math_3.pdf",
        asset_dir=tmp_path / "assets",
        question_numbers={1},
    )
    answer = raw["questions"][0]["options"][0]["content"]
    assert answer[0]["latex"] == "x="
    assert answer[1]["break_before"]
    assert answer[1]["latex"] == r"(by^{2}+a^{2})^{\frac{1}{2}}-a"


def test_targeted_raw_regeneration_preserves_every_unselected_record(tmp_path):
    import json

    from parsers.mathematics.__main__ import main

    source = ROOT / "acquisition/local/mathematics/matdev/math_11.pdf"
    existing = next((ROOT / "data/raw/mathematics").glob("math_11_*.raw.json"))
    before = json.loads(existing.read_text(encoding="utf8"))
    target = tmp_path / existing.name
    target.write_text(json.dumps(before), encoding="utf8")
    main([str(source), "--output-dir", str(tmp_path), "--overwrite", "--question", "3"])
    after = json.loads(target.read_text(encoding="utf8"))
    assert (
        after["pages"] == before["pages"]
        and after["answer_key"] == before["answer_key"]
    )
    for old, new in zip(before["questions"], after["questions"]):
        assert old["id"] == new["id"] and old["raw"] == new["raw"]
        if old["question_number"] != 3:
            assert old == new


def test_math_report_uses_shared_shell_and_canonical_lists(corrected_math11):
    data = {
        "sources": {
            corrected_math11["source_document"]["id"]: corrected_math11[
                "source_document"
            ]
        }
    }
    for width in (1166, 1350):
        html = render_report(data, corrected_math11["questions"], width=width)
        assert CSS.read_text(encoding="utf8") in html
        assert "class='website'" in html and "class='answer-option'" in html
        assert (
            "class='detailed-report'" in html and "Original question screenshot" in html
        )
        assert "<ul><li>" in html and "<mfrac>" in html
        assert (
            html.index("Detailed report")
            < html.index("<h3>Source</h3>")
            < html.index("<h3>Main Question</h3>")
        )
        assert "--preview-width:" + str(width) + "px" in html
        assert "Critical Thinking" not in html
