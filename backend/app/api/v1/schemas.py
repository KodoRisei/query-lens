import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.config import LLMProvider as LLMProviderName
from app.domain.models.query import ReviewMode
from app.domain.models.review import QueryReview
from app.infrastructure.database.models import QueryReviewORM

# ── Request ───────────────────────────────────────────────────────────────────


class ReviewRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=50_000, description="SQL query to review")
    dialect: str = Field(
        default="", pattern=r"^[a-z_]*$", description="sqlglot dialect (empty = generic SQL)"
    )
    review_mode: ReviewMode = Field(default=ReviewMode.senior)
    provider: LLMProviderName | None = Field(
        default=None, description="Override default LLM provider"
    )


# ── Response building blocks ──────────────────────────────────────────────────


class StaticFindingResponse(BaseModel):
    rule_id: str
    severity: str
    category: str
    title: str
    message: str
    suggestion: str | None = None
    line: int | None = None
    column: int | None = None


class StaticAnalysisResponse(BaseModel):
    query_type: str
    table_references: list[str]
    findings: list[StaticFindingResponse]
    critical_count: int
    warning_count: int
    info_count: int


class PlanFindingResponse(BaseModel):
    rule_id: str
    node_type: str
    severity: str
    category: str
    title: str
    message: str
    suggestion: str | None = None
    relation_name: str | None = None


class ExecutionPlanResponse(BaseModel):
    execution_time_ms: float | None
    planning_time_ms: float
    has_analyze_data: bool
    findings: list[PlanFindingResponse]


class AIFindingResponse(BaseModel):
    rule_id: str
    explanation: str
    suggestion: str | None = None


class AIReviewResponse(BaseModel):
    summary: str
    improved_query: str | None
    findings: list[AIFindingResponse]
    educational_note: str | None
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


class QueryReviewResponse(BaseModel):
    id: uuid.UUID
    sql: str
    dialect: str
    review_mode: str
    created_at: datetime
    static_analysis: StaticAnalysisResponse
    execution_plan: ExecutionPlanResponse | None
    ai_review: AIReviewResponse

    @classmethod
    def from_domain(
        cls,
        review: QueryReview,
        record_id: uuid.UUID,
        created_at: datetime,
    ) -> "QueryReviewResponse":
        static = review.static_analysis
        ai = review.ai_review
        plan = review.execution_plan

        return cls(
            id=record_id,
            sql=review.query.sql,
            dialect=review.query.dialect,
            review_mode=review.query.review_mode,
            created_at=created_at,
            static_analysis=StaticAnalysisResponse(
                query_type=static.query_type,
                table_references=static.table_references,
                findings=[
                    StaticFindingResponse(
                        rule_id=f.rule_id,
                        severity=f.severity,
                        category=f.category,
                        title=f.title,
                        message=f.message,
                        suggestion=f.suggestion,
                        line=f.line,
                        column=f.column,
                    )
                    for f in static.findings
                ],
                critical_count=static.critical_count,
                warning_count=static.warning_count,
                info_count=static.info_count,
            ),
            execution_plan=(
                ExecutionPlanResponse(
                    execution_time_ms=plan.execution_time_ms,
                    planning_time_ms=plan.plan.planning_time_ms,
                    has_analyze_data=plan.has_analyze_data,
                    findings=[
                        PlanFindingResponse(
                            rule_id=f.rule_id,
                            node_type=f.node_type,
                            severity=f.severity,
                            category=f.category,
                            title=f.title,
                            message=f.message,
                            suggestion=f.suggestion,
                            relation_name=f.relation_name,
                        )
                        for f in plan.findings
                    ],
                )
                if plan
                else None
            ),
            ai_review=AIReviewResponse(
                summary=ai.summary,
                improved_query=ai.improved_query,
                findings=[
                    AIFindingResponse(
                        rule_id=f.rule_id,
                        explanation=f.explanation,
                        suggestion=f.suggestion,
                    )
                    for f in ai.findings
                ],
                educational_note=ai.educational_note,
                provider=ai.provider,
                model=ai.model,
                input_tokens=ai.input_tokens,
                output_tokens=ai.output_tokens,
            ),
        )

    @classmethod
    def from_orm_record(cls, record: QueryReviewORM) -> "QueryReviewResponse":
        """Reconstruct a response from a persisted ORM record."""
        return cls(
            id=record.id,
            sql=record.sql,
            dialect=record.dialect,
            review_mode=record.review_mode,
            created_at=record.created_at,
            static_analysis=StaticAnalysisResponse(
                query_type=record.static_query_type or "UNKNOWN",
                table_references=record.static_table_refs or [],
                findings=[StaticFindingResponse(**f) for f in (record.static_findings or [])],
                critical_count=sum(
                    1 for f in (record.static_findings or []) if f.get("severity") == "critical"
                ),
                warning_count=sum(
                    1 for f in (record.static_findings or []) if f.get("severity") == "warning"
                ),
                info_count=sum(
                    1 for f in (record.static_findings or []) if f.get("severity") == "info"
                ),
            ),
            execution_plan=(
                ExecutionPlanResponse(
                    execution_time_ms=record.plan_execution_time_ms,
                    planning_time_ms=record.plan_planning_time_ms or 0.0,
                    has_analyze_data=record.plan_has_analyze_data or False,
                    findings=[PlanFindingResponse(**f) for f in (record.plan_findings or [])],
                )
                if record.plan_findings is not None
                else None
            ),
            ai_review=AIReviewResponse(
                summary=record.ai_summary or "",
                improved_query=record.ai_improved_query,
                findings=[AIFindingResponse(**f) for f in (record.ai_findings or [])],
                educational_note=record.ai_educational_note,
                provider=record.ai_provider or "",
                model=record.ai_model or "",
                input_tokens=record.ai_input_tokens or 0,
                output_tokens=record.ai_output_tokens or 0,
            ),
        )
