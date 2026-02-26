from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssignmentCreate(BaseModel):
    assignee_type: str  # GC_USER | SUB_COMPANY | OWNER_ACCOUNT
    assignee_id: UUID
    financial_access: bool = False
    bidding_access: bool = False
    trade: Optional[str] = None
    contract_value: Optional[Decimal] = None


class AssignmentUpdate(BaseModel):
    financial_access: Optional[bool] = None
    bidding_access: Optional[bool] = None
    trade: Optional[str] = None
    contract_value: Optional[Decimal] = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    assignee_type: str
    assignee_id: UUID
    financial_access: bool
    bidding_access: bool
    trade: Optional[str] = None
    contract_value: Optional[Decimal] = None
    assigned_by_user_id: Optional[UUID] = None
    assigned_at: datetime


class AssignmentListResponse(BaseModel):
    data: list[AssignmentResponse]
    meta: dict = {}
