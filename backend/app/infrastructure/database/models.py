import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class QueryReviewORM(Base):
    __tablename__ = "query_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sql: Mapped[str] = mapped_column(Text, nullable=False)
    dialect: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    review_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="senior")

    # Static analysis
    static_findings: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    static_query_type: Mapped[str | None] = mapped_column(String(20))
    static_table_refs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Execution plan (nullable — skipped if DB unreachable or DML query)
    plan_findings: Mapped[list | None] = mapped_column(JSONB)
    plan_execution_time_ms: Mapped[float | None] = mapped_column(Float)
    plan_planning_time_ms: Mapped[float | None] = mapped_column(Float)
    plan_has_analyze_data: Mapped[bool | None] = mapped_column(Boolean)

    # AI review
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_improved_query: Mapped[str | None] = mapped_column(Text)
    ai_findings: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ai_educational_note: Mapped[str | None] = mapped_column(Text)
    ai_provider: Mapped[str | None] = mapped_column(String(50))
    ai_model: Mapped[str | None] = mapped_column(String(100))
    ai_input_tokens: Mapped[int | None] = mapped_column(Integer)
    ai_output_tokens: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
