"""Plain data contract shared by explanation providers."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    content: object
    provider: str
    model: str
    attempts: int = 1


class ExplanationProvider(Protocol):
    def generate(self, prompt: str) -> GenerationResult: ...


class GenerationError(Exception):
    """Sanitized failure safe to persist; never contains a credential/HTTP body."""

    def __init__(self, code, *, attempts=0, retryable=False):
        super().__init__(code)
        self.code = code
        self.attempts = attempts
        self.retryable = retryable
