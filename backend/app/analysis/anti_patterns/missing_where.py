import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity


class MissingWhereRule(AntiPatternRule):
    """
    Flags DELETE and UPDATE statements that have no WHERE clause.

    These are data-destructive operations that will affect every row in the table
    if no predicate is present. Severity is critical because there is no undo.
    """

    rule_id = "missing_where"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for delete in ast.find_all(exp.Delete):
            if not delete.args.get("where"):
                table = self._table_name(delete)
                findings.append(AnalysisFinding(
                    rule_id=self.rule_id,
                    severity=Severity.critical,
                    category=FindingCategory.correctness,
                    title="DELETE without WHERE clause",
                    message=(
                        f"DELETE FROM {table} has no WHERE clause and will remove "
                        "every row in the table. This cannot be undone without a backup."
                    ),
                    suggestion=(
                        "Add a WHERE clause to target specific rows. "
                        "If you intend to truncate the table, use TRUNCATE instead — "
                        "it is faster and its intent is explicit."
                    ),
                    line=delete.meta.get("line"),
                    column=delete.meta.get("col"),
                ))

        for update in ast.find_all(exp.Update):
            if not update.args.get("where"):
                table = self._table_name(update)
                findings.append(AnalysisFinding(
                    rule_id=self.rule_id,
                    severity=Severity.critical,
                    category=FindingCategory.correctness,
                    title="UPDATE without WHERE clause",
                    message=(
                        f"UPDATE {table} has no WHERE clause and will modify "
                        "every row in the table."
                    ),
                    suggestion=(
                        "Add a WHERE clause to target specific rows. "
                        "Consider wrapping in a transaction so you can verify "
                        "the affected row count before committing."
                    ),
                    line=update.meta.get("line"),
                    column=update.meta.get("col"),
                ))

        return findings

    def _table_name(self, node: exp.Expression) -> str:
        table = node.find(exp.Table)
        return table.name if table else "unknown"
