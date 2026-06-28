"""create users table

Revision ID: e1a2b3c4d5f6
Revises: d9e2b4f7c1a8
"""

import sqlalchemy as sa
from alembic import op

revision = "e1a2b3c4d5f6"
down_revision = "d9e2b4f7c1a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
