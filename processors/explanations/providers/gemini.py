"""Gemini REST transport. No provider types escape this module.

References: https://ai.google.dev/api/generate-content and
https://ai.google.dev/gemini-api/docs/troubleshooting
"""

import json
import os
import re
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import GenerationError, GenerationResult

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiProvider:
    def __init__(self, *, api_key=None, model=None, timeout=45, max_attempts=3,
                 opener=urlopen, sleeper=time.sleep):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", self.model):
            raise GenerationError("invalid_model_configuration")
        if not 0 < timeout <= 60 or not 1 <= max_attempts <= 3:
            raise ValueError("Timeout must be <=60 seconds; attempts must be 1–3")
        self.timeout, self.max_attempts = timeout, max_attempts
        self._open, self._sleep = opener, sleeper

    def generate(self, prompt):
        if not self.api_key:
            raise GenerationError("authentication_not_configured")
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 4096},
        }
        request = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        for attempt in range(1, self.max_attempts + 1):
            try:
                with self._open(request, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                code = (
                    "authentication_failed" if error.code in (401, 403)
                    else "rate_limited" if error.code == 429
                    else "model_or_endpoint_unavailable" if error.code == 404
                    else "transient_http_failure" if error.code in (408, 500, 502, 503, 504)
                    else "request_rejected"
                )
                transient = error.code in (408, 429, 500, 502, 503, 504)
                error.close()
                if transient and attempt < self.max_attempts:
                    self._sleep(2 ** attempt)
                    continue
                raise GenerationError(code, attempts=attempt) from None
            except (TimeoutError, socket.timeout):
                if attempt < self.max_attempts:
                    self._sleep(2 ** attempt)
                    continue
                raise GenerationError("timeout", attempts=attempt) from None
            except URLError:
                if attempt < self.max_attempts:
                    self._sleep(2 ** attempt)
                    continue
                raise GenerationError("network_failure", attempts=attempt) from None
            except (ValueError, UnicodeError):
                raise GenerationError("malformed_response", attempts=attempt) from None
            return self._extract(body, attempt)
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
                part.get("text", "") for part in candidate.get("content", {}).get("parts", [])
                if not part.get("thought")
            )
            if not text.strip():
                raise GenerationError("empty_response", attempts=attempt)
            content = json.loads(text)
        except (ValueError, TypeError, AttributeError):
            raise GenerationError("malformed_response", attempts=attempt) from None
        return GenerationResult(content, "gemini", self.model, attempt)
