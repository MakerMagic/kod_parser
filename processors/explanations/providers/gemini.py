"""Gemini REST transport. No provider types escape this module.

References: https://ai.google.dev/api/generate-content and
https://ai.google.dev/gemini-api/docs/troubleshooting
"""

import json
import math
import os
import random
import re
import time
from datetime import timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import GenerationError, GenerationResult

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_REQUEST_DELAY_SECONDS = 8.0
_MAX_INLINE_WAIT_SECONDS = 60.0


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key=None,
        model=None,
        timeout=45,
        max_attempts=3,
        opener=urlopen,
        sleeper=time.sleep,
        request_delay=None,
        jitter=random.uniform,
        clock=time.monotonic,
        wall_clock=time.time,
    ):
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )
        if self.api_key and any(
            ord(char) < 33 or ord(char) > 126 for char in self.api_key
        ):
            raise GenerationError("invalid_api_key_configuration")
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.model):
            raise GenerationError("invalid_model_configuration")
        if not 0 < timeout <= 60 or not 1 <= max_attempts <= 3:
            raise ValueError("Timeout must be <=60 seconds; attempts must be 1–3")
        self.timeout, self.max_attempts = timeout, max_attempts
        self._open, self._sleep = opener, sleeper
        try:
            self.request_delay = float(
                request_delay
                if request_delay is not None
                else os.getenv(
                    "GEMINI_REQUEST_DELAY_SECONDS", DEFAULT_REQUEST_DELAY_SECONDS
                )
            )
        except (TypeError, ValueError):
            raise GenerationError("invalid_request_delay_configuration") from None
        if not math.isfinite(self.request_delay) or not 0 <= self.request_delay <= 60:
            raise GenerationError("invalid_request_delay_configuration")
        self._jitter, self._clock, self._wall_clock = jitter, clock, wall_clock
        self._not_before = 0.0
        self._wait_category = "cooldown"
        self._rate_limit_streak = 0
        self.audit_events = []  # Sanitized transport diagnostics, no bodies/keys.

    def _wait(self, request_hash, attempts):
        delay = max(0.0, self._not_before - self._clock())
        if delay > _MAX_INLINE_WAIT_SECONDS:
            # Never shorten an authoritative long Retry-After to retry early.
            # Return to the unchanged deferred scheduler instead of blocking it.
            self.audit_events.append(
                {
                    "request_sha256": request_hash,
                    "category": "rate_limit_wait_deferred",
                    "retry_after_seconds": round(delay, 3),
                }
            )
            raise GenerationError("rate_limited", attempts=attempts, retryable=True)
        if delay:
            self.audit_events.append(
                {
                    "request_sha256": request_hash,
                    "category": self._wait_category,
                    "delay_seconds": round(delay, 3),
                }
            )
            self._sleep(delay)

    def _http_failure(self, error):
        """Inspect bounded structured error data; discard all raw error content."""
        status, retry_delay = error.code, 0.0
        limited = False
        try:
            header = error.headers.get("Retry-After") if error.headers else None
            if header:
                try:
                    retry_delay = float(header)
                except ValueError:
                    stamp = parsedate_to_datetime(header)
                    if stamp.tzinfo is None:
                        stamp = stamp.replace(tzinfo=timezone.utc)
                    retry_delay = stamp.timestamp() - self._wall_clock()
        except (TypeError, ValueError, OverflowError):
            retry_delay = 0.0
        try:
            raw = error.read(65536)
            body = json.loads(raw.decode("utf-8")) if raw else {}
            detail = body.get("error", {})
            tokens = [
                str(detail.get(field, "")).lower()
                for field in ("status", "code", "message")
            ]
            limited = any(
                re.search(
                    r"\b(?:resource_exhausted|too_many_requests|rate_limit_exceeded|quota_exceeded)\b",
                    token,
                )
                for token in tokens
            )
            for item in detail.get("details", []):
                if not isinstance(item, dict) or not str(
                    item.get("@type", "")
                ).endswith(".RetryInfo"):
                    continue
                value = item.get("retryDelay", "")
                if isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?s", value):
                    retry_delay = max(retry_delay, float(value[:-1]))
                elif isinstance(value, dict):
                    retry_delay = max(
                        retry_delay,
                        float(value.get("seconds", 0))
                        + float(value.get("nanos", 0)) / 1e9,
                    )
        except (
            OSError,
            HTTPException,
            ValueError,
            UnicodeError,
            TypeError,
            AttributeError,
        ):
            pass  # Malformed retry hints must not erase an identified rate limit.
        finally:
            error.close()
        if status in (401, 403):
            return "authentication_failed", False, 0.0
        if status == 429 or limited:
            return (
                "rate_limited",
                True,
                retry_delay if math.isfinite(retry_delay) else 0.0,
            )
        if status == 404:
            return "model_or_endpoint_unavailable", False, 0.0
        if status in (408, 500, 502, 503, 504):
            return "transient_http_failure", True, 0.0
        return "request_rejected", False, 0.0

    @property
    def metadata(self):
        return {"provider": "gemini", "model": self.model}

    def generate(self, prompt):
        if not self.api_key:
            raise GenerationError("authentication_not_configured")
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": 4096,
            },
        }
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        request_hash = sha256(prompt.encode()).hexdigest()
        for attempt in range(1, self.max_attempts + 1):
            self._wait(request_hash, attempt - 1)
            try:
                with self._open(request, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                code, transient, retry_delay = self._http_failure(error)
                self.audit_events.append(
                    {
                        "request_sha256": request_hash,
                        "attempt": attempt,
                        "category": code,
                        "http_status": error.code,
                    }
                )
                if code == "rate_limited":
                    self._rate_limit_streak += 1
                    base = (5.0, 15.0, 35.0)[min(self._rate_limit_streak - 1, 2)]
                    delay = max(
                        base + self._jitter(0.0, min(base / 5, 5.0)), retry_delay
                    )
                    self._not_before = self._clock() + delay
                    self._wait_category = "rate_limit_backoff"
                if transient and attempt < self.max_attempts:
                    if code != "rate_limited":
                        self._sleep(2**attempt)
                    continue
                raise GenerationError(
                    code, attempts=attempt, retryable=transient
                ) from None
            except TimeoutError:
                if attempt < self.max_attempts:
                    self._sleep(2**attempt)
                    continue
                raise GenerationError(
                    "timeout", attempts=attempt, retryable=True
                ) from None
            except URLError as error:
                if attempt < self.max_attempts:
                    self._sleep(2**attempt)
                    continue
                code = (
                    "timeout"
                    if isinstance(error.reason, TimeoutError)
                    else "network_failure"
                )
                raise GenerationError(code, attempts=attempt, retryable=True) from None
            except (ConnectionError, HTTPException):
                # A peer can close a response without urllib wrapping the
                # exception in URLError. This is transport, not bad reasoning.
                if attempt < self.max_attempts:
                    self._sleep(2**attempt)
                    continue
                raise GenerationError(
                    "network_failure", attempts=attempt, retryable=True
                ) from None
            except (ValueError, UnicodeError):
                raise GenerationError("malformed_response", attempts=attempt) from None
            result = self._extract(body, attempt)
            self.audit_events.append(
                {
                    "request_sha256": request_hash,
                    "attempt": attempt,
                    "category": "response_returned",
                }
            )
            self._rate_limit_streak = 0
            self._not_before = self._clock() + self.request_delay
            self._wait_category = "successful_request_cooldown"
            return result
        raise AssertionError("Unreachable retry state")

    def _extract(self, body, attempt):
        try:
            candidates = body.get("candidates", [])
            if len(candidates) != 1:
                raise GenerationError("empty_or_ambiguous_response", attempts=attempt)
            candidate = candidates[0]
            if candidate.get("finishReason") != "STOP":
                raise GenerationError("response_not_completed", attempts=attempt)
            text = "".join(
                part.get("text", "")
                for part in candidate.get("content", {}).get("parts", [])
                if not part.get("thought")
            )
            if not text.strip():
                raise GenerationError("empty_response", attempts=attempt)
            content = json.loads(text)
        except (ValueError, TypeError, AttributeError):
            raise GenerationError("malformed_response", attempts=attempt) from None
        return GenerationResult(content, "gemini", self.model, attempt)
