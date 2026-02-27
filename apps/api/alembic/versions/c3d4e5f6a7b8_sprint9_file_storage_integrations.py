"""sprint9_file_storage_integrations_notifications

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Files table: add new columns ──
    op.add_column("files", sa.Column("category", sa.String(50), server_default=sa.text("'other'"), nullable=False))
    op.add_column("files", sa.Column("status", sa.String(20), server_default=sa.text("'PENDING'"), nullable=False))
    op.add_column("files", sa.Column("thumbnail_key", sa.String, nullable=True))
    op.add_column("files", sa.Column("exif_data", postgresql.JSONB, nullable=True))
    op.add_column("files", sa.Column("confirmed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("files", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))

    # Back-fill existing files as CONFIRMED
    op.execute("UPDATE files SET status = 'CONFIRMED', confirmed_at = created_at WHERE status = 'PENDING'")

    op.create_index("idx_files_project_category", "files", ["project_id", "category"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # ── Integration connections: add new columns ──
    op.add_column("integration_connections", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("integration_connections", sa.Column("token_expiry", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("integration_connections", sa.Column("scopes", postgresql.JSONB, nullable=True))
    op.add_column("integration_connections", sa.Column("provider_metadata", postgresql.JSONB,
                   server_default=sa.text("'{}'::jsonb"), nullable=False))

    op.create_index("idx_integrations_user_provider", "integration_connections",
                     ["user_id", "provider"])

    # ── Notifications: add new columns ──
    op.add_column("notifications", sa.Column("project_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("projects.id"), nullable=True))
    op.add_column("notifications", sa.Column("metadata", postgresql.JSONB,
                   server_default=sa.text("'{}'::jsonb"), nullable=False))

    op.create_index("idx_notifications_user", "notifications", ["user_type", "user_id", "created_at"])
    op.create_index("idx_notifications_unread", "notifications", ["user_type", "user_id"],
                     postgresql_where=sa.text("read_at IS NULL"))


def downgrade() -> None:
    # Notifications
    op.drop_index("idx_notifications_unread")
    op.drop_index("idx_notifications_user")
    op.drop_column("notifications", "metadata")
    op.drop_column("notifications", "project_id")

    # Integration connections
    op.drop_index("idx_integrations_user_provider")
    op.drop_column("integration_connections", "provider_metadata")
    op.drop_column("integration_connections", "scopes")
    op.drop_column("integration_connections", "token_expiry")
    op.drop_column("integration_connections", "user_id")

    # Files
    op.drop_index("idx_files_project_category")
    op.drop_column("files", "deleted_at")
    op.drop_column("files", "confirmed_at")
    op.drop_column("files", "exif_data")
    op.drop_column("files", "thumbnail_key")
    op.drop_column("files", "status")
    op.drop_column("files", "category")
