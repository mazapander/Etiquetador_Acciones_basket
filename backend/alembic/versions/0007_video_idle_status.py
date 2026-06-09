"""add idle video status

Revision ID: 0007_video_idle_status
Revises: 0006_video_dimensions
Create Date: 2026-06-09
"""

from alembic import op


revision = "0007_video_idle_status"
down_revision = "0006_video_dimensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'idle'")


def downgrade() -> None:
    # PostgreSQL enums do not support dropping individual values safely here.
    pass
