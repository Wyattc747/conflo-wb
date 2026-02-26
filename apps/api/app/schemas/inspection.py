"""Pydantic schemas for Inspections and Inspection Templates."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ============================================================
# TEMPLATES
# ============================================================

class ChecklistItemCreate(BaseModel):
    label: str
    required: bool = True
    order: int = 0


class InspectionTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "GENERAL"
    checklist_items: list[ChecklistItemCreate] = []


class InspectionTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    checklist_items: Optional[list[ChecklistItemCreate]] = None


class InspectionTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    category: str
    checklist_items: list[dict] = []
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


class InspectionTemplateListResponse(BaseModel):
    data: list[InspectionTemplateResponse]
    meta: dict


# ============================================================
# INSPECTIONS
# ============================================================

class InspectionCreate(BaseModel):
    template_id: Optional[UUID] = None
    title: Optional[str] = None
    category: str = "GENERAL"
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    inspector_name: Optional[str] = None
    inspector_company: Optional[str] = None
    notes: Optional[str] = None


class InspectionUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    inspector_name: Optional[str] = None
    inspector_company: Optional[str] = None
    notes: Optional[str] = None


class ChecklistResult(BaseModel):
    item_label: str
    result: str  # PASS | FAIL | NA
    notes: Optional[str] = None


class InspectionResultSubmit(BaseModel):
    results: list[ChecklistResult]
    overall_result: str  # PASSED | FAILED | CONDITIONAL
    notes: Optional[str] = None


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    number: int
    formatted_number: str
    title: str
    template_id: Optional[UUID] = None
    template_name: Optional[str] = None
    category: str
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    inspector_name: Optional[str] = None
    inspector_company: Optional[str] = None
    status: str
    overall_result: Optional[str] = None
    checklist_results: list[dict] = []
    photo_ids: list = []
    notes: Optional[str] = None
    comments_count: int = 0
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    updated_at: datetime


class InspectionListResponse(BaseModel):
    data: list[InspectionResponse]
    meta: dict
