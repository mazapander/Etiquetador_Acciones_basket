"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("active", "completed", name="videostatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_videos_id"), "videos", ["id"], unique=False)

    op.create_table(
        "tag_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.Enum("instant", "range", name="tagmode"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_tag_definitions_id"), "tag_definitions", ["id"], unique=False)

    op.create_table(
        "tag_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("tag_definition_id", sa.Integer(), nullable=False),
        sa.Column("start_seconds", sa.Float(), nullable=False),
        sa.Column("end_seconds", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tag_definition_id"], ["tag_definitions.id"]),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tag_events_id"), "tag_events", ["id"], unique=False)
    op.create_index(op.f("ix_tag_events_tag_definition_id"), "tag_events", ["tag_definition_id"], unique=False)
    op.create_index(op.f("ix_tag_events_video_id"), "tag_events", ["video_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tag_events_video_id"), table_name="tag_events")
    op.drop_index(op.f("ix_tag_events_tag_definition_id"), table_name="tag_events")
    op.drop_index(op.f("ix_tag_events_id"), table_name="tag_events")
    op.drop_table("tag_events")
    op.drop_index(op.f("ix_tag_definitions_id"), table_name="tag_definitions")
    op.drop_table("tag_definitions")
    op.drop_index(op.f("ix_videos_id"), table_name="videos")
    op.drop_table("videos")
