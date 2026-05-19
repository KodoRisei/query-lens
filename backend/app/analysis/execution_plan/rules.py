from abc import ABC, abstractmethod

from app.analysis.execution_plan.models import ExecutionPlan, PlanFinding, PlanNode
from app.domain.models.analysis import FindingCategory, Severity


class PlanRule(ABC):
    rule_id: str

    @abstractmethod
    def check(self, node: PlanNode, plan: ExecutionPlan) -> list[PlanFinding]:
        """Inspect a single plan node and return findings. Return [] if clean."""
        ...


class SeqScanRule(PlanRule):
    """
    Flags sequential scans on non-trivial row counts.

    A seq scan on a 5-row lookup table is fine. A seq scan on 50k rows
    with a WHERE clause almost certainly has a missing index.
    """

    rule_id = "seq_scan"
    THRESHOLD_ROWS = 500

    def check(self, node: PlanNode, plan: ExecutionPlan) -> list[PlanFinding]:
        if node.node_type != "Seq Scan":
            return []

        rows = node.total_actual_rows or node.plan_rows
        if rows <= self.THRESHOLD_ROWS:
            return []

        table = node.relation_name or "unknown"
        return [PlanFinding(
            rule_id=self.rule_id,
            node_type=node.node_type,
            severity=Severity.warning,
            category=FindingCategory.performance,
            title=f"Sequential scan on '{table}' ({rows:,} rows)",
            message=(
                f"PostgreSQL is reading every row in '{table}' ({rows:,} rows). "
                "Sequential scans are appropriate for small tables or when fetching most rows, "
                "but on large tables with selective WHERE conditions they indicate a missing index."
            ),
            suggestion=(
                f"Identify the columns used in WHERE / JOIN conditions on '{table}' "
                f"and add an index: CREATE INDEX ON {table} (column_name). "
                "Check pg_stat_user_indexes after to confirm the new index is used."
            ),
            relation_name=table,
        )]


class RowEstimationRule(PlanRule):
    """
    Flags large discrepancies between PostgreSQL's row estimate and actual row count.

    PostgreSQL's query planner makes join and sort strategy decisions based on its
    row estimates. A 10x+ error means the planner may have chosen the wrong strategy,
    typically because statistics are stale.
    """

    rule_id = "row_estimation_error"
    MIN_ROWS = 10
    MAX_RATIO = 10.0

    def check(self, node: PlanNode, plan: ExecutionPlan) -> list[PlanFinding]:
        ratio = node.row_estimation_ratio
        if ratio is None:
            return []

        total_actual = node.total_actual_rows or 0
        if total_actual < self.MIN_ROWS and node.plan_rows < self.MIN_ROWS:
            return []

        if ratio < self.MAX_RATIO:
            return []

        total = node.total_actual_rows or 0
        estimated = node.plan_rows
        direction = "under-estimated" if total > estimated else "over-estimated"
        label = node.relation_name or node.node_type

        return [PlanFinding(
            rule_id=self.rule_id,
            node_type=node.node_type,
            severity=Severity.warning,
            category=FindingCategory.performance,
            title=f"Row estimate {direction} for '{label}' ({ratio:.0f}×)",
            message=(
                f"PostgreSQL estimated {estimated:,} rows but got {total:,} — "
                f"a {ratio:.0f}× error. Poor estimates cause the planner to choose "
                "suboptimal join types (e.g. Nested Loop when Hash Join would be faster)."
            ),
            suggestion=(
                "Run ANALYZE on the relevant tables to refresh statistics. "
                "For heavily skewed columns, increase statistics target: "
                "ALTER TABLE t ALTER COLUMN c SET STATISTICS 500."
            ),
            relation_name=node.relation_name,
        )]


class ExpensiveSortRule(PlanRule):
    """
    Flags Sort nodes that contribute a meaningful fraction of total plan cost.

    A Sort node means PostgreSQL cannot satisfy ORDER BY via an index scan
    and must materialise and sort the rows in memory (or spill to disk).
    """

    rule_id = "expensive_sort"
    COST_FRACTION_THRESHOLD = 0.10

    def check(self, node: PlanNode, plan: ExecutionPlan) -> list[PlanFinding]:
        if node.node_type != "Sort":
            return []

        total_cost = plan.root.total_cost
        if total_cost > 0 and node.total_cost / total_cost < self.COST_FRACTION_THRESHOLD:
            return []

        return [PlanFinding(
            rule_id=self.rule_id,
            node_type=node.node_type,
            severity=Severity.warning,
            category=FindingCategory.performance,
            title=f"Expensive sort (cost {node.total_cost:.0f})",
            message=(
                f"A Sort node contributes {node.total_cost / max(total_cost, 1) * 100:.0f}% "
                "of total plan cost. PostgreSQL cannot use an index to satisfy the ORDER BY. "
                "For large result sets this may spill to disk."
            ),
            suggestion=(
                "Add an index on the ORDER BY column(s) to allow an Index Scan. "
                "For paginated queries, prefer keyset (cursor) pagination to avoid sorting "
                "the full result set on every page."
            ),
        )]


class NestedLoopRule(PlanRule):
    """
    Flags Nested Loop joins where the inner side executes many times.

    Nested Loop is O(outer_rows × inner_rows). When the outer side is large
    and the inner side lacks an index, it degrades to O(n²).
    """

    rule_id = "nested_loop_large"
    LOOP_THRESHOLD = 100

    def check(self, node: PlanNode, plan: ExecutionPlan) -> list[PlanFinding]:
        if node.node_type != "Nested Loop":
            return []

        loops = node.actual_loops
        if loops < self.LOOP_THRESHOLD:
            return []

        return [PlanFinding(
            rule_id=self.rule_id,
            node_type=node.node_type,
            severity=Severity.warning,
            category=FindingCategory.performance,
            title=f"Nested loop with {loops:,} iterations",
            message=(
                f"The Nested Loop join executed its inner side {loops:,} times. "
                "For large outer relations this is O(n×m) and will be dramatically "
                "slower than a Hash Join or Merge Join."
            ),
            suggestion=(
                "Ensure the inner side of the join has an index on the join key. "
                "You can force PostgreSQL to try alternatives with "
                "SET enable_nestloop = off in your session for benchmarking."
            ),
        )]


PLAN_RULE_REGISTRY: list[PlanRule] = [
    SeqScanRule(),
    RowEstimationRule(),
    ExpensiveSortRule(),
    NestedLoopRule(),
]
