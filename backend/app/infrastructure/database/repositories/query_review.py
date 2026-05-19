import uuid
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.review import QueryReview
from app.infrastructure.database.models import QueryReviewORM


class QueryReviewRepository:
    """
    Handles all persistence for QueryReview domain objects.

    Converts between the domain model and the ORM model here so that
    neither the domain layer nor the API layer touches SQLAlchemy directly.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, review: QueryReview) -> QueryReviewORM:
        record = _to_orm(review)
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, review_id: uuid.UUID) -> QueryReviewORM | None:
        result = await self._session.execute(
            select(QueryReviewORM).where(QueryReviewORM.id == review_id)
        )
        return result.scalar_one_or_none()


def _to_orm(review: QueryReview) -> QueryReviewORM:
    static = review.static_analysis
    ai = review.ai_review
    plan = review.execution_plan

    return QueryReviewORM(
        sql=review.query.sql,
        dialect=review.query.dialect,
        review_mode=review.query.review_mode,
        # Static analysis
        static_findings=[_static_finding_to_dict(f) for f in static.findings],
        static_query_type=static.query_type,
        static_table_refs=static.table_references,
        # Execution plan
        plan_findings=[_plan_finding_to_dict(f) for f in plan.findings] if plan else None,
        plan_execution_time_ms=plan.execution_time_ms if plan else None,
        plan_planning_time_ms=plan.plan.planning_time_ms if plan else None,
        plan_has_analyze_data=plan.has_analyze_data if plan else None,
        # AI review
        ai_summary=ai.summary,
        ai_improved_query=ai.improved_query,
        ai_findings=[_ai_finding_to_dict(f) for f in ai.findings],
        ai_educational_note=ai.educational_note,
        ai_provider=ai.provider,
        ai_model=ai.model,
        ai_input_tokens=ai.input_tokens,
        ai_output_tokens=ai.output_tokens,
        created_at=review.reviewed_at,
    )


def _static_finding_to_dict(f) -> dict:
    return {
        "rule_id": f.rule_id,
        "severity": f.severity,
        "category": f.category,
        "title": f.title,
        "message": f.message,
        "suggestion": f.suggestion,
        "line": f.line,
        "column": f.column,
    }


def _plan_finding_to_dict(f) -> dict:
    return {
        "rule_id": f.rule_id,
        "node_type": f.node_type,
        "severity": f.severity,
        "category": f.category,
        "title": f.title,
        "message": f.message,
        "suggestion": f.suggestion,
        "relation_name": f.relation_name,
    }


def _ai_finding_to_dict(f) -> dict:
    return {
        "rule_id": f.rule_id,
        "explanation": f.explanation,
        "suggestion": f.suggestion,
    }
