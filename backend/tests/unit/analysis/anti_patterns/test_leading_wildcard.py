import sqlglot

from app.analysis.anti_patterns.leading_wildcard import LeadingWildcardRule
from app.domain.models.analysis import Severity

rule = LeadingWildcardRule()


def check(sql: str):
    return rule.check(sqlglot.parse_one(sql))


def test_leading_wildcard_flagged():
    findings = check("SELECT * FROM users WHERE name LIKE '%john'")
    assert len(findings) == 1
    assert findings[0].severity == Severity.warning


def test_both_sides_wildcard_flagged():
    findings = check("SELECT * FROM users WHERE name LIKE '%john%'")
    assert len(findings) == 1


def test_trailing_only_is_clean():
    assert check("SELECT * FROM users WHERE name LIKE 'john%'") == []


def test_no_wildcard_is_clean():
    assert check("SELECT * FROM users WHERE name LIKE 'john'") == []


def test_ilike_leading_wildcard_flagged():
    findings = check("SELECT * FROM users WHERE name ILIKE '%john'")
    assert len(findings) == 1
    assert "ILIKE" in findings[0].title


def test_multiple_like_in_query():
    findings = check(
        "SELECT * FROM users WHERE first LIKE '%alice' OR last LIKE 'smith%'"
    )
    # Only the first LIKE has a leading wildcard
    assert len(findings) == 1


def test_dynamic_pattern_not_flagged():
    # LIKE on a non-literal (e.g. a column or parameter) — we can't inspect the value
    assert check("SELECT * FROM t WHERE name LIKE search_term") == []
