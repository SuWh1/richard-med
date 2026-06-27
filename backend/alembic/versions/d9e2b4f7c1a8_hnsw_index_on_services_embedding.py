"""HNSW index on services.embedding for semantic nearest-neighbor

The semantic stage of the match waterfall (§9) does a cosine nearest-neighbor over
`services.embedding`. At the current catalog size a brute-force scan is fine, but the
HNSW index keeps it sub-linear as the catalog grows. Cosine opclass to match the
`cosine_distance` used by the matcher. Safe to skip: NN still works without it.

Revision ID: d9e2b4f7c1a8
Revises: b7d4e2f1a9c3
Create Date: 2026-06-27 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd9e2b4f7c1a8'
down_revision: Union[str, None] = 'b7d4e2f1a9c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_services_embedding_hnsw",
        "services",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_services_embedding_hnsw", table_name="services")
