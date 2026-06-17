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


def upgrade() -> None:
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
