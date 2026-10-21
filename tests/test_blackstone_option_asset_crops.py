"""Own/foreign-anchor recognition and lossless clean answer derivation."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.backtest import collect_issues
from parsers.blackstone.visual_structure import foreign_option_anchors
from parsers.blackstone.visuals import _graph_cell
from processors.normalization.blackstone import clean_dataset
from processors.normalization.blackstone.backtest import (
    inspect_question,
    render_inspection,
)
from processors.normalization.blackstone.issues import write_report
from processors.normalization.blackstone.option_assets import (
    derive_crop,
    is_image_option,
    prepare_option_assets,
)
from processors.normalization.blackstone.png_pixels import decode_png, encode_png
from processors.normalization.blackstone.storage import write_clean


@pytest.fixture
def letter_image(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()
    rows = [bytearray(b"\xff" * 120 * 3) for _ in range(100)]
    for left, top, right, bottom, color in [
        (8, 11, 14, 20, b"\x00" * 3),
        (31, 8, 32, 92, b"\x00" * 3),
        (31, 91, 111, 92, b"\x00" * 3),
        (2, 58, 10, 64, b"\x00" * 3),
        (60, 94, 80, 98, b"\x00" * 3),
        (50, 30, 70, 50, b"\x20\x80\xd0"),
    ]:
        for y in range(top, bottom):
            rows[y][left * 3 : right * 3] = color * (right - left)
    data = encode_png(120, 100, 3, rows)
    (root / "answer.png").write_bytes(data)
    asset = {
        "image_id": "answer",
        "path": "answer.png",
        "bbox": [0, 0, 120, 100],
        "graphic_bbox": [30, 7, 112, 93],
        "page": 1,
        "option_label": "A",
        "belongs_to": "option",
        "warnings": [],
        "pixel_size": [120, 100],
        "sha256": sha256(data).hexdigest(),
        "visual_text": [
            {"text": "A", "bbox": [6, 9, 16, 22]},
            {"text": "vertical axis", "bbox": [2, 58, 10, 64]},
            {"text": "days", "bbox": [60, 94, 80, 98]},
        ],
    }
    option = {
        "label": "A",
        "label_bbox": [6, 9, 16, 22],
        "page": 1,
        "content_type": "image",
        "text": "",
        "images": [asset],
    }
    anchors = [{"label": "A", "bbox": option["label_bbox"], "page": 1}]
    return (
        root / "case.raw.json",
        data,
        asset,
        option,
        anchors,
        {1: {"width": 120, "height": 100}},
    )


def test_lossless_crop_keeps_real_axes_even_left_of_anchor(letter_image):
    raw, original, asset, option, anchors, pages = letter_image
    before = deepcopy(asset)
    payload, meta = derive_crop(asset, option, anchors, raw, pages, 72)
    _, _, channels, source = decode_png(original)
    width, height, _, pixels = decode_png(payload)
    left, top, right, bottom = meta["pixel_crop_box"]
    x0, y0, x1, y1 = meta["removed_label_rect_px"]
    assert left < 2 and right >= 111 and bottom >= 98
    assert (width, height) == (right - left, bottom - top)
    for y in range(height):
        for x in range(width):
            px, py = x + left, y + top
            expected = (
                b"\xff" * channels
                if x0 <= px < x1 and y0 <= py < y1
                else source[py][px * channels : (px + 1) * channels]
            )
            assert pixels[y][x * channels : (x + 1) * channels] == expected
    assert pixels[11 - top][(8 - left) * 3 : (9 - left) * 3] == b"\xff" * 3
    assert asset == before and (raw.parent / asset["path"]).read_bytes() == original


@pytest.mark.parametrize(
    "problem",
    [
        "foreign",
        "multiple",
        "wrong_owner",
        "overlap_text",
        "ambiguous",
        "bad_coordinates",
    ],
)
def test_unsafe_derivation_is_rejected_not_silently_applied(letter_image, problem):
    raw, original, asset, option, anchors, pages = letter_image
    if problem in {"foreign", "multiple"}:
        anchors.append({"label": "B", "bbox": [70, 8, 78, 21], "page": 1})
        if problem == "multiple":
            anchors.append({"label": "C", "bbox": [90, 8, 98, 21], "page": 1})
    elif problem == "wrong_owner":
        asset["option_label"] = "B"
    elif problem == "overlap_text":
        asset["visual_text"].append({"text": "axis label", "bbox": [10, 10, 19, 20]})
    elif problem == "ambiguous":
        asset["warnings"] = ["visual_crop_may_be_incomplete"]
    else:
        pages[1]["width"] = 119.2
    with pytest.raises(ValueError):
        derive_crop(asset, option, anchors, raw, pages, 72)
    assert (raw.parent / asset["path"]).read_bytes() == original


def test_anchor_outside_crop_is_copied_without_pixel_changes(letter_image):
    raw, original, asset, option, anchors, _ = letter_image
    asset["bbox"] = [20, 0, 140, 100]
    payload, meta = derive_crop(asset, option, anchors, raw, {}, None)
    assert payload == original and meta["removed_label_rect_px"] is None


def test_original_cid_glyph_uses_trusted_anchor_geometry_without_text_decoding(
    letter_image,
):
    raw, original, asset, option, anchors, pages = letter_image
    asset["visual_text"][0]["text"] = "(cid:36)" * 8
    payload, metadata = derive_crop(asset, option, anchors, raw, pages, 72)
    assert metadata["removed_label_rect_px"] and payload != original
    assert asset["visual_text"][0]["text"] == "(cid:36)" * 8
    asset["visual_text"][0]["text"] = "B"
    with pytest.raises(ValueError, match="overlaps"):
        derive_crop(asset, option, anchors, raw, pages, 72)


def test_graph_cell_near_top_guide_still_enforces_neighbor_boundaries():
    anchors = [
        {"label": "A", "bbox": [40, 100, 48, 112], "page": 1, "label_only": True},
        {"label": "B", "bbox": [240, 100, 248, 112], "page": 1, "label_only": True},
        {"label": "C", "bbox": [40, 250, 48, 262], "page": 1, "label_only": True},
    ]
    assert _graph_cell({"bbox": [60, 98, 200, 220]}, anchors, 1)["label"] == "A"
    assert not foreign_option_anchors([35, 95, 205, 225], anchors, 1, "A")
    for box in ([60, 85, 200, 220], [60, 98, 260, 220], [60, 98, 200, 265]):
        assert _graph_cell({"bbox": box}, anchors, 1) is None


@pytest.mark.parametrize("problem", [None, "foreign", "multiple", "uncertain"])
def test_clean_references_html_and_missing_derived_asset_reporting(
    letter_image, tmp_path, problem
):
    raw, original, asset, option, _, pages = letter_image
    q = {
        "question_id": "q",
        "question_number": 1,
        "source_question_key": {"source": "blackstone", "year": 2024},
        "page_reference": {"start_page": 1, "end_page": 1},
        "question_text": "Which answer is correct?",
        "subpoints": [],
        "options": [option],
        "visual_assets": [asset],
        "visual_previews": [],
        "images": [],
        "warnings": [],
        "raw": {
            "question_block": "1 Which answer is correct?\nA",
            "options_block": "A",
        },
    }
    data = {
        "questions": [q],
        "input": {"filename": "example.pdf"},
        "pages": [{"page_number": 1, **pages[1]}],
        "extraction": {"visual_assets": {"dpi": 72}},
        "year": 2024,
    }
    if problem in {"foreign", "multiple"}:
        for label, x in [("B", 70), ("C", 90)][: 2 if problem == "multiple" else 1]:
            q["options"].append(
                {
                    "label": label,
                    "text": "A text choice",
                    "images": [],
                    "page": 1,
                    "label_bbox": [x, 8, x + 8, 21],
                }
            )
    elif problem == "uncertain":
        asset["warnings"] = ["visual_crop_may_be_incomplete:requires_review"]
    raw.write_text(json.dumps(data), encoding="utf-8")
    raw_bytes = raw.read_bytes()
    target = write_clean(clean_dataset(data, raw), tmp_path / "clean/case.clean.json")
    stored = json.loads(target.read_text(encoding="utf-8"))
    image = stored["questions"][0]["options"][0]["images"][0]
    if problem:
        assert "clean_asset" not in image
        result = inspect_question([target], source="example.pdf", question_number=1)
        assert any(
            i["code"] == "clean_option_crop_unresolved"
            for i in result["cleaning_issues"]
        )
        assert (
            "original raw asset shown without silent modification"
            in render_inspection(result, "html")
        )
        report = tmp_path / "issues.md"
        write_report([target], report)
        assert "## Clean Answer Image Derivation (1 records)" in report.read_text(
            encoding="utf-8"
        )
        assert stored["questions"][0]["raw_record"] == q
        assert (
            raw.read_bytes() == raw_bytes
            and (raw.parent / asset["path"]).read_bytes() == original
        )
        return
    assert (
        image["path"] == asset["path"]
        and image["clean_asset"]["raw_asset_path"] == asset["path"]
    )
    derived_path = target.parent / image["clean_asset"]["path"]
    assert derived_path.exists()
    result = inspect_question([target], source="example.pdf", question_number=1)
    answers = (
        render_inspection(result, "html")
        .split("id='main-answers'")[1]
        .split("</section>")[0]
    )
    assert image["clean_asset"]["path"] in answers and "Derived clean crop" in answers
    assert stored["questions"][0]["raw_record"] == q
    assert (raw.parent / asset["path"]).read_bytes() == original
    derived_path.unlink()
    assert any(
        i["code"] == "broken_clean_image_reference"
        for i in inspect_question([target], source="example.pdf", question_number=1)[
            "cleaning_issues"
        ]
    )
    report = tmp_path / "issues.md"
    write_report([target], report)
    assert "broken_clean_image_reference" in report.read_text(encoding="utf-8")
    assert raw.read_bytes() == raw_bytes


@pytest.fixture(scope="module")
def parsed_2017(tmp_path_factory):
    source = (
        Path(__file__).resolve().parents[1] / "acquisition/local/critical_thinking_problem_solving/tsa/TSA Oxford 2017.pdf"
    )
    if not source.exists():
        pytest.skip("Local PDF unavailable")
    root = tmp_path_factory.mktemp("2017_own_letter")
    data = parse_pdf(source, asset_dir=root / "assets")
    validate_raw(data)
    raw = root / "2017.raw.json"
    raw.write_text(json.dumps(data), encoding="utf-8")
    return data, raw


def test_2017_q20_complete_raw_options_and_clean_answer_derivatives(
    parsed_2017, tmp_path
):
    data, raw = parsed_2017
    q = data["questions"][19]
    assert [x["question_number"] for x in data["questions"]] == list(range(1, 51))
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert len(q["visual_assets"]) == 6
    assert all(
        o["content_type"] == "image" and len(o["images"]) == 1 for o in q["options"]
    )
    assert q["options"][0]["images"][0]["path"].endswith("asset_02_a77c5d40c9.png")
    assert not [i for i in collect_issues(data, raw) if i.get("question_number") == 20]
    original = {
        a["path"]: sha256((raw.parent / a["path"]).read_bytes()).hexdigest()
        for a in q["visual_assets"]
    }
    target = write_clean(clean_dataset(data, raw), tmp_path / "clean/2017.clean.json")
    stored = json.loads(target.read_text(encoding="utf-8"))["questions"][19]
    assert all("clean_asset" in o["images"][0] for o in stored["options"])
    assert not any(
        i["code"] == "clean_option_crop_unresolved" for i in stored["cleaning_issues"]
    )
    assert all(
        sha256((raw.parent / path).read_bytes()).hexdigest() == digest
        for path, digest in original.items()
    )


@pytest.mark.parametrize(
    "year,number",
    [(2021, 26), (2021, 32), (2022, 8), (2011, 50), (2013, 44), (2014, 8)],
)
def test_saved_correct_graph_table_and_diagram_options_keep_all_answer_pixels(
    year, number, tmp_path
):
    root = Path(__file__).resolve().parents[1] / "data/raw/blackstone"
    paths = list(root.glob(f"*{year}*.raw.json"))
    if not paths:
        pytest.skip("Generated local raw dataset unavailable")
    raw = paths[0]
    raw_bytes = raw.read_bytes()
    data = json.loads(raw_bytes)
    clean = clean_dataset(data, raw)
    clean["questions"] = [
        q for q in clean["questions"] if q["question_number"] == number
    ]
    output = tmp_path / f"{year}.clean.json"
    q = prepare_option_assets(clean, output)["questions"][0]
    assert [o["label"] for o in q["options"]] == [
        o["label"] for o in data["questions"][number - 1]["options"]
    ]
    assert [o["label"] for o in q["options"]] == list("ABCDE")
    assert all(o["content_type"] == "image" and not o["text"] for o in q["options"])
    if year == 2013:
        # Raw geometry now resolves the CID label row; cleaning must preserve
        # that upstream result rather than expect the old A/C/E misassociation.
        assert "incomplete_or_ambiguous_options:A,C,E" not in q["raw_warnings"]
    assert not any(
        i["code"] == "clean_option_crop_unresolved" for i in q["cleaning_issues"]
    )
    for option in q["options"]:
        asset = option["images"][0]
        if not is_image_option(option):
            assert (
                "clean_asset" not in asset
            )  # Never repair ambiguous mixed options here.
            continue
        derived = asset["clean_asset"]
        original = (raw.parent / asset["path"]).read_bytes()
        _, _, channels, rows = decode_png(original)
        _, _, _, result = decode_png((output.parent / derived["path"]).read_bytes())
        if derived["removed_label_rect_px"]:
            x0, y0, x1, y1 = derived["removed_label_rect_px"]
            for y in range(y0, y1):
                rows[y][x0 * channels : x1 * channels] = b"\xff" * (x1 - x0) * channels
        left, top, right, bottom = derived["pixel_crop_box"]
        assert result == [
            row[left * channels : right * channels] for row in rows[top:bottom]
        ]
        assert sha256(original).hexdigest() == asset["sha256"]
    assert raw.read_bytes() == raw_bytes
