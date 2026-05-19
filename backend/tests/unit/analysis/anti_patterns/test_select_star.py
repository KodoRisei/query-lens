import sqlglot

from app.analysis.anti_patterns.select_star import SelectStarRule
from app.domain.models.analysis import Severity

rule = SelectStarRule()


def check(sql: str):
    return rule.check(sqlglot.parse_one(sql))


def test_select_star_flagged():
    findings = check("SELECT * FROM users")
    assert len(findings) == 1
    assert findings[0].rule_id == "select_star"
    assert findings[0].severity == Severity.warning


def test_select_qualified_star_flagged():
    findings = check("SELECT u.* FROM users u")
    assert len(findings) == 1
    assert "u.*" in findings[0].title


def test_explicit_columns_clean():
    assert check("SELECT id, name, email FROM users") == []


def test_count_star_not_flagged():
    # COUNT(*) is a valid aggregate — the Star is inside a function, not a projection
    assert check("SELECT COUNT(*) FROM users") == []


def test_mixed_star_and_column_flagged_once():
    # SELECT *, id is unusual but the Star should still be flagged
    findings = check("SELECT *, id FROM users")
    assert any(f.rule_id == "select_star" for f in findings)


def test_subquery_star_flagged():
    findings = check("SELECT id FROM (SELECT * FROM users) sub")
    assert len(findings) == 1


def test_cte_star_flagged():
    findings = check("WITH cte AS (SELECT * FROM orders) SELECT id FROM cte")
    assert len(findings) == 1
