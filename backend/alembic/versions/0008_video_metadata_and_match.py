"""Persist technical and match metadata on videos.

Revision ID: 0008_video_metadata_and_match
Revises: 0007_video_idle_status
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_video_metadata_and_match"
down_revision = "0007_video_idle_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column_type in (
        ("codec_name", sa.String(100)),
        ("container_name", sa.String(100)),
        ("bit_rate", sa.BigInteger()),
        ("size_bytes", sa.BigInteger()),
        ("game_format", sa.String(30)),
        ("category", sa.String(100)),
        ("match_name", sa.String(255)),
        ("competition", sa.String(150)),
        ("home_team", sa.String(120)),
        ("away_team", sa.String(120)),
        ("match_date", sa.Date()),
    ):
        op.add_column("videos", sa.Column(name, column_type, nullable=True))
    op.add_column("videos", sa.Column("details_completed", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    for name in (
        "details_completed", "match_date", "away_team", "home_team", "competition",
        "match_name", "category", "game_format", "size_bytes", "bit_rate", "container_name", "codec_name",
    ):
        op.drop_column("videos", name)
