from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    critical = "critical"
    warning = "warning"
    info = "info"


class FindingCategory(StrEnum):
    performance = "performance"
    correctness = "correctness"
    security = "security"
    style = "style"


@dataclass(frozen=True)
class AnalysisFinding:
    rule_id: str
    severity: Severity
    category: FindingCategory
    title: str
    message: str
    suggestion: str | None = None
    line: int | None = None
    column: int | None = None


@dataclass
class StaticAnalysisResult:
    findings: list[AnalysisFinding] = field(default_factory=list)
    query_type: str = "UNKNOWN"
    dialect: str = ""
    table_references: list[str] = field(default_factory=list)

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.critical)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.warning)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.info)
