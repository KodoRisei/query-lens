"""
Integration tests for QueryReviewRepository against a real PostgreSQL database.

Run with:
    INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://... pytest tests/integration/test_repository.py
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.analysis import (
    AnalysisFinding,
    FindingCategory,
    Severity,
    StaticAnalysisResult,
)
from app.domain.models.query import ReviewMode, SQLQuery
from app.domain.models.review import AIFinding, AIReview, QueryReview
from app.infrastructure.database.repositories.query_review import QueryReviewRepository


def make_query_review(
    sql: str = "SELECT id FROM users WHERE id = 1",
    mode: ReviewMode = ReviewMode.senior,
    with_findings: bool = False,
) -> QueryReview:
    findings = []
    if with_findings:
        findings = [
            AnalysisFinding(
                rule_id="select_star",
                severity=Severity.warning,
                category=FindingCategory.performance,
                title="SELECT * detected",
                message="Fetches all columns.",
                suggestion="List only the columns you need.",
            )
        ]
    return QueryReview(
        query=SQLQuery(sql=sql, review_mode=mode),
        static_analysis=StaticAnalysisResult(
            findings=findings,
            query_type="SELECT",
            table_references=["users"],
        ),
        ai_review=AIReview(
            summary="Looks good.",
            findings=[
                AIFinding(
                    rule_id="select_star",
                    explanation="SELECT * is slow.",
                    suggestion="Name your columns.",
                )
            ]
            if with_findings
            else [],
            improved_query="SELECT id FROM users WHERE id = 1" if with_findings else None,
            educational_note=None,
            provider="ollama",
            model="llama3.1",
            input_tokens=100,
            output_tokens=200,
        ),
        execution_plan=None,
    )


@pytest.mark.asyncio
async def test_save_returns_record_with_generated_id(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)
    review = make_query_review()

    record = await repo.save(review)
    await db_session.commit()

    assert record.id is not None
    assert isinstance(record.id, uuid.UUID)


@pytest.mark.asyncio
async def test_save_and_get_by_id_roundtrip(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)
    review = make_query_review(sql="SELECT name FROM users WHERE id = 99")

    record = await repo.save(review)
    await db_session.commit()

    fetched = await repo.get_by_id(record.id)

    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.sql == "SELECT name FROM users WHERE id = 99"
    assert fetched.review_mode == ReviewMode.senior
    assert fetched.ai_summary == "Looks good."
    assert fetched.ai_provider == "ollama"
    assert fetched.ai_input_tokens == 100
    assert fetched.ai_output_tokens == 200


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_unknown(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)

    result = await repo.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_static_findings_serialized_to_jsonb(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)
    review = make_query_review(with_findings=True)

    record = await repo.save(review)
    await db_session.commit()

    fetched = await repo.get_by_id(record.id)
    assert fetched is not None
    assert len(fetched.static_findings) == 1

    finding = fetched.static_findings[0]
    assert finding["rule_id"] == "select_star"
    assert finding["severity"] == "warning"
    assert finding["category"] == "performance"
    assert finding["title"] == "SELECT * detected"
    assert finding["suggestion"] == "List only the columns you need."


@pytest.mark.asyncio
async def test_ai_findings_serialized_to_jsonb(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)
    review = make_query_review(with_findings=True)

    record = await repo.save(review)
    await db_session.commit()

    fetched = await repo.get_by_id(record.id)
    assert fetched is not None
    assert len(fetched.ai_findings) == 1

    ai_finding = fetched.ai_findings[0]
    assert ai_finding["rule_id"] == "select_star"
    assert ai_finding["explanation"] == "SELECT * is slow."
    assert ai_finding["suggestion"] == "Name your columns."


@pytest.mark.asyncio
async def test_improved_query_persisted(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)
    review = make_query_review(with_findings=True)

    record = await repo.save(review)
    await db_session.commit()

    fetched = await repo.get_by_id(record.id)
    assert fetched is not None
    assert fetched.ai_improved_query == "SELECT id FROM users WHERE id = 1"


@pytest.mark.asyncio
async def test_multiple_reviews_are_independent(db_session: AsyncSession) -> None:
    repo = QueryReviewRepository(db_session)

    record_a = await repo.save(make_query_review(sql="SELECT 1"))
    record_b = await repo.save(make_query_review(sql="SELECT 2"))
    await db_session.commit()

    fetched_a = await repo.get_by_id(record_a.id)
    fetched_b = await repo.get_by_id(record_b.id)

    assert fetched_a is not None
    assert fetched_b is not None
    assert fetched_a.sql == "SELECT 1"
    assert fetched_b.sql == "SELECT 2"
    assert fetched_a.id != fetched_b.id
