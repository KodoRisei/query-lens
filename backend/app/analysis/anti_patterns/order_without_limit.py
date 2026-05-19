import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity


class OrderWithoutLimitRule(AntiPatternRule):
    """
    Flags SELECT statements with ORDER BY but no LIMIT/FETCH FIRST.

    Sorting the entire result set can be extremely expensive on large tables.
    Without a LIMIT the database must sort all matching rows before returning any,
    and the caller receives a potentially enormous payload.

    Exception: aggregate queries (GROUP BY) that use ORDER BY are common and
    intentional (e.g. ORDER BY count DESC for ranked aggregates). We skip those
    to reduce false positives.
    """

    rule_id = "order_without_limit"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for select in ast.find_all(exp.Select):
            has_order = bool(select.args.get("order"))
            has_limit = bool(select.args.get("limit"))
            has_group_by = bool(select.args.get("group"))

            if has_order and not has_limit and not has_group_by:
                order_node = select.args["order"]
                findings.append(AnalysisFinding(
                    rule_id=self.rule_id,
                    severity=Severity.warning,
                    category=FindingCategory.performance,
                    title="ORDER BY without LIMIT",
                    message=(
                        "Sorting the full result set without a LIMIT forces PostgreSQL to "
                        "complete the entire sort before returning any rows. On large tables "
                        "this can be slow and memory-intensive. The caller also receives "
                        "an unbounded result set."
                    ),
                    suggestion=(
                        "Add LIMIT N to cap the result set. "
                        "If you genuinely need all rows sorted, consider whether the "
                        "sort can be deferred to the application layer or whether a "
                        "cursor-based approach (keyset pagination) is more appropriate."
                    ),
                    line=order_node.meta.get("line"),
                    column=order_node.meta.get("col"),
                ))

        return findings
