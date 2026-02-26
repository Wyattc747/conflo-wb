from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class ActionItemEntry(BaseModel):
    description: str
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None


class MeetingCreate(BaseModel):
    title: str
    meeting_type: str = "PROGRESS"
    scheduled_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    virtual_provider: Optional[str] = None
    virtual_link: Optional[str] = None
    attendees: list[UUID] = []
    agenda: Optional[str] = None
    recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    meeting_type: Optional[str] = None
    scheduled_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    virtual_provider: Optional[str] = None
    virtual_link: Optional[str] = None
    attendees: Optional[list[UUID]] = None
    agenda: Optional[str] = None
    minutes: Optional[str] = None
    action_items: Optional[list[ActionItemEntry]] = None
    recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None


class PublishMinutesRequest(BaseModel):
    create_todos: bool = False


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    title: str
    meeting_type: str
    status: str
    scheduled_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    virtual_provider: Optional[str] = None
    virtual_link: Optional[str] = None
    attendees: list = []
    agenda: Optional[str] = None
    minutes: Optional[str] = None
    action_items: list = []
    recurring: bool = False
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    parent_meeting_id: Optional[UUID] = None
    minutes_published: bool = False
    minutes_published_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MeetingListResponse(BaseModel):
    data: list[MeetingResponse]
    meta: PaginationMeta
