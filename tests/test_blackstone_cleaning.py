"""Independent clean-stage regressions using raw JSON, never PDF extraction."""

import json
import socket
import struct
import zlib
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from processors.normalization.blackstone import clean_dataset, validate_clean
from processors.normalization.blackstone.__main__ import main as clean_main
from processors.normalization.blackstone.backtest import (
    inspect_question,
    main,
    render_inspection,
)
from processors.normalization.blackstone.issues import write_report
from processors.normalization.blackstone.storage import write_clean
from processors.normalization.blackstone.text import normalize_text


def png_bytes():
    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
        + chunk(
            b"IDAT",
            zlib.compress(
                b"\x00" + b"\xff\x00\x00" * 2 + b"\x00" + b"\xff\x00\x00" * 2
            ),
        )
        + chunk(b"IEND", b"")
    )


@pytest.fixture
def raw_case(tmp_path):
    directory = tmp_path / "raw"
    directory.mkdir()
    assets = directory / "assets"
    assets.mkdir()
    for name in ("body", "answer", "view"):
        (assets / f"{name}.png").write_bytes(png_bytes())

    def asset(name, owner, label=None):
        return {
            "image_id": name,
            "path": f"assets/{name}.png",
            "page": 3,
            "asset_index": 1,
            "bbox": [100, 100, 200, 150],
            "graphic_bbox": [100, 100, 200, 150],
            "belongs_to": owner,
            "option_label": label,
            "warnings": [],
            "object_ids": [],
        }

    body, answer, view = (
        asset("body", "question"),
        asset("answer", "option", "A"),
        asset("view", "question"),
    )
    view["asset_type"] = "rendered_question"
    body["placement"] = {"component": "intermediate"}
    text = "Some  background text that wraps\nonto another line.\nA second context paragraph.\nWhich answer fits the\ninformation given?\n"
    raw_text = "12 " + text + "A\nB Text choice\n"
    lines = raw_text.splitlines()
    blocks, offset = [], 0
    for index, line in enumerate(lines):
        blocks.append(
            {
                "block_id": f"t{index}",
                "type": "text",
                "component": "stimulus"
                if index < 3
                else "question_body"
                if index < 5
                else "option",
                "text": line,
                "page": 3,
                "bbox": [50, index * 20, 500, index * 20 + 12],
                "raw_span": {"start": offset, "end": offset + len(line)},
            }
        )
        offset += len(line) + 1
    blocks.insert(
        3,
        {
            "block_id": "body-picture",
            "type": "visual",
            "component": "intermediate",
            "asset_id": "body",
            "page": 3,
            "bbox": [100, 100, 200, 150],
        },
    )
    blocks.append(
        {
            "block_id": "answer-picture",
            "type": "visual",
            "component": "option",
            "label": "A",
            "asset_id": "answer",
            "page": 3,
            "bbox": [100, 200, 200, 250],
        }
    )
    for i, block in enumerate(blocks, 1):
        block["order"] = i
    question = {
        "question_id": "blackstone_2024_section_1_q12",
        "question_number": 12,
        "source_question_key": {
            "source": "blackstone",
            "year": 2024,
            "section": "section_1",
            "question_number": 12,
        },
        "question_text": text,
        "raw": {
            "question_block": raw_text,
            "options_block": "A\nB Text choice\n",
            "extraction_notes": [],
        },
        "page_reference": {"start_page": 3, "end_page": 3},
        "subpoints": [],
        "options": [
            {
                "label": "A",
                "text": "",
                "content_type": "image",
                "label_bbox": [80, 100, 90, 112],
                "page": 3,
                "images": [deepcopy(answer)],
            },
            {
                "label": "B",
                "text": "This longer choice has a\ncontinuation on another line.\n",
                "images": [],
            },
        ],
        "visual_assets": [body, answer],
        "visual_previews": [view],
        "images": [],
        "layout_blocks": blocks,
        "warnings": ["visual_crop_may_be_incomplete:requires_review"],
        "answer": None,
        "custom_unresolved_field": {"retain": True},
    }
    dataset = {
        "source": "blackstone",
        "year": 2024,
        "session": None,
        "section": "section_1",
        "input": {
            "filename": "example.pdf",
            "path": "original/example.pdf",
            "sha256": "a" * 64,
        },
        "warnings": ["source_assigned_by_parser_profile:not_verified_in_document"],
        "questions": [question],
        "pages": [],
    }
    path = directory / "example.raw.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    return path, dataset


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Some   text\t here. \r\n", "Some text here."),
        (
            "This prose line has several\nwords continuing its sentence.",
            "This prose line has several words continuing its sentence.",
        ),
        ("Paragraph one.\n\n\nParagraph two.", "Paragraph one.\n\nParagraph two."),
        ("cafe\u0301", "café"),
        ("A\u030angstro\u0308m", "Ångström"),
        (
            "1. First statement\n2. Second statement",
            "1. First statement\n2. Second statement",
        ),
        ("Jan 2012 124.1\nFeb 2012 61.4", "Jan 2012 124.1\nFeb 2012 61.4"),
        ("A valid sentence.", "A valid sentence."),
        ("5 × 10 − 2 = 48; ½ £", "5 × 10 − 2 = 48; ½ £"),
        (
            "First long line ends with-\nhyphenated content",
            "First long line ends with-\nhyphenated content",
        ),
        ("number of people\n0 10 20", "number of people\n0 10 20"),
    ],
)
def test_conservative_text_rules(raw, expected):
    assert normalize_text(raw) == expected
    assert normalize_text(expected) == expected


def test_immutable_traceable_deterministic_cleaning(raw_case, monkeypatch):
    path, dataset = raw_case
    original = deepcopy(dataset)
    before = path.read_bytes()

    def forbidden(*args, **kwargs):
        raise AssertionError("Cleaning attempted network/PDF extraction")

    import pdfplumber
    import pypdfium2

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(pdfplumber, "open", forbidden)
    monkeypatch.setattr(pypdfium2, "PdfDocument", forbidden)
    clean = clean_dataset(dataset, path)
    validate_clean(clean)
    assert clean == clean_dataset(dataset, path)
    assert dataset == original and path.read_bytes() == before
    q = clean["questions"][0]
    assert q["raw_record"] == original["questions"][0]
    assert q["raw_reference"]["sha256"] == sha256(before).hexdigest()
    assert q["raw_reference"]["json_pointer"] == "/questions/0"
    assert q["question_id"] == original["questions"][0]["question_id"]
    assert q["visual_assets"] == original["questions"][0]["visual_assets"]
    assert q["options"][0] == original["questions"][0]["options"][0]
    assert (
        q["options"][1]["text"]
        == "This longer choice has a continuation on another line."
    )
    assert q["raw_warnings"] == original["questions"][0]["warnings"]
    assert q["raw_document_warnings"] == original["warnings"]
    assert q["main_question"] == "Which answer fits the information given?"
    assert [b["type"] for b in q["main_body"]] == ["text", "visual"]
    assert (
        "Some background text that wraps onto another line."
        in q["main_body"][0]["text"]
    )
    assert not q["cleaning_issues"]  # Raw warnings are not blindly copied.


def test_null_empty_subpoints_and_unknown_fields_remain_traceable(raw_case):
    path, data = raw_case
    q = data["questions"][0]
    q["subpoints"] = [
        {"label": "1", "text": "  First  statement "},
        {"label": "2", "text": "Second statement"},
    ]
    q["options"][1]["text"] = None
    result = clean_dataset(data, path)["questions"][0]
    assert result["subpoints"] == [
        {"label": "1", "text": "First statement"},
        {"label": "2", "text": "Second statement"},
    ]
    assert result["options"][1]["text"] is None
    assert "text" in result["availability"]["raw_options"][1]["null_fields"]
    assert "answer" in result["availability"]["raw"]["null_fields"]
    assert "explanation" in result["availability"]["raw"]["missing_fields"]
    assert "images" in result["availability"]["raw"]["empty_fields"]
    assert "session" in result["availability"]["metadata"]["null_fields"]
    assert result["raw_record"]["custom_unresolved_field"] == {"retain": True}


def test_ambiguous_prompt_encoding_and_mapping_are_not_repaired(raw_case):
    path, data = raw_case
    q = data["questions"][0]
    q["question_text"] = "Which object?\nWhat position?\n(cid:66)\n:\n"
    result = clean_dataset(data, path)["questions"][0]
    codes = {i["code"] for i in result["cleaning_issues"]}
    assert {
        "ambiguous_body_question_split",
        "encoding_artifact_unresolved",
        "isolated_symbol_ordering_unresolved",
        "layout_alignment_unresolved",
    } <= codes
    assert result["main_question"] is None
    assert (
        "(cid:66)" in result["question_text"]
        and "\n:\n" in result["question_text"] + "\n"
    )
    assert result["raw_warnings"] == q["warnings"]


def test_html_all_sections_images_and_original_screenshot_are_present(
    raw_case, tmp_path
):
    raw, data = raw_case
    clean = clean_dataset(data, raw)
    path = write_clean(clean, tmp_path / "clean/example.clean.json")
    raw_before, clean_before = raw.read_bytes(), path.read_bytes()
    result = inspect_question(
        [path.parent], source="example.pdf", year=2024, question_number=12
    )
    html = render_inspection(result, "html")
    for heading in (
        "Main Body",
        "Main Question",
        "Main Answers",
        "Original Screenshot",
        "Source / Document Metadata",
        "Missing / Null Field Availability",
        "Visual Inspection Issues",
    ):
        assert f"<h2>{heading}</h2>" in html
    assert html.count("data:image/png;base64,") == 3
    body = html.split("<section id='main-body'>")[1].split("</section>")[0]
    assert "Some background text" in body and "Body context graphic" in body
    assert "Which answer" not in body and "<h2>Passage</h2>" not in html
    assert "preserved_raw_warnings" in html and "requires_review" in html
    assert render_inspection(result, "text") and json.loads(
        render_inspection(result, "json")
    )
    assert raw.read_bytes() == raw_before and path.read_bytes() == clean_before
    assert (
        main(
            [
                "inspect",
                "--clean-json",
                str(path),
                "--source",
                "example.pdf",
                "--question",
                "12",
                "--format",
                "html",
                "--output",
                str(tmp_path / "clean-preview.html"),
            ]
        )
        == 0
    )


def test_missing_asset_is_detected_without_copying_all_raw_issues(raw_case, tmp_path):
    raw, data = raw_case
    clean = clean_dataset(data, raw)
    path = write_clean(clean, tmp_path / "clean/example.clean.json")
    (raw.parent / "assets/body.png").unlink()
    result = inspect_question([path], source="example.pdf", question_number=12)
    assert any(i["code"] == "broken_image_reference" for i in result["cleaning_issues"])
    assert "Image unavailable" in render_inspection(result, "html")
    report = tmp_path / "clean-issues.md"
    write_report([path], report)
    text = report.read_text(encoding="utf-8")
    assert "## Broken Image References (1 records)" in text
    assert "assets/body.png" in text and "/questions/0" in text
    assert "requires_review" not in text
    assert write_report([path], report) == 1


def test_clean_output_cannot_overwrite_raw_or_unrelated_files(raw_case, tmp_path):
    raw, data = raw_case
    clean = clean_dataset(data, raw)
    before = raw.read_bytes()
    with pytest.raises(ValueError, match="outside raw"):
        write_clean(clean, raw, overwrite=True)
    with pytest.raises(ValueError, match="outside raw"):
        write_clean(clean, raw.parent / "new.clean.json")
    path = tmp_path / "clean/example.clean.json"
    write_clean(clean, path)
    with pytest.raises(FileExistsError):
        write_clean(clean, path)
    write_clean(clean, path, overwrite=True)
    manual = tmp_path / "clean/manual.clean.json"
    manual.write_text('{"manual":true}', encoding="utf-8")
    with pytest.raises(ValueError):
        write_clean(clean, manual, overwrite=True)
    assert raw.read_bytes() == before


def test_clean_cli_and_report_are_independent(raw_case, tmp_path):
    raw, _ = raw_case
    before = raw.read_bytes()
    output = tmp_path / "clean"
    report = tmp_path / "cleaning.md"
    args = [
        "--raw-json",
        str(raw),
        "--output-dir",
        str(output),
        "--issues-report",
        str(report),
    ]
    assert clean_main(args) == 0
    assert len(list(output.glob("*.clean.json"))) == 1
    assert "No clean-stage issues" in report.read_text(encoding="utf-8")
    assert clean_main([*args, "--overwrite"]) == 0
    assert raw.read_bytes() == before


def test_body_paragraph_boundaries_are_not_lost(raw_case):
    raw, data = raw_case
    q = data["questions"][0]
    q.pop("layout_blocks")
    q["visual_assets"] = []
    q["question_text"] = (
        "First background paragraph.\n\nSecond background paragraph.\nWhich answer fits?"
    )
    clean = clean_dataset(data, raw)["questions"][0]
    assert (
        clean["main_body"][0]["text"]
        == "First background paragraph.\n\nSecond background paragraph."
    )


def test_unknown_visual_is_preserved_without_option_reassignment(raw_case):
    raw, data = raw_case
    question = data["questions"][0]
    question["visual_assets"][0]["belongs_to"] = "unknown"
    question["visual_assets"][0]["placement"] = {"component": "unknown"}
    clean = clean_dataset(data, raw)["questions"][0]
    assert any(
        i["code"] == "visual_placement_unresolved" for i in clean["cleaning_issues"]
    )
    assert clean["visual_assets"][0] == question["visual_assets"][0]
    assert clean["options"][0]["images"] == question["options"][0]["images"]


def test_missing_option_structure_is_not_fabricated(raw_case):
    raw, data = raw_case
    data["questions"][0]["options"] = None
    clean = clean_dataset(data, raw)["questions"][0]
    assert clean["options"] is None
    assert "options" in clean["availability"]["raw"]["null_fields"]
    assert any(
        i["code"] == "option_structure_unavailable" for i in clean["cleaning_issues"]
    )


def test_clean_report_cannot_replace_raw_issue_report(raw_case, tmp_path):
    raw, data = raw_case
    path = write_clean(clean_dataset(data, raw), tmp_path / "clean/example.clean.json")
    report = tmp_path / "RAW_PARSING_ISSUES.md"
    original = "<!-- blackstone-raw-backtest-report -->\nUnresolved raw findings\n"
    report.write_text(original, encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_report([path], report)
    assert report.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    ("year", "number"),
    [(2012, 3), (2017, 20), (2022, 8), (2021, 32), (2021, 37), (2020, 12)],
)
def test_representative_local_records_preserve_raw_structure_and_images(year, number):
    root = Path(__file__).resolve().parents[1] / "data/raw/blackstone"
    paths = list(root.glob(f"*{year}*.raw.json"))
    if not paths:
        pytest.skip("Generated raw records unavailable")
    path = paths[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    before = path.read_bytes()
    clean = clean_dataset(data, path)
    q, raw = clean["questions"][number - 1], data["questions"][number - 1]
    assert q["main_question"] and "?" in q["main_question"]
    assert q["question_number"] == raw["question_number"]
    assert q["raw_record"] == raw and path.read_bytes() == before
    assert q["visual_assets"] == raw["visual_assets"]
    assert [o["label"] for o in q["options"]] == [o["label"] for o in raw["options"]]
    if (year, number) in ((2022, 8), (2021, 32)):
        assert all(
            o["content_type"] == "image" and o["text"] == "" and len(o["images"]) == 1
            for o in q["options"]
        )
    if (year, number) == (2012, 3):
        assert "(cid:" not in q["main_question"]
    if (year, number) == (2020, 12):
        assert any(
            i["code"] == "isolated_symbol_ordering_unresolved"
            for i in q["cleaning_issues"]
        )
