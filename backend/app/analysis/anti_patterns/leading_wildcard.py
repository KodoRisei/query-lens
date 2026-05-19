import sqlglot.expressions as exp

from app.analysis.anti_patterns.base import AntiPatternRule
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity


class LeadingWildcardRule(AntiPatternRule):
    """
    Flags LIKE patterns that begin with a wildcard (e.g. LIKE '%value').

    A leading wildcard forces a full table scan regardless of any B-tree index
    on the column. The database cannot use a prefix-based index seek.
    """

    rule_id = "leading_wildcard"

    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []

        for like_node in ast.find_all(exp.Like, exp.ILike):
            pattern = like_node.args.get("expression")
            if not isinstance(pattern, exp.Literal):
                continue

            pattern_str: str = pattern.this
            if pattern_str.startswith("%"):
                operator = "ILIKE" if isinstance(like_node, exp.ILike) else "LIKE"
                findings.append(AnalysisFinding(
                    rule_id=self.rule_id,
                    severity=Severity.warning,
                    category=FindingCategory.performance,
                    title=f"Leading wildcard in {operator} pattern",
                    message=(
                        f"The pattern '{pattern_str}' starts with '%', which forces "
                        "the database to scan every row. A B-tree index on the column "
                        "cannot be used for prefix matching in this direction."
                    ),
                    suggestion=(
                        "If you need full-text search, consider a GIN index with "
                        "pg_trgm (trigram matching) which supports leading wildcards efficiently: "
                        "CREATE INDEX ON table USING gin(column gin_trgm_ops). "
                        "If you control the data format, restructure so the searchable "
                        "part is a prefix, enabling LIKE 'value%' instead."
                    ),
                    line=like_node.meta.get("line"),
                    column=like_node.meta.get("col"),
                ))

        return findings
