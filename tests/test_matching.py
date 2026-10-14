"""Generic exact-key matching, safeguards, review reporting and read-only QA."""

import json
import socket
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_blackstone_cleaning import raw_case as make_raw_case
from test_blackstone_raw import write_pdf

from parsers.explained_answers.parser import parse_pdf
from processors.matching.__main__ import main as match_main
from processors.matching.backtest import inspect_question, render_inspection
from processors.matching.backtest import main as backtest_main
from processors.matching.core import match_records
from processors.matching.report import write_report
from processors.normalization.blackstone import clean_dataset
from processors.normalization.blackstone.storage import write_clean


@pytest.fixture
def match_case(tmp_path):
    raw_path, raw = make_raw_case.__wrapped__(tmp_path)
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    pdf = write_pdf(
        source_dir / "question.pdf", [[(40, 700, "Question original context")]]
    )
    raw["input"]["path"] = str(pdf)
    raw["input"]["sha256"] = sha256(pdf.read_bytes()).hexdigest()
    raw["year"] = 2008
    q = raw["questions"][0]
    q["source_question_key"]["year"] = 2008
    for a in [*q["visual_assets"], *q["visual_previews"], *q["options"][0]["images"]]:
        a["sha256"] = sha256((raw_path.parent / a["path"]).read_bytes()).hexdigest()
    raw_path.write_text(json.dumps(raw), encoding="utf-8")
    clean_path = write_clean(
        clean_dataset(raw, raw_path), tmp_path / "clean/q.clean.json"
    )
    source = write_pdf(
        source_dir / "explanations.pdf",
        [
            [(40, 750, "2008")],
            [
                (40, 750, "SECTION 1"),
                (40, 710, "Question 12: A"),
                (60, 670, "A detailed explanation."),
                (40, 600, "END OF SECTION"),
            ],
        ],
    )
    answer = parse_pdf(source, asset_dir=tmp_path / "answers/assets")
    answer_path = tmp_path / "answers/source.answers.json"
    answer_path.write_text(json.dumps(answer), encoding="utf-8")
    return clean_path, answer_path, answer


def match(case):
    return match_records(
        [case[0]], [case[1]], years={2008}, question_source="blackstone"
    )


def test_success_preserves_clean_raw_answer_and_image_traceability(match_case):
    data = match(match_case)
    assert data["readiness"]["ready"]
    r = data["records"][0]
    assert r["status"] == "matched" and r["correct_answer"] == "A"
    assert (
        r["question"]
        == json.loads(match_case[0].read_text(encoding="utf-8"))["questions"][0]
    )
    assert r["question"]["options"][0]["images"]
    assert r["question"]["raw_record"]["custom_unresolved_field"] == {"retain": True}
    assert r["matching"]["upstream_review_required"]
    assert not r["matching"]["paper_variant_verified"]
    assert r["answer"] == match_case[2]["answers"][0]
    assert r["question_reference"]["json_pointer"] == "/questions/0"
    assert r["answer_reference"]["json_pointer"] == "/answers/0"


@pytest.mark.parametrize(
    "failure,expected",
    [
        ("missing", "question_without_answer"),
        ("orphan", "answer_without_question"),
        ("duplicate", "duplicate_candidate_match"),
        ("label", "correct_answer_option_conflict"),
        ("section", "section_excluded"),
        ("header", "correct_answer_unavailable"),
        ("paper", "identity_metadata_conflict"),
    ],
)
def test_no_forced_conflicting_matches(match_case, failure, expected):
    _, path, answer = match_case
    if failure == "missing":
        answer["answers"] = []
    elif failure == "orphan":
        answer["answers"][0]["question_number"] = 99
    elif failure == "duplicate":
        answer["answers"].append(deepcopy(answer["answers"][0]))
    elif failure == "label":
        answer["answers"][0]["correct_answer"] = "Z"
    elif failure == "section":
        answer["answers"][0]["section"] = "section_2"
    elif failure == "header":
        answer["answers"][0]["correct_answer"] = None
    elif failure == "paper":
        answer["answers"][0]["paper"] = "conflicting"
        clean = json.loads(match_case[0].read_text(encoding="utf-8"))
        clean["questions"][0]["metadata"]["paper"] = "original"
        match_case[0].write_text(json.dumps(clean), encoding="utf-8")
    path.write_text(json.dumps(answer), encoding="utf-8")
    data = match(match_case)
    assert expected in {i["code"] for i in data["issues"]}
    assert not any(r["status"] == "matched" for r in data["records"])


def test_duplicate_question_candidates_are_not_selected(match_case):
    second = match_case[0].with_name("duplicate.clean.json")
    second.write_bytes(match_case[0].read_bytes())
    data = match_records([match_case[0], second], [match_case[1]])
    assert data["records"][0]["status"] == "ambiguous"
    assert data["records"][0]["question"] is None
    assert len(data["records"][0]["question_candidates"]) == 2


def test_matching_neither_extracts_pdf_nor_acquires_files(match_case, monkeypatch):
    import pdfplumber
    import pypdfium2

    def forbidden(*args, **kwargs):
        raise AssertionError("Matching must not acquire files or parse PDFs")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(pdfplumber, "open", forbidden)
    monkeypatch.setattr(pypdfium2, "PdfDocument", forbidden)
    assert match(match_case)["records"][0]["status"] == "matched"


@pytest.mark.parametrize(
    "side", ["raw", "answer_pdf", "answer_preview", "answer_contract"]
)
def test_readiness_blocks_changed_sources_before_matching(match_case, side):
    clean = json.loads(match_case[0].read_text(encoding="utf-8"))
    if side == "answer_contract":
        changed = deepcopy(match_case[2])
        changed["stage"] = "unrelated"
        match_case[1].write_text(json.dumps(changed), encoding="utf-8")
        data = match(match_case)
        assert not data["readiness"]["ready"] and not data["records"]
        return
    if side == "raw":
        path = Path(clean["raw_reference"]["path"])
    elif side == "answer_pdf":
        path = Path(match_case[2]["source_document"]["path"])
    else:
        path = (
            match_case[1].parent
            / match_case[2]["answers"][0]["visual_previews"][0]["path"]
        )
    path.write_bytes(path.read_bytes() + b"changed")
    data = match(match_case)
    assert not data["readiness"]["ready"]
    assert not data["records"]


def test_html_text_json_inspection_and_report_do_not_mutate_inputs(
    match_case, tmp_path
):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    merged = tmp_path / "merged/result.matched.json"
    report = tmp_path / "docs/MATCHING_2008-2016_ISSUES.md"
    assert (
        match_main(
            [
                "--clean-json",
                str(match_case[0]),
                "--answers-json",
                str(match_case[1]),
                "--output",
                str(merged),
                "--issues-report",
                str(report),
            ]
        )
        == 0
    )
    result = inspect_question(merged, year=2008, question_number=12)
    html = render_inspection(result, "html")
    for identifier in (
        "identity",
        "main-body",
        "main-question",
        "main-answers",
        "correct-answer",
        "main-explanation",
        "incorrect-explanations",
        "other-lists",
        "original-screenshot",
        "answer-source",
        "matching-metadata",
        "issues",
    ):
        assert f"id='{identifier}'" in html
    assert "data:image/png;base64" in html and "A detailed explanation." in html
    assert "correct_answer" in render_inspection(result)
    assert json.loads(render_inspection(result, "json")) == result
    output = tmp_path / "inspections/q12.html"
    assert (
        backtest_main(
            [
                "inspect",
                "--matched-json",
                str(merged),
                "--year",
                "2008",
                "--question",
                "12",
                "--format",
                "html",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert all(p.read_bytes() == content for p, content in before.items())
    with pytest.raises(SystemExit):
        backtest_main(
            [
                "inspect",
                "--matched-json",
                str(merged),
                "--year",
                "2008",
                "--question",
                "12",
                "--output",
                str(match_case[0]),
            ]
        )


def test_report_counts_unique_records_and_preserves_details(match_case, tmp_path):
    data = match(match_case)
    issue = {
        "code": "duplicate_candidate_match",
        "year": 2008,
        "section": "section_1",
        "question_number": 12,
        "reason": "Two candidates",
        "manual_review_required": True,
        "upstream_cause": ["upstream conflict"],
        "answer_source": {"filename": "example.pdf"},
        "answer_pages": {"start_page": 2, "end_page": 3},
    }
    data["issues"] = [issue, deepcopy(issue)]
    output = tmp_path / "issues.md"
    write_report(data, output)
    text = output.read_text(encoding="utf-8")
    assert "## Duplicate Candidate Match (1 records)" in text
    assert text.count("| 2008 | section_1 | 12 |") == 1
    assert "example.pdf" in text and "upstream conflict" in text
    assert "(0 records)" not in text


def test_actual_scope_identity_and_review_when_local_outputs_present():
    root = Path(__file__).resolve().parents[1]
    merged = root / "data/merged/blackstone/tsa_2008-2016.matched.json"
    if not merged.exists():
        pytest.skip(
            "Run documented parser + matching commands for integration validation"
        )
    data = json.loads(merged.read_text(encoding="utf-8"))
    assert data["readiness"]["ready"]
    assert len(data["records"]) == 450
    assert all(r["identity"]["section"] == "section_1" for r in data["records"])
    for record in data["records"]:
        labels = [o["label"] for o in record["question"]["options"] or []]
        expected = record["answer"]["correct_answer"]
        assert record["status"] == (
            "matched" if labels.count(expected) == 1 else "conflict"
        )
        if record["status"] != "matched":
            assert record["correct_answer"] is None and record["issues"]
    for year in range(2008, 2017):
        for number in (1, 50):
            result = inspect_question(merged, year=year, question_number=number)
            assert result["record"]["answer"]["correct_answer"]
            if result["record"]["status"] == "matched":
                assert result["record"]["correct_answer"]
            assert not any(
                i.get("code") == "inspection_reference_unavailable"
                for i in result["live_inspection_issues"]
            )
