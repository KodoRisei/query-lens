from app.analysis.execution_plan.analyzer import ExecutionPlanAnalyzer
from app.analysis.execution_plan.rules import SeqScanRule
from tests.unit.analysis.execution_plan.fixtures import (
    HASH_JOIN_WITH_SEQ_SCAN,
    INDEX_SCAN,
    SEQ_SCAN_LARGE,
    SEQ_SCAN_SMALL,
)


def test_clean_plan_no_findings():
    analyzer = ExecutionPlanAnalyzer()
    result = analyzer.analyze(INDEX_SCAN)
    assert not result.findings
    assert result.has_analyze_data is True


def test_seq_scan_detected():
    analyzer = ExecutionPlanAnalyzer()
    result = analyzer.analyze(SEQ_SCAN_LARGE)
    rule_ids = {f.rule_id for f in result.findings}
    assert "seq_scan" in rule_ids


def test_nested_plan_all_nodes_walked():
    # HASH_JOIN_WITH_SEQ_SCAN has Seq Scan on both orders and users
    analyzer = ExecutionPlanAnalyzer()
    result = analyzer.analyze(HASH_JOIN_WITH_SEQ_SCAN)
    seq_scan_findings = [f for f in result.findings if f.rule_id == "seq_scan"]
    # Both 'orders' and 'users' are large seq scans
    tables = {f.relation_name for f in seq_scan_findings}
    assert "orders" in tables
    assert "users" in tables


def test_custom_rule_injection():
    analyzer = ExecutionPlanAnalyzer(rules=[SeqScanRule()])
    result = analyzer.analyze(SEQ_SCAN_LARGE)
    assert all(f.rule_id == "seq_scan" for f in result.findings)


def test_has_analyze_data_propagated():
    from tests.unit.analysis.execution_plan.fixtures import NO_ANALYZE
    analyzer = ExecutionPlanAnalyzer()
    result = analyzer.analyze(NO_ANALYZE)
    assert result.has_analyze_data is False


def test_execution_time_in_result():
    analyzer = ExecutionPlanAnalyzer()
    result = analyzer.analyze(SEQ_SCAN_LARGE)
    assert result.execution_time_ms == 46.1
