from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    priority: str = "MEDIUM"
    category: Optional[str] = None
    cost_code_id: Optional[UUID] = None
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    cost_code_id: Optional[UUID] = None


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[date] = None
    category: Optional[str] = None
    cost_code_id: Optional[UUID] = None
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseModel):
    data: list[TodoResponse]
    meta: PaginationMeta
