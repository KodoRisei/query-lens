from app.analysis.execution_plan.models import ExecutionPlan, PlanNode
from app.core.exceptions import ExecutionPlanError


def parse_plan(raw: dict) -> ExecutionPlan:
    """
    Parse the top-level dict returned by EXPLAIN (FORMAT JSON).

    PostgreSQL EXPLAIN JSON shape:
    {
      "Plan": { "Node Type": "...", "Plans": [...], ... },
      "Planning Time": 1.2,
      "Execution Time": 45.6   -- only present with ANALYZE
    }
    """
    try:
        root = _parse_node(raw["Plan"])
    except (KeyError, TypeError) as exc:
        raise ExecutionPlanError(
            message=f"Unexpected EXPLAIN JSON structure: {exc}",
            details={"raw_keys": list(raw.keys()) if isinstance(raw, dict) else []},
        ) from exc

    return ExecutionPlan(
        root=root,
        planning_time_ms=float(raw.get("Planning Time", 0.0)),
        execution_time_ms=raw.get("Execution Time"),
    )


def _parse_node(raw: dict) -> PlanNode:
    children = [_parse_node(child) for child in raw.get("Plans", [])]

    return PlanNode(
        node_type=raw["Node Type"],
        total_cost=float(raw.get("Total Cost", 0.0)),
        startup_cost=float(raw.get("Startup Cost", 0.0)),
        plan_rows=int(raw.get("Plan Rows", 0)),
        plan_width=int(raw.get("Plan Width", 0)),
        actual_loops=int(raw.get("Actual Loops", 1)),
        relation_name=raw.get("Relation Name"),
        alias=raw.get("Alias"),
        actual_startup_time_ms=raw.get("Actual Startup Time"),
        actual_total_time_ms=raw.get("Actual Total Time"),
        actual_rows=raw.get("Actual Rows"),
        shared_hit_blocks=int(raw.get("Shared Hit Blocks", 0)),
        shared_read_blocks=int(raw.get("Shared Read Blocks", 0)),
        children=children,
        raw=raw,
    )
