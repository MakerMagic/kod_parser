"""Semantic triage cannot certify reasoning; Q5 calibrates the coexistence gate."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_explanation_pilot import FakeProvider, dataset, identities, output

from processors.explanations.generator import (
    PROMPT,
    approve_after_quality_review,
    reject_after_quality_review,
    run_pilot,
    select_pilot,
)
from processors.explanations.validator import (
    semantic_review,
    validate,
    validate_semantic_review,
)


def test_structurally_valid_candidate_is_not_accepted_without_reasoning_review():
    original = dataset()
    data = run_pilot(original, identities(), FakeProvider())
    assert data["explanation_pilot"]["counts"] == {"semantic_review_pending": 5}
    assert data["explanation_pilot"]["metrics"]["quality_evaluated"] == 0
    for before, after, audit in zip(
        original["records"],
        data["records"],
        data["explanation_pilot"]["audit"],
        strict=True,
    ):
        assert before["final_explanation"] == after["final_explanation"]
        assert not after["ai_explanation"]["explanation_by_ai"]
        assert audit["candidate"] == output()
        assert audit["semantic_review"]["status"] == "pending"


def q5_candidate():
    # TSA 2017 Q5 calibration. These coexist: inherited business talent and
    # being unlikely to be the best among all candidates. No runtime ID rule.
    return {
        "correct_answer": "B",
        "main_reasoning": "The argument needs a merit-based standard to move from unfair appointments to the demand for a ban. Option B supplies that required standard without alone proving the whole policy conclusion.",
        "incorrect_options": [
            {
                "label": "A",
                "reason": "Business talent running in families contradicts the premise that the son is unlikely to be the best candidate.",
            },
            {
                "label": "C",
                "reason": "Existing recognition of corruption is not needed for a fairness argument about appointments.",
            },
            {
                "label": "D",
                "reason": "Experience can matter without being irreplaceable in every possible appointment situation.",
            },
            {
                "label": "E",
                "reason": "Unrestricted owner choice is an opposing principle, not a premise the proposed restriction needs.",
            },
        ],
    }


def test_q5_false_contradiction_cannot_be_approved_with_coexistence_evidence():
    value = q5_candidate()
    assert (
        validate(
            value, options=[{"label": letter} for letter in "ABCDE"], correct_answer="B"
        )
        == []
    )
    checks = {
        part: "Review examines this specific claim against the argument rather than trusting its label."
        for part in semantic_review(value)["parts"]
    }
    coexistence = {
        "A": {
            "contradiction_asserted": True,
            "can_coexist": True,
            "reason": "A relative can possess inherited talent while better candidates still exist elsewhere.",
        }
    }
    with pytest.raises(ValueError, match="False contradiction"):
        validate_semantic_review(value, checks, coexistence)
    value["incorrect_options"][0]["reason"] = (
        "Inherited talent is not required by the argument; it could make relatives credible candidates without making them the best available."
    )
    assert validate_semantic_review(value, checks, {})["status"] == "pending"


@pytest.mark.parametrize(
    "word",
    [
        "necessary",
        "sufficient",
        "irrelevant",
        "weakens",
        "strengthens",
        "unsupported",
        "alternative explanation",
    ],
)
def test_logical_labels_trigger_review_not_automatic_truth(word):
    value = output()
    value["main_reasoning"] += " This claim is " + word + "."
    review = semantic_review(value)
    assert word in review["relationship_mentions"]["main_reasoning"]
    assert review["status"] == "pending"


def test_review_is_candidate_bound_and_requires_every_option():
    data = run_pilot(dataset(), identities(), FakeProvider())
    value = output()
    digest = sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    kwargs = {
        "reviewer": "test_reviewer",
        "candidate_sha256": digest,
        "checks": {},
        "coexistence_checks": {},
    }
    with pytest.raises(ValueError, match="substantive"):
        approve_after_quality_review(data, identities()[0], **kwargs)
    kwargs["candidate_sha256"] = "stale"
    with pytest.raises(ValueError, match="different candidate"):
        approve_after_quality_review(data, identities()[0], **kwargs)
    rejected = reject_after_quality_review(
        data,
        identities()[0],
        ["The claimed implication does not follow from the given premises."],
    )
    assert (
        rejected["records"][0]["ai_explanation"]["semantic_review_status"] == "rejected"
    )
    assert rejected["explanation_pilot"]["audit"][0]["candidate"] == value
    assert data["explanation_pilot"]["audit"][0]["status"] == "semantic_review_pending"


def test_explicit_calibration_does_not_relax_regular_pilot_guard():
    data = dataset()
    select_pilot(data, identities()[:1], calibration=True)
    with pytest.raises(ValueError):
        select_pilot(data, identities()[:1])
    with pytest.raises(ValueError):
        select_pilot(data, identities(), calibration=True)


def test_prompt_has_general_coexistence_and_assumption_rules_not_q5_wording():
    assert "both be true at the same time" in PROMPT
    assert "negate a candidate" in PROMPT
    assert "sufficient condition" in PROMPT
    assert "2000 characters" in PROMPT
    assert "business talent" not in PROMPT.lower()
    assert "boss" not in PROMPT.lower()


def test_negated_contradiction_mentions_are_reviewed_not_automatically_rejected():
    value = deepcopy(output())
    value["main_reasoning"] += (
        " These compatible statements do not contradict one another."
    )
    review = semantic_review(value)
    checks = {
        part: "The reviewer checks the stated relationship against the relevant question facts here."
        for part in review["parts"]
    }
    coexistence = {
        part: {
            "contradiction_asserted": False,
            "can_coexist": True,
            "reason": "The wording explicitly denies contradiction and the compatible claims can coexist here.",
        }
        for part in review["coexistence_review_required"]
    }
    validate_semantic_review(value, checks, coexistence)


def test_q5_real_record_and_backtest_preserve_bad_candidate_without_acceptance():
    from processors.matching.backtest import render_html
    from processors.matching.storage import load_matched

    path = Path("data/merged/blackstone/tsa_2017-2019.matched.json")
    if not path.exists():
        pytest.skip("Local matched record unavailable")
    source = load_matched(path)
    data = run_pilot(
        source, [(2017, "section_1", 5)], FakeProvider(q5_candidate()), calibration=True
    )
    entry = data["explanation_pilot"]["audit"][0]
    record = next(
        record
        for record in data["records"]
        if record["identity"]["question_number"] == 5
        and record["identity"]["year"] == 2017
    )
    assert entry["status"] == "semantic_review_pending"
    assert not record["final_explanation"]["blocks"]
    html = render_html(
        {
            "record": record,
            "live_inspection_issues": [],
            "explanation_candidate": entry["candidate"],
            "explanation_semantic_review": entry["semantic_review"],
        }
    )
    assert "Explanation by AI: False" in html
    assert "Semantic-review status: pending" in html
    assert "Candidate — Not Accepted: Semantic Review" in html
    assert "Business talent running in families contradicts" in html
    assert source != data


def test_disconnected_response_remains_bounded_transport_failure():
    from http.client import RemoteDisconnected

    from processors.explanations.providers import GenerationError
    from processors.explanations.providers.gemini import GeminiProvider

    calls = []

    def disconnected(request, **kwargs):
        calls.append(request.data)
        raise RemoteDisconnected("sensitive remote content must not be logged")

    provider = GeminiProvider(
        api_key="test-only", opener=disconnected, sleeper=lambda _: None
    )
    with pytest.raises(GenerationError, match="network_failure") as caught:
        provider.generate("identical request")
    assert caught.value.retryable
    assert caught.value.attempts == 3
    assert len(calls) == 3 and len(set(calls)) == 1
