"""Pydantic schemas for Submittals."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubmittalCreate(BaseModel):
    title: str
    spec_section: Optional[str] = None
    description: Optional[str] = None
    submittal_type: str = "SHOP_DRAWING"
    sub_company_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None
    lead_time_days: Optional[int] = None


class SubmittalUpdate(BaseModel):
    title: Optional[str] = None
    spec_section: Optional[str] = None
    description: Optional[str] = None
    submittal_type: Optional[str] = None
    sub_company_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None
    lead_time_days: Optional[int] = None


class SubmittalRevisionCreate(BaseModel):
    description: Optional[str] = None


class SubmittalReviewRequest(BaseModel):
    decision: str  # APPROVED | APPROVED_AS_NOTED | REVISE_AND_RESUBMIT | REJECTED
    notes: Optional[str] = None


class SubmittalRevisionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    revision: int
    formatted_number: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None


class SubmittalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    number: int
    revision: int
    formatted_number: str
    title: str
    spec_section: Optional[str] = None
    description: Optional[str] = None
    submittal_type: Optional[str] = None
    status: str
    sub_company_id: Optional[UUID] = None
    sub_company_name: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[date] = None
    days_open: Optional[int] = None
    cost_code_id: Optional[UUID] = None
    drawing_reference: Optional[str] = None
    lead_time_days: Optional[int] = None
    review_notes: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    revision_history: list[SubmittalRevisionSummary] = []
    comments_count: int = 0
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SubmittalListResponse(BaseModel):
    data: list[SubmittalResponse]
    meta: dict
