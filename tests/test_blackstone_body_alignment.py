"""Trace body-vs-answer graphics and exact source spans through raw and clean."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.parser import _project_body_exclusions
from parsers.blackstone.visual_structure import foreign_option_anchors
from parsers.blackstone.visuals import _graph_cell
from processors.normalization.blackstone import clean_dataset
from processors.normalization.blackstone.backtest import (
    inspect_question,
    render_inspection,
)
from processors.normalization.blackstone.storage import write_clean
from processors.normalization.blackstone.structure import _line_mapping, text_lines


def test_exact_footer_projection_preserves_real_repeated_numbers_and_raw_text():
    text = "The required number is\n18\naxis\n18\nWhat is the result?\n"
    block = "25 " + text + "A One\nB Two"
    first = text.index("18")
    footer = text.index("18", first + 2)
    axis = text.index("axis")
    q = {
        "question_text": text.replace("axis\n", ""),
        "raw": {
            "question_block": block,
            "options_block": "A One\nB Two",
            "text_question_candidate": text,
            "extraction_notes": [],
        },
    }
    raw_before = deepcopy(q["raw"])
    pending = {"segments": [{"page": 18, "start": 0, "text": block}]}
    excluded = {18: [{"start": footer + 3, "text": "18"}]}
    _project_body_exclusions(q, pending, excluded, [(axis, axis + len("axis\n"))])
    assert q["question_text"] == "The required number is\n18\nWhat is the result?\n"
    assert q["raw"]["question_block"] == raw_before["question_block"]
    assert q["raw"]["text_question_candidate"] == text
    assert "exact spans" in q["raw"]["extraction_notes"][-1]


def test_exclusions_outside_body_are_not_applied_to_options():
    block = "25 What is the result?\nA 18\nB 19"
    q = {
        "question_text": "What is the result?\n",
        "raw": {
            "question_block": block,
            "options_block": "A 18\nB 19",
            "extraction_notes": [],
        },
    }
    before = deepcopy(q)
    _project_body_exclusions(
        q,
        {"segments": [{"page": 18, "start": 0, "text": block}]},
        {18: [{"start": block.index("18"), "text": "18"}]},
        [],
    )
    assert q == before


@pytest.mark.parametrize(
    "header,offset,expected", [("36", 0, True), ("37", 0, False), ("36", 5, False)]
)
def test_only_exact_initial_question_number_is_metadata(header, offset, expected):
    q = {
        "question_number": 36,
        "question_text": "The measurement is\n36\nWhat is the total?",
        "raw": {"question_block": " " * 100, "options_block": ""},
        "layout_blocks": [
            {
                "block_id": "number",
                "type": "text",
                "component": "stimulus",
                "text": header,
                "raw_span": {"start": offset},
            },
            *[
                {
                    "block_id": str(i),
                    "type": "text",
                    "component": "stimulus",
                    "text": line,
                    "raw_span": {"start": 10 + i * 20},
                }
                for i, line in enumerate(
                    ["The measurement is", "36", "What is the total?"]
                )
            ],
        ],
    }
    mapping = _line_mapping(q, text_lines(q["question_text"]))
    assert (mapping is not None) == expected
    if expected:
        assert mapping == {"0": 0, "1": 1, "2": 2}


@pytest.fixture(scope="module")
def papers(tmp_path_factory):
    repo = Path(__file__).resolve().parents[1]
    root = tmp_path_factory.mktemp("body_association")
    result = {}
    for year in [2017, 2018, 2019, 2020, 2021]:
        source = repo / f"acquisition/local/critical_thinking_problem_solving/tsa/TSA Oxford {year}.pdf"
        if not source.is_file():
            pytest.skip("Local source PDFs unavailable")
        directory = root / "raw" / str(year)
        data = parse_pdf(source, asset_dir=directory / "assets")
        validate_raw(data)
        assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
        raw = directory / f"{year}.raw.json"
        raw.write_text(json.dumps(data), encoding="utf-8")
        result[year] = (data, raw, clean_dataset(data, raw))
    return result


@pytest.mark.parametrize(
    "year,number,footer",
    [
        (2017, 13, "© UCLES 2017 [Turn over"),
        (2019, 14, "12"),
        (2019, 42, "33"),
        (2020, 25, "18"),
        (2021, 38, "26"),
    ],
)
def test_analogous_reported_body_graphics_become_cleanly_aligned(
    papers, year, number, footer
):
    data, raw, clean = papers[year]
    q = data["questions"][number - 1]
    cq = clean["questions"][number - 1]
    assert (
        footer in q["raw"]["question_block"]
        and footer in q["raw"]["text_question_candidate"]
    )
    assert footer not in [l.strip() for l in q["question_text"].splitlines()]
    assert not any(
        i["code"] == "layout_alignment_unresolved" for i in cq["cleaning_issues"]
    )
    assert cq["main_question"] and not cq["cleaning_issues"]
    assert all(
        a["belongs_to"] == "question" and a["option_label"] is None
        for a in q["visual_assets"]
    )
    assert all(not o["images"] for o in q["options"])
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert cq["raw_record"] == q and cq["raw_warnings"] == q["warnings"]
    assert all((raw.parent / a["path"]).is_file() for a in q["visual_assets"])


def test_2020_q36_diagram_precedes_body_and_numeric_answers_are_unchanged(papers):
    data, _, clean = papers[2020]
    q = data["questions"][35]
    cq = clean["questions"][35]
    assert cq["main_body"][0]["type"] == "visual"
    assert cq["main_body"][1]["text"].startswith("The whole of my garden")
    assert [o["text"] for o in cq["options"]] == [
        "2000",
        "2180",
        "2184",
        "2268",
        "2272",
    ]
    assert all(not o["images"] for o in cq["options"])
    assert not cq["cleaning_issues"] and cq["main_question"]
    assert q["visual_assets"][0]["path"].endswith("asset_01_b7553aaeee.png")


def test_targets_html_uses_body_graphics_and_text_answers_without_mutating_raw(
    papers, tmp_path
):
    data, raw, clean = papers[2020]
    before = raw.read_bytes()
    output = write_clean(clean, tmp_path / "clean/2020.clean.json")
    for number, visual_count in [(25, 2), (36, 1)]:
        r = inspect_question(
            [output],
            source=data["input"]["filename"],
            year=2020,
            question_number=number,
        )
        html = render_inspection(r, "html")
        body = html.split("id='main-body'")[1].split("</section>")[0]
        answers = html.split("id='main-answers'")[1].split("</section>")[0]
        assert body.count("data:image/png;base64,") == visual_count
        assert "data:image/png;base64," not in answers
        assert not r["cleaning_issues"]
        assert "layout_alignment_unresolved" not in html
    assert raw.read_bytes() == before


def test_own_letters_are_still_valid_and_foreign_letters_still_conflict(papers):
    data, _, _ = papers[2017]
    q = data["questions"][19]
    assert all(
        o["content_type"] == "image" and len(o["images"]) == 1 for o in q["options"]
    )
    assert q["options"][0]["images"][0]["path"].endswith("asset_02_a77c5d40c9.png")
    anchors = [
        {"label": "A", "bbox": [40, 100, 48, 112], "page": 1, "label_only": True},
        {"label": "B", "bbox": [240, 100, 248, 112], "page": 1, "label_only": True},
    ]
    assert not foreign_option_anchors([35, 95, 205, 225], anchors, 1, "A")
    assert (
        foreign_option_anchors([35, 95, 260, 225], anchors, 1, "A")[0]["label"] == "B"
    )
    assert _graph_cell({"bbox": [60, 98, 260, 220]}, anchors, 1) is None
    q = papers[2021][0]["questions"][31]
    assert all(
        o["content_type"] == "image" and len(o["images"]) == 1 for o in q["options"]
    )
    old = json.loads(
        next(
            (Path(__file__).resolve().parents[1] / "data/raw/blackstone").glob(
                "*2021*.raw.json"
            )
        ).read_text(encoding="utf-8")
    )["questions"][31]
    assert [o["images"][0]["sha256"] for o in q["options"]] == [
        o["images"][0]["sha256"] for o in old["options"]
    ]


@pytest.mark.parametrize("year,number", [(2018, 20), (2019, 44)])
def test_real_ambiguous_visuals_remain_unassigned_after_footer_projection(
    papers, year, number
):
    data, _, clean = papers[year]
    q = data["questions"][number - 1]
    cq = clean["questions"][number - 1]
    assert "visual_component_association_uncertain" in q["warnings"]
    assert any(a["belongs_to"] == "unknown" for a in q["visual_assets"])
    assert any(
        i["code"] == "visual_placement_unresolved" for i in cq["cleaning_issues"]
    )
    unassigned = {
        a["image_id"] for a in q["visual_assets"] if a["belongs_to"] == "unknown"
    }
    assigned = {a["image_id"] for o in q["options"] for a in o["images"]}
    assert unassigned.isdisjoint(assigned)
