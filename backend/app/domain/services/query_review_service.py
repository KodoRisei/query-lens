from app.ai.base import LLMProvider
from app.ai.prompts.builder import PromptBuilder
from app.ai.response_parser import AIResponseParser
from app.analysis.execution_plan import ExecutionPlanAnalyzer, ExecutionPlanResult, ExplainAnalyzeRunner
from app.analysis.static_analyzer import StaticAnalyzer
from app.core.exceptions import ExecutionPlanError
from app.core.logging import get_logger
from app.domain.models.query import SQLQuery
from app.domain.models.review import QueryReview

logger = get_logger(__name__)


class QueryReviewService:
    """
    Orchestrates the full SQL review pipeline:

      1. Static analysis    — deterministic, always runs
      2. Execution plan     — EXPLAIN ANALYZE against PostgreSQL (optional)
      3. Prompt building    — formats all findings + query for the LLM
      4. LLM completion     — AI explanations and rewrite suggestions
      5. Response parsing   — structured AIReview from raw LLM text

    The service holds no state and has no framework dependencies.
    Inject a mock LLMProvider in tests to avoid real API calls.
    Omit plan_runner to skip the execution plan step (e.g. no DB in tests).
    """

    def __init__(
        self,
        analyzer: StaticAnalyzer,
        provider: LLMProvider,
        prompt_builder: PromptBuilder,
        response_parser: AIResponseParser,
        plan_runner: ExplainAnalyzeRunner | None = None,
        plan_analyzer: ExecutionPlanAnalyzer | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._response_parser = response_parser
        self._plan_runner = plan_runner
        self._plan_analyzer = plan_analyzer or ExecutionPlanAnalyzer()

    async def review(self, query: SQLQuery) -> QueryReview:
        logger.info(
            "review.start",
            dialect=query.dialect,
            mode=query.review_mode,
            provider=self._provider.provider_name,
            sql_length=len(query.sql),
        )

        static_result = self._analyzer.analyze(query)

        logger.info(
            "review.static_analysis_complete",
            findings=len(static_result.findings),
            critical=static_result.critical_count,
            query_type=static_result.query_type,
        )

        plan_result = await self._run_explain(query.sql, static_result.query_type)

        messages = self._prompt_builder.build_review_messages(
            query, static_result, plan_result
        )
        llm_response = await self._provider.complete(messages)
        ai_review = self._response_parser.parse(llm_response, static_result)

        logger.info(
            "review.complete",
            provider=llm_response.provider,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            ai_findings=len(ai_review.findings),
            plan_findings=len(plan_result.findings) if plan_result else 0,
        )

        return QueryReview(
            query=query,
            static_analysis=static_result,
            ai_review=ai_review,
            execution_plan=plan_result,
        )

    async def _run_explain(
        self, sql: str, query_type: str
    ) -> ExecutionPlanResult | None:
        if self._plan_runner is None:
            return None

        try:
            raw_plan = await self._plan_runner.run(sql, query_type)
            result = self._plan_analyzer.analyze(raw_plan)
            logger.info(
                "review.plan_analysis_complete",
                findings=len(result.findings),
                execution_time_ms=result.execution_time_ms,
                has_analyze_data=result.has_analyze_data,
            )
            return result
        except ExecutionPlanError as exc:
            logger.warning(
                "review.plan_analysis_skipped",
                reason=exc.message,
            )
            return None
