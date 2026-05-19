import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_review_repository, get_review_service
from app.core.exceptions import LLMProviderError, SQLParseError
from app.domain.models.analysis import (
    AnalysisFinding,
    FindingCategory,
    Severity,
    StaticAnalysisResult,
)
from app.domain.models.query import ReviewMode, SQLQuery
from app.domain.models.review import AIFinding, AIReview, QueryReview
from app.main import app

BASE = "/api/v1/queries"


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_review(sql: str = "SELECT id FROM users WHERE id = 1") -> QueryReview:
    return QueryReview(
        query=SQLQuery(sql=sql, review_mode=ReviewMode.senior),
        static_analysis=StaticAnalysisResult(
            findings=[],
            query_type="SELECT",
            table_references=["users"],
        ),
        ai_review=AIReview(
            summary="Query looks good.",
            findings=[],
            provider="mock",
            model="mock-model",
            input_tokens=50,
            output_tokens=100,
        ),
        execution_plan=None,
    )


def make_orm_record(review_id: uuid.UUID, review: QueryReview):
    record = MagicMock()
    record.id = review_id
    record.sql = review.query.sql
    record.dialect = review.query.dialect
    record.review_mode = review.query.review_mode
    record.created_at = datetime.now(UTC)
    record.static_findings = []
    record.static_query_type = "SELECT"
    record.static_table_refs = ["users"]
    record.plan_findings = None
    record.plan_execution_time_ms = None
    record.plan_planning_time_ms = None
    record.plan_has_analyze_data = None
    record.ai_summary = "Query looks good."
    record.ai_improved_query = None
    record.ai_findings = []
    record.ai_educational_note = None
    record.ai_provider = "mock"
    record.ai_model = "mock-model"
    record.ai_input_tokens = 50
    record.ai_output_tokens = 100
    return record


def mock_service_dep(review: QueryReview):
    svc = MagicMock()
    svc.review = AsyncMock(return_value=review)
    return svc


def mock_repo_dep(review_id: uuid.UUID, review: QueryReview):
    record = make_orm_record(review_id, review)
    repo = MagicMock()
    repo.save = AsyncMock(return_value=record)
    repo.get_by_id = AsyncMock(return_value=record)
    return repo


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_review_returns_201() -> None:
    review = make_review()
    review_id = uuid.uuid4()

    app.dependency_overrides[get_review_service] = lambda: mock_service_dep(review)
    app.dependency_overrides[get_review_repository] = lambda: mock_repo_dep(review_id, review)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"{BASE}/review",
            json={"sql": "SELECT id FROM users WHERE id = 1"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(review_id)
    assert data["sql"] == "SELECT id FROM users WHERE id = 1"
    assert data["ai_review"]["summary"] == "Query looks good."


@pytest.mark.asyncio
async def test_create_review_response_structure() -> None:
    review = make_review()
    review_id = uuid.uuid4()

    app.dependency_overrides[get_review_service] = lambda: mock_service_dep(review)
    app.dependency_overrides[get_review_repository] = lambda: mock_repo_dep(review_id, review)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": "SELECT 1"})

    app.dependency_overrides.clear()

    data = response.json()
    assert "static_analysis" in data
    assert "ai_review" in data
    assert "created_at" in data
    assert data["static_analysis"]["query_type"] == "SELECT"


@pytest.mark.asyncio
async def test_sql_parse_error_returns_422() -> None:
    svc = MagicMock()
    svc.review = AsyncMock(side_effect=SQLParseError(message="Failed to parse SQL: syntax error"))

    app.dependency_overrides[get_review_service] = lambda: svc
    app.dependency_overrides[get_review_repository] = lambda: MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": "SELECT FROM WHERE"})

    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SQL_PARSE_ERROR"


@pytest.mark.asyncio
async def test_llm_provider_error_returns_502() -> None:
    svc = MagicMock()
    svc.review = AsyncMock(
        side_effect=LLMProviderError(message="OpenAI failed", provider="openai")
    )

    app.dependency_overrides[get_review_service] = lambda: svc
    app.dependency_overrides[get_review_repository] = lambda: MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": "SELECT 1"})

    app.dependency_overrides.clear()

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_empty_sql_returns_422() -> None:
    # Dependency must be overridden: FastAPI resolves Depends before validating
    # the body, so the real get_review_service would fail on missing API key first.
    app.dependency_overrides[get_review_service] = lambda: MagicMock()
    app.dependency_overrides[get_review_repository] = lambda: MagicMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": ""})

    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_review_returns_200() -> None:
    review = make_review()
    review_id = uuid.uuid4()

    app.dependency_overrides[get_review_repository] = lambda: mock_repo_dep(review_id, review)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{BASE}/review/{review_id}")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(review_id)


@pytest.mark.asyncio
async def test_get_review_returns_404_for_unknown_id() -> None:
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)

    app.dependency_overrides[get_review_repository] = lambda: repo

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{BASE}/review/{uuid.uuid4()}")

    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_with_findings_serialized() -> None:
    review = make_review()
    review.static_analysis.findings.append(
        AnalysisFinding(
            rule_id="select_star",
            severity=Severity.warning,
            category=FindingCategory.performance,
            title="SELECT * detected",
            message="Fetches all columns.",
        )
    )
    review_id = uuid.uuid4()

    app.dependency_overrides[get_review_service] = lambda: mock_service_dep(review)
    app.dependency_overrides[get_review_repository] = lambda: mock_repo_dep(review_id, review)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": "SELECT * FROM users"})

    app.dependency_overrides.clear()

    data = response.json()
    assert data["static_analysis"]["warning_count"] == 1
    assert data["static_analysis"]["findings"][0]["rule_id"] == "select_star"


@pytest.mark.asyncio
async def test_review_mode_defaults_to_senior() -> None:
    review = make_review()
    review_id = uuid.uuid4()

    app.dependency_overrides[get_review_service] = lambda: mock_service_dep(review)
    app.dependency_overrides[get_review_repository] = lambda: mock_repo_dep(review_id, review)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"{BASE}/review", json={"sql": "SELECT 1"})

    app.dependency_overrides.clear()

    assert response.json()["review_mode"] == "senior"
