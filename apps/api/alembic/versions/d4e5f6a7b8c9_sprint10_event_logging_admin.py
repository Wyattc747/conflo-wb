"""sprint10_event_logging_admin_benchmarks

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── EventLog: add new columns for structured event data ──
    op.add_column("event_logs", sa.Column("action", sa.String(50), nullable=True))
    op.add_column("event_logs", sa.Column("entity_type", sa.String(50), nullable=True))
    op.add_column("event_logs", sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("event_logs", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("event_logs", sa.Column("user_agent", sa.String(500), nullable=True))

    op.create_index("idx_event_logs_org_type", "event_logs", ["organization_id", "event_type", "created_at"])
    op.create_index("idx_event_logs_entity", "event_logs", ["entity_type", "entity_id"])
    op.create_index("idx_event_logs_user", "event_logs", ["user_type", "user_id", "created_at"])

    # ── Admin Users table ──
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default=sa.text("'admin'"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    # ── AuditLog: add actor_type for admin impersonation tracking ──
    op.add_column("audit_logs", sa.Column("actor_type", sa.String(20), nullable=True))
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])


def downgrade() -> None:
    # AuditLog
    op.drop_index("idx_audit_logs_resource")
    op.drop_column("audit_logs", "actor_type")

    # Admin Users
    op.drop_table("admin_users")

    # EventLog
    op.drop_index("idx_event_logs_user")
    op.drop_index("idx_event_logs_entity")
    op.drop_index("idx_event_logs_org_type")
    op.drop_column("event_logs", "user_agent")
    op.drop_column("event_logs", "ip_address")
    op.drop_column("event_logs", "entity_id")
    op.drop_column("event_logs", "entity_type")
    op.drop_column("event_logs", "action")
