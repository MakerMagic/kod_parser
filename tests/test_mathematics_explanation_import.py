from copy import deepcopy

import pytest

from processors.explanations.mathematics import build, validate_explanation
from processors.explanations.mathematics_import import import_reviewed, record, text_digest
from processors.explanations.mathematics_latex import validate
from test_mathematics_explanations import question, prefinal


def decision(q, text):
    return {
        q["id"]: {
            "status": "approved",
            "explanation_sha256": text_digest(text),
            "question_content_sha256": q["content_sha256"],
        }
    }


def test_import_binds_id_preserves_exact_text_and_sets_ai_flag():
    q = question()
    text = r"\[\frac12+\frac92=5.\] Choose A."
    data, audit = import_reviewed(
        prefinal(q), {"questions": []}, [{"id": q["id"], "explanation": text}],
        decision(q, text), source={"path": "provided.json", "sha256": "s"},
    )
    row = data["questions"][0]
    assert row["final_explanation"]["blocks"][0]["text"] == text
    assert row["final_explanation"]["explanation_by_ai"] is True
    assert validate_explanation(q, row) == []
    assert audit[0]["status"] == "imported"


def test_duplicates_unknown_null_and_existing_conflicts_are_explicit():
    q = question()
    text = r"\(2+3=5\), option A."
    original = record(q, text)
    old = {"questions": [original]}
    candidates = [
        {"id": q["id"], "explanation": text},
        {"id": "unknown", "explanation": text},
        {"id": "duplicate", "explanation": text},
        {"id": "duplicate", "explanation": None},
    ]
    result, audit = import_reviewed(prefinal(q), old, candidates, decision(q, text), source={})
    assert result == old
    assert [a["status"] for a in audit] == [
        "existing_preserved", "unknown_id", "duplicate_id", "duplicate_id",
    ]
    _, audit = import_reviewed(prefinal(q), old, [{"id": q["id"], "explanation": None}], {}, source={})
    assert audit[0]["status"] == "no_explanation_supplied"


def test_review_is_invalidated_by_text_or_question_changes():
    q = question()
    text = r"\(2+3=5\)."
    reviewed = decision(q, text)
    q["content_sha256"] = "changed"
    data, audit = import_reviewed(prefinal(q), {"questions": []}, [{"id": q["id"], "explanation": text}], reviewed, source={})
    assert not data["questions"]
    assert audit[0]["status"] == "unreviewed"


@pytest.mark.parametrize("formula", [
    r"\boxed{\frac12}", r"\binom82\binom21", r"\sqrt2+\sqrt[3]4",
    r"\int_{-2}^2(2-x^2/2)\,dx", r"\sum_{k=1}^{500}k",
    r"\frac15\implies x\ge2", r"\$4.25", r"n\equiv3\pmod5",
])
def test_standard_explanation_latex_is_supported_without_rewriting(formula):
    assert validate(formula) == []


@pytest.mark.parametrize("formula", [r"\frac{1}{", r"\sqrt", r"\bogus{x}", r"x^{2", r"\♪"])
def test_invalid_explanation_latex_is_rejected(formula):
    assert validate(formula)


def test_orphan_math_commands_and_duplicate_explanation_records_fail():
    q = question()
    assert "math_command_outside_math_delimiters" in validate_explanation(q, record(q, r"Use \sqrt{25}=5."))
    r = record(q, r"\(2+3=5\).")
    with pytest.raises(ValueError, match="Duplicate"):
        build(prefinal(q), existing={"questions": [r, deepcopy(r)]})
