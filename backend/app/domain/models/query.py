from dataclasses import dataclass
from enum import StrEnum


class ReviewMode(StrEnum):
    junior = "junior"
    senior = "senior"
    performance = "performance"


@dataclass(frozen=True)
class SQLQuery:
    sql: str
    dialect: str = ""
    review_mode: ReviewMode = ReviewMode.senior
    language: str = "en"
