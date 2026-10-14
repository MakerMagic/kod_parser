"""Source-specific boundaries/layout, independent of matching and acquisition."""

import json
from collections import Counter
from pathlib import Path

import pytest
from test_blackstone_raw import write_pdf

from parsers.explained_answers.parser import parse_pdf, validate_answers
from parsers.explained_answers.structure import structure

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def explained(tmp_path):
    (tmp_path / "source").mkdir()
    pdf = write_pdf(
        tmp_path / "source" / "solutions.pdf",
        [
            [(40, 740, "Contents 2008 SECTION 1 Question 1: E")],
            [(40, 740, "2008")],
            [
                (40, 760, "SECTION 1"),
                (40, 720, "Question 1: A"),
                (60, 680, "The first explanatory paragraph."),
                (40, 664, "A continuation on the same page."),
                (60, 630, "A separate second paragraph."),
                (60, 590, "Let us consider why the other answers are wrong:"),
                (80, 564, "B- The first incorrect choice explanation begins"),
            ],
            [
                (80, 750, "and continues on this page."),
                (80, 730, "C- The second choice is inconsistent."),
                (40, 680, "Question 2: B"),
                (60, 640, "There are two useful facts:"),
                (80, 610, "- one ordinary list item"),
                (80, 590, "- another ordinary item"),
                (40, 530, "END OF SECTION"),
                (40, 500, "SECTION 2"),
                (40, 460, "Question 99: E"),
                (40, 420, "DO NOT MATCH THIS"),
                (40, 380, "END OF PAPER"),
            ],
            [(40, 740, "2009")],
            [
                (40, 750, "SECTION 1"),
                (40, 720, "Question 1: D"),
                (60, 680, "A fresh year explanation."),
                (40, 600, "END OF SECTION"),
            ],
        ],
    )
    return parse_pdf(pdf, asset_dir=tmp_path / "answers" / "assets")


def test_year_section_and_crosspage_boundaries(explained):
    assert [
        (a["year"], a["question_number"], a["correct_answer"])
        for a in explained["answers"]
    ] == [(2008, 1, "A"), (2008, 2, "B"), (2009, 1, "D")]
    assert all(a["section"] == "section_1" for a in explained["answers"])
    first = explained["answers"][0]
    assert first["page_reference"] == {"start_page": 3, "end_page": 4}
    assert first["raw"]["boundary"] == "next_question"
    assert "DO NOT MATCH" not in "".join(
        a["raw"]["source_excerpt"] for a in explained["answers"]
    )
    assert explained["answers"][1]["raw"]["boundary"] == "end_section"
    validate_answers(explained)


def test_paragraphs_and_distinct_list_roles(explained):
    first, other = explained["answers"][:2]
    assert len(first["explanation"]["paragraphs"]) == 2
    assert [b["label"] for b in first["explanation"]["choice_analysis"]] == ["B", "C"]
    assert (
        "continues on this page" in first["explanation"]["choice_analysis"][0]["text"]
    )
    assert not first["explanation"]["other_lists"]
    assert not other["explanation"]["choice_analysis"]
    assert len(other["explanation"]["other_lists"][0]["items"]) == 2
    assert all(a["visual_previews"] for a in explained["answers"])


def test_image_only_continuation_and_malformed_header(tmp_path):
    path = write_pdf(
        tmp_path / "example.pdf",
        [
            [(40, 750, "2010")],
            [(40, 750, "SECTION 1"), (40, 710, "Question 1: A")],
            [],
            [
                (40, 750, "Question 2: unknown"),
                (60, 710, "Preserve this text."),
                (40, 650, "SECTION 2"),
                (40, 610, "Question 3: B"),
            ],
        ],
        graphics=True,
    )
    data = parse_pdf(path, asset_dir=tmp_path / "answers" / "assets")
    one, two = data["answers"]
    assert [p["page"] for p in one["visual_previews"]] == [2, 3, 4]
    assert (
        "explanation_text_unavailable:source_preview_requires_review" in one["warnings"]
    )
    assert two["correct_answer"] is None
    assert any(w.startswith("malformed_question_header") for w in two["warnings"])
    assert any(w.startswith("explanation_boundary_unresolved") for w in two["warnings"])


def test_ambiguous_choice_list_is_not_forced():
    strings = ["Let us eliminate the other answers:", "- A: one", "- A: two"]
    lines = [
        {
            "text": s,
            "bbox": [40 if i == 0 else 70, i * 22, 400, i * 22 + 12],
            "page": 1,
            "line_id": i + 1,
            "start": i * 100,
            "end": i * 100 + len(s),
        }
        for i, s in enumerate(strings)
    ]
    result, warnings = structure(lines, "E")
    assert not result["choice_analysis"]
    assert (
        result["bulleted_blocks"][0]["role"] == "incorrect_choices_unmapped"
        and warnings
    )


def test_compact_dash_items_end_before_indented_prose():
    values = [
        (26, "- The first observation."),
        (26, "-The second observation."),
        (44, "Thus, the explanation resumes."),
        (26, "A continuation of the prose."),
        (44, "1.25 is a decimal, not a bullet."),
        (26, "-Y is not an English list marker."),
    ]
    lines = [
        {
            "text": s,
            "bbox": [x, i * 16, 400, i * 16 + 12],
            "page": 1,
            "line_id": i + 1,
            "start": i * 100,
            "end": i * 100 + len(s),
        }
        for i, (x, s) in enumerate(values)
    ]
    result, warnings = structure(lines, "E")
    assert [i["text"] for i in result["other_lists"][0]["items"]] == [
        "The first observation.",
        "The second observation.",
    ]
    assert "Thus, the explanation resumes." in result["main_explanation"]
    assert "1.25 is a decimal" in result["main_explanation"]
    assert "-Y" in result["main_explanation"] and not warnings


def test_real_source_generated_intermediate():
    paths = list((ROOT / "data/raw/explained_answers").glob("*.answers.json"))
    if not paths:
        pytest.skip("Run the documented local source parser for integration validation")
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    validate_answers(data)
    assert Counter(a["year"] for a in data["answers"]) == {
        year: 50 for year in range(2008, 2017)
    }
    for year in range(2008, 2017):
        selected = [a for a in data["answers"] if a["year"] == year]
        assert [a["question_number"] for a in selected] == list(range(1, 51))
        assert selected[-1]["raw"]["boundary"] == "end_section"
    assert all(a["section"] == "section_1" for a in data["answers"])
    assert any(
        a["page_reference"]["end_page"] > a["page_reference"]["start_page"]
        for a in data["answers"]
    )
    assert any(a["explanation"]["other_lists"] for a in data["answers"])
    wrong = next(
        a for a in data["answers"] if (a["year"], a["question_number"]) == (2016, 1)
    )
    assert [b["label"] for b in wrong["explanation"]["choice_analysis"]] == [
        "A",
        "B",
        "C",
        "E",
    ]
    graph = next(
        a for a in data["answers"] if (a["year"], a["question_number"]) == (2008, 12)
    )
    assert (
        not graph["explanation"]["blocks"]
        and graph["visual_previews"]
        and graph["warnings"]
    )
    # Prose after a list must not become a hanging list continuation.
    rates = next(
        a for a in data["answers"] if (a["year"], a["question_number"]) == (2014, 6)
    )
    assert [len(b["items"]) for b in rates["explanation"]["other_lists"]] == [3, 5]
    assert "Adding this up" in rates["explanation"]["main_explanation"]
    symbols = next(
        a for a in data["answers"] if (a["year"], a["question_number"]) == (2014, 20)
    )
    assert len(symbols["explanation"]["other_lists"][0]["items"]) == 2
    assert "Thus, we know" in symbols["explanation"]["main_explanation"]
    encoded = next(
        a for a in data["answers"] if (a["year"], a["question_number"]) == (2016, 38)
    )
    assert len(encoded["explanation"]["other_lists"][0]["items"]) == 5
    assert any(
        "unexpected_encoded_list_marker_preserved" in w for w in encoded["warnings"]
    )


def test_encoded_list_marker_is_preserved_and_flagged():
    values = ["• Pip=28°54", "©Eve-27*56", "© Bob=24*63"]
    lines = [
        {
            "text": s,
            "bbox": [5, i * 15, 70, i * 15 + 10],
            "page": 1,
            "line_id": i + 1,
            "start": i * 100,
            "end": i * 100 + len(s),
        }
        for i, s in enumerate(values)
    ]
    result, warnings = structure(lines, "E")
    assert len(result["other_lists"][0]["items"]) == 3
    assert result["other_lists"][0]["items"][1]["text"] == "©Eve-27*56"
    assert any("unexpected_encoded_list_marker_preserved" in w for w in warnings)
