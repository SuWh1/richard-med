"""doctors enrichment: doctors, doctor_details, doctor_reviews + price.doctor_id

Revision ID: f3a9c1e88b22
Revises: e1a2b3c4d5f6
"""

import sqlalchemy as sa
from alembic import op

revision = "f3a9c1e88b22"
down_revision = "e1a2b3c4d5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doq_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(256), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(32), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_doctors_doq_id", "doctors", ["doq_id"], unique=True)
    op.create_index("ix_doctors_name", "doctors", ["name"])

    op.create_table(
        "doctor_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("detail_type", sa.String(64), nullable=False),
        sa.Column("detail_type_id", sa.Integer(), nullable=True),
        sa.Column("info", sa.Text(), nullable=False),
        sa.Column("year", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_doctor_details_doctor_id", "doctor_details", ["doctor_id"]
    )

    op.create_table(
        "doctor_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("doq_feedback_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("text_ru", sa.Text(), nullable=True),
        sa.Column("service_name", sa.String(256), nullable=True),
        sa.Column("client_name", sa.String(256), nullable=True),
        sa.Column("waiting_time", sa.Integer(), nullable=True),
        sa.Column("clinic_reply", sa.Text(), nullable=True),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_doctor_reviews_doctor_id", "doctor_reviews", ["doctor_id"]
    )
    op.create_index(
        "ix_doctor_reviews_doq_feedback_id",
        "doctor_reviews",
        ["doq_feedback_id"],
        unique=True,
    )

    op.add_column(
        "clinic_service_prices",
        sa.Column("doctor_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_clinic_service_prices_doctor_id",
        "clinic_service_prices",
        ["doctor_id"],
    )
    op.create_foreign_key(
        "fk_clinic_service_prices_doctor_id",
        "clinic_service_prices",
        "doctors",
        ["doctor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_clinic_service_prices_doctor_id",
        "clinic_service_prices",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_clinic_service_prices_doctor_id", table_name="clinic_service_prices"
    )
    op.drop_column("clinic_service_prices", "doctor_id")

    op.drop_index("ix_doctor_reviews_doq_feedback_id", table_name="doctor_reviews")
    op.drop_index("ix_doctor_reviews_doctor_id", table_name="doctor_reviews")
    op.drop_table("doctor_reviews")
    op.drop_index("ix_doctor_details_doctor_id", table_name="doctor_details")
    op.drop_table("doctor_details")
    op.drop_index("ix_doctors_name", table_name="doctors")
    op.drop_index("ix_doctors_doq_id", table_name="doctors")
    op.drop_table("doctors")
