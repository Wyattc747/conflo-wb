from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class BidPackageCreate(BaseModel):
    title: str
    description: Optional[str] = None
    trade: Optional[str] = None
    trades: list[str] = []
    bid_due_date: Optional[datetime] = None
    pre_bid_meeting_date: Optional[datetime] = None
    estimated_value_cents: Optional[int] = None
    requirements: Optional[str] = None
    scope_documents: list = []


class BidPackageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    trade: Optional[str] = None
    trades: Optional[list[str]] = None
    bid_due_date: Optional[datetime] = None
    pre_bid_meeting_date: Optional[datetime] = None
    estimated_value_cents: Optional[int] = None
    requirements: Optional[str] = None
    scope_documents: Optional[list] = None


class DistributeBidPackageRequest(BaseModel):
    invited_sub_ids: list[UUID]


class AwardBidRequest(BaseModel):
    submission_id: UUID
    trade: Optional[str] = None


class BidSubmissionCreate(BaseModel):
    total_amount_cents: Optional[int] = None
    line_items: list = []
    qualifications: Optional[str] = None
    schedule_duration_days: Optional[int] = None
    exclusions: Optional[str] = None
    inclusions: Optional[str] = None
    notes: Optional[str] = None


class BidSubmissionUpdate(BaseModel):
    total_amount_cents: Optional[int] = None
    line_items: Optional[list] = None
    qualifications: Optional[str] = None
    schedule_duration_days: Optional[int] = None
    exclusions: Optional[str] = None
    inclusions: Optional[str] = None
    notes: Optional[str] = None


class BidSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    bid_package_id: UUID
    sub_company_id: UUID
    sub_company_name: Optional[str] = None
    total_amount_cents: int = 0
    line_items: list = []
    qualifications: Optional[str] = None
    schedule_duration_days: Optional[int] = None
    exclusions: Optional[str] = None
    inclusions: Optional[str] = None
    notes: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime


class BidComparisonResponse(BaseModel):
    submissions: list[BidSubmissionResponse]
    lowest_amount_cents: int = 0
    highest_amount_cents: int = 0
    average_amount_cents: int = 0
    recommended_submission_id: Optional[UUID] = None


class BidPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    title: str
    description: Optional[str] = None
    trade: Optional[str] = None
    trades: list[str] = []
    status: str
    bid_due_date: Optional[datetime] = None
    pre_bid_meeting_date: Optional[datetime] = None
    estimated_value_cents: int = 0
    requirements: Optional[str] = None
    scope_documents: list = []
    invited_sub_ids: list = []
    submission_count: int = 0
    awarded_sub_id: Optional[UUID] = None
    awarded_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BidPackageListResponse(BaseModel):
    data: list[BidPackageResponse]
    meta: PaginationMeta
