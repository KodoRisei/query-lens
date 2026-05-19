from app.analysis.execution_plan.parser import parse_plan
from app.analysis.execution_plan.rules import (
    ExpensiveSortRule,
    NestedLoopRule,
    RowEstimationRule,
    SeqScanRule,
)
from app.domain.models.analysis import Severity
from tests.unit.analysis.execution_plan.fixtures import (
    INDEX_SCAN,
    NESTED_LOOP_LARGE,
    NO_ANALYZE,
    POOR_ROW_ESTIMATE,
    SEQ_SCAN_LARGE,
    SEQ_SCAN_SMALL,
    SORT_WITHOUT_INDEX,
)


# ── SeqScanRule ──────────────────────────────────────────────────────────────

def test_seq_scan_large_flagged():
    plan = parse_plan(SEQ_SCAN_LARGE)
    rule = SeqScanRule()
    findings = rule.check(plan.root, plan)
    assert len(findings) == 1
    assert findings[0].rule_id == "seq_scan"
    assert findings[0].severity == Severity.warning
    assert "users" in findings[0].title


def test_seq_scan_small_not_flagged():
    plan = parse_plan(SEQ_SCAN_SMALL)
    rule = SeqScanRule()
    findings = rule.check(plan.root, plan)
    assert findings == []


def test_index_scan_not_flagged():
    plan = parse_plan(INDEX_SCAN)
    rule = SeqScanRule()
    findings = rule.check(plan.root, plan)
    assert findings == []


def test_seq_scan_without_analyze_uses_plan_rows():
    # Without ANALYZE data, fall back to plan_rows for threshold check
    plan = parse_plan(NO_ANALYZE)
    rule = SeqScanRule()
    findings = rule.check(plan.root, plan)
    assert len(findings) == 1  # plan_rows=10000 > threshold


# ── RowEstimationRule ─────────────────────────────────────────────────────────

def test_poor_row_estimate_flagged():
    plan = parse_plan(POOR_ROW_ESTIMATE)
    rule = RowEstimationRule()
    findings = rule.check(plan.root, plan)
    assert len(findings) == 1
    assert findings[0].rule_id == "row_estimation_error"
    assert "500×" in findings[0].title or "under-estimated" in findings[0].title


def test_accurate_row_estimate_not_flagged():
    plan = parse_plan(SEQ_SCAN_LARGE)  # plan_rows=10000, actual_rows=9876 — close
    rule = RowEstimationRule()
    findings = rule.check(plan.root, plan)
    assert findings == []


def test_row_estimation_without_analyze_not_flagged():
    plan = parse_plan(NO_ANALYZE)
    rule = RowEstimationRule()
    findings = rule.check(plan.root, plan)
    assert findings == []  # Can't evaluate without actual data


# ── ExpensiveSortRule ─────────────────────────────────────────────────────────

def test_expensive_sort_flagged():
    plan = parse_plan(SORT_WITHOUT_INDEX)
    root = plan.root  # This IS the Sort node
    rule = ExpensiveSortRule()
    findings = rule.check(root, plan)
    assert len(findings) == 1
    assert findings[0].rule_id == "expensive_sort"


def test_non_sort_node_not_flagged():
    plan = parse_plan(SEQ_SCAN_LARGE)
    rule = ExpensiveSortRule()
    findings = rule.check(plan.root, plan)
    assert findings == []


# ── NestedLoopRule ────────────────────────────────────────────────────────────

def test_nested_loop_large_flagged():
    plan = parse_plan(NESTED_LOOP_LARGE)
    root = plan.root  # This IS the Nested Loop node
    rule = NestedLoopRule()
    findings = rule.check(root, plan)
    assert len(findings) == 1
    assert findings[0].rule_id == "nested_loop_large"
    assert "200" in findings[0].title


def test_non_nested_loop_not_flagged():
    plan = parse_plan(INDEX_SCAN)
    rule = NestedLoopRule()
    findings = rule.check(plan.root, plan)
    assert findings == []
