"""add tag shortcut key

Revision ID: 0005_tag_shortcuts
Revises: 0004_antagonistic_groups
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_tag_shortcuts"
down_revision = "0004_antagonistic_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.add_column(sa.Column("shortcut_key", sa.String(length=20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.drop_column("shortcut_key")
