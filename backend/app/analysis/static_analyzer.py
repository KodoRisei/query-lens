from app.analysis.anti_patterns import RULE_REGISTRY
from app.analysis.anti_patterns.base import AntiPatternRule
from app.analysis.parser import extract_query_type, extract_table_references, parse
from app.core.config import get_settings
from app.core.exceptions import QueryTooLongError, SQLParseError
from app.domain.models.analysis import StaticAnalysisResult
from app.domain.models.query import SQLQuery


class StaticAnalyzer:
    """
    Orchestrates deterministic SQL analysis.

    Pipeline:
      1. Validate input length
      2. Parse SQL into AST (raises SQLParseError on failure)
      3. Run all registered anti-pattern rules
      4. Extract metadata (query type, table references)

    The analyzer is stateless — rules are instantiated once and reused.
    Inject a custom rule list in tests to isolate individual rules.
    """

    def __init__(self, rules: list[AntiPatternRule] | None = None) -> None:
        self._rules = rules if rules is not None else RULE_REGISTRY

    def analyze(self, query: SQLQuery) -> StaticAnalysisResult:
        settings = get_settings()

        if len(query.sql) > settings.max_query_length:
            raise QueryTooLongError(
                message=(
                    f"Query length {len(query.sql)} exceeds the maximum "
                    f"of {settings.max_query_length} characters."
                ),
                length=len(query.sql),
                max_length=settings.max_query_length,
            )

        ast = parse(query.sql, dialect=query.dialect)

        findings = []
        for rule in self._rules:
            findings.extend(rule.check(ast))

        return StaticAnalysisResult(
            findings=findings,
            query_type=extract_query_type(ast),
            dialect=query.dialect,
            table_references=extract_table_references(ast),
        )
