import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id"), nullable=False
    )
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    captured_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    device_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linked_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linked_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
