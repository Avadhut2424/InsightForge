"""switch embedding index to hnsw cosine

Revision ID: 1d301862bd73
Revises: 14a8421883eb
Create Date: 2026-09-23 18:12:25.016591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '1d301862bd73'
down_revision: Union[str, Sequence[str], None] = '14a8421883eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding;")
    op.execute("CREATE INDEX ix_kb_chunks_embedding ON kb_chunks USING hnsw (embedding vector_cosine_ops);")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_kb_chunks_embedding;")
    op.execute("CREATE INDEX ix_kb_chunks_embedding ON kb_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists='100');")
