"""Pydantic schemas for Transmittals."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransmittalItemCreate(BaseModel):
    description: str
    quantity: int = 1
    document_type: Optional[str] = None  # DRAWINGS | SPECS | SHOP_DRAWINGS | SAMPLES | REPORTS | OTHER


class TransmittalCreate(BaseModel):
    subject: str
    to_company: Optional[str] = None
    to_contact: Optional[str] = None
    to_email: Optional[str] = None
    from_company: Optional[str] = None
    from_contact: Optional[str] = None
    purpose: str = "FOR_REVIEW"
    description: Optional[str] = None
    items: list[TransmittalItemCreate] = []
    due_date: Optional[date] = None
    sent_via: str = "CONFLO"


class TransmittalUpdate(BaseModel):
    subject: Optional[str] = None
    to_company: Optional[str] = None
    to_contact: Optional[str] = None
    to_email: Optional[str] = None
    from_company: Optional[str] = None
    from_contact: Optional[str] = None
    purpose: Optional[str] = None
    description: Optional[str] = None
    items: Optional[list[TransmittalItemCreate]] = None
    due_date: Optional[date] = None
    sent_via: Optional[str] = None


class TransmittalItemResponse(BaseModel):
    description: str
    quantity: int = 1
    document_type: Optional[str] = None


class TransmittalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    subject: str
    to_company: Optional[str] = None
    to_contact: Optional[str] = None
    to_email: Optional[str] = None
    from_company: Optional[str] = None
    from_contact: Optional[str] = None
    purpose: str
    description: Optional[str] = None
    status: str
    items: list[TransmittalItemResponse] = []
    sent_via: str
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    due_date: Optional[date] = None
    comments_count: int = 0
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransmittalListResponse(BaseModel):
    data: list[TransmittalResponse]
    meta: dict
