from abc import ABC, abstractmethod

import sqlglot.expressions as exp

from app.domain.models.analysis import AnalysisFinding


class AntiPatternRule(ABC):
    """
    Base class for all anti-pattern detection rules.

    Each rule is stateless and operates on a single sqlglot AST.
    Rules must declare a stable `rule_id` used in API responses and logs.
    """

    rule_id: str

    @abstractmethod
    def check(self, ast: exp.Expression) -> list[AnalysisFinding]:
        """Inspect the AST and return any findings. Return [] if clean."""
        ...
