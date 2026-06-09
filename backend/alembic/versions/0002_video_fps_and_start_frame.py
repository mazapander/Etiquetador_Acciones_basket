"""add video fps and event start frame

Revision ID: 0002_video_fps_and_start_frame
Revises: 0001_initial
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_video_fps_and_start_frame"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("fps", sa.Float(), nullable=True))
    op.add_column("tag_events", sa.Column("start_frame", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tag_events", "start_frame")
    op.drop_column("videos", "fps")
