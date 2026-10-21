"""Independent official-source extraction, inference and generic matching QA."""

import json
import re
import socket
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
import pytest
from test_blackstone_raw import write_pdf
from test_matching import match_case as shared_matching_case

from parsers.official_2020_answers import parse_pdf, validate_answers
from parsers.official_2020_answers.inference import infer_answer
from processors.matching.__main__ import main as match_main
from processors.matching.backtest import inspect_question, render_html
from processors.matching.core import (
    existing_question_source_conflicts,
    match_records,
    verify_question_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
match_case = shared_matching_case


@pytest.mark.parametrize(
    "text,label",
    [
        ("The principle is illustrated in option B.", "B"),
        ("The CORRECT answer is\noption C.", "C"),
        ("This assumption is expressed in option D.", "D"),
        ("This conclusion is expressed in option E.", "E"),
        ("Option A expresses the main conclusion.", "A"),
        ("Option B identifies this erroneous step in the reasoning.", "B"),
        ("Option C illustrates this principle.", "C"),
        ("The passage and option D both share the same underlying structure.", "D"),
        ("Option E expresses this erroneous step in the argument.", "E"),
        ("Option A is a statement of the main conclusion.", "A"),
        ("This follows from the condition, which is stated in option B.", "B"),
        ("Option C illustrates the same principle.", "C"),
        ("Option D states the main conclusion.", "D"),
        ("From this information we can draw option C as a conclusion.", "C"),
        ("Option A supplies this connection: wellbeing requires cohesion.", "A"),
    ],
)
def test_answer_assertion_families(text, label):
    result = infer_answer(text)
    assert result["correct_answer"] == label
    assert result["evidence"] and result["status"] == "resolved"


@pytest.mark.parametrize(
    "text",
    [
        "Option A is incorrect. Option B does not state the flaw.",
        "We cannot draw option C as a conclusion.",
        "Option B illustrates a different principle.",
        "If option A states the main conclusion, it would be relevant.",
        "It is not true that option C states the main conclusion.",
        "Option A is correct. The correct answer is option B.",
        "The answer might be A or B.",
        "Option A weakens the argument.",  # No weakening prompt supplied.
    ],
)
def test_negative_hypothetical_unresolved_and_conflicting_mentions(text):
    assert infer_answer(text)["correct_answer"] is None


def test_weakening_is_conditioned_on_the_actual_prompt():
    text = "Option D weakens the inference to the intermediate conclusion. Option B has the potential to strengthen the argument."
    assert (
        infer_answer(text, "Which option weakens the argument?")["correct_answer"]
        == "D"
    )
    assert infer_answer(text, "Which option strengthens it?")["correct_answer"] is None


def synthetic(tmp_path, *, missing=False, continuation=False):
    source = write_pdf(
        tmp_path / "arbitrary-name.pdf",
        [
            [(50, 750, "TSA 2020 Section 1 explained answers")],
            [
                (
                    50,
                    740,
                    "1 A sufficiently long question introduction for identity verification.",
                ),
                (80, 710, "A sentence in the question is not option A."),
                (80, 680, "Which choice is supported?"),
                (80, 640, "A First answer"),
                (105, 626, "and its wrapped continuation."),
                (80, 600, "B Second answer"),
                (80, 570, "C Third answer"),
                (80, 540, "D Fourth answer"),
                (80, 510, "E Fifth answer"),
            ]
            + (
                []
                if missing
                else [
                    (50, 440, "The correct answer is option A."),
                    (50, 425, "This remains in the same paragraph."),
                    (50, 390, "Option B fails because the premise rules it out."),
                    (50, 375, "All option discussion stays in the full explanation."),
                ]
            ),
            [
                (
                    50,
                    740,
                    "2 Another complete question with no carryover from question one.",
                ),
                (80, 690, "Which statement is supported?"),
                (80, 640, "A Alpha"),
                (80, 610, "B Beta"),
                (80, 580, "C Gamma"),
                (80, 550, "D Delta"),
                (80, 520, "E Epsilon"),
                (50, 440, "This conclusion is expressed in option B."),
            ],
        ]
        + (
            [[(50, 740, "Unrecognised explanation continuation must be reviewed.")]]
            if continuation
            else []
        ),
    )
    return source, parse_pdf(source, asset_dir=tmp_path / "answers/assets")


def test_question_options_full_explanation_raw_spans_and_no_network(
    tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Parser must not acquire source documents")

    monkeypatch.setattr(socket, "socket", forbidden)
    source, data = synthetic(tmp_path)
    first, second = data["answers"]
    assert [a["question_number"] for a in data["answers"]] == [1, 2]
    assert [a["correct_answer"] for a in data["answers"]] == ["A", "B"]
    assert [o["label"] for o in first["question_evidence"]["options"]] == list("ABCDE")
    assert (
        first["question_evidence"]["options"][0]["text"]
        == "First answer\nand its wrapped continuation."
    )
    assert "A sentence in the question" in first["question_evidence"]["question_text"]
    exp = first["explanation"]
    assert len(exp["blocks"]) == 1
    assert not exp["choice_analysis"] and not exp["other_lists"]
    assert "\n\nOption B" in exp["main_explanation"]
    assert "First answer" not in exp["main_explanation"]
    assert "Another complete question" not in exp["main_explanation"]
    assert "option A" not in second["explanation"]["main_explanation"]
    with pdfplumber.open(source) as pdf:
        assert [p["raw_text"] for p in data["pages"]] == [
            p.extract_text() or "" for p in pdf.pages
        ]
    validate_answers(data)
    changed = deepcopy(data)
    changed["answers"][0]["raw"]["source_excerpt"] += "invented"
    with pytest.raises(ValueError, match="span changed"):
        validate_answers(changed)


def test_missing_explanation_preserved_unresolved(tmp_path):
    _, data = synthetic(tmp_path, missing=True)
    first = data["answers"][0]
    assert first["correct_answer"] is None
    assert first["warnings"]
    assert first["visual_previews"]  # Whole original page still reviewable.
    assert not first["explanation"]["blocks"]


def test_unexpected_continuation_is_not_silently_discarded(tmp_path):
    _, data = synthetic(tmp_path, continuation=True)
    assert data["answers"][-1]["correct_answer"] is None
    assert "continuation" in data["pages"][-1]["raw_text"]
    assert any(
        "possible_continuation_page" in w for w in data["answers"][-1]["warnings"]
    )


def test_existing_source_manual_explanations_and_answers_cannot_be_silently_overwritten():
    record = {
        "identity": {"year": 2020, "section": "section_1", "question_number": 1},
        "correct_answer": "A",
        "answer": {
            "correct_answer": "A",
            "question_evidence": {},
            "source_document": {"sha256": "source"},
        },
        "final_explanation": {"status": "available", "blocks": [{"text": "Original"}]},
    }
    data = {"records": [record]}
    assert not existing_question_source_conflicts(data, deepcopy(data))
    old = deepcopy(data)
    old["records"][0]["correct_answer"] = "B"
    assert existing_question_source_conflicts(data, old)
    old = deepcopy(data)
    old["records"][0]["final_explanation"]["blocks"][0]["text"] = "Manual explanation"
    old["records"][0]["answer"]["source_document"]["sha256"] = "manual_source"
    assert existing_question_source_conflicts(data, old)


def test_optional_source_question_verification_blocks_wrong_identity(
    match_case,
):
    clean_path, answer_path, data = match_case
    clean = json.loads(clean_path.read_text(encoding="utf-8"))["questions"][0]
    answer = data["answers"][0]
    answer["question_evidence"] = {
        "question_text": "Another unrelated question with a sufficiently long opening sentence.",
        "options": clean["options"],
    }
    answer_path.write_text(json.dumps(data), encoding="utf-8")
    result = match_records([clean_path], [answer_path], years={2008})
    r = result["records"][0]
    assert r["status"] == "conflict"
    assert r["correct_answer"] is None
    assert any(i["code"] == "source_question_content_conflict" for i in r["issues"])


def test_source_verification_requires_both_prose_and_options():
    question = {
        "question_text": "This is a sufficiently long introductory sentence to identify the source question.",
        "options": [{"label": "A", "text": "First"}, {"label": "B", "text": "Second"}],
    }
    answer = {"question_evidence": deepcopy(question)}
    assert verify_question_evidence(answer, question) is True
    answer["question_evidence"]["options"][1]["text"] = "Conflicting content"
    assert verify_question_evidence(answer, question) is False


@pytest.mark.parametrize(
    "source,target", [("-3", "3"), ("0.5", "05"), ("x < 4", "x > 4"), ("£50", "$50")]
)
def test_source_verification_does_not_erase_mathematical_mismatches(source, target):
    text = "This is a sufficiently long introductory sentence to identify the source question."
    answer = {
        "question_evidence": {
            "question_text": text,
            "options": [{"label": "A", "text": source}],
        }
    }
    question = {"question_text": text, "options": [{"label": "A", "text": target}]}
    assert verify_question_evidence(answer, question) is False


@pytest.fixture(scope="module")
def real_source(tmp_path_factory):
    path = ROOT / "acquisition/local/critical_thinking_problem_solving/tsa/TSA-2020-Explained-Answers-official.pdf"
    if not path.exists():
        pytest.skip("Optional local official 2020 source unavailable")
    directory = tmp_path_factory.mktemp("official2020")
    data = parse_pdf(path, asset_dir=directory / "answers/assets")
    answer_path = directory / "answers/official.answers.json"
    answer_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    clean = next((ROOT / "data/clean/blackstone").glob("*2020*.clean.json"))
    return data, answer_path, clean, directory


def test_all_real_questions_inference_numbering_traceability_and_independent_backend(
    real_source,
):
    data, path, clean_path, _ = real_source
    assert len(data["answers"]) == 50
    assert [a["question_number"] for a in data["answers"]] == list(range(1, 51))
    assert not data["issues"]
    clean = json.loads(clean_path.read_text(encoding="utf-8"))["questions"]
    anchors = {1: "A", 3: "A", 9: "C", 10: "C", 15: "D", 23: "B"}

    def compact(text):
        return "".join(re.findall(r"[^\W_]", text.casefold()))

    with pdfium.PdfDocument(data["source_document"]["path"]) as doc:
        for a, q in zip(data["answers"], clean):
            n = a["question_number"]
            assert a["correct_answer"] in "ABCDE"
            assert verify_question_evidence(a, q) is True
            if n in anchors:
                assert a["correct_answer"] == anchors[n]
            exp = a["explanation"]
            assert len(exp["blocks"]) == 1 and not exp["choice_analysis"]
            assert (
                a["raw"]["boundary_evidence"]["start"]
                > a["raw"]["boundary_evidence"]["anchors"][-1]["line_index"]
            )
            p = doc[a["page_reference"]["start_page"] - 1]
            tp = p.get_textpage()
            try:
                independent = compact(tp.get_text_range())
                for evidence in a["answer_inference"]["evidence"]:
                    assert compact(evidence["text"]) in independent
                assert compact(exp["main_explanation"]) in independent
            finally:
                tp.close()
                p.close()
            preview = a["visual_previews"][0]
            assert (
                sha256((path.parent / preview["path"]).read_bytes()).hexdigest()
                == preview["sha256"]
            )


def test_all_real_matches_and_full_explanation_html(real_source):
    data, path, clean, folder = real_source
    output = match_records([clean], [path], years={2020}, question_source="blackstone")
    assert output["readiness"]["ready"]
    assert len(output["records"]) == 50
    assert all(r["status"] == "matched" for r in output["records"])
    assert not output["issues"]
    merged = folder / "merged/2020.matched.json"
    merged.parent.mkdir()
    merged.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    for n in [1, 3, 9, 10, 15, 23, 38, 50]:
        result = inspect_question(merged, year=2020, question_number=n)
        html = render_html(result)
        assert "<h2>Full Explanation</h2>" in html
        assert "<h2>Incorrect Answer Explanations</h2>" not in html
        assert "<h2>Other Explanation Lists</h2>" not in html
        assert "<h2>Correct-Answer Inference</h2>" in html
        assert "Explanation by AI: False" in html
        assert not any(
            i["code"] == "inspection_reference_unavailable"
            for i in result["live_inspection_issues"]
        )
        r = result["record"]
        assert r["final_explanation"]["status"] == "available"
        assert (
            r["final_explanation"]["blocks"][0]["text"]
            == data["answers"][n - 1]["explanation"]["main_explanation"]
        )


def test_cli_retains_existing_explanation_on_conflict(real_source):
    _, answers, clean, folder = real_source
    data = match_records([clean], [answers], years={2020}, question_source="blackstone")
    data["records"][0]["correct_answer"] = "B"
    output = folder / "existing/2020.matched.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(data), encoding="utf-8")
    before = output.read_bytes()
    report = folder / "qa/issues.md"
    with pytest.raises(SystemExit):
        match_main(
            [
                "--clean-json",
                str(clean),
                "--answers-json",
                str(answers),
                "--years",
                "2020",
                "--output",
                str(output),
                "--issues-report",
                str(report),
                "--overwrite",
            ]
        )
    assert output.read_bytes() == before
    assert "Existing Answer Explanation Conflict" in report.read_text(encoding="utf-8")
