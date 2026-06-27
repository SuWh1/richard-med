"""make clinic_service_prices.city NOT NULL

The active-price key is (clinic, service, city). A NULL city breaks the upsert's dedup
(`city = NULL` is never true → duplicate active rows) and escapes city-scoped staling
(deactivation is per-city, so NULL rows stay active forever). Retire any legacy NULL-city
rows, then enforce NOT NULL so it can't recur.

Revision ID: b7d4e2f1a9c3
Revises: a3f1c0d9b7e2
Create Date: 2026-06-27 19:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7d4e2f1a9c3'
down_revision: Union[str, None] = 'a3f1c0d9b7e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Legacy NULL-city rows (from before the city column was populated) are stale,
    # duplicated, and stuck active — delete them rather than carry the cruft forward.
    op.execute("DELETE FROM clinic_service_prices WHERE city IS NULL")
    op.alter_column(
        "clinic_service_prices",
        "city",
        existing_type=sa.String(length=64),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "clinic_service_prices",
        "city",
        existing_type=sa.String(length=64),
        nullable=True,
    )
