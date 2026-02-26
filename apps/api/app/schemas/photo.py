from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class PhotoCreate(BaseModel):
    file_id: Optional[UUID] = None
    linked_type: Optional[str] = None
    linked_id: Optional[UUID] = None
    caption: Optional[str] = None
    tags: list[str] = []
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PhotoUpdate(BaseModel):
    caption: Optional[str] = None
    tags: Optional[list[str]] = None
    location: Optional[str] = None
    linked_type: Optional[str] = None
    linked_id: Optional[UUID] = None


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    linked_type: Optional[str] = None
    linked_id: Optional[UUID] = None
    caption: Optional[str] = None
    tags: list[str] = []
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    uploaded_by: Optional[UUID] = None
    uploaded_by_name: Optional[str] = None
    captured_at: Optional[datetime] = None
    created_at: datetime


class PhotoListResponse(BaseModel):
    data: list[PhotoResponse]
    meta: PaginationMeta
