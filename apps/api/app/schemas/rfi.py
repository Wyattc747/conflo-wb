from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class RfiCreate(BaseModel):
    subject: str
    question: str
    assigned_to: Optional[UUID] = None
    distribution_list: list[UUID] = []
    due_date: Optional[date] = None
    priority: str = "NORMAL"
    cost_impact: Optional[bool] = None
    schedule_impact: Optional[bool] = None
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None
    location: Optional[str] = None


class RfiUpdate(BaseModel):
    subject: Optional[str] = None
    question: Optional[str] = None
    assigned_to: Optional[UUID] = None
    distribution_list: Optional[list[UUID]] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    cost_impact: Optional[bool] = None
    schedule_impact: Optional[bool] = None
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None
    location: Optional[str] = None


class RfiResponseCreate(BaseModel):
    """Official response to an RFI (not a comment)."""
    response: str
    attachments: list[UUID] = []


class RfiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    subject: str
    question: str
    official_response: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[date] = None
    days_open: Optional[int] = None
    cost_impact: bool
    schedule_impact: bool
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None
    location: Optional[str] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    responded_by: Optional[UUID] = None
    responded_by_name: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0


class RfiListResponse(BaseModel):
    data: list[RfiResponse]
    meta: PaginationMeta
