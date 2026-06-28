"""merge doctors and cabinet branches

Revision ID: 6a2bc8a626c1
Revises: a1b2c3d4e5f6, b6e3f9a1c4d2
Create Date: 2026-06-28 16:46:40.204258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a2bc8a626c1'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'b6e3f9a1c4d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
