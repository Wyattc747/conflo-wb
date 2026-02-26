import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    license_numbers: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'America/Denver'")
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'STARTER'")
    )
    subscription_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'TRIALING'")
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    grace_period_end: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    contract_start_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    contract_end_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
