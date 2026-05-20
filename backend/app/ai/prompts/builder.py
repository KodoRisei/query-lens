from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.base import Message
from app.ai.prompts.templates import MODE_FOCUS, RESPONSE_SCHEMA, SYSTEM_PROMPTS
from app.domain.models.analysis import AnalysisFinding, StaticAnalysisResult
from app.domain.models.query import SQLQuery

if TYPE_CHECKING:
    from app.analysis.execution_plan.models import ExecutionPlanResult


class PromptBuilder:
    """
    Builds the message list for a SQL review request.

    Separating prompt construction from provider invocation means prompts
    can be tested, versioned, and swapped independently of the LLM client.
    """

    def build_review_messages(
        self,
        query: SQLQuery,
        analysis: StaticAnalysisResult,
        plan_result: ExecutionPlanResult | None = None,
    ) -> list[Message]:
        system = SYSTEM_PROMPTS[query.review_mode]
        user = self._build_user_message(query, analysis, plan_result)
        return [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]

    def _build_user_message(
        self,
        query: SQLQuery,
        analysis: StaticAnalysisResult,
        plan_result: ExecutionPlanResult | None,
    ) -> str:
        parts = [
            "## SQL Query",
            f"```sql\n{query.sql.strip()}\n```",
        ]

        if query.dialect:
            parts.append(f"**Dialect:** {query.dialect}")

        parts.append("")
        parts.append("## Static Analysis Findings")
        if analysis.findings:
            parts.append(self._format_static_findings(analysis.findings[:5]))
            if len(analysis.findings) > 5:
                parts.append(f"_…and {len(analysis.findings) - 5} more findings._")
        else:
            parts.append("_No anti-patterns detected._")

        if plan_result is not None:
            parts.append("")
            parts.append(self._format_plan_section(plan_result))

        parts.append("")
        parts.append("## Task")
        parts.append(f"Review the query above. Focus: {MODE_FOCUS[query.review_mode]}")
        parts.append("")
        parts.append(RESPONSE_SCHEMA)

        return "\n".join(parts)

    def _format_static_findings(self, findings: list[AnalysisFinding]) -> str:
        lines = []
        for i, f in enumerate(findings, 1):
            lines.append(
                f"{i}. **[{f.severity.upper()}] {f.title}** (`{f.rule_id}`)\n   {f.message}"
            )
            if f.suggestion:
                lines.append(f"   *Suggestion:* {f.suggestion}")
        return "\n\n".join(lines)

    def _format_plan_section(self, plan_result: ExecutionPlanResult) -> str:
        lines = ["## Execution Plan Analysis"]

        if plan_result.has_analyze_data and plan_result.execution_time_ms is not None:
            lines.append(
                f"**Execution time:** {plan_result.execution_time_ms:.1f}ms  "
                f"**Planning time:** {plan_result.plan.planning_time_ms:.1f}ms"
            )

        if plan_result.findings:
            lines.append("")
            for i, f in enumerate(plan_result.findings[:3], 1):
                lines.append(
                    f"{i}. **[{f.severity.upper()}] {f.title}** (`{f.rule_id}`)\n   {f.message}"
                )
                if f.suggestion:
                    lines.append(f"   *Suggestion:* {f.suggestion}")
        else:
            lines.append("_No bottlenecks detected in the execution plan._")

        return "\n".join(lines)
