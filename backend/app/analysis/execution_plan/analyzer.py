from typing import Any

from app.analysis.execution_plan.models import (
    ExecutionPlan,
    ExecutionPlanResult,
    PlanFinding,
    PlanNode,
)
from app.analysis.execution_plan.parser import parse_plan
from app.analysis.execution_plan.rules import PLAN_RULE_REGISTRY, PlanRule


class ExecutionPlanAnalyzer:
    """
    Parses a raw EXPLAIN JSON dict and runs all registered plan rules
    across every node in the plan tree.

    Inject a custom rule list in tests to isolate individual rules.
    """

    def __init__(self, rules: list[PlanRule] | None = None) -> None:
        self._rules = rules if rules is not None else PLAN_RULE_REGISTRY

    def analyze(self, raw_plan: dict[str, Any]) -> ExecutionPlanResult:
        plan = parse_plan(raw_plan)
        findings: list[PlanFinding] = []
        self._walk(plan.root, plan, findings)

        return ExecutionPlanResult(
            plan=plan,
            findings=findings,
            has_analyze_data=plan.root.has_analyze_data,
        )

    def _walk(
        self,
        node: PlanNode,
        plan: ExecutionPlan,
        findings: list[PlanFinding],
    ) -> None:
        for rule in self._rules:
            findings.extend(rule.check(node, plan))
        for child in node.children:
            self._walk(child, plan, findings)
