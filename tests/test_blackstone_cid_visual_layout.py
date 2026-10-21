"""CID geometry regressions: raw bytes survive readable visual decisions."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_blackstone_visual_structure import spatial_line

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import (
    collect_issues,
    inspect_question,
    render_inspection,
)
from parsers.blackstone.image_options import image_choice_anchors
from parsers.blackstone.visual_structure import focused_crop, intersects
from processors.normalization.blackstone import clean_dataset, validate_clean

CASES = {
    2012: [8, 14, 26, 32, 44, 50],
    2013: [44],
    2014: [8, 14, 26, 32],
    "specimen": [36],
}


@pytest.fixture(scope="module")
def cid_papers(tmp_path_factory):
    root = tmp_path_factory.mktemp("cid_visuals")
    repo = Path(__file__).resolve().parents[1]
    result = {}
    for year in CASES:
        source = repo / f"acquisition/local/critical_thinking_problem_solving/tsa/TSA Oxford {year}.pdf"
        if not source.is_file():
            pytest.skip("Local PDF regression sources unavailable")
        raw = root / str(year) / f"{year}.raw.json"
        data = parse_pdf(source, asset_dir=raw.parent / "assets")
        validate_raw(data)
        raw.write_text(json.dumps(data), encoding="utf-8")
        clean = clean_dataset(data, raw)
        validate_clean(clean)
        result[year] = data, raw, clean
    return result


@pytest.mark.parametrize("year,number", [(y, n) for y, ns in CASES.items() for n in ns])
def test_cid_choice_groups_have_one_correct_anchor_and_image(cid_papers, year, number):
    data, raw, clean = cid_papers[year]
    q = data["questions"][number - 1]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert all(o["text"] == "" and o["content_type"] == "image" for o in q["options"])
    if isinstance(year, int):
        assert "text_option_candidates" in q["raw"]
    # Specimen Q36 already had correct text labels: deduplicating overprinted
    # anchors fixes association without replacing those text candidates.
    ids = []
    for option in q["options"]:
        assert len(option["images"]) == 1
        asset = option["images"][0]
        ids.append(asset["image_id"])
        assert (
            asset["option_label"] == option["label"] and asset["belongs_to"] == "option"
        )
        assert not asset["warnings"]
        assert option["label_bbox"][2] <= asset["graphic_bbox"][0] + 0.1
        for other in q["options"]:
            if other["label"] != option["label"] and other["page"] == asset["page"]:
                assert not intersects(asset["bbox"], other["label_bbox"])
    assert len(set(ids)) == 5
    if isinstance(year, int):
        assert "(cid:" in q["raw"]["options_block"]
    assert not [
        r for r in collect_issues(data, raw) if r.get("question_number") == number
    ]
    cleaned = clean["questions"][number - 1]
    assert [(o["label"], o["text"], len(o["images"])) for o in cleaned["options"]] == [
        (l, "", 1) for l in "ABCDE"
    ]
    assert cleaned["raw_record"] == q
    if year == 2012 and number == 8:
        # Clean now proves decoded/raw equality per span, including blank CID
        # lines. Incorrect/unverified encodings have separate negative coverage.
        assert "layout_alignment_unresolved" not in {
            i["code"] for i in cleaned["cleaning_issues"]
        }


def test_q8_focused_body_crop_excludes_prose_but_keeps_whole_visual(cid_papers):
    data, raw, _ = cid_papers[2012]
    q = data["questions"][7]
    asset = q["visual_assets"][0]
    assert asset["belongs_to"] == "question"
    prose = q["layout_blocks"][0]
    assert not intersects(asset["bbox"], prose["bbox"])
    assert asset["bbox"][1] < asset["graphic_bbox"][1]
    assert asset["bbox"][3] > asset["graphic_bbox"][3]
    assert asset["excluded_text_spans"]
    assert "Below are pictures of three cylinders." in q["question_text"]
    before = raw.read_bytes()
    result = inspect_question([raw], source="TSA Oxford 2012.pdf", question_number=8)
    html = render_inspection(result, "html")
    assert all(f"Answer option {label}" in html for label in "ABCDE")
    assert "data:image/png;base64," in html
    assert render_inspection(result, "text") and render_inspection(result, "json")
    assert raw.read_bytes() == before


def test_cid_prose_uses_readable_evidence_but_original_span_lengths():
    readable = "Below are pictures of three cylinders."
    original = "".join(f"(cid:{ord(c) - 29})" for c in readable)
    line = spatial_line(readable, 40, 74, [20] * 7, 19)
    line["text"] = original
    line["readable_text"] = readable
    crop, evidence = focused_crop({"bbox": [80, 98, 250, 250]}, [line], 1, 600, 800)
    assert crop[1] == 94
    assert evidence["excluded_text_spans"] == [{"start": 19, "end": 19 + len(original)}]


def test_shape_width_variation_requires_complete_label_only_region():
    # Different silhouettes can share height without sharing width. The complete
    # structural sequence and bijective geometry must still be present.
    question = {
        "raw": {"question_block": "A B C\nD E", "options_block": "A B C\nD E"},
        "options": [],
        "warnings": [],
    }
    lines = []
    groups = []
    for i, label in enumerate("ABCDE"):
        x, top = 50 + i % 3 * 160, 100 + i // 3 * 140
        line = spatial_line(label, x, top, [8], i * 2)
        lines.append(line)
        groups.append(
            {
                "bbox": [x + 18, top, x + 18 + (100 if i == 0 else 60), top + 90],
                "objects": [{"image_id": label}],
            }
        )
    before = deepcopy(question)
    assert len(image_choice_anchors(question, lines, {1: (groups, 600, 800)})) == 5
    assert all(o["text"] == "" for o in question["options"])
    # Meaningful external text disqualifies the relaxed shape-width evidence.
    lines.append(spatial_line("Meaningful answer text", 40, 400, [25, 25, 25], 12))
    assert not image_choice_anchors(before, lines, {1: (groups, 600, 800)})


def test_all_question_numbers_raw_spans_and_core_fields_survive(cid_papers):
    repo = Path(__file__).resolve().parents[1]
    baseline = repo / "inspections/critical_thinking_problem_solving/tsa/raw/cid_visual_baseline_20261014"
    for year, (data, _, _) in cid_papers.items():
        assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
        assert data["input"]["sha256"] and data["source"]
        for q in data["questions"]:
            parts = [
                data["pages"][s["page"] - 1]["raw_text"][s["start"] : s["end"]]
                for s in q["raw"]["page_spans"]
            ]
            assert "\n".join(parts) == q["raw"]["question_block"]
            for b in q["layout_blocks"]:
                if b["type"] == "text":
                    assert (
                        q["raw"]["question_block"][
                            b["raw_span"]["start"] : b["raw_span"]["end"]
                        ]
                        == b["text"]
                    )
        old_file = (
            next(baseline.glob(f"*{year}*.raw.json"), None)
            if baseline.exists()
            else None
        )
        if old_file:
            old = json.loads(old_file.read_text(encoding="utf-8"))
            assert [p["raw_text"] for p in data["pages"]] == [
                p["raw_text"] for p in old["pages"]
            ]
            for q, original in zip(data["questions"], old["questions"]):
                recovered_boundary = (
                    [o["label"] for o in original["options"]] != list("ABCDE")
                    and [o["label"] for o in q["options"]] == list("ABCDE")
                    and all(len(o["images"]) == 1 for o in q["options"])
                )
                for key in (
                    "question_id",
                    "source_question_key",
                    "page_reference",
                    "subpoints",
                ):
                    assert q[key] == original[key]
                for key in ("question_block", "page_spans"):
                    assert q["raw"][key] == original["raw"][key]
                if recovered_boundary:
                    assert original["question_text"] in q["question_text"]
                    assert (
                        q["raw"]["options_block"] in original["raw"]["question_block"]
                    )
                    assert all(
                        o["images"][0]["option_label"] == o["label"]
                        for o in q["options"]
                    )
                else:
                    assert q["question_text"] == original["question_text"]
                    assert q["raw"]["options_block"] == original["raw"]["options_block"]
                if q["question_number"] not in CASES[year] and not recovered_boundary:
                    assert [(o["label"], o["text"]) for o in q["options"]] == [
                        (o["label"], o["text"]) for o in original["options"]
                    ]
