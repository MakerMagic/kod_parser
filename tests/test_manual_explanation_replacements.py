"""Approved replacements are scoped, fingerprint-pinned, reversible and readable."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_matching import match_case as shared_matching_case

from parsers.manual_explanations import main as import_manual
from parsers.manual_explanations import parse_manual
from processors.matching.backtest import inspect_question, render_html
from processors.matching.core import match_records
from processors.matching.report import write_report


@pytest.fixture
def replacement_case(tmp_path):
    clean, pdf_answers, data = shared_matching_case.__wrapped__(tmp_path)
    original = data["answers"][0]
    original["warnings"] = ["bullet_structure_ambiguous:source_marker_preserved"]
    pdf_answers.write_text(json.dumps(data), encoding="utf-8")
    definition = {
        "origin": "user_supplied_manual",
        "approval": "single_question",
        "supplied_by": "user",
        "verification": "Explicitly supplied explanation for this fixture only.",
        "year": 2008,
        "section": "section_1",
        "question_number": 12,
        "correct_answer": "A",
        "correct_answer_origin": "Unchanged source answer",
        "target_question_key": json.loads(clean.read_text(encoding="utf-8"))[
            "questions"
        ][0]["source_question_key"],
        "related_source_document": data["source_document"],
        "replaces_explanation": {
            "answer_id": original["answer_id"],
            "source_sha256": data["source_document"]["sha256"],
            "explanation_sha256": sha256(
                json.dumps(
                    original["explanation"], ensure_ascii=False, sort_keys=True
                ).encode()
            ).hexdigest(),
        },
        "explanation_text": "Here are the scores:\n• Pip=28*54\n- Eve=27*56\n\nConclusion remains.",
        "explanation_blocks": [
            {"type": "paragraph", "role": "main", "text": "Here are the scores:"},
            {
                "type": "list",
                "role": "other",
                "items": [
                    {"text": "Pip=28*54", "raw_text": "• Pip=28*54"},
                    {"text": "Eve=27*56", "raw_text": "- Eve=27*56"},
                ],
            },
            {"type": "paragraph", "role": "main", "text": "Conclusion remains."},
        ],
    }
    directory = tmp_path / "manual_sources"
    directory.mkdir()
    source = directory / "approved.json"
    source.write_text(json.dumps(definition), encoding="utf-8")
    output = tmp_path / "manual_intermediate/approved.answers.json"
    assert import_manual([str(source), "--output", str(output)]) == 0
    return clean, pdf_answers, data, source, output


def run(case):
    return match_records([case[0]], [case[1], case[4]], years={2008})


def test_selected_manual_preserves_source_and_ordered_lists(replacement_case, tmp_path):
    case = replacement_case
    before = case[1].read_bytes()
    data = run(case)
    r = data["records"][0]
    assert r["status"] == "matched" and r["correct_answer"] == "A"
    assert r["answer"]["provenance"]["origin"] == "user_supplied_manual"
    assert r["superseded_answer_candidates"][0]["record"] == case[2]["answers"][0]
    assert case[1].read_bytes() == before
    final = r["final_explanation"]
    assert final["status"] == "available"
    assert [b["type"] for b in final["blocks"]] == ["paragraph", "list", "paragraph"]
    assert [i["text"] for i in final["blocks"][1]["items"]] == [
        "Pip=28*54",
        "Eve=27*56",
    ]
    assert not data["issues"]
    path = tmp_path / "result.matched.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    result = inspect_question(path, year=2008, question_number=12)
    assert not any(
        i["code"] == "inspection_reference_unavailable"
        for i in result["live_inspection_issues"]
    )
    # The fixture's unrelated raw visual warning must not be hidden by a manual explanation.
    assert any(
        i["code"] == "raw_visual_issue" for i in result["live_inspection_issues"]
    )
    html = render_html(result)
    assert "Manually supplied by the user" in html
    assert "Original PDF Explanation — Manually Superseded" in html
    assert "bullet_structure_ambiguous:source_marker_preserved" in html
    assert "Original superseded explanation" in html
    report = tmp_path / "issues.md"
    write_report(data, report)
    assert "Manually Superseded Source Findings (1 records)" in report.read_text()


@pytest.mark.parametrize(
    "failure",
    [
        "answer_id",
        "source_sha256",
        "explanation_sha256",
        "answer",
        "duplicate",
        "no_approval",
        "fragment",
    ],
)
def test_invalid_or_ambiguous_replacements_are_not_forced(replacement_case, failure):
    case = replacement_case
    manual = json.loads(case[4].read_text(encoding="utf-8"))
    a = manual["answers"][0]
    if failure in ("answer_id", "source_sha256", "explanation_sha256"):
        a["provenance"]["replaces_explanation"][failure] = "wrong"
    elif failure == "answer":
        a["correct_answer"] = "B"
    elif failure == "duplicate":
        manual["answers"].append(deepcopy(a))
    elif failure == "no_approval":
        a["provenance"].pop("replaces_explanation")
    else:
        a["provenance"]["preserved_source_fragments"] = [
            {"order": 1, "text": "Invented"}
        ]
    case[4].write_text(json.dumps(manual), encoding="utf-8")
    data = run(case)
    assert data["records"][0]["status"] == "ambiguous"
    assert len(data["records"][0]["answer_candidates"]) >= 2
    assert not data["records"][0].get("superseded_answer_candidates")


@pytest.mark.parametrize("change", ["lost_text", "changed_item", "changed_evidence"])
def test_manual_import_rejects_loss_or_unverified_evidence(replacement_case, change):
    source = replacement_case[3]
    data = json.loads(source.read_text(encoding="utf-8"))
    if change == "lost_text":
        data["explanation_blocks"].pop()
    elif change == "changed_item":
        data["explanation_blocks"][1]["items"][0]["text"] = "Different"
    else:
        data["evidence"] = [{"path": str(source), "sha256": "wrong"}]
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        parse_manual(source)


def test_real_manual_definitions_and_protected_originals():
    root = Path("processors/matching/manual_sources")
    q12 = parse_manual(root / "tsa_2008_q012.json")["answers"][0]
    q38 = parse_manual(root / "tsa_2016_q038.json")["answers"][0]
    assert (q12["year"], q12["question_number"], q12["correct_answer"]) == (
        2008,
        12,
        "C",
    )
    assert "30Y + 10Z = 700" in q12["explanation"]["main_explanation"]
    assert q12["explanation"]["main_explanation"].endswith("the overtime rate is 25.")
    assert [i["text"] for i in q38["explanation"]["blocks"][1]["items"]] == [
        "Pip=28*54",
        "Eve=27*56",
        "Bob=24*63",
        "Viv-22*68",
        "Nan=21*72",
    ]
    assert "1*2 modulo 3" in q38["explanation"]["main_explanation"]
    assert q38["explanation"]["paragraphs"][-1]["text"].startswith(
        "This is an important takeaway"
    )


def test_real_manual_explanations_match_and_render_without_losing_originals():
    path = Path("data/merged/blackstone/tsa_2008-2016.matched.json")
    if not path.exists():
        pytest.skip("Run documented matching command with explicit manual supplements")
    digest = sha256(path.read_bytes()).hexdigest()
    for year, number, correct in ((2008, 12, "C"), (2016, 38, "E")):
        result = inspect_question(path, year=year, question_number=number)
        record = result["record"]
        assert record["status"] == "matched" and record["correct_answer"] == correct
        assert record["final_explanation"]["status"] == "available"
        assert not result["live_inspection_issues"]
        original = record["superseded_answer_candidates"][0]
        raw = json.loads(
            Path(original["reference"]["path"]).read_text(encoding="utf-8")
        )
        index = int(original["reference"]["json_pointer"].rsplit("/", 1)[1])
        assert raw["answers"][index] == original["record"]
        assert original["record"]["warnings"]
        html = render_html(result)
        assert "Manually supplied by the user" in html
        assert "Original PDF Explanation — Manually Superseded" in html
        if year == 2016:
            assert "Pip=28*54" in html and "Eve=27*56" in html
            assert len(record["answer"]["explanation"]["blocks"][1]["items"]) == 5
    assert sha256(path.read_bytes()).hexdigest() == digest
