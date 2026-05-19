"""
Integration tests for the /queries/review endpoints against a real PostgreSQL database.

The AI service is mocked so no LLM API key is required.
Run with:
    INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://... pytest tests/integration/test_api_integration.py
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_review_service
from app.domain.models.analysis import StaticAnalysisResult
from app.domain.models.query import ReviewMode, SQLQuery
from app.domain.models.review import AIReview, QueryReview
from app.main import app


def _make_review(sql: str = "SELECT id FROM users WHERE id = 1") -> QueryReview:
    return QueryReview(
        query=SQLQuery(sql=sql, review_mode=ReviewMode.senior),
        static_analysis=StaticAnalysisResult(
            findings=[],
            query_type="SELECT",
            table_references=["users"],
        ),
        ai_review=AIReview(
            summary="No issues found.",
            findings=[],
            improved_query=None,
            educational_note=None,
            provider="ollama",
            model="llama3.1",
            input_tokens=80,
            output_tokens=120,
        ),
        execution_plan=None,
    )


def _mock_service(review: QueryReview) -> MagicMock:
    svc = MagicMock()
    svc.review = AsyncMock(return_value=review)
    return svc


@pytest.mark.asyncio
async def test_post_review_returns_201_with_id(api_client: AsyncClient) -> None:
    review = _make_review()
    app.dependency_overrides[get_review_service] = lambda: _mock_service(review)

    response = await api_client.post(
        "/api/v1/queries/review",
        json={"sql": "SELECT id FROM users WHERE id = 1"},
    )

    app.dependency_overrides.pop(get_review_service, None)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert uuid.UUID(data["id"])  # valid UUID
    assert data["sql"] == "SELECT id FROM users WHERE id = 1"
    assert data["ai_review"]["summary"] == "No issues found."
    assert data["ai_review"]["provider"] == "ollama"


@pytest.mark.asyncio
async def test_post_then_get_roundtrip(api_client: AsyncClient) -> None:
    """Record created by POST is retrievable by GET."""
    review = _make_review(sql="SELECT name FROM products WHERE id = 5")
    app.dependency_overrides[get_review_service] = lambda: _mock_service(review)

    post_response = await api_client.post(
        "/api/v1/queries/review",
        json={"sql": "SELECT name FROM products WHERE id = 5"},
    )
    app.dependency_overrides.pop(get_review_service, None)

    assert post_response.status_code == 201
    review_id = post_response.json()["id"]

    get_response = await api_client.get(f"/api/v1/queries/review/{review_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == review_id
    assert data["sql"] == "SELECT name FROM products WHERE id = 5"
    assert data["static_analysis"]["query_type"] == "SELECT"
    assert data["static_analysis"]["table_references"] == ["users"]


@pytest.mark.asyncio
async def test_get_unknown_id_returns_404(api_client: AsyncClient) -> None:
    response = await api_client.get(f"/api/v1/queries/review/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REVIEW_NOT_FOUND"


@pytest.mark.asyncio
async def test_multiple_posts_create_independent_records(api_client: AsyncClient) -> None:
    app.dependency_overrides[get_review_service] = lambda: _mock_service(_make_review("SELECT 1"))
    r1 = await api_client.post("/api/v1/queries/review", json={"sql": "SELECT 1"})
    app.dependency_overrides.pop(get_review_service, None)

    app.dependency_overrides[get_review_service] = lambda: _mock_service(_make_review("SELECT 2"))
    r2 = await api_client.post("/api/v1/queries/review", json={"sql": "SELECT 2"})
    app.dependency_overrides.pop(get_review_service, None)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


@pytest.mark.asyncio
async def test_review_mode_stored_correctly(api_client: AsyncClient) -> None:
    review = QueryReview(
        query=SQLQuery(sql="SELECT 1", review_mode=ReviewMode.junior),
        static_analysis=StaticAnalysisResult(findings=[], query_type="SELECT", table_references=[]),
        ai_review=AIReview(
            summary="Keep it simple.",
            findings=[],
            improved_query=None,
            educational_note="Great first query!",
            provider="ollama",
            model="llama3.1",
            input_tokens=50,
            output_tokens=80,
        ),
        execution_plan=None,
    )
    app.dependency_overrides[get_review_service] = lambda: _mock_service(review)

    response = await api_client.post(
        "/api/v1/queries/review",
        json={"sql": "SELECT 1", "review_mode": "junior"},
    )
    app.dependency_overrides.pop(get_review_service, None)

    assert response.status_code == 201
    data = response.json()
    assert data["review_mode"] == "junior"
    assert data["ai_review"]["educational_note"] == "Great first query!"

    # GET also returns correct review_mode
    get_resp = await api_client.get(f"/api/v1/queries/review/{data['id']}")
    assert get_resp.json()["review_mode"] == "junior"
