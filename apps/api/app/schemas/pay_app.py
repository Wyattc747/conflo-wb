from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class PayAppLineItemCreate(BaseModel):
    budget_line_item_id: Optional[UUID] = None
    description: str
    scheduled_value: int  # Cents
    previous_applications: int = 0  # Cents
    current_amount: int  # Cents
    materials_stored: int = 0  # Cents


class PayAppCreate(BaseModel):
    pay_app_type: str  # "SUB_TO_GC" | "GC_TO_OWNER"
    period_from: date
    period_to: date
    sub_company_id: Optional[UUID] = None
    retainage_percent: float = 10.0
    line_items: list[PayAppLineItemCreate]


class PayAppUpdate(BaseModel):
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    retainage_percent: Optional[float] = None
    line_items: Optional[list[PayAppLineItemCreate]] = None


class PayAppLineItemResponse(BaseModel):
    budget_line_item_id: Optional[UUID] = None
    cost_code: Optional[str] = None
    description: str
    scheduled_value: int  # Cents
    previous_applications: int  # Cents
    current_amount: int  # Cents
    materials_stored: int  # Cents
    total_completed: int  # Cents
    percent_complete: float
    balance_to_finish: int  # Cents
    retainage: int  # Cents


class PayAppResponse(BaseModel):
    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    pay_app_type: str
    period_from: date
    period_to: date
    status: str

    # G702 summary (all cents)
    original_contract_sum: int
    net_change_orders: int
    contract_sum_to_date: int
    total_completed_and_stored: int
    retainage_percent: float
    retainage_amount: int
    total_earned_less_retainage: int
    previous_certificates: int
    current_payment_due: int
    balance_to_finish: int

    sub_company_id: Optional[UUID] = None
    sub_company_name: Optional[str] = None
    submitted_by_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    line_items: list[PayAppLineItemResponse]
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime


class PayAppListResponse(BaseModel):
    data: list[PayAppResponse]
    meta: PaginationMeta


class PayAppDecision(BaseModel):
    notes: Optional[str] = None
