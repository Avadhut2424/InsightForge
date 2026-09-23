"""
Switch to 384 dim

Revision ID: 14a8421883eb
Revises: c8fa643e47c6
Create Date: 2026-09-23 22:41:50.085128

DESTRUCTIVE MIGRATION: Drops all existing kb_chunks rows because 1536-dim OpenAI
embeddings are incompatible with the new 384-dim local model
(BAAI/bge-small-en-v1.5). Old vectors cannot be cast or preserved.

If run against a populated kb_chunks table, this migration fails with an explicit
error unless ALLOW_DESTRUCTIVE_MIGRATIONS=1 is set. This prevents accidental data
loss in shared environments.

Dev: set ALLOW_DESTRUCTIVE_MIGRATIONS=1 in .env before running.
"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

revision: str = '14a8421883eb'
down_revision: Union[str, Sequence[str], None] = 'c8fa643e47c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    row_count = conn.execute(sa.text("SELECT count(*) FROM kb_chunks")).scalar()

    if row_count and row_count > 0:
        allow = os.environ.get("ALLOW_DESTRUCTIVE_MIGRATIONS", "0")
        if allow != "1":
            raise RuntimeError(
                f"Refusing to run destructive migration: kb_chunks has {row_count} rows. "
                f"Set ALLOW_DESTRUCTIVE_MIGRATIONS=1 to override."
            )

    op.execute("TRUNCATE TABLE kb_chunks;")
    op.alter_column(
        "kb_chunks", "embedding",
        existing_type=pgvector.sqlalchemy.Vector(dim=1536),
        type_=pgvector.sqlalchemy.Vector(dim=384),
        existing_nullable=False,
    )


def downgrade() -> None:
    conn = op.get_bind()
    row_count = conn.execute(sa.text("SELECT count(*) FROM kb_chunks")).scalar()

    if row_count and row_count > 0:
        allow = os.environ.get("ALLOW_DESTRUCTIVE_MIGRATIONS", "0")
        if allow != "1":
            raise RuntimeError(
                f"Refusing to run destructive downgrade: kb_chunks has {row_count} rows. "
                f"Set ALLOW_DESTRUCTIVE_MIGRATIONS=1 to override."
            )

    op.execute("TRUNCATE TABLE kb_chunks;")
    op.alter_column(
        "kb_chunks", "embedding",
        existing_type=pgvector.sqlalchemy.Vector(dim=384),
        type_=pgvector.sqlalchemy.Vector(dim=1536),
        existing_nullable=False,
    )
