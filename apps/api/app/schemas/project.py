from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    project_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = None
    project_type: str = "COMMERCIAL"
    contract_value: Optional[Decimal] = None
    phase: str = "BIDDING"
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    owner_client_name: Optional[str] = None
    owner_client_company: Optional[str] = None
    ae_name: Optional[str] = None
    ae_company: Optional[str] = None
    bid_due_date: Optional[datetime] = None
    cost_code_template_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    project_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = None
    project_type: Optional[str] = None
    contract_value: Optional[Decimal] = None
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    owner_client_name: Optional[str] = None
    owner_client_company: Optional[str] = None
    ae_name: Optional[str] = None
    ae_company: Optional[str] = None
    bid_due_date: Optional[datetime] = None
    cost_code_template_id: Optional[UUID] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    project_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = None
    project_type: str
    contract_value: Optional[Decimal] = None
    is_major: Optional[bool] = None
    phase: str
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    owner_client_name: Optional[str] = None
    owner_client_company: Optional[str] = None
    ae_name: Optional[str] = None
    ae_company: Optional[str] = None
    cost_code_template_id: Optional[UUID] = None
    bid_due_date: Optional[datetime] = None
    created_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class ProjectListResponse(BaseModel):
    data: list[ProjectResponse]
    meta: PaginationMeta


class PhaseTransitionRequest(BaseModel):
    target_phase: str


class PhaseTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phase: str
    previous_phase: Optional[str] = None


class VisibleToolsResponse(BaseModel):
    tools: list[dict]
