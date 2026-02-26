import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OwnerPortalConfig(Base):
    __tablename__ = "owner_portal_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, nullable=False
    )
    show_schedule: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_submittals: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_rfis: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_transmittals: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_drawings: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_punch_list: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    show_budget_summary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    show_daily_logs: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    allow_punch_creation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
