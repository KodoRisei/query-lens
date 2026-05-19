import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_provider
from app.ai.prompts.builder import PromptBuilder
from app.ai.response_parser import AIResponseParser
from app.analysis.execution_plan import ExecutionPlanAnalyzer, ExplainAnalyzeRunner
from app.analysis.static_analyzer import StaticAnalyzer
from app.api.dependencies import get_review_repository, get_review_service
from app.api.v1.schemas import QueryReviewResponse, ReviewRequest
from app.core.config import Settings, get_settings
from app.domain.models.query import SQLQuery
from app.domain.services.query_review_service import QueryReviewService
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.repositories.query_review import QueryReviewRepository

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/review", response_model=QueryReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    request: ReviewRequest,
    service: QueryReviewService = Depends(get_review_service),
    repo: QueryReviewRepository = Depends(get_review_repository),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> QueryReviewResponse:
    """
    Submit a SQL query for review.

    Runs deterministic static analysis, optionally EXPLAIN ANALYZE, then
    calls the configured LLM for explanations and rewrite suggestions.
    The result is persisted and returned as a structured review.
    """
    # Rebuild service with the requested provider if it differs from the default.
    # The default service (from Depends) can be overridden in tests; only the
    # provider-swap path is not covered by dependency overrides.
    if request.provider and request.provider != settings.default_llm_provider:
        service = QueryReviewService(
            analyzer=StaticAnalyzer(),
            provider=get_provider(request.provider, settings=settings),
            prompt_builder=PromptBuilder(),
            response_parser=AIResponseParser(),
            plan_runner=ExplainAnalyzeRunner(db, settings.explain_analyze_timeout_seconds),
            plan_analyzer=ExecutionPlanAnalyzer(),
        )

    query = SQLQuery(
        sql=request.sql,
        dialect=request.dialect,
        review_mode=request.review_mode,
    )

    review = await service.review(query)
    record = await repo.save(review)
    await db.commit()

    return QueryReviewResponse.from_domain(review, record.id, record.created_at)


@router.get("/review/{review_id}", response_model=QueryReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    repo: QueryReviewRepository = Depends(get_review_repository),
) -> QueryReviewResponse:
    """Retrieve a previously created review by ID."""
    record = await repo.get_by_id(review_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REVIEW_NOT_FOUND",
                "message": f"No review found with id '{review_id}'.",
            },
        )
    return QueryReviewResponse.from_orm_record(record)
