"""saved services become per-clinic

Revision ID: a4d8e1f6c2b9
Revises: 8c2f1a5b9d34
"""

import sqlalchemy as sa
from alembic import op

revision = "a4d8e1f6c2b9"
down_revision = "8c2f1a5b9d34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_saved_services", sa.Column("clinic_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_user_saved_services_clinic_id", "user_saved_services", ["clinic_id"]
    )
    op.create_foreign_key(
        "fk_user_saved_services_clinic_id",
        "user_saved_services",
        "clinics",
        ["clinic_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "uq_user_saved_service", "user_saved_services", type_="unique"
    )
    op.create_unique_constraint(
        "uq_user_saved_service",
        "user_saved_services",
        ["user_id", "service_id", "clinic_id", "city"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_saved_service", "user_saved_services", type_="unique")
    op.create_unique_constraint(
        "uq_user_saved_service",
        "user_saved_services",
        ["user_id", "service_id", "city"],
    )
    op.drop_constraint(
        "fk_user_saved_services_clinic_id", "user_saved_services", type_="foreignkey"
    )
    op.drop_index(
        "ix_user_saved_services_clinic_id", table_name="user_saved_services"
    )
    op.drop_column("user_saved_services", "clinic_id")
