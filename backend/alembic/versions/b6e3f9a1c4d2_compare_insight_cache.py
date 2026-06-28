"""compare insight cache

Revision ID: b6e3f9a1c4d2
Revises: a4d8e1f6c2b9
"""

import sqlalchemy as sa
from alembic import op

revision = "b6e3f9a1c4d2"
down_revision = "a4d8e1f6c2b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compare_insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cache_key", sa.String(128), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_compare_insights_cache_key", "compare_insights", ["cache_key"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_compare_insights_cache_key", table_name="compare_insights")
    op.drop_table("compare_insights")
