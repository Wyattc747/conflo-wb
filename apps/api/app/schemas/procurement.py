from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class ProcurementCreate(BaseModel):
    item_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    spec_section: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    vendor: Optional[str] = None
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    estimated_cost_cents: Optional[int] = None
    lead_time_days: Optional[int] = None
    required_on_site_date: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    sub_company_id: Optional[UUID] = None
    linked_schedule_task_id: Optional[UUID] = None
    notes: Optional[str] = None


class ProcurementUpdate(BaseModel):
    item_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    spec_section: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    vendor: Optional[str] = None
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    estimated_cost_cents: Optional[int] = None
    actual_cost_cents: Optional[int] = None
    po_number: Optional[str] = None
    lead_time_days: Optional[int] = None
    required_on_site_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    assigned_to: Optional[UUID] = None
    sub_company_id: Optional[UUID] = None
    linked_schedule_task_id: Optional[UUID] = None
    notes: Optional[str] = None


class ProcurementTransition(BaseModel):
    """Body for status transition endpoints."""
    po_number: Optional[str] = None
    tracking_number: Optional[str] = None
    actual_delivery_date: Optional[datetime] = None


class ProcurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    item_name: str
    description: Optional[str] = None
    status: str
    category: Optional[str] = None
    spec_section: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    vendor: Optional[str] = None
    vendor_contact: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_email: Optional[str] = None
    estimated_cost_cents: int = 0
    actual_cost_cents: int = 0
    po_number: Optional[str] = None
    lead_time_days: Optional[int] = None
    required_on_site_date: Optional[datetime] = None
    order_by_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    is_at_risk: bool = False
    assigned_to: Optional[UUID] = None
    sub_company_id: Optional[UUID] = None
    linked_schedule_task_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ProcurementListResponse(BaseModel):
    data: list[ProcurementResponse]
    meta: PaginationMeta
