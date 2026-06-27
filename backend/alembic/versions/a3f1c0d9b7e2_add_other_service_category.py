"""add 'прочее' (other) service_category value

Internal quarantine bucket for auto-grown services the pipeline can't classify.
Postgres 12+ allows ADD VALUE inside a transaction (image is pg16); IF NOT EXISTS
makes it idempotent. Removing an enum value is not supported, so downgrade is a no-op.

Revision ID: a3f1c0d9b7e2
Revises: 69f88a1adbc4
Create Date: 2026-06-27 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3f1c0d9b7e2'
down_revision: Union[str, None] = '69f88a1adbc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'прочее'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value without recreating the type; left as a no-op.
    pass
