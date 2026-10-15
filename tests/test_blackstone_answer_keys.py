"""Ruled answer-only profile, exact-key matching and old-format isolation."""

import json
import re
import socket
from hashlib import sha256
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from test_blackstone_raw import write_pdf
from test_matching import match_case as shared_matching_case

from parsers.blackstone_answer_keys import parse_pdf
from parsers.blackstone_answer_keys.__main__ import main
from processors.matching.backtest import inspect_question, render_html
from processors.matching.core import match_records, validate_answer_input
from processors.matching.report import write_report

ROOT = Path(__file__).resolve().parents[1]


def table_pdf(tmp_path, rows, *, section=1, year=2017, additional_year=None):
    source = tmp_path / "source"
    source.mkdir(exist_ok=True)
    lines = [
        (40, 780, f"Thinking Skills Assessment October {year}"),
        (40, 760, f"SECTION {section}"),
        (40, 740, "Answer key"),
        (65, 695, "Question"),
        (125, 695, "Answer"),
    ]
    for index, (number, answer) in enumerate(rows):
        lines += [(75, 675 - 20 * index, str(number)), (135, 675 - 20 * index, answer)]
    bottom = 690 - len(rows) * 20
    commands = [f"{x} {bottom} m {x} 710 l S" for x in (60, 120, 180)]
    commands += [f"60 {y} m 180 {y} l S" for y in range(bottom, 711, 20)]
    pages = [lines]
    if additional_year:
        pages.append(
            [
                (x, y, text.replace(str(year), str(additional_year)))
                for x, y, text in lines
            ]
        )
    return write_pdf(source / "arbitrary-name.pdf", pages, graphics_commands=commands)


def test_table_geometry_raw_trace_and_no_acquisition(tmp_path, monkeypatch):
    pdf = table_pdf(tmp_path, [(1, "A"), (2, "E"), (3, "C")])
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("No network"))
    raw = parse_pdf(pdf, asset_dir=tmp_path / "answers/assets")
    assert [a["question_number"] for a in raw["answers"]] == [1, 2, 3]
    assert [a["correct_answer"] for a in raw["answers"]] == ["A", "E", "C"]
    for a in raw["answers"]:
        assert a["year"] == 2017 and a["section"] == "section_1"
        assert a["explanation"]["main_explanation"] == ""
        assert a["explanation"]["blocks"] == []
        assert a["explanation"]["availability"] == "not_supplied_by_source_format"
        assert a["raw"]["cells"] == [str(a["question_number"]), a["correct_answer"]]
        assert a["visual_previews"][0]["role"] == "answer_key_row"
        for line in a["raw"]["line_refs"]:
            assert (
                raw["pages"][0]["layout_text"][line["start"] : line["end"]]
                == line["text"]
            )
    assert {i["question_number"] for i in raw["issues"]} == set(range(4, 51))
    validate_answer_input(raw, tmp_path / "answers/key.answers.json")


@pytest.mark.parametrize(
    "rows,code",
    [
        ([(1, "A"), (1, "B"), (3, "C")], "duplicate_answer"),
        ([(1, "X"), (2, "B"), (3, "C")], "malformed_answer_row"),
        ([(2, "A"), (1, "B"), (3, "C")], "table_extraction_ambiguity"),
    ],
)
def test_uncertain_rows_not_force_matched(tmp_path, rows, code):
    raw = parse_pdf(table_pdf(tmp_path, rows), asset_dir=tmp_path / "answers/assets")
    assert code in {i["code"] for i in raw["issues"]}
    assert all(
        a["correct_answer"] is None for a in raw["answers"] if code in a["warnings"]
    )


def test_section_two_not_accepted(tmp_path):
    raw = parse_pdf(
        table_pdf(tmp_path, [(1, "A")], section=2),
        asset_dir=tmp_path / "answers/assets",
    )
    assert raw["answers"][0]["correct_answer"] is None
    assert raw["answers"][0]["section"] == "section_2"
    assert "section_header_parsing_issue" in raw["answers"][0]["warnings"]


def test_conflicting_source_years_reported_not_guessed(tmp_path):
    pdf = table_pdf(tmp_path, [(1, "A")], additional_year=2018)
    raw = parse_pdf(pdf, asset_dir=tmp_path / "answers/assets")
    assert {a["year"] for a in raw["answers"]} == {2017, 2018}
    assert all(a["correct_answer"] is None for a in raw["answers"])
    assert all("year_mismatch" in a["warnings"] for a in raw["answers"])
    assert {i["year"] for i in raw["issues"] if i["code"] == "year_mismatch"} == {
        2017,
        2018,
    }


@pytest.mark.parametrize(
    "year,expected",
    [(2017, ["E", "E", "D"]), (2018, ["B", "D", "C"]), (2019, ["E", "C", "D"])],
)
def test_real_fifty_rows_and_independent_extractor(tmp_path, year, expected):
    pdf = ROOT / f"acquisition/local/TSA-{year}-Answers-blackstone.pdf"
    if not pdf.exists():
        pytest.skip("Local source unavailable")
    raw = parse_pdf(pdf, asset_dir=tmp_path / "answers/assets")
    assert raw["issues"] == []
    assert [a["question_number"] for a in raw["answers"]] == list(range(1, 51))
    assert [raw["answers"][i - 1]["correct_answer"] for i in (1, 25, 50)] == expected
    with pdfium.PdfDocument(str(pdf)) as doc:
        page = doc[0]
        text = page.get_textpage()
        independent = {
            int(n): answer
            for n, answer in re.findall(
                r"(?m)^\s*(\d+)\s+([A-E])\s*$", text.get_text_range()
            )
        }
        text.close()
        page.close()
    assert independent == {
        a["question_number"]: a["correct_answer"] for a in raw["answers"]
    }
    validate_answer_input(raw, tmp_path / "answers/key.answers.json")


def test_cli_refuses_unrelated_output(tmp_path):
    pdf = table_pdf(tmp_path, [(1, "A")])
    assert main([str(pdf), "--output-dir", str(tmp_path / "answers")]) == 0
    path = next((tmp_path / "answers").glob("*.answers.json"))
    path.write_text('{"stage":"unrelated"}', encoding="utf-8")
    with pytest.raises(SystemExit):
        main([str(pdf), "--output-dir", str(path.parent), "--overwrite"])


@pytest.fixture
def prepared_case(tmp_path):
    return shared_matching_case.__wrapped__(tmp_path)


def test_source_issues_survive_when_no_rows_can_be_accepted(prepared_case):
    clean_path, answer_path, parsed = prepared_case
    parsed["answers"] = []
    parsed["issues"] = [
        {
            "code": "malformed_answer_row",
            "year": 2008,
            "section": "section_1",
            "question_number": 12,
            "reason": "Unreadable table row retained in raw page text",
        }
    ]
    answer_path.write_text(json.dumps(parsed), encoding="utf-8")
    matched = match_records([clean_path], [answer_path], years={2008})
    assert {i["code"] for i in matched["issues"]} == {
        "malformed_answer_row",
        "question_without_answer",
    }
    assert matched["records"][0]["status"] == "unmatched_question"


def test_generic_match_answer_only_and_readonly_html(tmp_path, prepared_case):
    clean_path = prepared_case[0]
    clean = json.loads(clean_path.read_text(encoding="utf-8"))
    clean["document"]["year"] = 2017
    raw_path = Path(clean["raw_reference"]["path"])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["year"] = 2017
    raw["questions"][0]["source_question_key"]["year"] = 2017
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    digest = sha256(raw_path.read_bytes()).hexdigest()
    clean["raw_reference"]["sha256"] = digest
    q = clean["questions"][0]
    q["metadata"]["year"] = q["source_question_key"]["year"] = 2017
    q["raw_reference"]["sha256"] = digest
    q["raw_record"] = raw["questions"][0]
    clean_path.write_text(json.dumps(clean), encoding="utf-8")
    pdf = table_pdf(tmp_path, [(12, "A")])
    parsed = parse_pdf(pdf, asset_dir=tmp_path / "answers/assets")
    answer_path = tmp_path / "answers/key.answers.json"
    answer_path.write_text(json.dumps(parsed), encoding="utf-8")
    data = match_records([clean_path], [answer_path], years={2017})
    assert data["readiness"]["ready"]
    assert data["records"][0]["status"] == "matched"
    output = tmp_path / "merged/key.matched.json"
    output.parent.mkdir()
    output.write_text(json.dumps(data), encoding="utf-8")
    hashes = [
        sha256(p.read_bytes()).hexdigest()
        for p in (clean_path, raw_path, answer_path, output)
    ]
    result = inspect_question(output, year=2017, question_number=12)
    html = render_html(result)
    assert "this source format supplies answers only" in html
    assert "Answer-Key Source" in html and "parsed_answer_key_row" in html
    # The shared fixture deliberately preserves a raw visual ordering issue.
    assert result["live_inspection_issues"] == [
        {
            "code": "raw_visual_issue",
            "reason": "visual_asset_order_inconsistent",
            "asset_path": None,
        }
    ]
    assert hashes == [
        sha256(p.read_bytes()).hexdigest()
        for p in (clean_path, raw_path, answer_path, output)
    ]
    report = tmp_path / "MATCHING_2017-2019_ISSUES.md"
    write_report(data, report)
    assert "Missing Answer (49 records)" in report.read_text(encoding="utf-8")
