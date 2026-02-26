import uuid

from sqlalchemy import ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScheduleDependency(Base):
    __tablename__ = "schedule_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    predecessor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedule_tasks.id"), nullable=False
    )
    successor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedule_tasks.id"), nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(
        String(5), nullable=False, server_default=text("'FS'")
    )  # FS, SS, FF, SF
    lag_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
