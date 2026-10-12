"""Small, offline regressions for chart text ownership and option recovery."""

import json

import pytest
from test_blackstone_raw import write_pdf
from test_blackstone_visual_structure import spatial_line

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import collect_issues
from parsers.blackstone.visual_structure import focused_crop


def test_wrapped_short_paragraph_end_is_not_a_caption():
    lines = [
        spatial_line(
            "The following graph shows the values but one point has", 40, 60, [15] * 11
        ),
        spatial_line("been incorrectly plotted.", 40, 74, [20, 38, 30], 65),
    ]
    crop, evidence = focused_crop({"bbox": [80, 98, 250, 250]}, lines, 1, 600, 800)
    assert crop[1] == 94
    assert evidence["excluded_text_spans"] == [{"start": 65, "end": 90}]


def test_neighbor_owns_axis_text_and_padding_cannot_cross_graphic():
    legend = {"bbox": [100, 100, 250, 140]}
    chart = {"bbox": [100, 147, 250, 250]}
    lines = [spatial_line("100", 75, 145, [21])]
    crop, _ = focused_crop(legend, lines, 1, 600, 800, [legend, chart])
    assert crop == [96, 96, 254, 144]
    crop, evidence = focused_crop(chart, lines, 1, 600, 800, [legend, chart])
    assert crop[0] == 71 and crop[1] > legend["bbox"][3]
    assert evidence["included_text_spans"]


def chart_fixture(tmp_path, outside_text=False):
    lines = [(50, 740, "1 Which chart shows the correct values?")]
    graphics = []
    for i, label in enumerate("ABCDE"):
        x, y = 80 + (i % 2) * 240, 650 - (i // 2) * 170
        lines.extend([(x, y, label), (x + 23, y, "100"), (x + 30, y - 90, "0")])
        graphics.append(f"{x + 45} {y - 90} 140 90 re S")
        graphics.append(
            f"BT /F1 12 Tf 0.707 -0.707 0.707 0.707 {x + 45} {y - 102} Tm (2019) Tj ET"
        )
    if outside_text:
        lines.append((80, 700, "Unrelated introduction."))
        lines.append((80, 510, "Genuine answer text outside the chart."))
    source = write_pdf(tmp_path / "charts.pdf", [lines], graphics_commands=graphics)
    return parse_pdf(
        source,
        metadata={"year": 2022, "section": "section_1"},
        asset_dir=tmp_path / "assets",
    )


def test_repeated_charts_recover_missing_labels_and_preserve_internal_text(tmp_path):
    data = chart_fixture(tmp_path)
    validate_raw(data)
    q = data["questions"][0]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert [a["option_label"] for a in q["visual_assets"]] == list("ABCDE")
    assert all(
        o.get("content_type") == "image" and o["text"] == "" for o in q["options"]
    )
    assert all(
        len(o["images"]) == 1 and o["images"][0]["visual_text"] for o in q["options"]
    )
    assert "A 100 B 100" in q["raw"]["options_block"]
    assert [o["label"] for o in q["raw"]["text_option_candidates"]] == list("ACE")
    assert q["raw"]["question_block"] in data["pages"][0]["raw_text"]
    raw = tmp_path / "charts.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    assert not [r for r in collect_issues(data, raw) if r["scope"] == "question"]
    q["options"][0]["images"] = []
    issues = collect_issues(data, raw)
    assert "visual_image_option_mapping_inconsistent:A" in str(issues)


def test_external_answer_text_blocks_image_only_classification(tmp_path):
    data = chart_fixture(tmp_path, outside_text=True)
    q = data["questions"][0]
    assert not any(o.get("content_type") == "image" for o in q["options"])
    assert all(a["belongs_to"] == "unknown" for a in q["visual_assets"])
    assert "Genuine answer text" in q["raw"]["options_block"]
    assert "visual_image_option_association_uncertain:outside_text" in q["warnings"]
    assert "visual_image_option_association_uncertain:outside_text" in str(
        collect_issues(data, tmp_path / "charts.raw.json")
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_crop_result_does_not_depend_on_neighbor_iteration_order(reverse):
    groups = [{"bbox": [100, 100, 230, 200]}, {"bbox": [280, 100, 410, 200]}]
    line = spatial_line("100", 255, 100, [21])
    order = list(reversed(groups)) if reverse else groups
    crop, _ = focused_crop(groups[0], [line], 1, 600, 800, order)
    assert crop == [96, 96, 234, 204]
