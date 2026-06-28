"""add cabinet tables

Revision ID: 8c2f1a5b9d34
Revises: f2b9c4e7a1d0
"""

import sqlalchemy as sa
from alembic import op

revision = "8c2f1a5b9d34"
down_revision = "f2b9c4e7a1d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_saved_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(64), nullable=False),
        sa.Column("notify_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("baseline_min_price", sa.Integer(), nullable=True),
        sa.Column("last_seen_min_price", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "service_id", "city", name="uq_user_saved_service"),
    )
    op.create_index(
        op.f("ix_user_saved_services_user_id"), "user_saved_services", ["user_id"]
    )
    op.create_index(
        op.f("ix_user_saved_services_service_id"),
        "user_saved_services",
        ["service_id"],
    )
    op.create_index(
        op.f("ix_user_saved_services_city"), "user_saved_services", ["city"]
    )

    op.create_table(
        "user_search_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("q", sa.String(512), nullable=False),
        sa.Column("city", sa.String(64), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="SET NULL"),
    )
    op.create_index(
        op.f("ix_user_search_history_user_id"), "user_search_history", ["user_id"]
    )
    op.create_index(
        op.f("ix_user_search_history_city"), "user_search_history", ["city"]
    )
    op.create_index(
        op.f("ix_user_search_history_service_id"),
        "user_search_history",
        ["service_id"],
    )
    op.create_index(
        op.f("ix_user_search_history_created_at"),
        "user_search_history",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_search_history_created_at"), table_name="user_search_history")
    op.drop_index(op.f("ix_user_search_history_service_id"), table_name="user_search_history")
    op.drop_index(op.f("ix_user_search_history_city"), table_name="user_search_history")
    op.drop_index(op.f("ix_user_search_history_user_id"), table_name="user_search_history")
    op.drop_table("user_search_history")
    op.drop_index(op.f("ix_user_saved_services_city"), table_name="user_saved_services")
    op.drop_index(op.f("ix_user_saved_services_service_id"), table_name="user_saved_services")
    op.drop_index(op.f("ix_user_saved_services_user_id"), table_name="user_saved_services")
    op.drop_table("user_saved_services")
