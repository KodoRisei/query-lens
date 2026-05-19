from dataclasses import dataclass, field

from app.domain.models.analysis import FindingCategory, Severity


@dataclass
class PlanNode:
    node_type: str
    total_cost: float
    startup_cost: float
    plan_rows: int
    plan_width: int
    actual_loops: int = 1
    relation_name: str | None = None
    alias: str | None = None
    actual_startup_time_ms: float | None = None
    actual_total_time_ms: float | None = None
    actual_rows: int | None = None
    shared_hit_blocks: int = 0
    shared_read_blocks: int = 0
    children: list["PlanNode"] = field(default_factory=list)
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def has_analyze_data(self) -> bool:
        return self.actual_rows is not None

    @property
    def total_actual_rows(self) -> int | None:
        if self.actual_rows is None:
            return None
        return self.actual_rows * self.actual_loops

    @property
    def row_estimation_ratio(self) -> float | None:
        if self.actual_rows is None or self.plan_rows == 0:
            return None
        actual = max(self.total_actual_rows or 1, 1)
        estimated = max(self.plan_rows, 1)
        return max(actual, estimated) / min(actual, estimated)


@dataclass
class ExecutionPlan:
    root: PlanNode
    planning_time_ms: float = 0.0
    execution_time_ms: float | None = None


@dataclass(frozen=True)
class PlanFinding:
    rule_id: str
    node_type: str
    severity: Severity
    category: FindingCategory
    title: str
    message: str
    suggestion: str | None = None
    relation_name: str | None = None


@dataclass
class ExecutionPlanResult:
    plan: ExecutionPlan
    findings: list[PlanFinding] = field(default_factory=list)
    has_analyze_data: bool = False

    @property
    def execution_time_ms(self) -> float | None:
        return self.plan.execution_time_ms
