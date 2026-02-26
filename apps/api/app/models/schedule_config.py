import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScheduleConfig(Base):
    __tablename__ = "schedule_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, nullable=False
    )

    # Schedule mode
    schedule_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'SINGLE'")
    )  # SINGLE | THREE_TIER_AUTO | THREE_TIER_MANUAL

    # Derivation method for three-tier
    derivation_method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'FIXED_DAYS'")
    )  # PERCENTAGE | FIXED_DAYS
    owner_buffer_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sub_compress_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Health thresholds (days of slippage)
    health_on_track_max_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("5")
    )
    health_at_risk_max_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("15")
    )

    # Sub notification intervals (days before mobilization)
    sub_notify_intervals: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[14, 7, 1]'::jsonb")
    )
