"""Deferred transport scheduling never changes prompts or consumes quality retries."""

import json
from copy import deepcopy

import pytest
from test_explanation_pilot import FakeProvider, dataset, identities, output, run_pilot

from processors.explanations.generator import write_report
from processors.explanations.providers import GenerationError, GenerationResult


class NumberedProvider:
    def __init__(self, failures=None):
        self.metadata = {"provider": "fake", "model": "test-model"}
        self.failures = dict(failures or {})
        self.calls = []

    def generate(self, prompt):
        data = json.loads(prompt.split("QUESTION DATA:\n")[1])
        number = int(data["question_text"].split("case=")[1].split()[0])
        self.calls.append((number, prompt))
        if self.failures.get(number, 0) > 0:
            self.failures[number] -= 1
            raise GenerationError("transient_http_failure", attempts=3, retryable=True)
        return GenerationResult(output(), "fake", "test-model")


def numbered():
    data = dataset()
    for index, record in enumerate(data["records"], 1):
        record["question"]["question_text"] += f" case={index} "
    return data


def test_defer_then_retry_after_subsequent_question_with_identical_prompt():
    provider = NumberedProvider({1: 2})
    checkpoints = []
    data = run_pilot(
        numbered(),
        identities(),
        provider,
        checkpoint=lambda value: checkpoints.append(deepcopy(value)),
    )
    assert [number for number, _ in provider.calls] == [1, 2, 1, 3, 1, 4, 5]
    assert len({prompt for number, prompt in provider.calls if number == 1}) == 1
    assert (
        checkpoints[0]["records"][0]["ai_explanation"]["generation_status"]
        == "provider_failure_deferred"
    )
    meta = data["records"][0]["ai_explanation"]
    assert meta["generation_status"] == "accepted"
    assert meta["deferred_retry_cycles"] == 2
    assert meta["attempts"] == 7
    assert not meta["retry_attempted"]
    history = data["explanation_pilot"]["audit"][0]["generation_attempts"]
    assert [item["generation_attempt"] for item in history] == [1, 1, 1]
    assert history[1]["after_question"]["question_number"] == 2
    assert (
        data["records"][0]["final_explanation"]["source_reference"]["json_pointer"]
        == "/explanation_pilot/audit/0/candidate"
    )
    assert data["explanation_pilot"]["metrics"]["received_output"] == 5


def test_all_failures_exhaust_strict_two_cycle_budget_including_last_question():
    provider = NumberedProvider({number: 100 for number in range(1, 6)})
    data = run_pilot(numbered(), identities(), provider)
    assert len(provider.calls) == 15
    assert data["explanation_pilot"]["counts"] == {"provider_failure_exhausted": 5}
    for entry, record in zip(
        data["explanation_pilot"]["audit"], data["records"], strict=True
    ):
        assert record["ai_explanation"]["deferred_retry_cycles"] == 2
        assert record["ai_explanation"]["rerunnable"] is True
        assert not record["final_explanation"]["explanation_by_ai"]
        assert len(entry["generation_attempts"]) == 3
        assert (
            len({attempt["request_sha256"] for attempt in entry["generation_attempts"]})
            == 1
        )
    assert data["explanation_pilot"]["metrics"]["quality_evaluated"] == 0


def test_provider_only_resume_preserves_accepted_records_and_can_target_one():
    original = numbered()
    failed = run_pilot(original, identities(), NumberedProvider({1: 100}))
    before = deepcopy(failed)
    provider = NumberedProvider()
    resumed = run_pilot(original, [identities()[0]], provider, resume=failed)
    assert [n for n, _ in provider.calls] == [1]
    assert failed == before
    assert resumed["records"][1:] == before["records"][1:]
    assert resumed["explanation_pilot"]["counts"] == {"accepted": 5}
    assert len(resumed["explanation_pilot"]["audit"][0]["generation_attempts"]) == 4
    assert resumed["explanation_pilot"]["selected_identities"] == [
        list(value) for value in identities()
    ]


def test_resume_rejects_changed_context_prompt_and_model_before_calling_provider():
    original = numbered()
    failed = run_pilot(original, identities(), NumberedProvider({1: 100}))
    provider = NumberedProvider()
    for change in ("prompt", "source", "model"):
        altered = deepcopy(failed)
        if change == "prompt":
            altered["explanation_pilot"]["prompt_sha256"] = "changed"
        elif change == "source":
            altered["records"][0]["correct_answer"] = "A"
        else:
            altered["explanation_pilot"]["audit"][0]["metadata"]["model"] = (
                "other-model"
            )
        with pytest.raises(ValueError):
            run_pilot(original, [identities()[0]], provider, resume=altered)
    assert not provider.calls


def test_quality_regeneration_survives_transport_deferral_without_resetting_budget():
    class Provider(NumberedProvider):
        def generate(self, prompt):
            data = json.loads(prompt.split("QUESTION DATA:\n")[1])
            number = int(data["question_text"].split("case=")[1].split()[0])
            self.calls.append((number, prompt))
            if number == 1:
                if "regeneration" not in data:
                    return GenerationResult(
                        {"correct_answer": "A"}, "fake", "test-model"
                    )
                if len([n for n, _ in self.calls if n == 1]) == 2:
                    raise GenerationError("timeout", attempts=3, retryable=True)
            return GenerationResult(output(), "fake", "test-model")

    provider = Provider()
    result = run_pilot(numbered(), identities(), provider)
    prompts = [p for n, p in provider.calls if n == 1]
    assert len(prompts) == 3
    assert prompts[1] == prompts[2]
    history = result["explanation_pilot"]["audit"][0]["generation_attempts"]
    assert [a["generation_attempt"] for a in history] == [1, 2, 2]
    assert result["records"][0]["ai_explanation"]["retry_result"] == "accepted"


def test_availability_and_quality_have_distinct_denominators(tmp_path):
    class Mixed(NumberedProvider):
        def generate(self, prompt):
            data = json.loads(prompt.split("QUESTION DATA:\n")[1])
            number = int(data["question_text"].split("case=")[1].split()[0])
            if number == 1:
                raise GenerationError("timeout", attempts=3, retryable=True)
            return GenerationResult(
                {"correct_answer": "A"} if number == 2 else output(),
                "fake",
                "test-model",
            )

    result = run_pilot(numbered(), identities(), Mixed())
    assert result["explanation_pilot"]["metrics"] == {
        "selected": 5,
        "received_output": 4,
        "quality_evaluated": 4,
        "accepted": 3,
        "provider_interrupted_after_output": 0,
    }
    report = tmp_path / "issues.md"
    write_report(result, report)
    text = report.read_text(encoding="utf-8")
    assert "Generation availability: 4/5" in text
    assert "3/4 accepted" in text
    assert "Overall completed: 3/5" in text
    assert "Provider Failure Exhausted (1 questions)" in text
    assert "Validation Rejected (1 questions)" in text


def test_nontransient_configuration_failures_are_not_deferred():
    class Auth(FakeProvider):
        def generate(self, prompt):
            self.requests.append(prompt)
            raise GenerationError("authentication_failed", attempts=1)

    provider = Auth()
    data = run_pilot(numbered(), identities(), provider)
    assert len(provider.requests) == 5
    assert data["explanation_pilot"]["counts"] == {"provider_failure_exhausted": 5}


def test_resume_mid_quality_retry_preserves_feedback_and_one_regeneration_limit():
    class Interrupted(NumberedProvider):
        def generate(self, prompt):
            values = json.loads(prompt.split("QUESTION DATA:\n")[1])
            if "case=1 " in values["question_text"]:
                if "regeneration" not in values:
                    return GenerationResult(
                        {"correct_answer": "A"}, "fake", "test-model"
                    )
                raise GenerationError("timeout", attempts=3, retryable=True)
            return GenerationResult(output(), "fake", "test-model")

    original = numbered()
    failed = run_pilot(original, identities(), Interrupted())
    assert failed["records"][0]["ai_explanation"]["pending_generation_attempt"] == 2
    repaired = NumberedProvider()
    resumed = run_pilot(original, [identities()[0]], repaired, resume=failed)
    assert len(repaired.calls) == 1
    values = json.loads(repaired.calls[0][1].split("QUESTION DATA:\n")[1])
    assert values["regeneration"]["validator_rejection_reasons"]
    assert resumed["explanation_pilot"]["counts"] == {"accepted": 5}
    assert resumed["records"][0]["ai_explanation"]["retry_result"] == "accepted"


def test_provider_interrupted_after_invalid_output_is_excluded_from_quality_denominator():
    class Interrupted(NumberedProvider):
        def generate(self, prompt):
            values = json.loads(prompt.split("QUESTION DATA:\n")[1])
            if "case=1 " in values["question_text"]:
                if "regeneration" not in values:
                    return GenerationResult(
                        {"correct_answer": "A"}, "fake", "test-model"
                    )
                raise GenerationError("timeout", attempts=3, retryable=True)
            return GenerationResult(output(), "fake", "test-model")

    data = run_pilot(numbered(), identities(), Interrupted())
    metrics = data["explanation_pilot"]["metrics"]
    assert metrics["received_output"] == 5
    assert metrics["quality_evaluated"] == 4
    assert metrics["accepted"] == 4
    assert metrics["provider_interrupted_after_output"] == 1


def test_provider_metadata_is_whitelisted_before_checkpointing():
    provider = NumberedProvider()
    provider.metadata["api_key"] = "never-persist-this"
    result = run_pilot(numbered(), identities(), provider)
    assert "never-persist-this" not in json.dumps(result)


def test_provider_cannot_switch_model_when_returning_deferred_content():
    class Changed(NumberedProvider):
        def generate(self, prompt):
            return GenerationResult(output(), "fake", "other-model")

    result = run_pilot(numbered(), identities(), Changed())
    assert result["explanation_pilot"]["counts"] == {"provider_failure_exhausted": 5}
    assert all(
        r["ai_explanation"]["failure_code"] == "provider_configuration_changed"
        for r in result["records"]
    )
