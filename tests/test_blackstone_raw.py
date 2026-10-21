"""Raw extraction regressions using tiny PDFs and the available local papers."""

import json
import shutil
import socket
from copy import deepcopy
from pathlib import Path

import pdfplumber
import pytest

from parsers.blackstone import parse_pdf, validate_raw
from parsers.blackstone.__main__ import main
from parsers.blackstone.cid_text import decode_cids, supports_shifted_cids

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "acquisition/local/critical_thinking_problem_solving/tsa"


def write_pdf(
    path,
    pages,
    *,
    graphics=False,
    raster=False,
    graphics_commands=(),
    extra_resources="",
):
    """Build minimal ASCII test PDFs using only the standard library."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids = []
    if raster:
        pixels = bytes([255, 0, 0, 255, 255, 255, 0, 0, 255, 0, 255, 0])
        objects.append(
            b"<< /Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 12 >>\nstream\n"
            + pixels
            + b"\nendstream"
        )
    for lines in pages:
        commands = []
        for x, y, text in lines:
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"BT /F1 12 Tf {x} {y} Td ({escaped}) Tj ET")
        if graphics:
            commands.append("80 600 m 150 600 l S")
        if raster:
            commands.append("q 48 0 0 36 120 640 cm /Im1 Do Q")
        commands.extend(graphics_commands)
        content = "\n".join(commands).encode("ascii")
        page_id = len(objects) + 1
        page_ids.append(page_id)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 3 0 R >> {'/XObject << /Im1 4 0 R >>' if raster else ''} {extra_resources} >> /Contents {page_id + 1} 0 R >>".encode()
        )
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode()
            + content
            + b"\nendstream"
        )
    objects[1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] >>".encode()
    )
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010} 00000 n \n".encode())
    data.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(data)
    return path


@pytest.fixture
def tiny_pdf(tmp_path):
    cover = [
        (50, 750, "Thinking Skills Assessment 2024 Section 1"),
        (50, 720, "Instructions to Candidates"),
        (50, 690, "Attempt all 2 questions."),
    ]
    content = [
        (50, 740, "1 What follows?"),
        (80, 720, "A premise before the choices."),
        (100, 700, "1. First statement"),
        (100, 684, "2. Second statement"),
        (80, 660, "A First choice"),
        (110, 644, "continued choice"),
        (80, 620, "B Second choice"),
        (80, 600, "C Third choice"),
        (80, 580, "D Fourth choice"),
        (80, 560, "E Fifth choice"),
        (50, 500, "2 Which number?"),
        (80, 470, "A 10"),
        (80, 450, "B 20"),
        (80, 430, "D 40"),
        (80, 410, "E 50"),
        (250, 12, "Footer text must survive."),
    ]
    return write_pdf(tmp_path / "arbitrary-input.pdf", [cover, content], graphics=True)


def test_required_fields_numbering_options_and_subpoints(tiny_pdf):
    data = parse_pdf(tiny_pdf)
    validate_raw(data)
    assert data["source"] == "blackstone"
    assert data["year"] == 2024
    assert data["section"] == "section_1"
    assert data["acquisition"] == {"method": "unknown", "origin": None}
    assert [q["question_number"] for q in data["questions"]] == [1, 2]
    first, second = data["questions"]
    assert [o["label"] for o in first["options"]] == list("ABCDE")
    assert first["options"][0]["text"] == "First choice\ncontinued choice\n"
    assert "A premise before the choices." in first["question_text"]
    assert first["subpoints"] == [
        {"label": "1", "text": "First statement"},
        {"label": "2", "text": "Second statement"},
    ]
    assert "incomplete_or_ambiguous_options:A,B,D,E" in second["warnings"]
    assert first["images"] and first["images"][0]["kind"] == "vector"
    assert first["page_reference"] == {"start_page": 2, "end_page": 2}


def test_raw_pages_are_exact_backend_output_and_blocks_are_slices(tiny_pdf):
    data = parse_pdf(tiny_pdf)
    with pdfplumber.open(tiny_pdf) as pdf:
        assert [p["raw_text"] for p in data["pages"]] == [
            p.extract_text(layout=False) or "" for p in pdf.pages
        ]
    assert "Footer text must survive." in data["pages"][1]["raw_text"]
    assert (
        "Footer text must survive." not in data["questions"][1]["options"][-1]["text"]
    )
    broken = deepcopy(data)
    broken["questions"][0]["raw"]["question_block"] += "modified"
    with pytest.raises(ValueError, match="source page spans"):
        validate_raw(broken)
    assert json.loads(json.dumps(data)) == data


@pytest.mark.parametrize(
    "mutation", ["number", "source", "option_fields", "span", "dataset_fields"]
)
def test_validator_rejects_inconsistent_raw_records(tiny_pdf, mutation):
    data = parse_pdf(tiny_pdf)
    question = data["questions"][0]
    if mutation == "number":
        question["question_number"] = "1"
    elif mutation == "source":
        question["source_question_key"]["source"] = "other"
    elif mutation == "option_fields":
        del question["options"][0]["text"]
    elif mutation == "span":
        question["raw"]["page_spans"][0]["start"] = -1
    else:
        del data["input"]
    with pytest.raises(ValueError):
        validate_raw(data)


def test_question_can_continue_across_pages(tmp_path):
    path = write_pdf(
        tmp_path / "continued.pdf",
        [
            [(50, 740, "1 Long question"), (80, 700, "A First"), (80, 660, "B Second")],
            [
                (80, 740, "C Third"),
                (80, 700, "D Fourth"),
                (80, 660, "E Fifth"),
                (50, 600, "2 Next question"),
                (80, 560, "A Next A"),
                (80, 520, "B Next B"),
            ],
        ],
    )
    data = parse_pdf(path, metadata={"year": 2024, "section": "section_1"})
    first = data["questions"][0]
    assert first["page_reference"] == {"start_page": 1, "end_page": 2}
    assert [o["label"] for o in first["options"]] == list("ABCDE")
    assert len(first["raw"]["page_spans"]) == 2
    assert "2 Next question" not in first["raw"]["question_block"]


def test_grouped_graphical_labels_are_preserved_without_inventing_option_text(tmp_path):
    path = write_pdf(
        tmp_path / "graphs.pdf",
        [
            [
                (50, 740, "1 Choose the graph."),
                (80, 700, "A B C"),
                (100, 660, "graph annotation"),
                (80, 620, "D E"),
            ]
        ],
        graphics=True,
    )
    question = parse_pdf(path)["questions"][0]
    assert [option["label"] for option in question["options"]] == list("ABCDE")
    assert all(
        option["text"] == "" and option["warnings"] for option in question["options"]
    )
    assert "graph annotation" in question["raw"]["options_block"]
    assert (
        "multi_column_options:text_and_image_association_unresolved"
        in question["warnings"]
    )


def test_section_heading_takes_precedence_over_next_section_instructions(tmp_path):
    path = write_pdf(
        tmp_path / "sections.pdf",
        [
            [
                (50, 750, "Thinking Skills Assessment 2024"),
                (50, 720, "SECTION 1"),
                (50, 690, "Instructions to Candidates"),
                (50, 660, "Your supervisor will give out Section 2 later."),
                (50, 600, "1 Actual question"),
                (80, 560, "A One"),
            ]
        ],
    )
    assert parse_pdf(path)["section"] == "section_1"


def test_path_filename_and_acquisition_do_not_change_identity(
    tiny_pdf, tmp_path, monkeypatch
):
    def no_network(*args, **kwargs):
        raise AssertionError("Parser attempted network access")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    other = tmp_path / "renamed.pdf"
    shutil.copyfile(tiny_pdf, other)
    first = parse_pdf(tiny_pdf, acquisition={"method": "manual", "origin": "test"})
    second = parse_pdf(other, acquisition={"method": "archive", "origin": "another"})
    assert first["input"]["filename"] != second["input"]["filename"]
    assert first["input"]["sha256"] == second["input"]["sha256"]
    assert first["questions"] == second["questions"]


def test_unknown_metadata_and_no_text_are_not_invented(tmp_path):
    path = write_pdf(tmp_path / "TSA-2099.pdf", [[]], graphics=True)
    data = parse_pdf(path)
    assert data["year"] is None
    assert data["section"] is None
    assert data["document_role"] is None
    assert data["questions"] == []
    assert "no_questions_detected:full_page_text_preserved" in data["warnings"]
    assert "no_extractable_text:blank_or_scanned_page" in data["pages"][0]["warnings"]
    assert data["pages"][0]["images"]


def test_missing_metadata_retains_question_with_null_id(tmp_path):
    path = write_pdf(
        tmp_path / "unknown.pdf",
        [[(50, 740, "1 Detectable question"), (80, 700, "A Answer")]],
    )
    data = parse_pdf(path)
    question = data["questions"][0]
    assert question["question_id"] is None
    assert question["source_question_key"]["year"] is None
    assert "question_id_unavailable:uncertain_metadata" in question["warnings"]


def test_duplicate_numbers_and_count_mismatch_are_flagged(tiny_pdf, tmp_path):
    path = write_pdf(
        tmp_path / "duplicate.pdf",
        [
            [
                (50, 750, "Thinking Skills Assessment 2024 Section 1"),
                (50, 730, "Instructions to Candidates"),
                (50, 710, "Attempt all 3 questions."),
                (50, 660, "1 One"),
                (80, 640, "A Choice"),
                (50, 600, "1 Duplicate"),
                (80, 580, "A Choice"),
            ]
        ],
    )
    data = parse_pdf(path)
    assert len(data["questions"]) == 2
    assert "nonsequential_or_duplicate_question_numbers" in data["warnings"]
    assert "question_count_mismatch:expected_3_extracted_2" in data["warnings"]


def test_cli_discovers_by_content_and_prevents_overwrite(tiny_pdf, tmp_path, capsys):
    write_pdf(tmp_path / "other.PDF", [[(50, 740, "Unrelated document")]])
    output = tmp_path / "raw"
    assert main([str(tmp_path), "--output-dir", str(output)]) == 0
    assert "Skipped unrecognized" in capsys.readouterr().err
    files = list(output.glob("*.raw.json"))
    assert len(files) == 1
    original = files[0].read_bytes()
    assert main([str(tiny_pdf), "--output-dir", str(output)]) == 1
    assert files[0].read_bytes() == original
    assert main([str(tiny_pdf), "--output-dir", str(output), "--overwrite"]) == 0


def test_cli_reports_missing_inputs(tmp_path):
    assert (
        main([str(tmp_path / "absent.pdf"), "--output-dir", str(tmp_path / "raw")]) == 1
    )


@pytest.mark.skipif(
    not (LOCAL / "TSA Oxford 2020.pdf").exists(),
    reason="Local integration PDF unavailable",
)
def test_real_local_pdf():
    path = LOCAL / "TSA Oxford 2020.pdf"
    data = parse_pdf(path)
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    assert all(
        [o["label"] for o in q["options"]] == list("ABCDE") for q in data["questions"]
    )
    assert data["input"]["filename"] == path.name
    assert Path(data["input"]["path"]) == path.resolve()
    assert data["year"] == 2020 and data["section"] == "section_1"
    assert (
        data["extraction"]["pdf_metadata"]["Author"]
        == "Cambridge Assessment Admissions Testing"
    )
    assert len(data["pages"]) == 36
    with pdfplumber.open(path) as pdf:
        assert data["pages"][2]["raw_text"] == pdf.pages[2].extract_text(layout=False)
    assert "mental illness" in data["questions"][0]["raw"]["question_block"]
    assert any(q["images"] for q in data["questions"])


def test_shifted_cid_decoder_is_gated_and_preserves_unknown_glyphs():
    sample = "(cid:55)(cid:75)(cid:72)(cid:3)(cid:133)(cid:20)(cid:19)(cid:19)"
    assert supports_shifted_cids(sample * 4 + "(cid:87)(cid:75)(cid:72)", 43)
    assert not supports_shifted_cids("(cid:57)" * 31, 900)
    assert decode_cids(sample) == "The £100"
    assert decode_cids("(cid:131)(cid:177)(cid:182)(cid:999)") == "°–’(cid:999)"


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (
            2012,
            {
                3: ("When the government", "Farmers' profits"),
                4: ("One in ten adults", "Good piercers"),
                5: ("In the UK 45%", "Most women"),
            },
        ),
        (
            2013,
            {1: ("This week a controversial chef", "There is no logical difference")},
        ),
        (2014, {1: ("In the past 15 years", "If people do not gain")}),
    ],
)
def test_encoded_font_pdf_recovers_readable_fields_and_retains_raw_tokens(
    year, expected, tmp_path
):
    source = LOCAL / f"TSA Oxford {year}.pdf"
    if not source.is_file():
        pytest.skip("Local encoded PDF unavailable")
    data = parse_pdf(source, asset_dir=tmp_path / "assets")
    validate_raw(data)
    assert [q["question_number"] for q in data["questions"]] == list(range(1, 51))
    for number, (question_start, option_start) in expected.items():
        question = data["questions"][number - 1]
        assert question["question_text"].startswith(question_start)
        assert question["options"][0]["text"].startswith(option_start)
        assert [option["label"] for option in question["options"]] == list("ABCDE")
        assert "(cid:" in question["raw"]["question_block"]
        assert "(cid:" not in question["question_text"]
        assert all("(cid:" not in option["text"] for option in question["options"])
        assert any(
            "original CID tokens remain" in note
            for note in question["raw"]["extraction_notes"]
        )
        assert not any(
            "font_encoding_artifacts" in warning for warning in question["warnings"]
        )
    if year == 2013:
        from collections import Counter

        page_density = Counter(
            q["page_reference"]["start_page"] for q in data["questions"]
        )
        assert {1, 2, 3} <= set(page_density.values())
