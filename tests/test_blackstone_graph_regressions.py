"""Offline source-PDF controls for graph choices and transformed axis glyphs."""

import json
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import inspect_question, render_inspection
from parsers.blackstone.visual_inspection import read_png
from parsers.blackstone.visual_structure import foreign_option_anchors

SOURCE = Path(__file__).parents[1] / "acquisition/local/critical_thinking_problem_solving/tsa/TSA Oxford 2021.pdf"
SOURCE_2020 = Path(__file__).parents[1] / "acquisition/local/critical_thinking_problem_solving/tsa/TSA Oxford 2020.pdf"
Q32_OPTION_HASHES = [
    "30fc955314afeb2d2f86ec145a2549359c76dcd7bdb7fdbf0f25396f6c2552f6",
    "b4ddcf1e1676f964c116bcffc0a1cf232e90c1a949f9c2b699a9d9ef06ab664a",
    "1fab6d1b30a95fd9833a512cfe51c7579c2e5dd766d894120998315962f0d0d2",
    "5874c0af371de22fd5f82bd0278013d74b686e5f331aaefca826e9068d24490d",
    "9f30fc1c95503ffbbc31f14710fa880762da45a2158fd761e8e9034ee29cd365",
]


@pytest.fixture(scope="module")
def oxford_2021(tmp_path_factory):
    if not SOURCE.is_file():
        pytest.skip("Local TSA Oxford 2021 PDF is not available")
    folder = tmp_path_factory.mktemp("oxford_2021_graphs")
    data = parse_pdf(SOURCE, asset_dir=folder / "assets")
    validate_raw(data)
    raw = folder / "TSA Oxford 2021.raw.json"
    raw.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data, raw, {q["question_number"]: q for q in data["questions"]}


def test_q26_one_complete_graph_per_option(oxford_2021):
    data, raw, questions = oxford_2021
    q = questions[26]
    assert len(data["questions"]) == 50
    assert q["question_number"] == 26
    assert q["source_question_key"]["year"] == 2021
    assert q["raw"]["question_block"]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert len(q["visual_assets"]) == 6  # stimulus table + five answer graphs
    assert [o["images"][0]["asset_index"] for o in q["options"]] == [2, 3, 4, 5, 6]
    objects = {obj["image_id"]: obj for obj in q["images"]}
    for option in q["options"]:
        assert option["content_type"] == "image" and option["text"] == ""
        assert len(option["images"]) == 1
        asset = option["images"][0]
        assert asset["visual_kind"] == "graph"
        assert asset["option_label"] == option["label"]
        assert len(asset["object_ids"]) >= 6
        assert read_png(raw.parent / asset["path"])
        assert all(
            asset["graphic_bbox"][0] <= objects[image_id]["bbox"][0]
            and asset["graphic_bbox"][1] <= objects[image_id]["bbox"][1]
            and asset["graphic_bbox"][2] >= objects[image_id]["bbox"][2]
            and asset["graphic_bbox"][3] >= objects[image_id]["bbox"][3]
            for image_id in asset["object_ids"]
        )
        assert not foreign_option_anchors(
            asset["bbox"],
            [
                {
                    "label": letter["label"],
                    "bbox": letter["label_bbox"],
                    "page": letter["page"],
                }
                for letter in q["options"]
            ],
            asset["page"],
            option["label"],
        )
    assert q["options"][0]["images"][0]["graphic_bbox"][1] < 380
    assert q["options"][4]["images"][0]["graphic_bbox"][1] > 630


def test_q32_existing_table_option_crops_are_bit_identical(oxford_2021):
    _, _, questions = oxford_2021
    q = questions[32]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert all(len(o["images"]) == 1 for o in q["options"])
    assert [o["images"][0]["sha256"] for o in q["options"]] == Q32_OPTION_HASHES
    assert not any(a.get("visual_kind") == "graph" for a in q["visual_assets"])


@pytest.mark.parametrize(
    ("number", "y_label", "x_label", "corrupt"),
    [
        (37, "distance (km)", "day", ")mk(ecnatsid"),
        (38, "Number of people", "Year", "elpoep"),
    ],
)
def test_graph_axis_labels_are_complete_and_raw_is_preserved(
    oxford_2021, number, y_label, x_label, corrupt
):
    _, raw, questions = oxford_2021
    q = questions[number]
    asset = next(a for a in q["visual_assets"] if a.get("visual_kind") == "graph")
    labels = {(label["axis"], label["text"]) for label in asset["axis_labels"]}
    assert ("y", y_label) in labels and ("x", x_label) in labels
    assert y_label in [item["text"] for item in asset["visual_text"]]
    assert corrupt in q["raw"]["question_block"]
    assert corrupt in q["raw"]["text_question_candidate"]
    assert corrupt not in q["question_text"]
    assert q["raw"]["options_block"]
    assert q["source_question_key"]["year"] == 2021
    assert any(
        b["component"] == "visual_label" and corrupt in b.get("text", "")
        for b in q["layout_blocks"]
    )
    assert all(label["source_line_spans"] for label in asset["axis_labels"])
    assert read_png(raw.parent / asset["path"])


def test_graph_html_inspection_is_read_only_and_shows_corrected_axis(oxford_2021):
    _, raw, _ = oxford_2021
    digest = sha256(raw.read_bytes()).hexdigest()
    choices = inspect_question([raw], source=SOURCE.name, question_number=26, year=2021)
    choice_html = render_inspection(choices, "html")
    assert all(f"Answer option {letter}" in choice_html for letter in "ABCDE")
    assert choice_html.count("[image-based option]") == 5
    result = inspect_question([raw], source=SOURCE.name, question_number=37, year=2021)
    html = render_inspection(result, "html")
    assert "data:image/png;base64," in html
    assert "y: distance (km); x: day" in html
    assert (
        ")mk(ecnatsid"
        not in html.split("<h2>Stored question text</h2>")[1].split("</pre>")[0]
    )
    assert "FULL STORED QUESTION RECORD" in render_inspection(result, "text")
    assert '"axis_labels"' in render_inspection(result, "json")
    assert sha256(raw.read_bytes()).hexdigest() == digest


def test_other_year_rotated_graph_labels_are_not_lost(tmp_path):
    if not SOURCE_2020.is_file():
        pytest.skip("Local TSA Oxford 2020 PDF is not available")
    data = parse_pdf(SOURCE_2020, asset_dir=tmp_path / "assets")
    q = data["questions"][24]
    assert q["question_number"] == 25
    graphs = [a for a in q["visual_assets"] if a.get("visual_kind") == "graph"]
    assert len(graphs) == 2
    assert all(
        ("y", "Price") in {(l["axis"], l["text"]) for l in a["axis_labels"]}
        for a in graphs
    )
    assert all("Price" in [v["text"] for v in a["visual_text"]] for a in graphs)
    assert q["raw"]["question_block"] and q["raw"]["options_block"]
