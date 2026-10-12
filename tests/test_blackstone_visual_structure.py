"""Focused crops, choice anchors, and raw source-order layout regressions."""

import json
from pathlib import Path

import pytest
from test_blackstone_raw import write_pdf

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import (
    collect_issues,
    inspect_question,
    render_inspection,
)
from parsers.blackstone.visual_structure import focused_crop, foreign_option_anchors


def spatial_line(text, x, y, widths, start=0):
    boxes = []
    cursor = x
    for width in widths:
        boxes.append([cursor, y, cursor + width, y + 10])
        cursor += width + 3
    return {
        "text": text,
        "page": 1,
        "x0": x,
        "top": y,
        "x1": cursor - 3,
        "bottom": y + 10,
        "block_start": start,
        "word_boxes": boxes,
        "word_texts": text.split(),
    }


def test_focused_crop_rejects_prose_but_preserves_internal_table_text_and_caption():
    lines = [
        spatial_line("The terms of the sale are as follows:", 40, 80, [18] * 9),
        spatial_line("Total marked price before discount", 45, 104, [25] * 5, 50),
        spatial_line("Reduction (%)", 185, 104, [30, 20], 90),
        spatial_line("Table 1", 90, 94, [25, 6], 110),
        spatial_line("Distance (km)", 90, 192, [38, 22], 120),
        spatial_line(
            "How much less would they actually spend on these goods?",
            40,
            210,
            [25] * 11,
            150,
        ),
    ]
    crop, context = focused_crop({"bbox": [40, 100, 260, 190]}, lines, 1, 600, 800)
    assert crop[1] > 80 + 10  # prose excluded even though a nearby caption is kept
    assert crop[3] < 210
    assert crop[1] <= 94 and crop[3] >= 202
    assert {s["start"] for s in context["included_text_spans"]} >= {50, 90, 110, 120}
    assert context["excluded_text_spans"][0]["start"] == 0


def test_named_long_caption_is_kept_and_uncertainty_is_reported():
    line = spatial_line(
        "Figure 1 shows the changing distance between the two towns", 80, 85, [14] * 11
    )
    crop, context = focused_crop({"bbox": [80, 100, 270, 190]}, [line], 1, 600, 800)
    assert crop[1] <= 85
    assert (
        "visual_caption_boundary_uncertain:external_caption_preserved"
        in context["warnings"]
    )


@pytest.mark.parametrize("labels_below", [False, True])
def test_six_image_choices_have_associations_and_source_order(tmp_path, labels_below):
    letters = "ABCDEF"
    rows = [
        (80 + (i % 3) * 160, 600 - (i // 3) * 180, letter)
        for i, letter in enumerate(letters)
    ]
    drawing = []
    for x, y, _ in rows:
        bottom = y + 25 if labels_below else y - 60
        drawing.append(f"{x} {bottom} 40 40 re S")
    source = write_pdf(
        tmp_path / "choices.pdf",
        [[(50, 740, "1 Which picture is correct?"), *rows]],
        graphics_commands=drawing,
    )
    data = parse_pdf(
        source,
        metadata={"year": 2022, "section": "section_1"},
        asset_dir=tmp_path / "assets",
    )
    validate_raw(data)
    question = data["questions"][0]
    assert [o["label"] for o in question["options"]] == list(letters)
    assert [a["option_label"] for a in question["visual_assets"]] == list(letters)
    assert [a["asset_index"] for a in question["visual_assets"]] == list(range(1, 7))
    assert all(len(o["images"]) == 1 and not o["warnings"] for o in question["options"])
    anchors = [
        {"label": o["label"], "bbox": o["label_bbox"], "page": o["page"]}
        for o in question["options"]
    ]
    assert all(
        not foreign_option_anchors(
            o["images"][0]["bbox"], anchors, o["page"], o["label"]
        )
        for o in question["options"]
    )
    assert all(
        a["placement"]["component"] == "option" for a in question["visual_assets"]
    )
    assert all((tmp_path / a["path"]).is_file() for a in question["visual_assets"])
    raw = tmp_path / "choices.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    original = raw.read_bytes()
    result = inspect_question([raw], source="choices.pdf", question_number=1)
    html = render_inspection(result, "html")
    assert "Stored question structure" in html and "Answer option F" in html
    assert "data-component='option'" in html
    assert render_inspection(
        result, "json"
    ) and "FULL STORED QUESTION RECORD" in render_inspection(result, "text")
    assert raw.read_bytes() == original
    assert not any(r["scope"] == "question" for r in collect_issues(data, raw))
    for block in question["layout_blocks"]:
        if block["type"] == "text":
            span = block["raw_span"]
            assert (
                question["raw"]["question_block"][span["start"] : span["end"]]
                == block["text"]
            )


def test_close_choice_images_are_not_merged_across_label_cells(tmp_path):
    source = write_pdf(
        tmp_path / "close.pdf",
        [
            [
                (50, 740, "1 Which picture?"),
                (90, 600, "A"),
                (146, 600, "B"),
                (80, 450, "C"),
                (80, 420, "D"),
                (80, 390, "E"),
            ]
        ],
        graphics_commands=["80 535 50 45 re S", "136 535 50 45 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assets = data["questions"][0]["visual_assets"]
    assert len(assets) == 2 and [a["option_label"] for a in assets] == ["A", "B"]


def test_shared_choice_geometry_stays_unresolved_and_is_reported(tmp_path):
    source = write_pdf(
        tmp_path / "shared.pdf",
        [
            [
                (50, 740, "1 Which picture?"),
                (90, 600, "A"),
                (146, 600, "B"),
                (80, 450, "C"),
                (80, 420, "D"),
                (80, 390, "E"),
            ]
        ],
        graphics_commands=["80 535 110 45 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    asset = data["questions"][0]["visual_assets"][0]
    assert asset["path"] and asset["belongs_to"] == "unknown"
    reasons = [
        reason
        for row in collect_issues(data, tmp_path / "shared.raw.json")
        for reason in row["reasons"]
    ]
    assert (
        "visual_multiple_option_images_merged:shared_geometry_requires_review"
        in reasons
    )


def test_tall_choices_with_left_labels_and_small_gap_stay_separate(tmp_path):
    source = write_pdf(
        tmp_path / "tall.pdf",
        [
            [
                (50, 740, "1 Which picture?"),
                (80, 600, "A"),
                (80, 480, "B"),
                (80, 300, "C Third"),
                (80, 270, "D Fourth"),
                (80, 240, "E Fifth"),
            ]
        ],
        graphics_commands=["114 490 40 110 re S", "114 370 40 110 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assets = data["questions"][0]["visual_assets"]
    assert len(assets) == 2 and [a["option_label"] for a in assets] == ["A", "B"]
    options = data["questions"][0]["options"]
    anchors = [
        {"label": o["label"], "bbox": o["label_bbox"], "page": o["page"]}
        for o in options
        if o.get("images")
    ]
    assert all(
        not foreign_option_anchors(
            o["images"][0]["bbox"], anchors, o["page"], o["label"]
        )
        for o in options
        if o.get("images")
    )


def test_wide_chart_rows_match_left_labels_one_to_one(tmp_path):
    source = write_pdf(
        tmp_path / "wide.pdf",
        [
            [
                (50, 740, "1 Which chart?"),
                (80, 600, "A"),
                (300, 600, "B"),
                (80, 430, "C"),
                (300, 430, "D"),
                (80, 260, "E"),
            ]
        ],
        graphics_commands=[
            "150 535 140 65 re S",
            "370 535 140 65 re S",
            "150 365 140 65 re S",
            "370 365 140 65 re S",
            "150 195 140 65 re S",
        ],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert [a["option_label"] for a in data["questions"][0]["visual_assets"]] == list(
        "ABCDE"
    )
    options = data["questions"][0]["options"]
    anchors = [
        {"label": o["label"], "bbox": o["label_bbox"], "page": o["page"]}
        for o in options
        if o.get("images")
    ]
    assert all(
        not foreign_option_anchors(
            o["images"][0]["bbox"], anchors, o["page"], o["label"]
        )
        for o in options
        if o.get("images")
    )


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2011.pdf"
    ).is_file(),
    reason="Local TSA Oxford 2011 PDF unavailable",
)
def test_2011_q50_option_a_excludes_b_and_inspection_detects_regression(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2011.pdf"
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    q = data["questions"][49]
    assert q["question_number"] == 50
    assert (
        q["raw"]["question_block"]
        and q["raw"]["options_block"].strip() == "A B\nC D\nE"
    )
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert all(len(o["images"]) == 1 for o in q["options"])
    anchors = [
        {"label": o["label"], "bbox": o["label_bbox"], "page": o["page"]}
        for o in q["options"]
    ]
    for option in q["options"]:
        asset = option["images"][0]
        assert not foreign_option_anchors(
            asset["bbox"], anchors, asset["page"], option["label"]
        )
        assert (tmp_path / asset["path"]).is_file()
    a = q["options"][0]["images"][0]
    b_anchor = q["options"][1]["label_bbox"]
    assert a["bbox"][2] < b_anchor[0]
    raw = tmp_path / "2011.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    assert not [r for r in collect_issues(data, raw) if r["question_number"] == 50]
    a["bbox"][2] = b_anchor[2] + 1
    assert any(
        "foreign_option_letter_in_crop:A->B" in row["reasons"]
        for row in collect_issues(data, raw)
        if row["question_number"] == 50
    )


def test_layout_reference_or_order_damage_is_reported(tmp_path):
    source = write_pdf(
        tmp_path / "layout.pdf",
        [[(50, 740, "1 Which follows?"), (80, 500, "A Text")]],
        graphics=True,
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][0]
    question["layout_blocks"][0]["order"] = 99
    question["layout_blocks"] = [
        b for b in question["layout_blocks"] if b["type"] != "visual"
    ]
    reasons = [
        reason
        for row in collect_issues(data, tmp_path / "layout.raw.json")
        for reason in row["reasons"]
    ]
    assert "visual_layout_order_inconsistent" in reasons
    assert "visual_layout_asset_reference_inconsistent" in reasons


def test_prose_and_nonchoice_letter_rows_do_not_change_existing_options(tmp_path):
    source = write_pdf(
        tmp_path / "prose.pdf",
        [
            [
                (50, 740, "1 Read the diagram and statements."),
                (100, 700, "A D G E F C J"),
                (65, 680, "F is a letter in the diagram, not a choice."),
                (80, 600, "A First"),
                (80, 560, "B Second"),
                (80, 520, "C Third"),
                (80, 480, "D Fourth"),
                (80, 440, "E Fifth"),
                (80, 420, "I am describing the fifth choice."),
            ]
        ],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][0]
    assert [o["label"] for o in question["options"]] == list("ABCDE")
    assert "I am describing" in question["options"][-1]["text"]
    assert "A D G E F C J" in question["question_text"]


def test_letter_valued_text_choices_are_not_reinterpreted_as_image_labels(tmp_path):
    source = write_pdf(
        tmp_path / "letters.pdf",
        [
            [
                (50, 740, "1 Which node is next?"),
                (80, 600, "A V"),
                (80, 560, "B W"),
                (80, 520, "C X"),
                (80, 480, "D Y"),
                (80, 440, "E Z"),
            ]
        ],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert [o["text"].strip() for o in data["questions"][0]["options"]] == list("VWXYZ")


def test_duplicate_parsed_option_labels_do_not_get_guessed_images(tmp_path):
    source = write_pdf(
        tmp_path / "duplicates.pdf",
        [
            [
                (50, 740, "1 Select a diagram."),
                (80, 650, "A B C"),
                (80, 600, "A D E"),
            ]
        ],
        graphics_commands=["120 555 50 35 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][0]
    assert question["visual_assets"][0]["path"]
    assert question["visual_assets"][0]["placement"]["component"] == "unknown"
    assert all(not o["images"] for o in question["options"])
    assert (
        "visual_option_labels_ambiguous:duplicate_structural_labels"
        in question["warnings"]
    )


def test_subpart_diagram_placement_and_unrelated_paragraph_remain_in_raw(tmp_path):
    source = write_pdf(
        tmp_path / "subparts.pdf",
        [
            [
                (50, 740, "1 Compare these numbered statements."),
                (80, 650, "1. First statement describes a diagram."),
                (80, 540, "2. Second statement."),
                (80, 450, "A First"),
                (80, 420, "B Second"),
                (80, 390, "C Third"),
                (80, 360, "D Fourth"),
                (80, 330, "E Fifth"),
            ]
        ],
        graphics_commands=["100 575 60 45 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][0]
    assert question["visual_assets"][0]["placement"]["component"] == "subpart"
    assert question["visual_assets"][0]["placement"]["label"] == "1"
    types = [b["type"] for b in question["layout_blocks"]]
    assert types.index("visual") > 0
    assert [o["label"] for o in question["options"]] == list("ABCDE")
    assert "First statement describes a diagram" in question["raw"]["question_block"]


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2010.pdf"
    ).exists(),
    reason="Local PDF unavailable",
)
def test_attached_bad_crop_regressions_on_local_2010_paper(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2010.pdf"
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    clock = data["questions"][6]
    table = data["questions"][11]
    assert clock["visual_assets"][0]["bbox"][3] < 270
    assert table["visual_assets"][0]["bbox"][1] > 396.3
    assert "It is light outside" in clock["raw"]["question_block"]
    assert "Sue and Ben" in table["raw"]["question_block"]
    assert clock["visual_assets"][0]["placement"]["component"] == "stimulus"
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    assert all(len(o["images"]) == 1 for o in data["questions"][13]["options"])
    assert all(len(o["images"]) == 1 for o in data["questions"][19]["options"])
