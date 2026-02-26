from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class DrawingSheetCreate(BaseModel):
    sheet_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    revision: str = "0"
    file_id: Optional[UUID] = None


class DrawingSheetUpdate(BaseModel):
    sheet_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    revision: Optional[str] = None
    file_id: Optional[UUID] = None


class DrawingSheetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    drawing_id: UUID
    sheet_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    revision: str
    revision_date: Optional[datetime] = None
    is_current: bool = True
    file_id: Optional[UUID] = None
    uploaded_by: Optional[UUID] = None
    created_at: datetime


class DrawingSetCreate(BaseModel):
    set_number: str
    title: str
    discipline: Optional[str] = None
    description: Optional[str] = None
    received_from: Optional[str] = None


class DrawingSetUpdate(BaseModel):
    set_number: Optional[str] = None
    title: Optional[str] = None
    discipline: Optional[str] = None
    description: Optional[str] = None
    received_from: Optional[str] = None


class DrawingSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    set_number: str
    title: str
    discipline: Optional[str] = None
    description: Optional[str] = None
    received_from: Optional[str] = None
    is_current_set: bool
    sheet_count: int = 0
    sheets: list[DrawingSheetResponse] = []
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DrawingSetListResponse(BaseModel):
    data: list[DrawingSetResponse]
    meta: PaginationMeta
