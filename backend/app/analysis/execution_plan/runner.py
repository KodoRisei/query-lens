import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExecutionPlanError
from app.core.logging import get_logger

logger = get_logger(__name__)

_DML_TYPES = {"INSERT", "UPDATE", "DELETE", "MERGE"}


class ExplainAnalyzeRunner:
    """
    Executes EXPLAIN against a live PostgreSQL connection.

    For SELECT queries, uses ANALYZE and BUFFERS to capture actual runtime
    statistics. For DML (INSERT/UPDATE/DELETE/MERGE), uses plain EXPLAIN
    without ANALYZE to avoid executing the statement.

    asyncpg parses the PostgreSQL JSON type automatically, so the result
    is returned as a Python dict ready for the plan parser.
    """

    def __init__(self, session: AsyncSession, timeout_seconds: int = 30) -> None:
        self._session = session
        self._timeout_seconds = timeout_seconds

    async def run(self, sql: str, query_type: str = "SELECT") -> dict:
        use_analyze = query_type not in _DML_TYPES
        options = "ANALYZE, BUFFERS, FORMAT JSON" if use_analyze else "FORMAT JSON"
        explain_sql = f"EXPLAIN ({options}) {sql}"

        logger.info(
            "explain.run",
            query_type=query_type,
            analyze=use_analyze,
        )

        try:
            result = await asyncio.wait_for(
                self._session.execute(text(explain_sql)),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ExecutionPlanError(
                message=f"EXPLAIN ANALYZE timed out after {self._timeout_seconds}s.",
                details={"timeout_seconds": self._timeout_seconds},
            ) from exc
        except Exception as exc:
            raise ExecutionPlanError(
                message=f"EXPLAIN ANALYZE failed: {exc}",
            ) from exc

        rows = result.fetchall()
        plan_data = rows[0][0]

        # asyncpg returns PostgreSQL JSON as a Python object.
        # EXPLAIN FORMAT JSON produces a list with one element.
        if isinstance(plan_data, list):
            return plan_data[0]
        return plan_data
