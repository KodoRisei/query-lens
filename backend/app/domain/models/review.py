from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.domain.models.analysis import StaticAnalysisResult
from app.domain.models.query import SQLQuery

if TYPE_CHECKING:
    from app.analysis.execution_plan.models import ExecutionPlanResult


@dataclass(frozen=True)
class AIFinding:
    rule_id: str
    explanation: str
    suggestion: str | None = None


@dataclass
class AIReview:
    summary: str
    findings: list[AIFinding]
    improved_query: str | None = None
    educational_note: str | None = None
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class QueryReview:
    query: SQLQuery
    static_analysis: StaticAnalysisResult
    ai_review: AIReview
    execution_plan: ExecutionPlanResult | None = None
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
