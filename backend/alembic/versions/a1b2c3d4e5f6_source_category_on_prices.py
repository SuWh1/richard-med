"""source-native category on clinic_service_prices

Revision ID: a1b2c3d4e5f6
Revises: f3a9c1e88b22
Create Date: 2026-06-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a9c1e88b22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clinic_service_prices",
        sa.Column("source_category", sa.String(length=128), nullable=True),
    )
    op.create_index(
        op.f("ix_clinic_service_prices_source_category"),
        "clinic_service_prices",
        ["source_category"],
    )
    # Backfill from the raw evidence already on disk so seeded rows show their section
    # without a full re-parse.
    op.execute(
        """
        UPDATE clinic_service_prices AS p
        SET source_category = r.metadata_json ->> 'category'
        FROM raw_price_items AS r
        WHERE p.raw_price_item_id = r.id
          AND p.source_category IS NULL
          AND r.metadata_json ->> 'category' IS NOT NULL
          AND r.metadata_json ->> 'category' NOT IN (
              'лаборатория', 'приём врача', 'диагностика', 'процедура', 'прочее'
          )
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clinic_service_prices_source_category"),
        table_name="clinic_service_prices",
    )
    op.drop_column("clinic_service_prices", "source_category")
