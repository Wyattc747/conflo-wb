from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class BudgetLineItemCreate(BaseModel):
    cost_code: str
    description: str
    original_amount: int  # Cents
    notes: Optional[str] = None


class BudgetLineItemUpdate(BaseModel):
    description: Optional[str] = None
    original_amount: Optional[int] = None  # Cents
    notes: Optional[str] = None


class BudgetLineItemResponse(BaseModel):
    id: UUID
    project_id: UUID
    cost_code: str
    description: Optional[str] = None
    original_amount: int  # Cents
    approved_changes: int  # Cents
    revised_amount: int  # Cents (original + approved_changes)
    billed_to_date: int  # Cents
    remaining: int  # Cents (revised - billed)
    percent_complete: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BudgetSummaryResponse(BaseModel):
    original_contract: int  # Cents
    approved_changes: int  # Cents
    revised_contract: int  # Cents
    billed_to_date: int  # Cents
    remaining: int  # Cents
    percent_complete: float
    line_items: list[BudgetLineItemResponse]
    change_orders_pending: int
    change_orders_pending_amount: int  # Cents


class BudgetImportItem(BaseModel):
    cost_code: str
    description: str
    amount: int  # Cents
