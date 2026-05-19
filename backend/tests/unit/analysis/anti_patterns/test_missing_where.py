import sqlglot

from app.analysis.anti_patterns.missing_where import MissingWhereRule
from app.domain.models.analysis import Severity

rule = MissingWhereRule()


def check(sql: str):
    return rule.check(sqlglot.parse_one(sql))


def test_delete_without_where_is_critical():
    findings = check("DELETE FROM users")
    assert len(findings) == 1
    assert findings[0].severity == Severity.critical
    assert "DELETE" in findings[0].title


def test_update_without_where_is_critical():
    findings = check("UPDATE users SET status = 'inactive'")
    assert len(findings) == 1
    assert findings[0].severity == Severity.critical
    assert "UPDATE" in findings[0].title


def test_delete_with_where_clean():
    assert check("DELETE FROM users WHERE id = 42") == []


def test_update_with_where_clean():
    assert check("UPDATE users SET status = 'inactive' WHERE last_login < '2020-01-01'") == []


def test_select_not_affected():
    assert check("SELECT * FROM users") == []


def test_insert_not_affected():
    assert check("INSERT INTO users (name) VALUES ('Alice')") == []


def test_table_name_in_message():
    findings = check("DELETE FROM orders")
    assert "orders" in findings[0].message
