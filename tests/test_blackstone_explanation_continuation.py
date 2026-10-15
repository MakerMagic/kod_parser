"""Complete list continuations, ordinal gaps and explicit manual provenance."""

import json
import re
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_blackstone_explained_answers import parse_case
from test_matching import match_case as shared_matching_case

from parsers.blackstone_explained_answers.structure import structure
from parsers.manual_explanations import main as import_manual
from parsers.manual_explanations import parse_manual
from processors.matching.backtest import inspect_question, render_inspection
from processors.matching.core import match_records, validate_answer_input

ROOT = Path(__file__).resolve().parents[1]
MANUAL_TEXT = "Each event can give 10, 6, 3, or 1 point, and a student can enter at most three events. We test the options: 15 = 6 + 6 + 3, 22 = 10 + 6 + 6, but 24 cannot be made using any combination of at most three of these scores. Therefore, the lowest impossible score is 24 (C)."


def rows(values):
    result, offset = [], 0
    for i, (page, x, y, value) in enumerate(values, 1):
        result.append(
            {
                "page": page,
                "line_id": i,
                "text": value,
                "start": offset,
                "end": offset + len(value),
                "bbox": [x, y, x + len(value) * 5, y + 11],
            }
        )
        offset += len(value) + 1
    return result


def test_prose_list_wrapped_bullet_and_prose_remain_one_explanation():
    source = rows(
        [
            (1, 40, 0, "The introductory paragraph ends here."),
            (1, 40, 15, "The possible results are:"),
            (1, 40, 30, "- First result has a wrapped"),
            (1, 48, 45, "continuation across lines."),
            (2, 40, 0, "- Second result."),
            (2, 40, 15, "The final prose remains in this explanation."),
        ]
    )
    result, warnings = structure(source, "C")
    assert [b["type"] for b in result["blocks"]] == [
        "paragraph",
        "paragraph",
        "list",
        "paragraph",
    ]
    assert result["blocks"][1]["text"] == "The possible results are:"
    assert [i["text"] for i in result["bulleted_blocks"][0]["items"]] == [
        "First result has a wrapped\ncontinuation across lines.",
        "Second result.",
    ]
    assert result["paragraphs"][-1]["text"].startswith("The final prose")
    assert not warnings


@pytest.mark.parametrize(
    "text", ["A colon is normal: it continues the sentence.", "There is a label:"]
)
def test_colon_without_real_items_is_not_a_list_or_forced_paragraph(text):
    result, _ = structure(
        rows(
            [
                (1, 40, 0, "Ordinary prose."),
                (1, 40, 15, text),
                (1, 40, 30, "This remains ordinary prose."),
            ]
        ),
        "A",
    )
    assert len(result["paragraphs"]) == 1 and not result["bulleted_blocks"]


def test_ordinal_gap_alone_does_not_invalidate_complete_previous_explanation(tmp_path):
    _, data = parse_case(
        tmp_path,
        [
            [
                (40, 775, "TSA SECTION 1 - 2021"),
                (40, 735, "1) The correct answer is A"),
                (40, 710, "A complete explanation."),
                (40, 650, "3) The correct answer is C"),
                (40, 625, "Another complete explanation."),
            ]
        ],
    )
    assert not data["answers"][0]["warnings"]
    assert (
        data["answers"][0]["explanation"]["main_explanation"]
        == "A complete explanation."
    )
    assert any(
        i["code"] == "answer_header_missing" and i["question_number"] == 2
        for i in data["issues"]
    )
    assert [a["question_number"] for a in data["answers"]] == [1, 3]


@pytest.fixture
def manual_case(tmp_path):
    clean, _, parsed = shared_matching_case.__wrapped__(tmp_path)
    question = json.loads(clean.read_text(encoding="utf-8"))["questions"][0]
    source = tmp_path / "approved/source.json"
    source.parent.mkdir()
    payload = json.loads(
        (ROOT / "processors/matching/manual_sources/tsa_2022_q046.json").read_text(
            encoding="utf-8"
        )
    )
    payload.update(
        year=2008,
        question_number=12,
        correct_answer="A",
        target_question_key=question["source_question_key"],
        verification="Explicit single-question test fixture",
    )
    payload["related_source_document"] = {
        k: parsed["source_document"][k] for k in ("path", "sha256")
    }
    source.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "manual/one.answers.json"
    assert import_manual([str(source), "--output", str(output)]) == 0
    return clean, source, output


def test_manual_source_is_explicit_scoped_exact_and_traceable(manual_case):
    clean, source, output = manual_case
    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data["answers"]) == 1
    answer = data["answers"][0]
    assert answer["explanation"]["main_explanation"] == MANUAL_TEXT
    assert answer["provenance"]["origin"] == "user_supplied_manual"
    assert answer["raw"]["page_spans"] == []
    assert answer["page_reference"] == {"start_page": None, "end_page": None}
    assert answer["provenance"]["text_reference"]["json_pointer"] == "/explanation_text"
    validate_answer_input(data, output)
    result = match_records([clean], [output], years={2008})
    assert result["records"][0]["status"] == "matched"
    altered = deepcopy(data)
    altered["answers"][0]["target_question_key"]["paper"] = "different paper"
    output.write_text(json.dumps(altered), encoding="utf-8")
    assert (
        match_records([clean], [output], years={2008})["records"][0]["status"]
        == "conflict"
    )
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not match_records([clean], [output], years={2008})["readiness"]["ready"]


def test_manual_source_never_overrides_duplicate_or_other_questions(manual_case):
    clean, _, output = manual_case
    data = json.loads(output.read_text(encoding="utf-8"))
    data["answers"].append(deepcopy(data["answers"][0]))
    output.write_text(json.dumps(data), encoding="utf-8")
    assert (
        match_records([clean], [output], years={2008})["records"][0]["status"]
        == "ambiguous"
    )
    data["answers"] = data["answers"][:1]
    data["answers"][0]["question_number"] = 99
    output.write_text(json.dumps(data), encoding="utf-8")
    results = match_records([clean], [output], years={2008})["records"]
    assert any(r["status"] == "unmatched_question" for r in results)
    assert not any(r["status"] == "matched" for r in results)


def test_changed_related_pdf_blocks_manual_matching(manual_case):
    clean, _, output = manual_case
    data = json.loads(output.read_text(encoding="utf-8"))
    related = Path(data["source_document"]["related_sources"][0]["path"])
    related.write_bytes(related.read_bytes() + b"\nchanged fixture")
    with pytest.raises(ValueError, match="Related answer source"):
        validate_answer_input(data, output)
    assert not match_records([clean], [output], years={2008})["readiness"]["ready"]


def test_manual_import_rejects_identity_mismatch_and_missing_approval(manual_case):
    _, source, _ = manual_case
    data = json.loads(source.read_text(encoding="utf-8"))
    data["year"] = 2026
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        parse_manual(source)
    data["approval"] = "automatic_fallback"
    source.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="approve one question"):
        parse_manual(source)


def test_real_q45_and_manual_q46_backtest_complete_in_order_and_read_only():
    path = ROOT / "data/merged/blackstone/tsa_2022.matched.json"
    if not path.exists():
        pytest.skip("Run documented source + manual + matching commands")
    before = sha256(path.read_bytes()).hexdigest()
    q45 = inspect_question(path, year=2022, question_number=45)
    answer = q45["record"]["answer"]
    assert (
        q45["record"]["status"] == "matched" and q45["record"]["correct_answer"] == "B"
    )
    blocks = answer["explanation"]["blocks"]
    assert [b["type"] for b in blocks] == [
        "paragraph",
        "paragraph",
        "paragraph",
        "list",
        "paragraph",
    ]
    assert [b["text"] for b in blocks if b["type"] == "paragraph"] == [
        "The reasoning is flawed, and is that because something is ostensibly visible, it shows that some\nopinion or fact is true - whilst it may in fact not be.",
        "A student can enter a maximum of three events. The highest points they can earn in one event is 10\npoints for 1st place.",
        "Three possible combinations of points a student can earn are:",
        "The scores of 30, 26, and 19 can be made, as can all scores below them except for 24. Therefore, the\nlowest score that is not possible for a student to achieve is 24 points.",
    ]
    assert [item["text"] for item in blocks[3]["items"]] == [
        "Three 1st places: 10 + 10 + 10 = 30 points",
        "Two 1st places and one 2nd place: 10 + 10 + 6 = 26 points",
        "One 1st place, one 2nd place, and one 3rd place: 10 + 6 + 3 = 19 points",
    ]
    assert (
        blocks[2]["text"]
        == "Three possible combinations of points a student can earn are:"
    )
    assert len(blocks[3]["items"]) == 3
    assert blocks[-1]["text"].endswith(
        "lowest score that is not possible for a student to achieve is 24 points."
    )
    html = render_inspection(q45, "html")
    body = re.search(
        r"<section id='main-explanation'>(.*?)</section>", html, re.DOTALL
    )[1]
    fragments = [
        "The reasoning is flawed",
        "A student can enter",
        "Three possible combinations",
        "Three 1st places",
        "Two 1st places",
        "One 1st place",
        "The scores of 30",
    ]
    assert [body.index(s) for s in fragments] == sorted(
        body.index(s) for s in fragments
    )
    assert body.count("<li ") == 3 and "<ul>" in body
    q46 = inspect_question(path, year=2022, question_number=46)
    assert (
        q46["record"]["status"] == "matched" and q46["record"]["correct_answer"] == "C"
    )
    assert q46["record"]["answer"]["explanation"]["main_explanation"] == MANUAL_TEXT
    assert q46["record"]["answer"]["provenance"]["origin"] == "user_supplied_manual"
    assert "Manually supplied by the user" in render_inspection(q46, "html")
    assert not q45["live_inspection_issues"] and not q46["live_inspection_issues"]
    assert sha256(path.read_bytes()).hexdigest() == before
