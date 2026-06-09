"""add antagonistic group key

Revision ID: 0004_antagonistic_groups
Revises: 0003_tag_source_and_antagonistic
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_antagonistic_groups"
down_revision = "0003_tag_source_and_antagonistic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.add_column(sa.Column("group_key", sa.String(length=100), nullable=True))
        batch_op.create_index("ix_tag_definitions_group_key", ["group_key"], unique=False)

    op.execute("UPDATE tag_definitions SET group_key = name WHERE mode = 'antagonistic' AND group_key IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.drop_index("ix_tag_definitions_group_key")
        batch_op.drop_column("group_key")
