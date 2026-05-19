from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryLensError(Exception):
    """Base exception. All domain errors inherit from this."""

    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


@dataclass
class SQLParseError(QueryLensError):
    """Raised when sqlglot cannot parse the input SQL."""


@dataclass
class ExecutionPlanError(QueryLensError):
    """Raised when EXPLAIN ANALYZE fails or times out."""


@dataclass
class LLMProviderError(QueryLensError):
    """Raised when an LLM provider call fails after retries."""

    provider: str = ""
    status_code: int | None = None


@dataclass
class LLMProviderNotConfigured(QueryLensError):
    """Raised when a requested provider has no credentials configured."""

    provider: str = ""


@dataclass
class QueryTooLongError(QueryLensError):
    """Raised when the submitted query exceeds the configured max length."""

    length: int = 0
    max_length: int = 0
