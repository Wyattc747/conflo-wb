import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BudgetLineItem(Base):
    __tablename__ = "budget_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    cost_code: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0")
    )
    approved_changes: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0")
    )
    committed: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0")
    )
    actuals: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0")
    )
    projected: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
