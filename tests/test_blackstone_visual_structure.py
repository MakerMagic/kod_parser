"""Focused crops, choice anchors, and raw source-order layout regressions."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_blackstone_raw import write_pdf

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import (
    collect_issues,
    inspect_question,
    render_inspection,
)
from parsers.blackstone.parser import _white_page_enclosure_stroke
from parsers.blackstone.pdf_graphics import is_white
from parsers.blackstone.visual_structure import (
    focused_crop,
    foreign_option_anchors,
    option_anchor_is_left_of_visual,
)
from parsers.blackstone.visuals import _is_table


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


def test_spot_color_tint_is_not_mistaken_for_white():
    assert not is_white(1, "Separation")
    assert not is_white(1, "DeviceN")
    assert not is_white(1)
    assert is_white(1, "DeviceGray")
    assert is_white((1, 1, 1), "DeviceRGB")
    assert is_white((0, 0, 0, 0), "DeviceCMYK")
    assert not is_white((0, 0, 0, 1), "DeviceCMYK")


def test_table_requires_intersecting_grid_and_text_in_multiple_cells():
    objects = [
        {"object_type": "line", "bbox": box}
        for box in (
            [100, 100, 300, 100],
            [100, 150, 300, 150],
            [100, 200, 300, 200],
            [100, 100, 100, 200],
            [200, 100, 200, 200],
            [300, 100, 300, 200],
        )
    ]
    group = {"bbox": [100, 100, 300, 200], "objects": objects}
    lines = [
        spatial_line("Jan 10", 120, 120, [20, 12]),
        spatial_line("Feb 20", 220, 170, [20, 12]),
    ]
    assert _is_table(group, lines, 1)
    assert not _is_table(group, [], 1)  # Empty geometry is not a text table.
    assert not _is_table({**group, "graph": True}, lines, 1)
    assert not _is_table({**group, "objects": objects[:3]}, lines, 1)
    assert not _is_table(
        {**group, "objects": [objects[i] for i in (0, 2, 3, 5)]}, lines, 1
    )  # A border around prose is not a table.


def test_spot_color_rectangle_grid_saves_a_focused_table(tmp_path):
    source = write_pdf(
        tmp_path / "spot-grid.pdf",
        [
            [
                (50, 750, "1 Compare the values in the table."),
                (160, 615, "Jan 10"),
                (260, 615, "Jan 20"),
                (160, 555, "Feb 30"),
                (260, 555, "Feb 40"),
                (50, 490, "Which value is largest?"),
                *[
                    (80, 450 - i * 20, f"{label} {i + 1}")
                    for i, label in enumerate("ABCDE")
                ],
            ]
        ],
        extra_resources=(
            "/ColorSpace << /Ink [/Separation /Black /DeviceCMYK "
            "<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] "
            "/C1 [0 0 0 1] /N 1 >>] >>"
        ),
        graphics_commands=[
            "1 g 20 20 50 10 re f",  # A genuinely white decoration stays excluded.
            "/Ink cs 1 scn",
            *[f"{x} 520 0.6 120 re f" for x in (150, 250, 350)],
            *[f"150 {y} 200 0.6 re f" for y in (520, 580, 640)],
        ],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    question = data["questions"][0]
    assert question["question_number"] == 1
    assert [o["label"] for o in question["options"]] == list("ABCDE")
    assert "Jan 10 Jan 20" in question["raw"]["question_block"]
    assert "Which value is largest?" in question["question_text"]
    assert len(question["visual_assets"]) == 1
    asset = question["visual_assets"][0]
    assert asset["visual_kind"] == "table"
    assert asset["crop_method"] == "pdf_closed_border"
    assert asset["bbox"][1] > 140 and asset["bbox"][3] < 300
    assert not asset["warnings"]
    assert (tmp_path / asset["path"]).is_file()
    assert any(i["decorative"] for i in data["pages"][0]["images"])


def test_2017_q20_spot_color_table_and_existing_chart_warnings(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2017.pdf"
    )
    if not source.is_file():
        pytest.skip("Local 2017 PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    question = data["questions"][19]
    assert [o["label"] for o in question["options"]] == list("ABCDE")
    tables = [a for a in question["visual_assets"] if a.get("visual_kind") == "table"]
    assert len(tables) == 1
    table = tables[0]
    assert table["crop_method"] == "pdf_closed_border"
    assert not table["warnings"]
    assert table["option_label"] is None
    assert table["bbox"][1] > 100 and table["bbox"][3] < 312
    text = "\n".join(
        question["raw"]["question_block"][span["start"] : span["end"]]
        for span in table["included_text_spans"]
    )
    assert "Jan 2012 124.1 Jan 2007 161.2" in text
    assert "Dec 2012 123.1 Dec 2007 139.8" in text
    assert "After the financial crash" not in text
    assert "Which one of the following" not in text
    # The table fix must not erase unresolved answer-chart problems.
    assert any(a["warnings"] for a in question["visual_assets"] if a is not table)
    raw = tmp_path / "2017.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    before = raw.read_bytes()
    result = inspect_question([raw], source=source.name, year=2017, question_number=20)
    html = render_inspection(result, "html")
    assert "data:image/png;base64," in html and table["image_id"] in html
    assert render_inspection(result, "text") and render_inspection(result, "json")
    assert raw.read_bytes() == before
    assert any(r.get("question_number") == 20 for r in collect_issues(data, raw))


def test_white_page_margin_stroke_is_not_a_dark_diagram_stroke():
    page = SimpleNamespace(width=600, height=800, images=[], rects=[], curves=[])
    stroke = {
        "object_type": "line",
        "stroke": True,
        "fill": False,
        "stroking_color": (0, 0, 0, 0),
        "x0": 44,
        "x1": 44,
        "top": 760,
        "bottom": 775,
    }
    assert _white_page_enclosure_stroke(stroke, page)
    assert not _white_page_enclosure_stroke({**stroke, "x0": 200, "x1": 200}, page)
    assert not _white_page_enclosure_stroke({**stroke, "stroking_color": 0}, page)
    page.rects = [
        {
            "x0": 40,
            "x1": 50,
            "top": 755,
            "bottom": 780,
            "fill": True,
            "non_stroking_color": 0,
        }
    ]
    assert not _white_page_enclosure_stroke(stroke, page)


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
        drawing.append(f"{x + 30} {bottom} 40 40 re S")
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
        graphics_commands=["110 535 30 45 re S", "166 535 30 45 re S"],
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
        graphics_commands=["110 535 110 45 re S"],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    asset = data["questions"][0]["visual_assets"][0]
    assert asset["path"] and asset["belongs_to"] == "unknown"
    reasons = [
        reason
        for row in collect_issues(data, tmp_path / "shared.raw.json")
        for reason in row["reasons"]
    ]
    assert "visual_component_association_uncertain" in reasons


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
def test_2011_q25_contour_and_q50_option_boundaries(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2011.pdf"
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    q25 = data["questions"][24]
    assert [option["label"] for option in q25["options"]] == list("ABCDE")
    assert all(len(option["images"]) == 1 for option in q25["options"])
    for label in ("A", "B"):
        asset = q25["options"][ord(label) - ord("A")]["images"][0]
        assert asset["option_label"] == label
        assert not asset["warnings"]
    assert not any(
        warning.startswith(
            (
                "visual_multiple_option_images_merged",
                "visual_component_association_uncertain",
            )
        )
        for warning in q25["warnings"]
    )
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
    a["bbox"][1] = b_anchor[1] - 1
    a["graphic_bbox"][2] = b_anchor[2] + 1
    a["graphic_bbox"][1] = b_anchor[1] - 1
    assert any(
        "foreign_option_letter_in_crop:A->B" in row["reasons"]
        for row in collect_issues(data, raw)
        if row["question_number"] == 50
    )


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2011.pdf"
    ).is_file(),
    reason="Local TSA Oxford 2011 PDF unavailable",
)
def test_2011_q7_image_options_use_only_left_side_anchors(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2011.pdf"
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    q = data["questions"][6]
    assert q["question_number"] == 7
    assert [option["label"] for option in q["options"]] == list("ABCDE")
    assert all(len(option["images"]) == 1 for option in q["options"])
    c = q["options"][2]
    d = q["options"][3]
    asset = c["images"][0]
    assert option_anchor_is_left_of_visual(
        {"bbox": c["label_bbox"]}, asset["graphic_bbox"]
    )
    assert not foreign_option_anchors(
        asset["bbox"],
        [
            {
                "label": option["label"],
                "bbox": option["label_bbox"],
                "page": option["page"],
            }
            for option in q["options"]
        ],
        asset["page"],
        "C",
    )
    assert asset["bbox"][2] < d["label_bbox"][0]


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2012.pdf"
    ).is_file(),
    reason="Local TSA Oxford 2012 PDF unavailable",
)
def test_2012_q3_text_enclosures_do_not_create_visual_association_issues(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2012.pdf"
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    q = data["questions"][2]
    assert q["question_number"] == 3
    assert not q["visual_assets"]
    assert not any(
        warning.startswith("visual_component_association_uncertain")
        for warning in q["warnings"]
    )
    issues = [
        reason
        for row in collect_issues(data, tmp_path / "2012.raw.json")
        if row.get("question_number") == 3
        for reason in row["reasons"]
    ]
    assert not any(reason.startswith("visual_") for reason in issues)


@pytest.mark.parametrize(
    ("year", "questions"),
    [(2013, (25, 31)), (2014, (12,))],
)
def test_local_closed_border_tables_keep_internal_text_without_surrounding_prose(
    tmp_path, year, questions
):
    source = (
        Path(__file__).resolve().parents[1]
        / "acquisition"
        / "local"
        / f"TSA Oxford {year}.pdf"
    )
    if not source.is_file():
        pytest.skip("Local table PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    for number in questions:
        question = data["questions"][number - 1]
        assert [option["label"] for option in question["options"]] == list("ABCDE")
        assert question["raw"]["question_block"]
        assert question["visual_assets"]
        asset = question["visual_assets"][0]
        graphic, crop = asset["graphic_bbox"], asset["bbox"]
        assert asset["crop_method"] == "pdf_closed_border"
        assert all(abs(abs(crop[i] - graphic[i]) - 4) < 0.01 for i in range(4))
        assert not asset["warnings"]
        assert asset["included_text_spans"]
        assert (tmp_path / asset["path"]).is_file()
        if (year, number) in ((2013, 31), (2014, 12)):
            assert asset["visual_kind"] == "table"
    if year == 2014:
        # A different, non-table visual on the same paper must remain saved.
        assert data["questions"][6]["visual_assets"]


def test_2021_q19_table_notes_keep_existing_conservative_crop(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2021.pdf"
    )
    if not source.is_file():
        pytest.skip("Local 2021 PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][18]
    asset = question["visual_assets"][0]
    assert asset["visual_kind"] == "table"
    assert asset["crop_method"] == "pdf_objects_paragraph_barriers_text_ownership"
    assert asset["bbox"][3] > 310
    assert (
        "visual_caption_boundary_uncertain:external_caption_preserved"
        in asset["warnings"]
    )
    text = "\n".join(
        question["raw"]["question_block"][span["start"] : span["end"]]
        for span in asset["included_text_spans"]
    )
    assert "* Family of 4 can be" in text
    # The existing conservative crop retains the first note, but does not fully
    # capture the second. Keep its review warning and verbatim raw/layout text.
    assert "Family of 5 can be" in question["raw"]["question_block"]


def test_2015_text_frames_no_longer_flag_every_question(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2015.pdf"
    )
    if not source.is_file():
        pytest.skip("Local 2015 PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    assert all(
        q["question_text"] and q["raw"]["question_block"] for q in data["questions"]
    )
    assert all(
        [o["label"] for o in q["options"]] == list("ABCDE") for q in data["questions"]
    )
    assert all(not data["questions"][index]["visual_assets"] for index in (0, 1))
    assert data["questions"][24]["visual_assets"]  # Genuine Q25 graphic survives.
    assert data["questions"][49]["visual_assets"]  # Genuine Q50 raster survives.
    rows = collect_issues(data, tmp_path / "2015.raw.json")
    question_issues = [row for row in rows if row["scope"] == "question"]
    assert not question_issues


def test_2016_q32_two_diagrams_stay_unresolved(tmp_path):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA Oxford 2016.pdf"
    )
    if not source.is_file():
        pytest.skip("Local 2016 PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    q = data["questions"][31]
    assert [option["label"] for option in q["options"]] == list("ABCDE")
    assert q["raw"]["question_block"]
    merged = [
        asset
        for asset in q["visual_assets"]
        if "visual_multiple_option_images_merged:shared_geometry_requires_review"
        in asset["warnings"]
    ]
    assert merged and all(asset["belongs_to"] == "unknown" for asset in merged)
    assert any(
        "visual_multiple_option_images_merged:shared_geometry_requires_review"
        in row["reasons"]
        for row in collect_issues(data, tmp_path / "2016.raw.json")
        if row["question_number"] == 32
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
