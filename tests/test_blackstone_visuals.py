"""Saved raster/vector graphics, layout previews, and visual inspection QA."""

import json
import socket
from hashlib import sha256
from pathlib import Path

import pytest
from test_blackstone_raw import write_pdf

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import (
    collect_issues,
    inspect_question,
    main,
    render_inspection,
)
from parsers.blackstone.visual_inspection import read_png


@pytest.fixture
def visual_raw(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Visual extraction attempted network access")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    source = write_pdf(
        tmp_path / "visual.pdf",
        [
            [
                (50, 750, "Thinking Skills Assessment 2022 Section 1"),
                (50, 730, "Instructions to Candidates"),
                (50, 700, "1 Compare the diagram and image."),
                (80, 550, "A Choice one"),
                (80, 520, "B Choice two"),
                (80, 490, "C Choice three"),
                (80, 460, "D Choice four"),
                (80, 430, "E Choice five"),
            ]
        ],
        graphics=True,
        raster=True,
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    raw = tmp_path / "visual.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    return source, raw, data


def test_raster_and_vector_assets_are_saved_in_stable_order(visual_raw, tmp_path):
    source, raw, data = visual_raw
    validate_raw(data)
    question = data["questions"][0]
    assert [a["asset_index"] for a in question["visual_assets"]] == [1, 2]
    assert {
        kind for asset in question["visual_assets"] for kind in asset["detected_types"]
    } == {"raster", "vector"}
    assert (
        question["visual_assets"][0]["bbox"][1]
        < question["visual_assets"][1]["bbox"][1]
    )
    for asset in [*question["visual_assets"], *question["visual_previews"]]:
        assert asset["path"].endswith(".png")
        assert read_png(raw.parent / asset["path"])
        assert asset["question_number"] == 1 and asset["year"] == 2022
        assert asset["source_sha256"] == data["input"]["sha256"]
        assert asset["asset_type"].startswith("rendered_")
    assert all(image["path"] for image in question["images"])
    second = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert second["questions"] == data["questions"]


def test_universal_html_embeds_saved_assets_without_pdf_or_raw_mutation(
    visual_raw, tmp_path, capsys
):
    source, raw, data = visual_raw
    before = sha256(raw.read_bytes()).hexdigest()
    source.rename(tmp_path / "source-not-available-during-inspection.pdf")
    result = inspect_question([raw], source="visual.pdf", question_number=1)
    html = render_inspection(result, "html")
    assert "data:image/png;base64," in html
    assert "Question layout as saved during parsing" in html
    assert data["questions"][0]["raw"]["question_block"] in render_inspection(
        result, "text"
    )
    output = tmp_path / "inspections" / "question.html"
    assert (
        main(
            [
                "inspect",
                "--raw-json",
                str(raw),
                "--source",
                "visual.pdf",
                "--question",
                "1",
                "--format",
                "html",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert output.read_text(encoding="utf-8") == html
    assert sha256(raw.read_bytes()).hexdigest() == before
    assert (
        main(
            [
                "inspect",
                "--raw-json",
                str(raw),
                "--source",
                "visual.pdf",
                "--question",
                "1",
            ]
        )
        == 0
    )
    assert "FULL STORED QUESTION RECORD" in capsys.readouterr().out


def test_missing_asset_is_reported_and_html_displays_a_notice(visual_raw):
    _, raw, data = visual_raw
    asset = data["questions"][0]["visual_assets"][0]
    (raw.parent / asset["path"]).unlink()
    rows = collect_issues(data, raw)
    assert any("visual_asset_file_missing" in row["reasons"] for row in rows)
    assert any(asset["path"] in row["asset_paths"] for row in rows)
    result = inspect_question([raw], source="visual.pdf", question_number=1)
    assert "Visual unavailable" in render_inspection(result, "html")
    assert "visual_asset_file_missing" in render_inspection(result, "text")


def test_invalid_png_and_coordinates_are_reported(visual_raw):
    _, raw, data = visual_raw
    asset = data["questions"][0]["visual_assets"][0]
    (raw.parent / asset["path"]).write_bytes(b"broken png")
    asset["bbox"] = [-10, 0, 100, 100]
    rows = collect_issues(data, raw)
    reasons = [reason for row in rows for reason in row["reasons"]]
    assert "visual_invalid_bbox" in reasons
    assert "visual_asset_not_displayable:invalid_png" in reasons


def test_image_only_option_regions_are_saved_and_associated(tmp_path):
    source = write_pdf(
        tmp_path / "options.pdf",
        [
            [
                (50, 740, "1 Select a picture."),
                (80, 700, "A First"),
                (80, 625, "B"),
                (80, 580, "C Third"),
                (80, 530, "D Fourth"),
                (80, 480, "E Fifth"),
            ]
        ],
        graphics_commands=["110 625 m 180 625 l S"],
    )
    data = parse_pdf(
        source,
        metadata={"year": 2022, "section": "section_1"},
        asset_dir=tmp_path / "assets",
    )
    option = data["questions"][0]["options"][1]
    assert option["label"] == "B" and option["text"].strip() == ""
    assert option["images"]
    assert all((tmp_path / asset["path"]).exists() for asset in option["images"])


def test_renderer_failure_keeps_raw_records_and_reports_the_problem(
    tmp_path, monkeypatch
):
    from parsers.blackstone import visuals

    source = write_pdf(
        tmp_path / "failure.pdf",
        [[(50, 740, "1 Question"), (80, 700, "A Choice")]],
        graphics=True,
    )

    def failure(*args, **kwargs):
        raise ValueError("renderer unavailable")

    monkeypatch.setattr(visuals.pdfium, "PdfDocument", failure)
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert data["questions"][0]["raw"]["question_block"]
    assert any(
        w.startswith("visual_save_failed:") for w in data["questions"][0]["warnings"]
    )
    assert collect_issues(data, tmp_path / "failure.raw.json")


def test_html_also_works_for_questions_without_graphics(tmp_path):
    source = write_pdf(
        tmp_path / "text.pdf",
        [[(50, 740, "1 Ordinary question"), (80, 700, "A A text option")]],
    )
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    assert data["questions"][0]["visual_assets"] == []
    assert data["questions"][0]["visual_previews"][0]["path"]
    raw = tmp_path / "text.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_question([raw], source="text.pdf", question_number=1)
    assert "data:image/png;base64," in render_inspection(result, "html")


def test_coordinate_mismatch_saves_flagged_full_page_fallback(tmp_path, monkeypatch):
    from parsers.blackstone import visuals

    source = write_pdf(
        tmp_path / "mismatch.pdf",
        [[(50, 740, "1 Question"), (80, 700, "A Choice")]],
        graphics=True,
    )
    original = visuals.pdfium.PdfPage.get_size

    def mismatched_size(page):
        width, height = original(page)
        return width + 5, height + 5

    monkeypatch.setattr(visuals.pdfium.PdfPage, "get_size", mismatched_size)
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][0]
    assert question["raw"]["question_block"]
    assert question["visual_previews"] and question["visual_assets"]
    assert all(read_png(tmp_path / a["path"]) for a in question["visual_assets"])
    assert any(
        w.startswith("visual_coordinate_space_mismatch:") for w in question["warnings"]
    )
    assert question["visual_assets"][0]["belongs_to"] == "unknown"
    assert collect_issues(data, tmp_path / "mismatch.raw.json")


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1] / "acquisition/local/TSA_2022.pdf"
    ).exists(),
    reason="Local PDF unavailable",
)
def test_tsa_2022_question_50_vector_graphic(tmp_path):
    source = Path(__file__).resolve().parents[1] / "acquisition/local/TSA_2022.pdf"
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    question = data["questions"][49]
    assert question["question_number"] == 50
    assert question["visual_assets"]
    assert any(
        "vector" in asset["detected_types"] for asset in question["visual_assets"]
    )
    assert all(
        (tmp_path / asset["path"]).exists() for asset in question["visual_assets"]
    )
    assert [o["label"] for o in question["options"]] == list("ABCDE")
    # This previously good crop must still preserve all towns and five sign tables.
    assert len(question["visual_assets"]) == 6
    first = question["visual_assets"][0]
    label_lines = "\n".join(
        question["raw"]["question_block"][s["start"] : s["end"]]
        for s in first["included_text_spans"]
    )
    assert "Queensgate" in label_lines and "Tunborough" in label_lines
    for asset in question["visual_assets"]:
        crop, graphic = asset["bbox"], asset["graphic_bbox"]
        assert crop[0] <= graphic[0] and crop[1] <= graphic[1]
        assert crop[2] >= graphic[2] and crop[3] >= graphic[3]
    # Concrete 2022 regressions: short prose ending, legend bleeding, and
    # rotated chart labels being stolen by the following answer chart.
    q8, q20 = data["questions"][7], data["questions"][19]
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    assert [o["label"] for o in q8["options"]] == list("ABCDE")
    assert all(o["content_type"] == "image" and o["text"] == "" for o in q8["options"])
    assert len(q8["visual_assets"]) == 7
    assert q8["visual_assets"][1]["bbox"][3] < 311  # key excludes chart B
    assert q8["visual_assets"][1]["option_label"] is None
    for option in q8["options"]:
        assert len(option["images"]) == 1
        asset = option["images"][0]
        assert asset["option_label"] == option["label"]
        assert asset["placement"]["component"] == "option"
        assert asset["page"] == option["page"] == 7
        assert not asset["warnings"]
        assert asset["visual_text"]
    assert q8["options"][2]["images"][0]["bbox"][1] > 460.84
    assert q8["options"][4]["images"][0]["bbox"][1] > 614.68
    assert q8["options"][2]["images"][0]["bbox"][3] >= 614.68
    assert q8["options"][4]["images"][0]["bbox"][3] >= 768.64
    assert "A 100 B 100" in q8["raw"]["options_block"]
    assert q8["raw"]["text_option_candidates"][0]["text"].startswith("100 B 100")
    assert q20["visual_assets"][1]["bbox"][1] > 236.95
    assert "been incorrectly plotted." in q20["raw"]["question_block"]
    assert [o["text"].strip() for o in q20["options"]] == [
        "Ffion",
        "Gary",
        "Huw",
        "Ken",
        "Mei",
    ]
    for q in (q8, q20):
        for a in q["visual_assets"]:
            for other in q["visual_assets"]:
                if a is other:
                    continue
                b, g = a["bbox"], other["graphic_bbox"]
                assert b[2] <= g[0] or b[0] >= g[2] or b[3] <= g[1] or b[1] >= g[3]
    raw = tmp_path / "2022.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    before = raw.read_bytes()
    result = inspect_question([raw], source="TSA_2022.pdf", question_number=8)
    html = render_inspection(result, "html")
    visible = html.split("<summary>Full stored question record</summary>")[0]
    assert "A 100 B 100" not in visible and "[image-based option]" in visible
    assert all(f"Answer option {label}" in visible for label in "ABCDE")
    assert render_inspection(result, "json") and render_inspection(result, "text")
    assert raw.read_bytes() == before
    assert not [
        r for r in collect_issues(data, raw) if r.get("question_number") in (8, 20)
    ]
