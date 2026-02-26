from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class ChangeOrderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reason: str  # OWNER_REQUEST | DESIGN_ERROR | UNFORESEEN_CONDITIONS | VALUE_ENGINEERING | SCOPE_CHANGE | OTHER
    cost_code_id: Optional[UUID] = None
    amount: int = 0  # Cents
    schedule_impact_days: int = 0
    priority: str = "NORMAL"
    sub_company_ids: list[UUID] = []
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None


class ChangeOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    cost_code_id: Optional[UUID] = None
    amount: Optional[int] = None  # Cents
    schedule_impact_days: Optional[int] = None
    markup_percent: Optional[float] = None
    gc_amount: Optional[int] = None  # Cents
    priority: Optional[str] = None
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None


class SubPricingSubmit(BaseModel):
    amount: int  # Cents
    description: str
    schedule_impact_days: int = 0
    attachments: list[UUID] = []


class SubPricingResponse(BaseModel):
    sub_company_id: UUID
    sub_company_name: Optional[str] = None
    amount: Optional[int] = None  # Cents
    description: Optional[str] = None
    schedule_impact_days: int = 0
    status: str  # REQUESTED | SUBMITTED | ACCEPTED | REJECTED
    submitted_at: Optional[datetime] = None


class ChangeOrderResponse(BaseModel):
    id: UUID
    project_id: UUID
    number: int
    formatted_number: str  # "PCO-003" or "CO-003"
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    status: str
    order_type: str  # PCO | CO
    cost_code_id: Optional[UUID] = None
    cost_code: Optional[str] = None

    # Financial (cents)
    amount: int
    markup_percent: Optional[float] = None
    markup_amount: Optional[int] = None
    gc_amount: int
    schedule_impact_days: int

    sub_pricings: list[SubPricingResponse] = []

    # Workflow
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    submitted_to_owner_at: Optional[datetime] = None
    owner_decision: Optional[str] = None
    owner_decision_by: Optional[UUID] = None
    owner_decision_at: Optional[datetime] = None
    owner_decision_notes: Optional[str] = None

    priority: str
    drawing_reference: Optional[str] = None
    spec_section: Optional[str] = None
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime


class ChangeOrderListResponse(BaseModel):
    data: list[ChangeOrderResponse]
    meta: PaginationMeta


class OwnerDecision(BaseModel):
    decision: str  # APPROVED | REJECTED
    notes: Optional[str] = None
