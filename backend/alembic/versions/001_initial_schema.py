"""Initial schema — query_reviews table

Revision ID: 001
Revises:
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "query_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("sql", sa.Text, nullable=False),
        sa.Column("dialect", sa.String(50), nullable=False, server_default=""),
        sa.Column("review_mode", sa.String(20), nullable=False, server_default="senior"),
        # Static analysis
        sa.Column("static_findings", JSONB, nullable=False, server_default="[]"),
        sa.Column("static_query_type", sa.String(20)),
        sa.Column("static_table_refs", JSONB, nullable=False, server_default="[]"),
        # Execution plan (nullable)
        sa.Column("plan_findings", JSONB),
        sa.Column("plan_execution_time_ms", sa.Float),
        sa.Column("plan_planning_time_ms", sa.Float),
        sa.Column("plan_has_analyze_data", sa.Boolean),
        # AI review
        sa.Column("ai_summary", sa.Text),
        sa.Column("ai_improved_query", sa.Text),
        sa.Column("ai_findings", JSONB, nullable=False, server_default="[]"),
        sa.Column("ai_educational_note", sa.Text),
        sa.Column("ai_provider", sa.String(50)),
        sa.Column("ai_model", sa.String(100)),
        sa.Column("ai_input_tokens", sa.Integer),
        sa.Column("ai_output_tokens", sa.Integer),
        # Meta
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_query_reviews_created_at", "query_reviews", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_query_reviews_created_at", table_name="query_reviews")
    op.drop_table("query_reviews")
