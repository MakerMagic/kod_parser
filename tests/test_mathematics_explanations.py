import json

import pytest

from processors.explanations.mathematics import (
    artifacts,
    build,
    save,
    validate_explanation,
    validate_question,
)


def question(*, answer="A"):
    return {
        "id": "math_q001",
        "source_pdf": "math_1.pdf",
        "question_number": 1,
        "content_sha256": "question-hash",
        "main_body": [{"type": "text", "text": "Solve "}, {"type": "math", "latex": "2+3", "display": False}],
        "main_question": [{"type": "text", "text": "What is the value?"}],
        "main_answers": [
            {"label": "A", "content": [{"type": "math", "latex": "5", "display": False}]},
            {"label": "B", "content": [{"type": "math", "latex": "6", "display": False}]},
        ],
        "correct_answer": answer,
    }


def authored(q, text=r"\(2+3=5\), so choose A."):
    return {
        "id": q["id"],
        "source_pdf": q["source_pdf"],
        "question_number": q["question_number"],
        "content_sha256": q["content_sha256"],
        "correct_answer": q["correct_answer"],
        "final_explanation": {
            "status": "available",
            "ordering": "ai_generated_block_order",
            "blocks": [{"type": "paragraph", "role": "main", "order": 1, "text": text}],
            "unplaced_components": [],
            "omitted_artifacts": [],
            "issues": [],
            "source_type": "ai_generated_text_only",
            "explanation_by_ai": True,
            "source_reference": {
                "stage": "mathematics_pre_final",
                "question_id": q["id"],
                "content_sha256": q["content_sha256"],
            },
        },
    }


def prefinal(q):
    return {
        "domain": "mathematics",
        "stage": "mathematics_pre_final",
        "summary": {"ready_for_rendering": True, "blocking_issues": 0},
        "questions": [q],
    }


def test_directly_authored_explanation_is_hash_answer_bound_and_ai_flagged():
    q = question()
    record = authored(q)
    assert validate_explanation(q, record) == []
    output = build(prefinal(q), existing={"questions": [record]})
    assert output["questions"] == [record]
    assert output["questions"][0]["final_explanation"]["explanation_by_ai"] is True
    assert output["summary"]["explanations_authored"] == 1


@pytest.mark.parametrize("text", [
    r"\(2+3=5\), so choose A.",
    r"\[\frac{\sqrt{25}}{5}=1\] This gives the stored result.",
    r"\(2x+1=7\), hence \(x=3\).",
    r"\(x=2\). Substitution gives \(2^2+1=5\).",
    "A",
])
def test_math_explanation_forms_are_valid(text):
    q = question()
    assert validate_explanation(q, authored(q, text)) == []


def test_maximum_length_is_inclusive_and_no_minimum_is_imposed():
    q = question()
    assert validate_explanation(q, authored(q, "x" * 2000)) == []
    assert "explanation_exceeds_2000_characters" in validate_explanation(q, authored(q, "x" * 2001))
    assert "noncanonical_latex_delimiter" in validate_explanation(q, authored(q, "$2+3=5$"))


def test_stale_hash_answer_binding_and_missing_ai_flag_are_rejected():
    q = question()
    stale = authored(q)
    stale["content_sha256"] = "old-hash"
    stale["final_explanation"]["explanation_by_ai"] = False
    assert validate_explanation(q, stale) == ["missing_ai_provenance_flag", "stale_question_content_hash"]
    wrong = authored(q)
    wrong["correct_answer"] = "B"
    assert "stored_answer_binding_mismatch" in validate_explanation(q, wrong)


def test_missing_authored_text_is_an_explicit_issue_and_never_generated_by_code():
    q = question()
    output = build(prefinal(q))
    assert output["questions"] == []
    assert output["issues"][0]["code"] == "explanation_not_yet_authored"
    assert "No directly authored" in output["issues"][0]["reason"]


def test_directly_reported_issue_survives_deterministic_rebuilds():
    q = question()
    issue = {
        "id": q["id"],
        "source_pdf": q["source_pdf"],
        "question_number": q["question_number"],
        "content_sha256": q["content_sha256"],
        "code": "source_content_ambiguous",
        "reason": "The formula glyph is ambiguous in the canonical source.",
    }
    first = build(prefinal(q), existing={"questions": [], "issues": [issue]})
    second = build(prefinal(q), existing=first)
    assert first["issues"] == second["issues"] == [issue]


def test_explicit_issue_is_not_replaced_by_generic_missing_explanation_issue():
    q = question()
    explicit = {
        "id": q["id"],
        "source_pdf": q["source_pdf"],
        "question_number": q["question_number"],
        "content_sha256": q["content_sha256"],
        "code": "source_notation_ambiguous",
        "reason": "The stored variable glyph is ambiguous.",
    }
    generic = {**explicit, "code": "explanation_not_yet_authored", "reason": "Generic."}
    output = build(prefinal(q), existing={"questions": [], "issues": [explicit, generic]})
    assert output["issues"] == [explicit]
    assert output["summary"]["eligible_questions"] == 0


def test_incomplete_source_question_is_an_issue():
    q = question()
    q["correct_answer"] = "Z"
    assert validate_question(q)[0] == "source_answer_invalid"


def test_non_ready_pre_final_is_rejected():
    q = question()
    data = prefinal(q)
    data["summary"]["ready_for_rendering"] = False
    with pytest.raises(ValueError, match="ready PRE-FINAL"):
        build(data)


def test_artifacts_are_generated_from_structured_output_even_when_issue_free(tmp_path):
    q = question()
    output = build(prefinal(q), existing={"questions": [authored(q)]})
    backtesting, issues = artifacts(output)
    assert "Explanations authored and validated: 1" in backtesting
    assert "Total issues: 0" in issues
    target = tmp_path / "data" / "explanations.json"
    docs = tmp_path / "docs"
    save(output, target, docs)
    assert json.loads(target.read_text(encoding="utf8"))["questions"][0]["final_explanation"]["explanation_by_ai"] is True
    assert (docs / "EXPLANATION_BACKTESTING.md").is_file()
    assert (docs / "EXPLANATION_ISSUES.md").is_file()
