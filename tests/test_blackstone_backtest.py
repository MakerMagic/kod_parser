"""Read-only raw inspection, issue detection, and separate report regressions."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from parsers.blackstone.backtest import (
    collect_issues,
    inspect_question,
    main,
    write_report,
)


@pytest.fixture
def raw_json(tmp_path):
    question = {
        "question_id": "blackstone_2020_section_1_q12",
        "source_question_key": {
            "source": "blackstone",
            "year": 2020,
            "section": "section_1",
        },
        "question_number": 12,
        "page_reference": {"start_page": 3, "end_page": 3},
        "raw": {
            "question_block": "12 Original\nA One\nB Two\n",
            "options_block": "A One\nB Two\n",
            "extraction_notes": ["Keep every note."],
            "page_spans": [{"page": 3, "start": 0, "end": 24}],
        },
        "question_text": "Original\n",
        "subpoints": [{"label": "1", "text": "A subpart"}],
        "options": [
            {"label": "A", "text": "One\n", "images": [], "warnings": []},
            {"label": "B", "text": "Two\n", "images": [], "warnings": []},
        ],
        "answer": "B",
        "explanation": "Stored explanation.",
        "images": [{"image_id": "p3_image", "page": 3, "bbox": [10, 20, 30, 40]}],
        "warnings": ["incomplete_or_ambiguous_options:A,B"],
        "custom_raw_field": {"keep": [1, 2, "exact"]},
    }
    block = question["raw"]["question_block"]
    question["raw"]["page_spans"][0]["end"] = len(block)
    dataset = {
        "source": "blackstone",
        "year": 2020,
        "session": "November",
        "paper": "D512/11",
        "variant": None,
        "section": "section_1",
        "document_role": "question_paper",
        "input": {
            "filename": "paper.pdf",
            "path": str(tmp_path / "original" / "paper.pdf"),
            "url": "https://example.invalid/paper.pdf",
        },
        "acquisition": {"method": "unknown", "origin": None},
        "extraction": {"parser": "blackstone", "parser_version": "1"},
        "document_extension": {"preserve": True},
        "pages": [{"page_number": 3, "raw_text": block, "warnings": []}],
        "questions": [question],
        "warnings": [],
    }
    path = tmp_path / "paper.raw.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
    return path, dataset


@pytest.mark.parametrize("reference_kind", ["filename", "path", "url"])
def test_complete_record_and_source_metadata_are_returned_without_modification(
    raw_json, reference_kind
):
    path, original = raw_json
    before = path.read_bytes()
    result = inspect_question(
        [path],
        source=original["input"][reference_kind],
        question_number=12,
        year=2020,
        session="November",
        include_pages=True,
    )
    assert result["question"] == original["questions"][0]
    assert result["document"] == {
        k: v for k, v in original.items() if k not in {"questions", "pages"}
    }
    assert result["pages"] == original["pages"]
    assert result["availability"] == {"missing_fields": [], "null_fields": []}
    assert path.read_bytes() == before


def test_wrong_source_path_does_not_fall_back_to_filename(raw_json):
    path, _ = raw_json
    with pytest.raises(ValueError, match="No matching"):
        inspect_question(
            [path], source="some-other-directory/paper.pdf", question_number=12
        )


def test_ambiguous_records_require_disambiguation(raw_json, tmp_path):
    path, data = raw_json
    other = deepcopy(data)
    other["year"] = 2021
    other["questions"][0]["source_question_key"]["year"] = 2021
    other["questions"][0]["question_id"] = "blackstone_2021_section_1_q12"
    (tmp_path / "second.raw.json").write_text(json.dumps(other), encoding="utf-8")
    with pytest.raises(ValueError, match="Ambiguous selection"):
        inspect_question([tmp_path], source="paper.pdf", question_number=12)
    result = inspect_question(
        [tmp_path], source="paper.pdf", question_number=12, year=2020
    )
    assert result["raw_json"] == str(path)
    with pytest.raises(ValueError, match="No matching"):
        inspect_question([path], source="paper.pdf", question_number=12, session="June")


def test_missing_components_are_shown_separately_and_not_invented(raw_json, capsys):
    path, data = raw_json
    del data["questions"][0]["answer"]
    data["questions"][0]["explanation"] = None
    path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        main(
            [
                "inspect",
                "--raw-json",
                str(path),
                "--source",
                "paper.pdf",
                "--question",
                "12",
                "--format",
                "json",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["question"] == data["questions"][0]
    assert result["availability"]["missing_fields"] == ["answer"]
    assert result["availability"]["null_fields"] == ["explanation"]


def test_missing_or_null_raw_block_can_still_be_inspected(raw_json, capsys):
    path, data = raw_json
    data["questions"][0]["raw"]["question_block"] = None
    path.write_text(json.dumps(data), encoding="utf-8")
    assert (
        main(
            [
                "inspect",
                "--raw-json",
                str(path),
                "--source",
                "paper.pdf",
                "--question",
                "12",
            ]
        )
        == 0
    )
    assert "null (stored value)" in capsys.readouterr().out


def test_cli_text_and_json_export_preserve_the_complete_question(
    raw_json, tmp_path, capsys
):
    path, data = raw_json
    before = path.read_bytes()
    args = [
        "inspect",
        "--raw-json",
        str(path),
        "--source",
        "paper.pdf",
        "--question",
        "12",
    ]
    assert main(args) == 0
    output = capsys.readouterr().out
    assert data["questions"][0]["raw"]["question_block"] in output
    assert "custom_raw_field" in output and "Stored explanation." in output
    exported = tmp_path / "inspection.json"
    assert main([*args, "--format", "json", "--output", str(exported)]) == 0
    assert (
        json.loads(exported.read_text(encoding="utf-8"))["question"]
        == data["questions"][0]
    )
    assert main([*args, "--format", "json", "--output", str(path)]) == 1
    assert path.read_bytes() == before


def test_report_detects_actual_issues_and_never_changes_raw_data(raw_json, tmp_path):
    path, data = raw_json
    before = path.read_bytes()
    before_data = deepcopy(data)
    issues = collect_issues(data, path)
    assert data == before_data
    assert len(issues) == 1
    row = issues[0]
    assert row["source_file"] == data["input"]["path"]
    assert row["question_number"] == 12 and row["year"] == 2020
    assert row["page_reference"] == {"start_page": 3, "end_page": 3}
    assert row["components"] == ["options"]
    assert row["manual_review_required"] is True
    output = tmp_path / "issues.md"
    assert write_report([path], output) == issues
    assert "incomplete_or_ambiguous_options:A,B" in output.read_text(encoding="utf-8")
    assert write_report([path], output) == issues
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="separate Markdown"):
        write_report([path], path)
    unrelated = tmp_path / "notes.md"
    unrelated.write_text("Manual documentation", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_report([path], unrelated)
    assert unrelated.read_text(encoding="utf-8") == "Manual documentation"


def test_presence_of_graphics_empty_subpoints_and_missing_answers_are_not_faults(
    raw_json,
):
    path, data = raw_json
    question = data["questions"][0]
    question["warnings"] = ["graphics_present:option_association_not_resolved"]
    question["subpoints"] = []
    del question["answer"]
    del question["explanation"]
    assert collect_issues(data, path) == []


def test_shared_metadata_issues_are_document_rows_not_every_question(raw_json):
    path, data = raw_json
    data["warnings"] = [
        "uncertain_metadata:year",
        "source_assigned_by_parser_profile:not_verified_in_document",
    ]
    data["questions"][0]["warnings"] = ["question_id_unavailable:uncertain_metadata"]
    issues = collect_issues(data, path)
    assert len(issues) == 2
    assert all(
        row["scope"] == "document" and row["question_number"] is None for row in issues
    )


@pytest.mark.parametrize(
    "problem",
    [
        "empty_text",
        "page_span",
        "page_range",
        "metadata",
        "duplicates",
        "low_confidence",
    ],
)
def test_detectable_essential_component_problems_are_reported(raw_json, problem):
    path, data = raw_json
    question = data["questions"][0]
    question["warnings"] = []
    if problem == "empty_text":
        question["question_text"] = None
    elif problem == "page_span":
        question["raw"]["page_spans"][0]["start"] = -1
    elif problem == "page_range":
        data["pages"].append({"page_number": 2, "raw_text": "another page"})
        question["page_reference"] = {"start_page": 2, "end_page": 2}
    elif problem == "metadata":
        question["source_question_key"]["year"] = 2099
    elif problem == "duplicates":
        data["questions"].append(deepcopy(question))
    else:
        question["confidence"] = "low"
    assert collect_issues(data, path)


def test_report_cli_and_no_match_errors(raw_json, tmp_path):
    path, _ = raw_json
    assert (
        main(
            ["report", "--raw-json", str(path), "--output", str(tmp_path / "issues.md")]
        )
        == 0
    )
    assert (
        main(
            [
                "inspect",
                "--raw-json",
                str(path),
                "--source",
                "paper.pdf",
                "--question",
                "999",
            ]
        )
        == 1
    )


def test_parser_cli_emits_a_separate_issues_report(tmp_path, monkeypatch):
    import parsers.blackstone.__main__ as parser_cli

    raw = {
        "input": {"filename": "fake.pdf", "path": "fake.pdf", "sha256": "a" * 64},
        "source": "blackstone",
        "year": None,
        "extraction": {"recognized_question_paper": True},
        "questions": [],
        "warnings": ["no_questions_detected:full_page_text_preserved"],
    }
    source = tmp_path / "fake.pdf"
    source.write_bytes(b"not reparsed in this CLI integration test")
    monkeypatch.setattr(parser_cli, "parse_pdf", lambda path: deepcopy(raw))
    output = tmp_path / "raw"
    assert parser_cli.main([str(source), "--output-dir", str(output)]) == 1
    assert len(list(output.glob("*.raw.json"))) == 1
    assert "no_questions_detected" in (output / "PARSING_ISSUES.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[1]
        / "data/raw/blackstone/TSA Oxford 2020-ca4ee526afb0.raw.json"
    ).exists(),
    reason="Generated local raw output unavailable",
)
def test_real_stored_question_is_inspected_without_reparsing():
    path = (
        Path(__file__).resolve().parents[1]
        / "data/raw/blackstone/TSA Oxford 2020-ca4ee526afb0.raw.json"
    )
    before = path.read_bytes()
    dataset = json.loads(before)
    result = inspect_question(
        [path], source="TSA Oxford 2020.pdf", question_number=12, year=2020
    )
    assert result["question"] == dataset["questions"][11]
    assert path.read_bytes() == before
