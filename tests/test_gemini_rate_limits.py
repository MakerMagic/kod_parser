"""Provider-only pacing; no live API, model fallback or quality-rule changes."""

import io
import json
from email.utils import formatdate
from urllib.error import HTTPError

import pytest
from test_explanation_pilot import dataset, identities, output

from processors.explanations.generator import run_pilot
from processors.explanations.providers import GenerationError
from processors.explanations.providers.gemini import GeminiProvider


class Clock:
    def __init__(self):
        self.now = 1000.0
        self.waits = []

    def __call__(self):
        return self.now

    def sleep(self, delay):
        self.waits.append(delay)
        self.now += delay


def failure(status=429, body=None, headers=None):
    return HTTPError(
        "https://test.invalid",
        status,
        "not persisted",
        headers or {},
        io.BytesIO(json.dumps(body or {}).encode()),
    )


def response():
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


def provider(opener, **kwargs):
    clock = Clock()
    value = GeminiProvider(
        api_key="dummy",
        model="configured-test-model",
        opener=opener,
        sleeper=clock.sleep,
        clock=clock,
        wall_clock=clock,
        jitter=lambda low, high: 0.0,
        **kwargs,
    )
    return value, clock


@pytest.mark.parametrize(
    "status,body",
    [
        (429, {}),
        (400, {"error": {"status": "RESOURCE_EXHAUSTED"}}),
        (400, {"error": {"code": "too_many_requests"}}),
        (503, {"error": {"message": "RESOURCE_EXHAUSTED"}}),
    ],
)
def test_rate_limit_classification_and_strict_transport_limit(status, body):
    calls = []

    def limited(request, **kwargs):
        calls.append((request.full_url, request.data))
        raise failure(status, body)

    value, clock = provider(limited)
    with pytest.raises(GenerationError, match="rate_limited") as caught:
        value.generate("unchanged prompt")
    assert caught.value.retryable and caught.value.attempts == 3
    assert len(calls) == 3 and len(set(calls)) == 1
    assert "configured-test-model" in calls[0][0]
    assert clock.waits == [5, 15]
    assert len([e for e in value.audit_events if e["category"] == "rate_limited"]) == 3


def test_jitter_and_third_backoff_survive_deferred_call():
    calls = []

    def limited(*args, **kwargs):
        calls.append(1)
        raise failure()

    value, clock = provider(limited)
    value._jitter = lambda low, high: high
    for _ in range(2):
        with pytest.raises(GenerationError):
            value.generate("same prompt")
    assert len(calls) == 6
    assert clock.waits[:3] == [6, 18, 40]
    assert clock.waits[3:] == [40, 40]


@pytest.mark.parametrize(
    "headers,body,wait",
    [
        ({"Retry-After": "25"}, {}, 25),
        ({"Retry-After": formatdate(1030, usegmt=True)}, {}, 30),
        ({"Retry-After": "1"}, {}, 5),
        (
            {},
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "23.5s",
                        }
                    ]
                }
            },
            23.5,
        ),
        (
            {"Retry-After": "11"},
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "27s",
                        }
                    ]
                }
            },
            27,
        ),
    ],
)
def test_retry_after_and_retry_info_are_respected(headers, body, wait):
    calls = []

    def limited_once(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise failure(body=body, headers=headers)
        return response()

    value, clock = provider(limited_once)
    assert value.generate("q").attempts == 2
    assert clock.waits == [wait]


def test_long_authoritative_delay_defers_without_retrying_early():
    calls = []

    def daily_quota(*args, **kwargs):
        calls.append(1)
        raise failure(headers={"Retry-After": "3600"})

    value, clock = provider(daily_quota)
    for expected_attempts in (1, 0):
        with pytest.raises(GenerationError, match="rate_limited") as caught:
            value.generate("q")
        assert caught.value.attempts == expected_attempts
        assert caught.value.retryable
    assert len(calls) == 1 and clock.waits == []


def test_malformed_retry_hint_does_not_hide_resource_exhaustion_or_store_secrets():
    def limited(*args, **kwargs):
        raise failure(
            400,
            {
                "error": {
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "private response information",
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": {"seconds": "bad"},
                        }
                    ],
                }
            },
        )

    value, _ = provider(limited)
    with pytest.raises(GenerationError, match="rate_limited"):
        value.generate("private request information")
    assert "private" not in json.dumps(value.audit_events)


def test_missing_model_never_falls_back_to_another_model():
    urls = []

    def unavailable(request, **kwargs):
        urls.append(request.full_url)
        raise failure(404)

    value, _ = provider(unavailable)
    with pytest.raises(GenerationError, match="model_or_endpoint_unavailable"):
        value.generate("q")
    assert len(urls) == 1 and "configured-test-model" in urls[0]


def test_cooldown_environment_default_override_and_success_reset(monkeypatch):
    monkeypatch.delenv("GEMINI_REQUEST_DELAY_SECONDS", raising=False)
    value, clock = provider(lambda *a, **k: response())
    assert value.request_delay == 8
    value.generate("one")
    value.generate("two")
    assert clock.waits == [8]
    monkeypatch.setenv("GEMINI_REQUEST_DELAY_SECONDS", "12.5")
    value, clock = provider(lambda *a, **k: response())
    value.generate("one")
    value.generate("two")
    assert clock.waits == [12.5]


@pytest.mark.parametrize("value", ["nan", "inf", "-1", "nonsense", "61"])
def test_bad_cooldown_config_is_sanitized(monkeypatch, value):
    monkeypatch.setenv("GEMINI_REQUEST_DELAY_SECONDS", value)
    with pytest.raises(GenerationError, match="invalid_request_delay_configuration"):
        GeminiProvider(api_key="dummy")


@pytest.mark.parametrize(
    "status,code,retryable",
    [
        (403, "authentication_failed", False),
        (404, "model_or_endpoint_unavailable", False),
        (503, "transient_http_failure", True),
        (400, "request_rejected", False),
    ],
)
def test_other_error_classes_remain_distinct(status, code, retryable):
    def fails(*args, **kwargs):
        raise failure(status)

    value, _ = provider(fails)
    with pytest.raises(GenerationError, match=code) as caught:
        value.generate("q")
    assert caught.value.retryable is retryable
    assert caught.value.attempts == (3 if retryable else 1)


def test_rate_limits_stay_provider_failures_and_resume_without_quality_retry():
    def limited(*args, **kwargs):
        raise failure()

    value, _ = provider(limited)
    data = dataset()
    checkpoints = []
    failed = run_pilot(
        data,
        identities(),
        value,
        checkpoint=lambda d: checkpoints.append(
            d["explanation_pilot"]["counts"].copy()
        ),
    )
    assert any("provider_failure_deferred" in counts for counts in checkpoints)
    assert failed["explanation_pilot"]["counts"] == {"provider_failure_exhausted": 5}
    assert failed["explanation_pilot"]["metrics"]["quality_evaluated"] == 0
    assert all(
        not e["metadata"]["retry_attempted"]
        for e in failed["explanation_pilot"]["audit"]
    )
    recovered, _ = provider(lambda *a, **k: response())
    resumed = run_pilot(data, identities()[:1], recovered, resume=failed)
    assert (
        resumed["explanation_pilot"]["audit"][0]["status"] == "semantic_review_pending"
    )
    assert resumed["explanation_pilot"]["counts"]["provider_failure_exhausted"] == 4
    assert not resumed["records"][0]["ai_explanation"]["explanation_by_ai"]
