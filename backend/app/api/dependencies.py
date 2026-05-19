from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_provider
from app.ai.prompts.builder import PromptBuilder
from app.ai.response_parser import AIResponseParser
from app.analysis.execution_plan import ExecutionPlanAnalyzer, ExplainAnalyzeRunner
from app.analysis.static_analyzer import StaticAnalyzer
from app.core.config import Settings, get_settings
from app.domain.services.query_review_service import QueryReviewService
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.repositories.query_review import QueryReviewRepository


async def get_review_service(
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> QueryReviewService:
    """
    Builds the review service with the default LLM provider from config.

    Per-request provider overrides are handled inside the endpoint itself
    by constructing a new service when `request.provider` differs from the default.
    """
    return QueryReviewService(
        analyzer=StaticAnalyzer(),
        provider=get_provider(settings=settings),
        prompt_builder=PromptBuilder(),
        response_parser=AIResponseParser(),
        plan_runner=ExplainAnalyzeRunner(db, settings.explain_analyze_timeout_seconds),
        plan_analyzer=ExecutionPlanAnalyzer(),
    )


def get_review_repository(
    db: AsyncSession = Depends(get_db_session),
) -> QueryReviewRepository:
    return QueryReviewRepository(db)
