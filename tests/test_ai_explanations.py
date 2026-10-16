"""Strict validation for separately stored text-only AI explanations."""

import json
from copy import deepcopy

from processors.matching.ai_explanations import (
    apply_candidates,
    audit_data,
    eligibility,
    validate_candidate,
)
from processors.matching.explanation import build_final_explanation


def record(*, visual=False, warning=False, correct="C"):
    question = {
        "question_text": "Every metal in the set conducts electricity. Which conclusion follows?",
        "main_question": "Which conclusion follows?",
        "main_body": [
            {"type": "text", "text": "Every metal in the set conducts electricity."}
        ],
        "options": [
            {
                "label": "A",
                "text": "No metal conducts electricity.",
                "images": [],
                "warnings": [],
            },
            {
                "label": "B",
                "text": "Some non-metals conduct electricity.",
                "images": [],
                "warnings": [],
            },
            {
                "label": "C",
                "text": "Each metal in the set conducts electricity.",
                "images": [],
                "warnings": [],
            },
            {
                "label": "D",
                "text": "Only metals conduct electricity.",
                "images": [],
                "warnings": [],
            },
        ],
        "visual_assets": [{"path": "chart.png"}] if visual else [],
        "images": [],
        "cleaning_issues": [{"code": "incomplete"}] if warning else [],
        "raw_warnings": [],
    }
    return {
        "identity": {"year": 2017, "section": "section_1", "question_number": 1},
        "status": "matched",
        "correct_answer": correct,
        "question": question,
        "answer": {"explanation": {"availability": "not_supplied_by_source_format"}},
        "final_explanation": build_final_explanation(
            {"explanation": {"availability": "not_supplied_by_source_format"}}
        ),
    }


def candidate():
    return {
        "identity": {"year": 2017, "section": "section_1", "question_number": 1},
        "main_reasoning": "The premise states a universal rule: every member of the specified metal set conducts electricity. Option C restates exactly that consequence, without adding any claim about substances outside the set.",
        "incorrect_options": [
            {
                "label": "A",
                "reason": "A directly reverses the stated rule, since the premise says that every metal in the set does conduct electricity.",
            },
            {
                "label": "B",
                "reason": "B concerns non-metals, but the premise gives no information about non-metals or whether any of them conduct electricity.",
            },
            {
                "label": "D",
                "reason": "D turns the one-way claim about the metal set into an exclusive claim about all conductors, which the premise never establishes.",
            },
        ],
    }


def test_eligibility_excludes_visual_and_unresolved_questions():
    assert eligibility(record())[0] == "eligible"
    assert eligibility(record(visual=True))[0] == "skipped_visual_dependency"
    assert (
        eligibility(record(warning=True))[0] == "skipped_missing_or_incomplete_question"
    )


def test_candidate_requires_every_distinct_incorrect_option_reason():
    assert validate_candidate(record(), candidate()) == []
    duplicate = candidate()
    duplicate["incorrect_options"][1]["reason"] = duplicate["incorrect_options"][0][
        "reason"
    ]
    assert "incorrect_option_reasons_duplicated" in validate_candidate(
        record(), duplicate
    )
    incomplete = candidate()
    incomplete["incorrect_options"].pop()
    assert "incorrect_option_labels_do_not_match_question" in validate_candidate(
        record(), incomplete
    )


def test_apply_creates_separate_ai_final_explanation_and_keeps_input_unchanged(
    tmp_path,
):
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(
        json.dumps({"format": "text_only_explanation_v2", "candidates": [candidate()]}),
        encoding="utf-8",
    )
    original = {"records": [record()]}
    before = deepcopy(original)
    updated = apply_candidates(original, [candidate()], candidates_path)
    saved = updated["records"][0]
    assert original == before
    assert saved["final_explanation"]["explanation_by_ai"] is True
    assert saved["ai_explanation"]["generation_status"] == "generated"
    assert [
        item["label"] for item in saved["final_explanation"]["blocks"][1]["items"]
    ] == ["A", "B", "D"]
    assert updated["ai_explanations"]["status_counts"] == {"successfully_generated": 1}


def test_unlisted_eligible_records_fail_closed_instead_of_becoming_explanations(
    tmp_path,
):
    candidates_path = tmp_path / "empty.json"
    candidates_path.write_text("{}", encoding="utf-8")
    updated = apply_candidates({"records": [record()]}, [], candidates_path)
    saved = updated["records"][0]
    assert saved["ai_explanation"]["generation_status"] == "failed_validation"
    assert saved["final_explanation"]["explanation_by_ai"] is False
    assert updated["ai_explanations"]["status_counts"] == {
        "failed_generation_or_validation": 1
    }


def test_audit_reports_eligible_records_without_claiming_generation():
    audited = audit_data({"records": [record()]})
    assert audited["ai_explanations"]["status_counts"] == {
        "eligible_pending_generation": 1
    }
    assert audited["records"][0]["final_explanation"]["explanation_by_ai"] is False
