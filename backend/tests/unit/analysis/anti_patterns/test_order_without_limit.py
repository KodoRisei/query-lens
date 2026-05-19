import sqlglot

from app.analysis.anti_patterns.order_without_limit import OrderWithoutLimitRule
from app.domain.models.analysis import Severity

rule = OrderWithoutLimitRule()


def check(sql: str):
    return rule.check(sqlglot.parse_one(sql))


def test_order_without_limit_flagged():
    findings = check("SELECT id, name FROM users ORDER BY name")
    assert len(findings) == 1
    assert findings[0].severity == Severity.warning


def test_order_with_limit_clean():
    assert check("SELECT id, name FROM users ORDER BY name LIMIT 50") == []


def test_no_order_by_clean():
    assert check("SELECT id, name FROM users WHERE active = true") == []


def test_group_by_with_order_not_flagged():
    # Aggregate queries routinely ORDER BY a computed column — not the same pattern
    sql = "SELECT status, COUNT(*) AS cnt FROM users GROUP BY status ORDER BY cnt DESC"
    assert check(sql) == []


def test_subquery_order_without_limit_flagged():
    # Inner subquery has ORDER BY without LIMIT — still worth flagging
    sql = "SELECT * FROM (SELECT id FROM users ORDER BY id) sub"
    findings = check(sql)
    assert len(findings) == 1


def test_order_with_offset_only_flagged():
    # OFFSET without LIMIT is almost certainly a mistake
    findings = check("SELECT * FROM users ORDER BY id OFFSET 100")
    assert len(findings) == 1
