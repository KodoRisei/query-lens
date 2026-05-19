import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.base import LLMResponse, Message
from app.ai.prompts.builder import PromptBuilder
from app.ai.response_parser import AIResponseParser
from app.analysis.static_analyzer import StaticAnalyzer
from app.domain.models.query import ReviewMode, SQLQuery
from app.domain.services.query_review_service import QueryReviewService


def make_service(llm_content: str) -> QueryReviewService:
    mock_provider = MagicMock()
    mock_provider.provider_name = "mock"
    mock_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content=llm_content,
            provider="mock",
            model="mock-model",
            input_tokens=50,
            output_tokens=100,
        )
    )
    return QueryReviewService(
        analyzer=StaticAnalyzer(),
        provider=mock_provider,
        prompt_builder=PromptBuilder(),
        response_parser=AIResponseParser(),
    )


def valid_llm_response(summary: str = "Looks good.", improved: str | None = None) -> str:
    return json.dumps({
        "summary": summary,
        "improved_query": improved,
        "findings": [],
        "educational_note": None,
    })


@pytest.mark.asyncio
async def test_review_returns_query_review():
    service = make_service(valid_llm_response())
    result = await service.review(SQLQuery("SELECT id FROM users WHERE id = 1"))
    assert result.query.sql == "SELECT id FROM users WHERE id = 1"
    assert result.ai_review.summary == "Looks good."


@pytest.mark.asyncio
async def test_static_findings_populate_result():
    service = make_service(valid_llm_response())
    result = await service.review(SQLQuery("DELETE FROM users"))
    # Static analysis should catch the missing WHERE
    assert result.static_analysis.critical_count == 1


@pytest.mark.asyncio
async def test_ai_findings_from_llm_response():
    content = json.dumps({
        "summary": "Found an issue.",
        "improved_query": "SELECT id FROM users",
        "findings": [{"rule_id": "select_star", "explanation": "Fetches all columns.", "suggestion": "List them."}],
        "educational_note": None,
    })
    service = make_service(content)
    result = await service.review(SQLQuery("SELECT * FROM users"))
    assert any(f.rule_id == "select_star" for f in result.ai_review.findings)


@pytest.mark.asyncio
async def test_review_mode_passed_through():
    service = make_service(valid_llm_response())
    result = await service.review(SQLQuery("SELECT 1", review_mode=ReviewMode.junior))
    assert result.query.review_mode == ReviewMode.junior


@pytest.mark.asyncio
async def test_improved_query_from_llm():
    content = valid_llm_response(improved="SELECT id FROM users WHERE id = 1 LIMIT 10")
    service = make_service(content)
    result = await service.review(SQLQuery("SELECT * FROM users ORDER BY id"))
    assert result.ai_review.improved_query is not None
    assert "LIMIT" in result.ai_review.improved_query


@pytest.mark.asyncio
async def test_provider_called_once():
    mock_provider = MagicMock()
    mock_provider.provider_name = "mock"
    mock_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content=valid_llm_response(),
            provider="mock",
            model="mock-model",
            input_tokens=10,
            output_tokens=20,
        )
    )
    service = QueryReviewService(
        analyzer=StaticAnalyzer(),
        provider=mock_provider,
        prompt_builder=PromptBuilder(),
        response_parser=AIResponseParser(),
    )
    await service.review(SQLQuery("SELECT 1"))
    mock_provider.complete.assert_awaited_once()
