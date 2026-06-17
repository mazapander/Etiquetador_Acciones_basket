"""production auth and audit

Revision ID: 0002_production_auth_audit
Revises: 0001_initial
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_production_auth_audit"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _upgrade_existing_enums() -> None:
    if not _is_postgres():
        return
    op.execute("ALTER TYPE videostatus ADD VALUE IF NOT EXISTS 'idle'")
    op.execute("ALTER TYPE tagmode ADD VALUE IF NOT EXISTS 'antagonistic'")


def upgrade() -> None:
    bind = op.get_bind()
    _upgrade_existing_enums()

    tag_source_enum = sa.Enum("human", "system", name="tagsource")
    download_status_enum = sa.Enum("pending", "downloading", "completed", "failed", name="downloadstatus")
    tag_source_enum.create(bind, checkfirst=True)
    download_status_enum.create(bind, checkfirst=True)

    op.add_column("videos", sa.Column("fps", sa.Float(), nullable=True))
    op.add_column("videos", sa.Column("width", sa.Integer(), nullable=True))
    op.add_column("videos", sa.Column("height", sa.Integer(), nullable=True))

    op.add_column("tag_definitions", sa.Column("source", tag_source_enum, nullable=False, server_default="human"))
    op.add_column("tag_definitions", sa.Column("group_key", sa.String(length=100), nullable=True))
    op.add_column("tag_definitions", sa.Column("shortcut_key", sa.String(length=20), nullable=True))
    op.create_index("ix_tag_definitions_group_key", "tag_definitions", ["group_key"], unique=False)

    op.add_column("tag_events", sa.Column("start_frame", sa.Integer(), nullable=True))
    op.add_column("tag_events", sa.Column("source", tag_source_enum, nullable=False, server_default="human"))

    op.create_table(
        "app_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supabase_user_id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="annotator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supabase_user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_app_users_id", "app_users", ["id"], unique=False)
    op.create_index("ix_app_users_supabase_user_id", "app_users", ["supabase_user_id"], unique=False)
    op.create_index("ix_app_users_email", "app_users", ["email"], unique=False)

    op.add_column("videos", sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True))
    op.create_index("ix_videos_uploaded_by_user_id", "videos", ["uploaded_by_user_id"], unique=False)
    op.create_foreign_key("fk_videos_uploaded_by_user_id_app_users", "videos", "app_users", ["uploaded_by_user_id"], ["id"])

    op.add_column("tag_events", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_tag_events_user_id", "tag_events", ["user_id"], unique=False)
    op.create_foreign_key("fk_tag_events_user_id_app_users", "tag_events", "app_users", ["user_id"], ["id"])

    op.create_table(
        "download_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("channel", sa.String(length=255), nullable=True),
        sa.Column("quality", sa.String(length=20), nullable=False),
        sa.Column("download_format", sa.String(length=20), nullable=False),
        sa.Column("output_name", sa.String(length=255), nullable=True),
        sa.Column("status", download_status_enum, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["app_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_download_history_id", "download_history", ["id"], unique=False)
    op.create_index("ix_download_history_requested_by_user_id", "download_history", ["requested_by_user_id"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("video_id", sa.Integer(), nullable=True),
        sa.Column("annotation_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["annotation_id"], ["tag_events.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"]),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_id", "audit_events", ["id"], unique=False)
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"], unique=False)
    op.create_index("ix_audit_events_video_id", "audit_events", ["video_id"], unique=False)
    op.create_index("ix_audit_events_annotation_id", "audit_events", ["annotation_id"], unique=False)
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"], unique=False)
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_annotation_id", table_name="audit_events")
    op.drop_index("ix_audit_events_video_id", table_name="audit_events")
    op.drop_index("ix_audit_events_user_id", table_name="audit_events")
    op.drop_index("ix_audit_events_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_download_history_requested_by_user_id", table_name="download_history")
    op.drop_index("ix_download_history_id", table_name="download_history")
    op.drop_table("download_history")

    op.drop_constraint("fk_tag_events_user_id_app_users", "tag_events", type_="foreignkey")
    op.drop_index("ix_tag_events_user_id", table_name="tag_events")
    op.drop_column("tag_events", "user_id")

    op.drop_constraint("fk_videos_uploaded_by_user_id_app_users", "videos", type_="foreignkey")
    op.drop_index("ix_videos_uploaded_by_user_id", table_name="videos")
    op.drop_column("videos", "uploaded_by_user_id")

    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_index("ix_app_users_supabase_user_id", table_name="app_users")
    op.drop_index("ix_app_users_id", table_name="app_users")
    op.drop_table("app_users")

    op.drop_column("tag_events", "source")
    op.drop_column("tag_events", "start_frame")

    op.drop_index("ix_tag_definitions_group_key", table_name="tag_definitions")
    op.drop_column("tag_definitions", "shortcut_key")
    op.drop_column("tag_definitions", "group_key")
    op.drop_column("tag_definitions", "source")

    op.drop_column("videos", "height")
    op.drop_column("videos", "width")
    op.drop_column("videos", "fps")
