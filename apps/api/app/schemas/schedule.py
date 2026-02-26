"""Pydantic schemas for Schedule (Tasks, Dependencies, Delays, Versions, Config)."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ============================================================
# TASKS
# ============================================================

class ScheduleTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    wbs_code: Optional[str] = None
    parent_task_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = None
    assigned_to: Optional[UUID] = None
    assigned_to_sub_id: Optional[UUID] = None
    milestone: bool = False
    is_critical: bool = False
    cost_code_id: Optional[UUID] = None
    sort_order: int = 0


class ScheduleTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    wbs_code: Optional[str] = None
    parent_task_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = None
    percent_complete: Optional[int] = None
    assigned_to: Optional[UUID] = None
    assigned_to_sub_id: Optional[UUID] = None
    milestone: Optional[bool] = None
    is_critical: Optional[bool] = None
    cost_code_id: Optional[UUID] = None
    sort_order: Optional[int] = None


class ScheduleTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    wbs_code: Optional[str] = None
    parent_task_id: Optional[UUID] = None
    sort_order: int = 0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = None
    baseline_start: Optional[date] = None
    baseline_end: Optional[date] = None
    baseline_duration: Optional[int] = None
    owner_start_date: Optional[date] = None
    owner_end_date: Optional[date] = None
    sub_start_date: Optional[date] = None
    sub_end_date: Optional[date] = None
    percent_complete: int = 0
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    assigned_to: Optional[UUID] = None
    assigned_to_sub_id: Optional[UUID] = None
    milestone: bool = False
    is_critical: bool = False
    cost_code_id: Optional[UUID] = None
    dependencies: list[dict] = []
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ScheduleTaskListResponse(BaseModel):
    data: list[ScheduleTaskResponse]
    meta: dict


# ============================================================
# DEPENDENCIES
# ============================================================

class DependencyCreate(BaseModel):
    predecessor_id: UUID
    successor_id: UUID
    dependency_type: str = "FS"  # FS | SS | FF | SF
    lag_days: int = 0


class DependencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    predecessor_id: UUID
    successor_id: UUID
    dependency_type: str
    lag_days: int


# ============================================================
# DELAYS
# ============================================================

class ScheduleDelayCreate(BaseModel):
    task_ids: list[UUID] = []
    delay_days: int
    reason_category: str
    responsible_party: str
    description: str
    daily_log_id: Optional[UUID] = None
    rfi_id: Optional[UUID] = None
    change_order_id: Optional[UUID] = None


class ScheduleDelayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    task_ids: list = []
    delay_days: int
    reason_category: str
    responsible_party: str
    description: str
    impacts_gc_schedule: bool
    impacts_owner_schedule: bool
    impacts_sub_schedule: bool
    daily_log_id: Optional[UUID] = None
    rfi_id: Optional[UUID] = None
    change_order_id: Optional[UUID] = None
    status: str
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime


class ScheduleDelayListResponse(BaseModel):
    data: list[ScheduleDelayResponse]
    meta: dict


# ============================================================
# VERSIONS
# ============================================================

class SchedulePublishRequest(BaseModel):
    version_type: str = "FULL_SCHEDULE"  # FULL_SCHEDULE | LOOK_AHEAD
    title: Optional[str] = None
    notes: Optional[str] = None


class ScheduleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    version_type: str
    version_number: int
    title: str
    notes: Optional[str] = None
    snapshot_data: dict = {}
    published_by: UUID
    published_at: datetime


class ScheduleVersionListResponse(BaseModel):
    data: list[ScheduleVersionResponse]
    meta: dict


# ============================================================
# CONFIG
# ============================================================

class ScheduleConfigUpdate(BaseModel):
    schedule_mode: Optional[str] = None
    derivation_method: Optional[str] = None
    owner_buffer_percent: Optional[float] = None
    sub_compress_percent: Optional[float] = None
    health_on_track_max_days: Optional[int] = None
    health_at_risk_max_days: Optional[int] = None
    sub_notify_intervals: Optional[list[int]] = None


class ScheduleConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    schedule_mode: str
    derivation_method: str
    owner_buffer_percent: Optional[float] = None
    sub_compress_percent: Optional[float] = None
    health_on_track_max_days: int
    health_at_risk_max_days: int
    sub_notify_intervals: list = []


# ============================================================
# HEALTH
# ============================================================

class ScheduleHealthResponse(BaseModel):
    status: str  # ON_TRACK | AT_RISK | BEHIND
    slippage_days: int
    on_track_threshold: int
    at_risk_threshold: int
