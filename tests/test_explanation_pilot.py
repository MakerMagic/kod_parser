"""Offline provider transport, pilot limits, immutable inputs and QA integration."""

import ast
import io
import json
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError

import pytest
from test_ai_explanations import candidate, record

from processors.explanations.generator import (
    PROMPT,
    approve_after_quality_review,
    reject_after_quality_review,
    request_content,
    select_pilot,
)
from processors.explanations.generator import (
    run_pilot as run_unreviewed_pilot,
)
from processors.explanations.providers import GenerationError, GenerationResult
from processors.explanations.providers.gemini import DEFAULT_MODEL, GeminiProvider
from processors.explanations.validator import render_text, validate


def run_pilot(*args, **kwargs):
    """Explicit synthetic reviewer for pre-existing orchestration tests only.

    Production has no automatic reviewer. New semantic regressions call the
    unreviewed API and verify that structurally valid output stays pending.
    """
    from hashlib import sha256

    from processors.explanations.validator import semantic_review

    data = run_unreviewed_pilot(*args, **kwargs)
    for entry in list(data["explanation_pilot"]["audit"]):
        if entry["status"] != "semantic_review_pending":
            continue
        value = entry["candidate"]
        review = semantic_review(value)
        data = approve_after_quality_review(
            data,
            tuple(entry["identity"][f] for f in ("year", "section", "question_number")),
            reviewer="offline_synthetic_fixture_reviewer",
            candidate_sha256=sha256(
                json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest(),
            checks={
                part: "This synthetic fixture checks transport and storage behavior, not real examination reasoning."
                for part in review["parts"]
            },
            coexistence_checks={
                part: {
                    "contradiction_asserted": False,
                    "can_coexist": True,
                    "reason": "Synthetic fixture review only; no real entailment claim is being certified here.",
                }
                for part in review["coexistence_review_required"]
            },
        )
    return data


def output():
    value = candidate()
    value.pop("identity")
    return {"correct_answer": "C", **value}


def dataset(count=5):
    records = []
    for number in range(1, count + 1):
        value = record()
        value["identity"]["question_number"] = number
        records.append(value)
    return {"records": records}


def identities(count=5):
    return [(2017, "section_1", number) for number in range(1, count + 1)]


class FakeProvider:
    def __init__(self, content=None):
        self.content = output() if content is None else content
        self.requests = []

    def generate(self, prompt):
        self.requests.append(prompt)
        return GenerationResult(self.content, "fake", "test-model")


def test_model_environment_and_default(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert GeminiProvider().model == DEFAULT_MODEL
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    assert GeminiProvider().model == "test-model"


def test_generator_and_validator_do_not_import_provider_sdk():
    for name in ("generator", "validator"):
        source = Path(f"processors/explanations/{name}.py").read_text(encoding="utf-8")
        imports = [
            ast.unparse(node)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        assert not any("gemini" in item or "google" in item for item in imports)
        assert DEFAULT_MODEL not in source


def test_validation_complete_length_labels_and_meta():
    kwargs = {"options": record()["question"]["options"], "correct_answer": "C"}
    assert validate(output(), **kwargs) == []
    value = output()
    value["main_reasoning"] += "x" * 2000
    assert "explanation_too_long" in validate(value, **kwargs)
    value = output()
    value["incorrect_options"].pop()
    assert "incorrect_option_coverage" in validate(value, **kwargs)
    value = output()
    value["correct_answer"] = "A"
    assert "correct_answer_mismatch" in validate(value, **kwargs)
    value = output()
    value["main_reasoning"] += " As an AI I can explain option Z."
    assert "unknown_option_reference" in validate(value, **kwargs)
    assert "meta_commentary_or_extra_structure" in validate(value, **kwargs)
    value = output()
    value["incorrect_options"][1]["reason"] = value["incorrect_options"][0]["reason"]
    assert "duplicated_incorrect_option_reasons" in validate(value, **kwargs)
    value = output()
    value["main_reasoning"] += " Option C is wrong."
    assert "contradictory_correct_answer_claim" in validate(value, **kwargs)


def test_pilot_acceptance_is_separate_and_scoped():
    data, provider = dataset(6), FakeProvider()
    before = deepcopy(data)
    result = run_pilot(data, identities(), provider)
    assert data == before
    assert len(provider.requests) == 5
    assert result["explanation_pilot"]["counts"] == {"accepted": 5}
    assert result["records"][5] == before["records"][5]
    for value in result["records"][:5]:
        assert value["final_explanation"]["explanation_by_ai"] is True
        assert value["ai_explanation"]["validation_status"] == "accepted"
        assert value["ai_explanation"]["character_count"] == len(render_text(output()))
        assert value["answer"] == before["records"][0]["answer"]


def test_rejection_preserves_missing_explanation():
    provider = FakeProvider({"correct_answer": "A"})
    original = dataset()
    result = run_pilot(original, identities(), provider)
    assert result["explanation_pilot"]["counts"] == {"validation_rejected": 5}
    for old, new in zip(original["records"], result["records"], strict=True):
        assert old["final_explanation"] == new["final_explanation"]
        assert new["ai_explanation"]["explanation_by_ai"] is False
        assert new["ai_explanation"]["validation_errors"]


def test_one_regeneration_receives_feedback_without_previous_response():
    class RepairProvider:
        def __init__(self):
            self.requests = []

        def generate(self, prompt):
            self.requests.append(prompt)
            value = output()
            if len(self.requests) % 2:
                value["main_reasoning"] += " PRIOR_RESPONSE_SENTINEL"
                value["incorrect_options"].pop()
            return GenerationResult(value, "fake", "test-model", attempts=2)

    provider = RepairProvider()
    result = run_pilot(dataset(), identities(), provider)
    assert len(provider.requests) == 10
    assert result["explanation_pilot"]["counts"] == {"accepted": 5}
    for initial, retry in zip(
        provider.requests[::2], provider.requests[1::2], strict=True
    ):
        initial_data = json.loads(initial.split("QUESTION DATA:\n")[1])
        retry_data = json.loads(retry.split("QUESTION DATA:\n")[1])
        feedback = retry_data.pop("regeneration")
        assert feedback["validator_rejection_reasons"] == ["incorrect_option_coverage"]
        assert initial_data == retry_data
        assert "PRIOR_RESPONSE_SENTINEL" not in retry
        assert "Do not change the known answer" in feedback["instructions"]
    for entry, value in zip(
        result["explanation_pilot"]["audit"], result["records"], strict=True
    ):
        assert len(entry["generation_attempts"]) == 2
        meta = value["ai_explanation"]
        assert meta["first_attempt_validation_status"] == "rejected"
        assert meta["retry_attempted"] is True
        assert meta["retry_result"] == "accepted"
        assert meta["validation_status"] == "accepted"
        assert meta["attempts"] == 4  # transport calls across two generations


def test_failed_regeneration_is_not_accepted_or_retried_again():
    provider = FakeProvider({"correct_answer": "A"})
    result = run_pilot(dataset(), identities(), provider)
    assert len(provider.requests) == 10
    for entry, value in zip(
        result["explanation_pilot"]["audit"], result["records"], strict=True
    ):
        assert len(entry["generation_attempts"]) == 2
        assert value["ai_explanation"]["retry_result"] == "rejected"
        assert value["final_explanation"]["explanation_by_ai"] is False
        assert value["ai_explanation"]["generation_status"] == "validation_rejected"


def test_quality_retry_can_be_disabled_and_cannot_exceed_one():
    provider = FakeProvider({"correct_answer": "A"})
    run_pilot(dataset(), identities(), provider, quality_regenerations=0)
    assert len(provider.requests) == 5
    for invalid in (2, -1, True):
        with pytest.raises(ValueError, match="0 or 1"):
            run_pilot(dataset(), identities(), provider, quality_regenerations=invalid)
    assert len(provider.requests) == 5


def test_provider_failure_does_not_trigger_quality_regeneration():
    class FailingProvider:
        calls = 0

        def generate(self, prompt):
            self.calls += 1
            raise GenerationError("rate_limited", attempts=3)

    provider = FailingProvider()
    result = run_pilot(dataset(), identities(), provider)
    assert provider.calls == 5
    assert result["explanation_pilot"]["counts"] == {"provider_failure_exhausted": 5}
    assert not any(r["ai_explanation"]["retry_attempted"] for r in result["records"])


def test_retry_provider_failure_never_inherits_prior_acceptance():
    class BrokenRetry:
        calls = 0

        def generate(self, prompt):
            self.calls += 1
            if self.calls % 2:
                return GenerationResult({"correct_answer": "A"}, "fake", "test")
            raise GenerationError("timeout", attempts=3)

    provider = BrokenRetry()
    result = run_pilot(dataset(), identities(), provider)
    assert provider.calls == 10
    for r in result["records"]:
        assert r["ai_explanation"]["retry_result"] == "provider_failure_exhausted"
        assert r["ai_explanation"]["validation_status"] == "not_run"
        assert r["ai_explanation"]["character_count"] is None
        assert r["final_explanation"]["explanation_by_ai"] is False


def test_comparison_uses_saved_statuses_and_rejects_different_questions(tmp_path):
    from processors.explanations.comparison import write_comparison

    data = run_pilot(dataset(), identities(), FakeProvider())
    data.update(stage="matched", schema_version="1", issues=[])
    original = tmp_path / "first.matched.json"
    original.write_text(json.dumps(data), encoding="utf-8")
    report = tmp_path / "comparison.md"
    write_comparison([("First", original), ("Same", original)], report)
    text = report.read_text(encoding="utf-8")
    assert "Local validation: 5 accepted / 0 not accepted" in text
    assert "2017 Q1" in text and "test-model" in text
    other = tmp_path / "other.matched.json"
    data["explanation_pilot"]["selected_identities"][0][2] = 10
    other.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="same pilot"):
        write_comparison([("First", original), ("Other", other)], report)


def test_quality_review_can_reject_locally_accepted_candidate_without_losing_audit():
    original = run_pilot(dataset(), identities(), FakeProvider())
    result = reject_after_quality_review(
        original, identities()[0], ["The stated implication is unsupported."]
    )
    assert original["records"][0]["final_explanation"]["explanation_by_ai"] is True
    assert result["records"][0]["final_explanation"]["explanation_by_ai"] is False
    assert (
        result["records"][0]["ai_explanation"]["generation_status"]
        == "reasoning_review_rejected"
    )
    assert result["explanation_pilot"]["audit"][0]["candidate"] == output()
    assert result["explanation_pilot"]["counts"] == {
        "reasoning_review_rejected": 1,
        "accepted": 4,
    }


@pytest.mark.parametrize("count", [0, 4, 11, 100])
def test_pilot_bounds_prevent_provider_calls(count):
    provider = FakeProvider()
    with pytest.raises(ValueError, match="5–10"):
        run_pilot(dataset(max(5, count)), identities(count), provider)
    assert not provider.requests


def test_existing_uncertain_source_and_visuals_prevent_entire_pilot():
    data = dataset()
    data["records"][0]["answer"]["explanation"] = {
        "main_explanation": "Original source explanation."
    }
    with pytest.raises(ValueError, match="Existing explanation"):
        select_pilot(data, identities())
    data = dataset()
    data["records"][0]["question"]["visual_assets"] = [{"path": "image.png"}]
    with pytest.raises(ValueError, match="ineligible"):
        select_pilot(data, identities())


def test_minimal_request_omits_metadata_snapshots_and_other_questions():
    value = record()
    value["question"]["raw_record"] = {"secret_context": "NOT SENT"}
    request = request_content(value)
    assert request.startswith(PROMPT)
    assert "NOT SENT" not in request
    assert "2017" not in request


def test_transport_response_and_secret_header():
    requests = []

    def opener(request, *, timeout):
        requests.append((request, timeout))
        return io.BytesIO(
            json.dumps(
                {
                    "candidates": [
                        {
                            "finishReason": "STOP",
                            "content": {"parts": [{"text": json.dumps(output())}]},
                        }
                    ]
                }
            ).encode()
        )

    result = GeminiProvider(
        api_key="dummy-secret", model="test-model", opener=opener
    ).generate("one question")
    assert result.content == output()
    assert requests[0][1] == 45
    assert "dummy-secret" not in requests[0][0].full_url
    assert (
        json.loads(requests[0][0].data)["contents"][0]["parts"][0]["text"]
        == "one question"
    )


def test_auth_and_bounded_transient_failure(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(GenerationError, match="authentication_not_configured"):
        GeminiProvider().generate("q")
    calls = []

    def limited(*args, **kwargs):
        calls.append(1)
        raise HTTPError("https://example.com", 429, "private response", {}, None)

    with pytest.raises(GenerationError, match="rate_limited") as error:
        GeminiProvider(
            api_key="private-key", opener=limited, sleeper=lambda _: None
        ).generate("q")
    assert len(calls) == 3
    assert error.value.attempts == 3
    assert error.value.retryable is True
    assert "private" not in str(error.value)


def test_timeouts_are_bounded_and_auth_failure_is_not_retried():
    calls = []

    def timeout(*args, **kwargs):
        calls.append(1)
        raise TimeoutError

    with pytest.raises(GenerationError, match="timeout"):
        GeminiProvider(
            api_key="dummy", opener=timeout, sleeper=lambda _: None
        ).generate("q")
    assert len(calls) == 3
    calls.clear()

    def forbidden(*args, **kwargs):
        calls.append(1)
        raise HTTPError("https://example.com", 403, "private", {}, None)

    with pytest.raises(GenerationError, match="authentication_failed"):
        GeminiProvider(api_key="dummy", opener=forbidden).generate("q")
    assert len(calls) == 1
    with pytest.raises(GenerationError, match="invalid_api_key_configuration"):
        GeminiProvider(api_key="secret\nvalue")


@pytest.mark.parametrize(
    "body,code",
    [
        ({}, "empty_or_ambiguous_response"),
        (
            {"candidates": [{"finishReason": "STOP", "content": {"parts": []}}]},
            "empty_response",
        ),
        (
            {
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": "broken"}]}}
                ]
            },
            "malformed_response",
        ),
    ],
)
def test_malformed_empty_responses(body, code):
    provider = GeminiProvider(
        api_key="dummy", opener=lambda *a, **k: io.BytesIO(json.dumps(body).encode())
    )
    with pytest.raises(GenerationError, match=code):
        provider.generate("q")


def test_real_backtest_acceptance_and_rejection_visibility():
    from processors.matching.backtest import render_html
    from processors.matching.storage import load_matched

    path = Path("data/merged/blackstone/tsa_2017-2019.matched.json")
    if not path.exists():
        pytest.skip("Local matched data unavailable")
    data = load_matched(path)
    selected = [(2017, "section_1", n) for n in (1, 2, 3, 4, 5)]

    class Provider:
        def generate(self, prompt):
            values = json.loads(prompt.split("QUESTION DATA:\n")[1])
            return GenerationResult(
                {
                    "correct_answer": values["correct_answer"],
                    "main_reasoning": output()["main_reasoning"],
                    "incorrect_options": [
                        {
                            "label": o["label"],
                            "reason": "This option makes an unsupported additional claim about "
                            + o["text"],
                        }
                        for o in values["options"]
                        if o["label"] != values["correct_answer"]
                    ],
                },
                "fake",
                "test",
            )

    result = run_pilot(data, selected, Provider())
    first = result["records"][0]
    html = render_html({"record": first, "live_inspection_issues": []})
    assert "Explanation by AI: True" in html
    assert "validation_status" in html
    assert "A: " in html
    assert "First-attempt validation status: accepted" in html
    assert "Retry attempted: False" in html
    assert "Final validation status: accepted" in html
