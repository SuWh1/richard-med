"""add branch ratings + clinic_reviews

Revision ID: f2b9c4e7a1d0
Revises: e1a2b3c4d5f6
"""

import sqlalchemy as sa
from alembic import op

revision = "f2b9c4e7a1d0"
down_revision = "e1a2b3c4d5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clinic_branches", sa.Column("twogis_firm_id", sa.String(32), nullable=True)
    )
    op.add_column("clinic_branches", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column(
        "clinic_branches", sa.Column("reviews_count", sa.Integer(), nullable=True)
    )
    op.add_column(
        "clinic_branches",
        sa.Column("rating_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_clinic_branches_twogis_firm_id",
        "clinic_branches",
        ["twogis_firm_id"],
    )

    op.create_table(
        "clinic_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("author", sa.String(256), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("official_answer", sa.Text(), nullable=True),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="2gis"),
        sa.Column("external_id", sa.String(64), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["branch_id"], ["clinic_branches.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_clinic_reviews_branch_id", "clinic_reviews", ["branch_id"]
    )
    op.create_index(
        "ix_clinic_reviews_external_id", "clinic_reviews", ["external_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_clinic_reviews_external_id", table_name="clinic_reviews")
    op.drop_index("ix_clinic_reviews_branch_id", table_name="clinic_reviews")
    op.drop_table("clinic_reviews")
    op.drop_index(
        "ix_clinic_branches_twogis_firm_id", table_name="clinic_branches"
    )
    op.drop_column("clinic_branches", "rating_synced_at")
    op.drop_column("clinic_branches", "reviews_count")
    op.drop_column("clinic_branches", "rating")
    op.drop_column("clinic_branches", "twogis_firm_id")
