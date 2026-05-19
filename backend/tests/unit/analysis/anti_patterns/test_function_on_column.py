import sqlglot

from app.analysis.anti_patterns.function_on_column import FunctionOnColumnRule
from app.domain.models.analysis import Severity

rule = FunctionOnColumnRule()


def check(sql: str):
    return rule.check(sqlglot.parse_one(sql))


def test_lower_on_column_flagged():
    findings = check("SELECT * FROM users WHERE LOWER(email) = 'test@example.com'")
    assert len(findings) == 1
    assert findings[0].severity == Severity.warning
    assert "LOWER" in findings[0].title


def test_upper_on_column_flagged():
    findings = check("SELECT * FROM users WHERE UPPER(status) = 'ACTIVE'")
    assert len(findings) == 1


def test_function_on_constant_not_flagged():
    # NOW() has no column argument — safe
    assert check("SELECT * FROM events WHERE created_at > NOW()") == []


def test_clean_where_not_flagged():
    assert check("SELECT * FROM users WHERE id = 42 AND status = 'active'") == []


def test_function_in_select_not_flagged():
    # LOWER in the projection list is fine — only WHERE is checked
    assert check("SELECT LOWER(name) FROM users WHERE id = 1") == []


def test_function_in_group_by_not_flagged():
    assert check("SELECT status, COUNT(*) FROM users WHERE active = true GROUP BY status") == []


def test_cast_on_column_flagged():
    findings = check("SELECT * FROM logs WHERE CAST(created_at AS DATE) = '2024-01-01'")
    assert len(findings) >= 1
    assert any("created_at" in f.title or "CAST" in f.title for f in findings)
