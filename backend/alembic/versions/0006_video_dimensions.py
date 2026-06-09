"""add video dimensions

Revision ID: 0006_video_dimensions
Revises: 0005_tag_shortcuts
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_video_dimensions"
down_revision = "0005_tag_shortcuts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("videos", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("videos", sa.Column("height", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("videos", "height")
    op.drop_column("videos", "width")
