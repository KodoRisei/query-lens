from app.analysis.anti_patterns.base import AntiPatternRule
from app.analysis.anti_patterns.function_on_column import FunctionOnColumnRule
from app.analysis.anti_patterns.implicit_cross_join import ImplicitCrossJoinRule
from app.analysis.anti_patterns.leading_wildcard import LeadingWildcardRule
from app.analysis.anti_patterns.missing_where import MissingWhereRule
from app.analysis.anti_patterns.order_without_limit import OrderWithoutLimitRule
from app.analysis.anti_patterns.select_star import SelectStarRule

RULE_REGISTRY: list[AntiPatternRule] = [
    SelectStarRule(),
    MissingWhereRule(),
    ImplicitCrossJoinRule(),
    LeadingWildcardRule(),
    FunctionOnColumnRule(),
    OrderWithoutLimitRule(),
]

__all__ = [
    "AntiPatternRule",
    "RULE_REGISTRY",
    "SelectStarRule",
    "MissingWhereRule",
    "ImplicitCrossJoinRule",
    "LeadingWildcardRule",
    "FunctionOnColumnRule",
    "OrderWithoutLimitRule",
]
