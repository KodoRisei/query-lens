import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity


class SelectStarRule(AntiPatternRule):
    """
    Flags SELECT * and SELECT table.* in query projections.

    COUNT(*) and similar aggregate uses are intentionally excluded because
    the Star there carries semantic meaning (count all rows), not a lazy projection.
    """

    rule_id = "select_star"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for select in ast.find_all(exp.Select):
            for expr in select.expressions:
                if isinstance(expr, exp.Star):
                    findings.append(self._finding(expr, "SELECT *"))
                elif isinstance(expr, exp.Column) and isinstance(expr.this, exp.Star):
                    table = expr.table or "table"
                    findings.append(self._finding(expr, f"SELECT {table}.*"))

        return findings

    def _finding(self, node: exp.Expression, form: str) -> AnalysisFinding:
        return AnalysisFinding(
            rule_id=self.rule_id,
            severity=Severity.warning,
            category=FindingCategory.performance,
            title=f"{form} detected",
            message=(
                f"{form} fetches every column, including those you don't need. "
                "This increases I/O, network transfer, and breaks queries silently "
                "when the schema changes (added/removed columns)."
            ),
            suggestion=(
                "Explicitly list the columns you need: "
                "SELECT id, name, email FROM ... "
                "This makes the query self-documenting and index-friendly."
            ),
            line=node.meta.get("line"),
            column=node.meta.get("col"),
        )
