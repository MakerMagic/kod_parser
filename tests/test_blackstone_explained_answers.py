"""Independent 2021/2022 source layout, visuals and generic matching integration."""

import json
import re
import socket
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from test_blackstone_raw import write_pdf
from test_matching import match_case as shared_matching_case

from parsers.blackstone.visual_inspection import read_png
from parsers.blackstone_explained_answers import parse_pdf, validate_answers
from parsers.blackstone_explained_answers.__main__ import main as parse_main
from processors.matching.__main__ import main as match_main
from processors.matching.backtest import inspect_question, render_inspection
from processors.matching.core import match_records, validate_answer_input
from processors.matching.report import write_report

ROOT = Path(__file__).resolve().parents[1]


def parse_case(tmp_path, pages, **pdf_options):
    source_dir = tmp_path / "sources"
    source_dir.mkdir(exist_ok=True)
    source = write_pdf(
        source_dir / "misleading-2022-filename.pdf", pages, **pdf_options
    )
    return source, parse_pdf(source, asset_dir=tmp_path / "answers/assets")


def dump_answer(tmp_path, data):
    path = tmp_path / "answers/source.answers.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_new_source_boundaries_headers_raw_preservation_and_no_network(
    tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Source parsing must not acquire files")

    monkeypatch.setattr(socket, "socket", forbidden)
    source, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "1"),
                (40, 715, "The correct answer is A"),
                (40, 685, "The explanation contains a calculation:"),
                (40, 665, "12"),
                (40, 645, "This number is not a question header."),
                (40, 600, "2) The correct answer is B"),
                (40, 580, "A second explanation."),
                (40, 250, "TSA SECTION 1 - 2021"),
            ]
        ],
    )
    assert [a["question_number"] for a in data["answers"]] == [1, 2]
    assert [a["correct_answer"] for a in data["answers"]] == ["A", "B"]
    assert {a["year"] for a in data["answers"]} == {2021}
    assert "12\nThis number" in data["answers"][0]["explanation"]["main_explanation"]
    assert "TSA SECTION" not in data["answers"][0]["raw"]["source_excerpt"]
    assert "TSA SECTION" in data["pages"][0]["raw_text"]
    # A similar string in the body is not a repeated top-of-page header.
    assert "TSA SECTION" in data["answers"][1]["explanation"]["main_explanation"]
    assert data["source_document"]["sha256"] == sha256(source.read_bytes()).hexdigest()
    validate_answers(data)


def test_cross_page_text_list_continuation_and_section2_exclusion(tmp_path):
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "1"),
                (40, 715, "The correct answer is A"),
                (40, 685, "A sentence continues"),
            ],
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "on the next page."),
                (40, 705, "The facts are as follows:"),
                (40, 685, "- First item"),
                (50, 670, "with a hanging continuation."),
                (40, 650, "- Second item."),
                (40, 630, "Main prose resumes at the marker baseline."),
            ],
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "2"),
                (40, 715, "The correct answer is B"),
                (40, 685, "The last explanation."),
            ],
            [
                (40, 775, "TSA SECTION 2 - 2021"),
                (40, 735, "1"),
                (40, 715, "The correct answer is C"),
                (40, 685, "EXCLUDED SECOND SECTION"),
            ],
        ],
    )
    first, second = data["answers"]
    assert first["page_reference"] == {"start_page": 1, "end_page": 2}
    assert second["page_reference"] == {"start_page": 3, "end_page": 3}
    assert (
        "A sentence continues\non the next page."
        in first["explanation"]["main_explanation"]
    )
    assert "Main prose resumes" in first["explanation"]["main_explanation"]
    assert (
        "hanging continuation"
        in first["explanation"]["other_lists"][0]["items"][0]["text"]
    )
    assert all(
        "EXCLUDED SECOND SECTION" not in a["raw"]["source_excerpt"]
        for a in data["answers"]
    )
    assert any(issue["code"] == "section_excluded" for issue in data["issues"])


def test_raster_image_only_and_multiple_visuals_are_saved_in_stable_order(tmp_path):
    source, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 745, "1"),
                (40, 725, "The correct answer is A"),
                (40, 600, "2"),
                (40, 580, "The correct answer is B"),
                (40, 550, "A text explanation."),
            ]
        ],
        raster=True,
        graphics_commands=("q 48 0 0 36 220 640 cm /Im1 Do Q",),
    )
    first = data["answers"][0]
    assets = first["explanation"]["visual_assets"]
    assert len(assets) == 2
    assert [a["asset_index"] for a in assets] == [1, 2]
    assert assets[0]["bbox"][0] < assets[1]["bbox"][0]
    assert first["explanation"]["main_explanation"] == ""
    assert all(b["type"] == "visual" for b in first["explanation"]["blocks"])
    assert not first["warnings"]
    for asset in assets:
        png = read_png(tmp_path / "answers" / asset["path"])
        assert sha256(png).hexdigest() == asset["sha256"]
        assert asset["source_pdf"] == str(source.resolve())
    again = parse_pdf(source, asset_dir=tmp_path / "answers/assets")
    assert again == data
    path = dump_answer(tmp_path, data)
    validate_answer_input(data, path)
    (path.parent / assets[0]["path"]).unlink()
    with pytest.raises((ValueError, OSError)):
        validate_answer_input(data, path)


def test_vector_table_keeps_internal_text_and_interleaves_with_prose(tmp_path):
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 745, "1"),
                (40, 725, "The correct answer is A"),
                (40, 680, "Text before the table."),
                (90, 620, "Table cell text"),
                (40, 540, "Text after the table."),
            ]
        ],
        graphics_commands=(
            "80 580 200 60 re S",
            "80 610 m 280 610 l S",
            "180 580 m 180 640 l S",
        ),
    )
    explanation = data["answers"][0]["explanation"]
    assert len(explanation["visual_assets"]) == 1
    assert [b["type"] for b in explanation["blocks"]] == [
        "paragraph",
        "visual",
        "paragraph",
    ]
    assert "Table cell text" not in explanation["main_explanation"]
    assert "Table cell text" in data["answers"][0]["raw"]["source_excerpt"]
    assert explanation["blocks"][1]["line_refs"]
    assert (
        "Text before" in explanation["main_explanation"]
        and "Text after" in explanation["main_explanation"]
    )
    validate_answers(data)


def test_visual_crossing_question_boundary_is_saved_unassigned_not_forced(tmp_path):
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 745, "1"),
                (40, 725, "The correct answer is A"),
                (40, 660, "2"),
                (40, 640, "The correct answer is B"),
                (40, 590, "The second explanation."),
            ]
        ],
        raster=True,
    )
    issue = next(
        i for i in data["issues"] if i["code"] == "explanation_visual_unassigned"
    )
    assert read_png(tmp_path / "answers" / issue["visual_asset"]["path"])
    assert all(not a["explanation"]["visual_assets"] for a in data["answers"])


def test_gaps_duplicates_and_malformed_answers_are_preserved_not_inferred(tmp_path):
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "1) The correct answer is A"),
                (40, 715, "First explanation."),
                (40, 675, "Unlabelled intervening material."),
                (40, 655, "The correct answer is B"),
                (40, 635, "3) The correct answer is Z"),
                (40, 615, "Third explanation."),
                (40, 575, "3) The correct answer is C"),
                (40, 555, "Duplicate explanation."),
            ]
        ],
    )
    assert [a["question_number"] for a in data["answers"]] == [1, 3, 3]
    assert data["answers"][1]["correct_answer"] is None
    assert "Unlabelled intervening" in data["answers"][0]["raw"]["source_excerpt"]
    assert any(
        "explanation_boundary_unresolved" in w for w in data["answers"][0]["warnings"]
    )
    assert all(
        "duplicate_answer_identity" in a["warnings"] for a in data["answers"][1:]
    )
    assert any(
        i["code"] == "answer_header_missing" and i["question_number"] == 2
        for i in data["issues"]
    )


def test_cli_separates_source_output_and_refuses_legacy_format(tmp_path):
    source = write_pdf(
        tmp_path / "legacy.pdf", [[(40, 750, "2008"), (40, 710, "Question 1: A")]]
    )
    with pytest.raises(ValueError, match="header year"):
        parse_pdf(source, asset_dir=tmp_path / "assets")
    with pytest.raises(SystemExit):
        parse_main([str(source), "--output-dir", str(tmp_path / "within-source")])
    with pytest.raises(SystemExit):
        match_main(
            ["--clean-json", "unused", "--answers-json", "unused", "--years", "2021"]
        )


def test_empty_explanation_and_failed_visual_saves_remain_reported(
    tmp_path, monkeypatch
):
    from parsers.blackstone_explained_answers import visuals

    original = visuals._save_crop

    def fail_visual(bitmap, pixels, bbox, size, path, overwrite):
        if "_visual_" in path.name:
            raise OSError("simulated asset save failure")
        return original(bitmap, pixels, bbox, size, path, overwrite)

    monkeypatch.setattr(visuals, "_save_crop", fail_visual)
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 745, "1"),
                (40, 725, "The correct answer is A"),
                (40, 600, "2"),
                (40, 580, "The correct answer is B"),
            ]
        ],
        raster=True,
    )
    first, second = data["answers"]
    assert first["explanation"]["visual_assets"][0]["path"] is None
    assert any("visual_not_saved" in warning for warning in first["warnings"])
    assert any(
        "explanation_text_unavailable" in warning for warning in second["warnings"]
    )
    with pytest.raises((ValueError, OSError, KeyError)):
        validate_answer_input(data, dump_answer(tmp_path, data))


@pytest.fixture
def matching_case(tmp_path):
    return shared_matching_case.__wrapped__(tmp_path)


def test_generic_matching_preserves_visuals_and_source_issues(matching_case, tmp_path):
    clean, path, data = matching_case
    data = deepcopy(data)
    answer = data["answers"][0]
    asset = {**answer["visual_previews"][0], "asset_index": 1}
    answer["explanation"]["visual_assets"] = [asset]
    answer["explanation"]["blocks"].append(
        {"type": "visual", "asset_index": 1, "order": 2, "line_refs": []}
    )
    data["issues"] = [
        {
            "code": "explanation_visual_unassigned",
            "year": 2008,
            "question_number": 12,
            "reason": "An unassigned visual is retained",
            "page": 2,
        }
    ]
    path.write_text(json.dumps(data), encoding="utf-8")
    result = match_records([clean], [path], years={2008})
    assert result["records"][0]["answer"]["explanation"]["visual_assets"] == [asset]
    assert "explanation_visual_unassigned" in {i["code"] for i in result["issues"]}
    merged = tmp_path / "merged/result.matched.json"
    merged.parent.mkdir()
    merged.write_text(json.dumps(result), encoding="utf-8")
    baseline = {p: p.read_bytes() for p in (path, clean, merged)}
    inspected = inspect_question(merged, year=2008, question_number=12)
    assert (
        inspected["source_parsing_issues"][0]["code"] == "explanation_visual_unassigned"
    )
    html = render_inspection(inspected, "html")
    assert "id='explanation-visuals'" in html
    assert "Explanation visual 1" in html and "data:image/png;base64" in html
    assert json.loads(render_inspection(inspected, "json")) == inspected
    assert all(p.read_bytes() == value for p, value in baseline.items())
    report = tmp_path / "report.md"
    write_report(result, report)
    assert "# Matching 2008 issues" in report.read_text(encoding="utf-8")
    (path.parent / asset["path"]).unlink()
    assert any(
        i["code"] == "inspection_reference_unavailable"
        for i in inspect_question(merged, year=2008, question_number=12)[
            "live_inspection_issues"
        ]
    )
    blocked = match_records([clean], [path], years={2008})
    assert not blocked["readiness"]["ready"] and not blocked["records"]


@pytest.fixture(scope="module", params=[2021, 2022])
def actual_source(request, tmp_path_factory):
    year = request.param
    source = ROOT / f"acquisition/local/critical_thinking_problem_solving/tsa/TSA-{year}-Explained-Answers-blackstone.pdf"
    if not source.exists():
        pytest.skip("Local worked-solutions PDF not available")
    folder = tmp_path_factory.mktemp(f"answers{year}")
    return year, parse_pdf(source, asset_dir=folder / "assets"), folder


def test_actual_first_last_correct_answers_and_all_boundaries(actual_source):
    year, data, _ = actual_source
    numbers = [a["question_number"] for a in data["answers"]]
    assert numbers == [n for n in range(1, 51) if year == 2021 or n != 46]
    assert data["answers"][0]["correct_answer"] == ("D" if year == 2021 else "A")
    assert data["answers"][-1]["correct_answer"] == ("A" if year == 2021 else "D")
    validate_answers(data)
    for answer in data["answers"]:
        for block in answer["explanation"]["blocks"]:
            values = (
                [item["text"] for item in block["items"]]
                if block["type"] == "list"
                else [block.get("text", "")]
            )
            assert not any(
                re.search(r"TSA\s*SECTION\s*1\s*[-–—]?\s*202[12]", value, re.IGNORECASE)
                for value in values
            )
    assert all(a["correct_answer"] in "ABCDE" for a in data["answers"])
    # Independent extraction backend confirms every source answer declaration,
    # including the real absence of a 2022 Q46 header.
    observed = []
    pattern = re.compile(
        r"^\s*(\d{1,2})[.)]?\s*The\s*correct\s*answer\s*is\s*([A-E])",
        re.MULTILINE | re.IGNORECASE,
    )
    with pdfium.PdfDocument(data["source_document"]["path"]) as document:
        for page in document:
            textpage = page.get_textpage()
            try:
                observed.extend(
                    (int(n), label.upper())
                    for n, label in pattern.findall(textpage.get_text_range())
                )
            finally:
                textpage.close()
                page.close()
    assert observed == [
        (a["question_number"], a["correct_answer"]) for a in data["answers"]
    ]


def test_actual_cross_page_explanations_and_source_visual_inventory(actual_source):
    year, data, folder = actual_source
    answers = {a["question_number"]: a for a in data["answers"]}
    expected = (
        {10: (1, 2), 27: (3, 4)}
        if year == 2021
        else {18: (2, 3), 27: (3, 4), 37: (4, 5)}
    )
    for number, (first, last) in expected.items():
        assert answers[number]["page_reference"] == {
            "start_page": first,
            "end_page": last,
        }
        assert len(answers[number]["visual_previews"]) == 2
    if year == 2021:
        q48 = answers[48]
        assert q48["correct_answer"] == "E" and q48["page_reference"]["start_page"] == 6
        assert q48["explanation"]["main_explanation"] == "" and not q48["warnings"]
        assert [b["type"] for b in q48["explanation"]["blocks"]] == ["visual"]
        asset = q48["explanation"]["visual_assets"][0]
        assert read_png(folder / asset["path"])
        assert asset["bbox"][1] <= asset["graphic_bbox"][1]
        assert asset["bbox"][3] >= asset["graphic_bbox"][3]
        assert [
            a["question_number"]
            for a in data["answers"]
            if a["explanation"]["visual_assets"]
        ] == [48]
        assert not data["issues"]
    else:
        assert not any(a["explanation"]["visual_assets"] for a in data["answers"])
        assert [len(b["items"]) for b in answers[6]["explanation"]["other_lists"]] == [
            2,
            2,
        ]
        assert "0.6 * x + 0.3 * y = 3" in answers[6]["explanation"]["main_explanation"]
        assert "Both equations match" in answers[37]["explanation"]["main_explanation"]
        assert not answers[45]["warnings"]
        assert any(
            i["code"] == "answer_header_missing" and i["question_number"] == 46
            for i in data["issues"]
        )


@pytest.mark.parametrize(
    "year,numbers", [(2021, (1, 10, 27, 48, 50)), (2022, (1, 6, 18, 37, 45, 46, 50))]
)
def test_generated_year_matching_and_html_are_traceable_read_only(year, numbers):
    path = ROOT / f"data/merged/blackstone/tsa_{year}.matched.json"
    if not path.exists():
        pytest.skip("Generate year-specific matched outputs first")
    baseline = path.read_bytes()
    data = json.loads(baseline)
    assert data["readiness"]["ready"] and len(data["records"]) == 50
    assert {r["identity"]["year"] for r in data["records"]} == {year}
    counts = {
        status: sum(r["status"] == status for r in data["records"])
        for status in ("matched", "conflict", "unmatched_question")
    }
    assert counts == {"matched": 50, "conflict": 0, "unmatched_question": 0}
    for number in numbers:
        result = inspect_question(path, year=year, question_number=number)
        if year == 2022 and number == 46:
            assert any(
                issue["code"] == "answer_header_missing"
                for issue in result["source_parsing_issues"]
            )
        assert not any(
            i["code"] == "inspection_reference_unavailable"
            for i in result["live_inspection_issues"]
        )
        html = render_inspection(result, "html")
        for section in (
            "identity",
            "main-body",
            "main-question",
            "main-answers",
            "correct-answer",
            "main-explanation",
            "original-screenshot",
            "answer-source",
            "matching-metadata",
            "issues",
        ):
            assert f"id='{section}'" in html
        if year == 2021 and number == 48:
            gallery = re.search(
                r"<section id='explanation-visuals'>(.*?)</section>", html, re.DOTALL
            )[1]
            assert "<img " in gallery and "data:image/png;base64" in gallery
        assert json.loads(render_inspection(result, "json")) == result
    assert path.read_bytes() == baseline
    report = (ROOT / f"docs/critical_thinking_problem_solving/tsa/MATCHING_{year}_ISSUES.md").read_text(encoding="utf-8")
    assert f"# Matching {year} issues" in report and "(0 records)" not in report
    if year == 2022:
        assert (
            "| 2022 | section_1 | 45 |" not in report
            and "| 2022 | section_1 | 46 |" in report
        )
