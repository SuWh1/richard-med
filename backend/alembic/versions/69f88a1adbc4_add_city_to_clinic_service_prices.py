"""add city to clinic_service_prices

Revision ID: 69f88a1adbc4
Revises: c5c750828c71
Create Date: 2026-06-27 16:19:45.777924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69f88a1adbc4'
down_revision: Union[str, None] = 'c5c750828c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'clinic_service_prices', sa.Column('city', sa.String(length=64), nullable=True)
    )
    op.create_index(
        op.f('ix_clinic_service_prices_city'), 'clinic_service_prices', ['city']
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_clinic_service_prices_city'), table_name='clinic_service_prices')
    op.drop_column('clinic_service_prices', 'city')
