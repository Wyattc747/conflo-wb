"""sprint8_remaining_tools

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. CREATE document_folders table (before documents FK)
    op.create_table(
        "document_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("parent_folder_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_folders.id"), nullable=True),
        sa.Column("is_system", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_doc_folders_project", "document_folders", ["project_id"])

    # 2. ADD COLUMNS to meetings
    op.add_column("meetings", sa.Column("meeting_type", sa.String(20), server_default=sa.text("'PROGRESS'"), nullable=False))
    op.add_column("meetings", sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("meetings", sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("meetings", sa.Column("virtual_provider", sa.String(50), nullable=True))
    op.add_column("meetings", sa.Column("virtual_link", sa.String, nullable=True))
    op.add_column("meetings", sa.Column("recurring", sa.Boolean, server_default=sa.text("false"), nullable=False))
    op.add_column("meetings", sa.Column("recurrence_rule", sa.String, nullable=True))
    op.add_column("meetings", sa.Column("recurrence_end_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("meetings", sa.Column("parent_meeting_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meetings.id"), nullable=True))
    op.add_column("meetings", sa.Column("minutes_published", sa.Boolean, server_default=sa.text("false"), nullable=False))
    op.add_column("meetings", sa.Column("minutes_published_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("meetings", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_meetings_project_date", "meetings", ["project_id", "scheduled_date"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 3. ADD COLUMNS to todos
    op.alter_column("todos", "status", server_default=sa.text("'OPEN'"))
    op.execute("UPDATE todos SET status = 'OPEN' WHERE status = 'TODO'")
    op.add_column("todos", sa.Column("category", sa.String(50), nullable=True))
    op.add_column("todos", sa.Column("cost_code_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("todos", sa.Column("source_type", sa.String(50), nullable=True))
    op.add_column("todos", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("todos", sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("todos", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_todos_project_status", "todos", ["project_id", "status"],
                     postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_todos_assigned", "todos", ["assigned_to"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 4. ADD COLUMNS to procurement_items
    op.add_column("procurement_items", sa.Column("category", sa.String(50), nullable=True))
    op.add_column("procurement_items", sa.Column("spec_section", sa.String, nullable=True))
    op.add_column("procurement_items", sa.Column("quantity", sa.Integer, nullable=True))
    op.add_column("procurement_items", sa.Column("unit", sa.String(20), nullable=True))
    op.add_column("procurement_items", sa.Column("vendor_contact", sa.String, nullable=True))
    op.add_column("procurement_items", sa.Column("vendor_phone", sa.String, nullable=True))
    op.add_column("procurement_items", sa.Column("vendor_email", sa.String, nullable=True))
    op.add_column("procurement_items", sa.Column("lead_time_days", sa.Integer, nullable=True))
    op.add_column("procurement_items", sa.Column("required_on_site_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("procurement_items", sa.Column("order_by_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("procurement_items", sa.Column("expected_delivery_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("procurement_items", sa.Column("actual_delivery_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("procurement_items", sa.Column("tracking_number", sa.String, nullable=True))
    op.add_column("procurement_items", sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("procurement_items", sa.Column("sub_company_id", postgresql.UUID(as_uuid=True),
                                                  sa.ForeignKey("sub_companies.id"), nullable=True))
    op.add_column("procurement_items", sa.Column("linked_schedule_task_id", postgresql.UUID(as_uuid=True),
                                                  sa.ForeignKey("schedule_tasks.id"), nullable=True))
    op.add_column("procurement_items", sa.Column("notes", sa.Text, nullable=True))
    op.add_column("procurement_items", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_procurement_project_status", "procurement_items", ["project_id", "status"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 5. ADD COLUMNS to drawings
    op.add_column("drawings", sa.Column("description", sa.Text, nullable=True))
    op.add_column("drawings", sa.Column("received_from", sa.String, nullable=True))
    op.add_column("drawings", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_drawings_project", "drawings", ["project_id"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 6. ADD COLUMNS to drawing_sheets
    op.add_column("drawing_sheets", sa.Column("revision_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("drawing_sheets", sa.Column("description", sa.Text, nullable=True))
    op.add_column("drawing_sheets", sa.Column("is_current", sa.Boolean, server_default=sa.text("true"), nullable=False))
    op.add_column("drawing_sheets", sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True))

    # 7. ADD COLUMNS to documents
    op.add_column("documents", sa.Column("description", sa.Text, nullable=True))
    op.add_column("documents", sa.Column("folder_id", postgresql.UUID(as_uuid=True),
                                          sa.ForeignKey("document_folders.id"), nullable=True))
    op.add_column("documents", sa.Column("tags", postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column("documents", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_documents_project_folder", "documents", ["project_id", "folder_id"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 8. ADD COLUMNS to photos
    op.add_column("photos", sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey("organizations.id"), nullable=True))
    op.add_column("photos", sa.Column("project_id", postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey("projects.id"), nullable=True))
    op.add_column("photos", sa.Column("caption", sa.String, nullable=True))
    op.add_column("photos", sa.Column("tags", postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column("photos", sa.Column("location", sa.String, nullable=True))
    op.add_column("photos", sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("photos", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_photos_project", "photos", ["project_id"],
                     postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_photos_linked", "photos", ["linked_type", "linked_id"])

    # 9. ADD COLUMNS to bid_packages
    op.add_column("bid_packages", sa.Column("trade", sa.String, nullable=True))
    op.add_column("bid_packages", sa.Column("pre_bid_meeting_date", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("bid_packages", sa.Column("estimated_value", sa.Numeric(15, 2), nullable=True))
    op.add_column("bid_packages", sa.Column("requirements", sa.Text, nullable=True))
    op.add_column("bid_packages", sa.Column("scope_documents", postgresql.JSONB,
                                             server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column("bid_packages", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("idx_bid_packages_project", "bid_packages", ["project_id", "status"],
                     postgresql_where=sa.text("deleted_at IS NULL"))

    # 10. ADD COLUMNS to bid_submissions
    op.add_column("bid_submissions", sa.Column("schedule_duration_days", sa.Integer, nullable=True))
    op.add_column("bid_submissions", sa.Column("exclusions", sa.Text, nullable=True))
    op.add_column("bid_submissions", sa.Column("inclusions", sa.Text, nullable=True))
    op.add_column("bid_submissions", sa.Column("notes", sa.Text, nullable=True))
    op.add_column("bid_submissions", sa.Column("status", sa.String(20), server_default=sa.text("'DRAFT'"), nullable=False))
    op.create_index("idx_bid_submissions_package", "bid_submissions", ["bid_package_id", "sub_company_id"])


def downgrade() -> None:
    # Reverse order: drop indexes, drop columns, drop tables
    op.drop_index("idx_bid_submissions_package", "bid_submissions")
    op.drop_column("bid_submissions", "status")
    op.drop_column("bid_submissions", "notes")
    op.drop_column("bid_submissions", "inclusions")
    op.drop_column("bid_submissions", "exclusions")
    op.drop_column("bid_submissions", "schedule_duration_days")

    op.drop_index("idx_bid_packages_project", "bid_packages")
    op.drop_column("bid_packages", "deleted_at")
    op.drop_column("bid_packages", "scope_documents")
    op.drop_column("bid_packages", "requirements")
    op.drop_column("bid_packages", "estimated_value")
    op.drop_column("bid_packages", "pre_bid_meeting_date")
    op.drop_column("bid_packages", "trade")

    op.drop_index("idx_photos_linked", "photos")
    op.drop_index("idx_photos_project", "photos")
    op.drop_column("photos", "deleted_at")
    op.drop_column("photos", "uploaded_by")
    op.drop_column("photos", "location")
    op.drop_column("photos", "tags")
    op.drop_column("photos", "caption")
    op.drop_column("photos", "project_id")
    op.drop_column("photos", "organization_id")

    op.drop_index("idx_documents_project_folder", "documents")
    op.drop_column("documents", "deleted_at")
    op.drop_column("documents", "tags")
    op.drop_column("documents", "folder_id")
    op.drop_column("documents", "description")

    op.drop_column("drawing_sheets", "uploaded_by")
    op.drop_column("drawing_sheets", "is_current")
    op.drop_column("drawing_sheets", "description")
    op.drop_column("drawing_sheets", "revision_date")

    op.drop_index("idx_drawings_project", "drawings")
    op.drop_column("drawings", "deleted_at")
    op.drop_column("drawings", "received_from")
    op.drop_column("drawings", "description")

    op.drop_index("idx_procurement_project_status", "procurement_items")
    op.drop_column("procurement_items", "deleted_at")
    op.drop_column("procurement_items", "notes")
    op.drop_column("procurement_items", "linked_schedule_task_id")
    op.drop_column("procurement_items", "sub_company_id")
    op.drop_column("procurement_items", "assigned_to")
    op.drop_column("procurement_items", "tracking_number")
    op.drop_column("procurement_items", "actual_delivery_date")
    op.drop_column("procurement_items", "expected_delivery_date")
    op.drop_column("procurement_items", "order_by_date")
    op.drop_column("procurement_items", "required_on_site_date")
    op.drop_column("procurement_items", "lead_time_days")
    op.drop_column("procurement_items", "vendor_email")
    op.drop_column("procurement_items", "vendor_phone")
    op.drop_column("procurement_items", "vendor_contact")
    op.drop_column("procurement_items", "unit")
    op.drop_column("procurement_items", "quantity")
    op.drop_column("procurement_items", "spec_section")
    op.drop_column("procurement_items", "category")

    op.drop_index("idx_todos_assigned", "todos")
    op.drop_index("idx_todos_project_status", "todos")
    op.drop_column("todos", "deleted_at")
    op.drop_column("todos", "completed_at")
    op.drop_column("todos", "source_id")
    op.drop_column("todos", "source_type")
    op.drop_column("todos", "cost_code_id")
    op.drop_column("todos", "category")
    op.execute("UPDATE todos SET status = 'TODO' WHERE status = 'OPEN'")
    op.alter_column("todos", "status", server_default=sa.text("'TODO'"))

    op.drop_index("idx_meetings_project_date", "meetings")
    op.drop_column("meetings", "deleted_at")
    op.drop_column("meetings", "minutes_published_at")
    op.drop_column("meetings", "minutes_published")
    op.drop_column("meetings", "parent_meeting_id")
    op.drop_column("meetings", "recurrence_end_date")
    op.drop_column("meetings", "recurrence_rule")
    op.drop_column("meetings", "recurring")
    op.drop_column("meetings", "virtual_link")
    op.drop_column("meetings", "virtual_provider")
    op.drop_column("meetings", "end_time")
    op.drop_column("meetings", "start_time")
    op.drop_column("meetings", "meeting_type")

    op.drop_index("idx_doc_folders_project", "document_folders")
    op.drop_table("document_folders")
