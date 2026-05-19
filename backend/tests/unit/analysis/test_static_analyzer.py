import pytest

from app.analysis.static_analyzer import StaticAnalyzer
from app.core.exceptions import QueryTooLongError, SQLParseError
from app.domain.models.query import SQLQuery


def test_clean_query_no_findings():
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(SQLQuery("SELECT id, name FROM users WHERE id = 1"))
    assert not result.has_findings
    assert result.query_type == "SELECT"
    assert "users" in result.table_references


def test_multiple_rules_fire_independently():
    sql = "SELECT * FROM users ORDER BY name"
    result = StaticAnalyzer().analyze(SQLQuery(sql))
    rule_ids = {f.rule_id for f in result.findings}
    assert "select_star" in rule_ids
    assert "order_without_limit" in rule_ids


def test_invalid_sql_raises_parse_error():
    with pytest.raises(SQLParseError):
        StaticAnalyzer().analyze(SQLQuery("SELECT FROM WHERE"))


def test_query_too_long_raises_error(monkeypatch):
    from app.core import config as cfg
    settings = cfg.get_settings()
    original = settings.max_query_length

    monkeypatch.setattr(settings, "max_query_length", 10)
    with pytest.raises(QueryTooLongError) as exc_info:
        StaticAnalyzer().analyze(SQLQuery("SELECT id FROM users WHERE id = 1"))
    assert exc_info.value.max_length == 10


def test_critical_count_property():
    result = StaticAnalyzer().analyze(SQLQuery("DELETE FROM users"))
    assert result.critical_count == 1
    assert result.warning_count == 0


def test_table_references_extracted():
    sql = "SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id"
    result = StaticAnalyzer().analyze(SQLQuery(sql))
    assert "users" in result.table_references
    assert "orders" in result.table_references


def test_custom_rule_injection():
    from app.analysis.anti_patterns.select_star import SelectStarRule

    analyzer = StaticAnalyzer(rules=[SelectStarRule()])
    result = analyzer.analyze(SQLQuery("SELECT * FROM users ORDER BY name"))
    rule_ids = {f.rule_id for f in result.findings}
    # Only the injected rule should fire
    assert rule_ids == {"select_star"}
