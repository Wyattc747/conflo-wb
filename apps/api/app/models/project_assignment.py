import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "assignee_type", "assignee_id", name="uq_project_assignment"
        ),
        Index("idx_assignments_project", "project_id", "assignee_type"),
        Index("idx_assignments_assignee", "assignee_type", "assignee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    assignee_type: Mapped[str] = mapped_column(String(20), nullable=False)
    assignee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    financial_access: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    bidding_access: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    trade: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contract_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    assigned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
