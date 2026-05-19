import sqlglot
import sqlglot.expressions as exp
from sqlglot.errors import ParseError, SqlglotError

from app.core.exceptions import SQLParseError


def parse(sql: str, dialect: str = "") -> exp.Expression:
    """
    Parse SQL into a sqlglot AST.

    Raises SQLParseError on invalid SQL. Uses 'ansi' dialect by default,
    which is the most permissive for generic analysis. Pass 'postgres',
    'mysql', etc. to enable dialect-specific syntax.
    """
    try:
        ast = sqlglot.parse_one(sql, dialect=dialect, error_level=sqlglot.ErrorLevel.RAISE)
    except ParseError as exc:
        errors = exc.errors
        first = errors[0] if errors else {}
        raise SQLParseError(
            message=f"Failed to parse SQL: {exc}",
            details={
                "description": first.get("description", ""),
                "line": first.get("line"),
                "column": first.get("col"),
            },
        ) from exc
    except SqlglotError as exc:
        raise SQLParseError(message=f"SQL parsing error: {exc}") from exc

    return ast


def extract_query_type(ast: exp.Expression) -> str:
    type_map: dict[type[exp.Expression], str] = {
        exp.Select: "SELECT",
        exp.Insert: "INSERT",
        exp.Update: "UPDATE",
        exp.Delete: "DELETE",
        exp.Create: "CREATE",
        exp.Drop: "DROP",
        exp.Alter: "ALTER",
        exp.Merge: "MERGE",
    }
    for node_type, label in type_map.items():
        if isinstance(ast, node_type):
            return label
    # CTE / WITH wraps a SELECT
    if isinstance(ast, exp.With):
        return extract_query_type(ast.this)
    return "UNKNOWN"


def extract_table_references(ast: exp.Expression) -> list[str]:
    """Return unique table names referenced in the query."""
    seen: set[str] = set()
    tables: list[str] = []
    for table in ast.find_all(exp.Table):
        name = table.name
        if name and name not in seen:
            seen.add(name)
            tables.append(name)
    return tables
