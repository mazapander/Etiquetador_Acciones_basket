"""add tag source and antagonistic mode

Revision ID: 0003_tag_source_and_antagonistic
Revises: 0002_video_fps_and_start_frame
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_tag_source_and_antagonistic"
down_revision = "0002_video_fps_and_start_frame"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.add_column(sa.Column("source", sa.Enum("human", "system", name="tagsource"), nullable=True))
    with op.batch_alter_table("tag_events") as batch_op:
        batch_op.add_column(sa.Column("source", sa.Enum("human", "system", name="tagsource"), nullable=True))

    op.execute("UPDATE tag_definitions SET source = 'human' WHERE source IS NULL")
    op.execute("UPDATE tag_events SET source = 'human' WHERE source IS NULL")

    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.alter_column("source", nullable=False)
    with op.batch_alter_table("tag_events") as batch_op:
        batch_op.alter_column("source", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("tag_events") as batch_op:
        batch_op.drop_column("source")
    with op.batch_alter_table("tag_definitions") as batch_op:
        batch_op.drop_column("source")
