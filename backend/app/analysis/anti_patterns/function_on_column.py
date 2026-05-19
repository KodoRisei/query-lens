import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity

# These functions on a column in WHERE are always non-sargable.
# We track them by name for a more specific suggestion in the finding message.
_COMMON_OFFENDERS: dict[type[exp.Func], str] = {
    exp.Lower: "LOWER",
    exp.Upper: "UPPER",
    exp.Year: "YEAR",
    exp.Month: "MONTH",
    exp.Day: "DAY",
    exp.TsOrDsToDate: "DATE",
    exp.Cast: "CAST",
    exp.Substring: "SUBSTRING",
    exp.Trim: "TRIM",
    exp.Coalesce: "COALESCE",
}


class FunctionOnColumnRule(AntiPatternRule):
    """
    Flags WHERE clauses where a function is applied directly to a column.

    This is the "non-sargable predicate" anti-pattern. When a function wraps
    a column, the database cannot use a B-tree index on that column — it must
    evaluate the function for every row.

    Pattern detected:  WHERE func(column) = value
    Safe alternative:  WHERE column = func_inverse(value)  — or use a functional index.
    """

    rule_id = "function_on_column"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for select in ast.find_all(exp.Select):
            where = select.args.get("where")
            if not where:
                continue

            for func in where.find_all(exp.Func):
                func_name = self._func_name(func)
                primary_arg = self._primary_arg(func)

                if isinstance(primary_arg, exp.Column):
                    col_name = primary_arg.name or "column"
                    findings.append(
                        AnalysisFinding(
                            rule_id=self.rule_id,
                            severity=Severity.warning,
                            category=FindingCategory.performance,
                            title=f"Non-sargable predicate: {func_name}({col_name})",
                            message=(
                                f"Wrapping '{col_name}' in {func_name}() inside the WHERE clause "
                                "prevents the database from using any B-tree index on that column. "
                                "PostgreSQL must compute the function for every row in the table."
                            ),
                            suggestion=(
                                f"Consider a functional index: "
                                f"CREATE INDEX ON table ({func_name}({col_name})). "
                                "Alternatively, restructure the predicate to isolate the column: "
                                f"instead of WHERE {func_name}({col_name}) = val, use a range "
                                "condition or store the pre-computed value."
                            ),
                            line=func.meta.get("line"),
                            column=func.meta.get("col"),
                        )
                    )

        return findings

    def _primary_arg(self, func: exp.Func) -> exp.Expression | None:
        if isinstance(func, exp.Anonymous):
            # Anonymous: args are in 'expressions', not 'this'
            exprs = func.args.get("expressions") or []
            return exprs[0] if exprs else None
        return func.args.get("this")

    def _func_name(self, func: exp.Func) -> str:
        for func_type, name in _COMMON_OFFENDERS.items():
            if isinstance(func, func_type):
                return name
        if isinstance(func, exp.Anonymous):
            return str(func.args.get("this", "FUNC")).upper()
        return type(func).__name__.upper()
