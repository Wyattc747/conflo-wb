import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Computed, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index(
            "idx_projects_org_phase",
            "organization_id",
            "phase",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    project_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    project_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'COMMERCIAL'")
    )
    contract_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    is_major: Mapped[Optional[bool]] = mapped_column(
        Boolean, Computed("contract_value >= 250000", persisted=True)
    )
    phase: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'BIDDING'")
    )
    estimated_start_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    estimated_end_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    owner_client_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner_client_company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ae_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ae_company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cost_code_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cost_code_templates.id"), nullable=True
    )
    bid_due_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
