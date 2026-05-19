import pytest

from app.analysis.execution_plan.parser import parse_plan
from app.core.exceptions import ExecutionPlanError
from tests.unit.analysis.execution_plan.fixtures import (
    HASH_JOIN_WITH_SEQ_SCAN,
    INDEX_SCAN,
    NO_ANALYZE,
    SEQ_SCAN_LARGE,
)


def test_parses_root_node():
    plan = parse_plan(SEQ_SCAN_LARGE)
    assert plan.root.node_type == "Seq Scan"
    assert plan.root.relation_name == "users"
    assert plan.root.total_cost == 1540.00


def test_parses_timing():
    plan = parse_plan(SEQ_SCAN_LARGE)
    assert plan.planning_time_ms == 0.5
    assert plan.execution_time_ms == 46.1


def test_parses_actual_rows():
    plan = parse_plan(SEQ_SCAN_LARGE)
    assert plan.root.actual_rows == 9876
    assert plan.root.actual_loops == 1


def test_no_analyze_missing_actual_data():
    plan = parse_plan(NO_ANALYZE)
    assert plan.root.actual_rows is None
    assert plan.root.actual_total_time_ms is None
    assert plan.execution_time_ms is None


def test_parses_nested_plan():
    plan = parse_plan(HASH_JOIN_WITH_SEQ_SCAN)
    root = plan.root
    assert root.node_type == "Hash Join"
    assert len(root.children) == 2
    assert root.children[0].node_type == "Seq Scan"
    assert root.children[1].node_type == "Hash"
    # The Hash node has a child Seq Scan
    assert root.children[1].children[0].node_type == "Seq Scan"


def test_parses_index_scan():
    plan = parse_plan(INDEX_SCAN)
    assert plan.root.node_type == "Index Scan"
    assert plan.root.actual_rows == 1


def test_invalid_plan_raises_error():
    with pytest.raises(ExecutionPlanError):
        parse_plan({"not": "a plan"})


def test_has_analyze_data_property():
    plan = parse_plan(SEQ_SCAN_LARGE)
    assert plan.root.has_analyze_data is True

    plan_no_analyze = parse_plan(NO_ANALYZE)
    assert plan_no_analyze.root.has_analyze_data is False
