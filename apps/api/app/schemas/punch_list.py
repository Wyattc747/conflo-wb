"""Pydantic schemas for Punch List Items."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PunchListItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    category: str = "DEFICIENCY"
    priority: str = "NORMAL"
    assigned_to_sub_id: Optional[UUID] = None
    assigned_to_user_id: Optional[UUID] = None
    due_date: Optional[date] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None


class PunchListItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_sub_id: Optional[UUID] = None
    assigned_to_user_id: Optional[UUID] = None
    due_date: Optional[date] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None


class PunchListCompleteRequest(BaseModel):
    completion_notes: Optional[str] = None


class PunchListVerifyRequest(BaseModel):
    verified: bool
    verification_notes: Optional[str] = None


class PunchListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    category: str
    priority: str
    status: str
    assigned_to_sub_id: Optional[UUID] = None
    assigned_to_sub_name: Optional[str] = None
    assigned_to_user_id: Optional[UUID] = None
    assigned_to_user_name: Optional[str] = None
    due_date: Optional[date] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None
    before_photo_ids: list = []
    after_photo_ids: list = []
    verification_photo_ids: list = []
    completion_notes: Optional[str] = None
    completed_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    comments_count: int = 0
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PunchListListResponse(BaseModel):
    data: list[PunchListItemResponse]
    meta: dict
