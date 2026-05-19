import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity


class ImplicitCrossJoinRule(AntiPatternRule):
    """
    Flags FROM a, b (comma-separated tables) which produce a cartesian product.

    sqlglot normalizes FROM a, b into a CrossJoin node without an ON clause.
    We only flag joins with no ON or USING predicate — CROSS JOIN without
    a predicate is sometimes intentional (e.g. cross-joining a small lookup table),
    but should be explicit and reviewed.
    """

    rule_id = "implicit_cross_join"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for join in ast.find_all(exp.Join):
            is_cross = str(join.args.get("kind", "")).upper() == "CROSS"
            has_on = join.args.get("on") is not None
            has_using = join.args.get("using") is not None

            if is_cross and not has_on and not has_using:
                joined_table = join.find(exp.Table)
                table_name = joined_table.name if joined_table else "unknown"
                findings.append(
                    AnalysisFinding(
                        rule_id=self.rule_id,
                        severity=Severity.warning,
                        category=FindingCategory.performance,
                        title=f"Cartesian product with '{table_name}'",
                        message=(
                            f"The join with '{table_name}' has no ON or USING condition, "
                            "producing a cartesian product. Every row in one table is "
                            "paired with every row in the other. This grows as O(n×m)."
                        ),
                        suggestion=(
                            "Add an explicit JOIN condition: "
                            f"JOIN {table_name} ON a.id = {table_name}.a_id. "
                            "If the cross product is intentional, use CROSS JOIN explicitly "
                            "and add a comment explaining the intent."
                        ),
                        line=join.meta.get("line"),
                        column=join.meta.get("col"),
                    )
                )

        return findings
