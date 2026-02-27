"""Pydantic response models for benchmark/analytics endpoints."""
from typing import Optional

from pydantic import BaseModel


class OrgOverview(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    closed_projects: int = 0
    total_users: int = 0
    active_users: int = 0
    total_subs: int = 0
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None


class ProjectMetrics(BaseModel):
    rfi_count: int = 0
    rfi_avg_close_days: Optional[float] = None
    rfi_open_count: int = 0
    submittal_count: int = 0
    submittal_avg_review_days: Optional[float] = None
    submittal_approval_rate: Optional[float] = None
    change_order_count: int = 0
    change_order_total_value: Optional[int] = None  # cents
    change_order_approval_rate: Optional[float] = None
    punch_list_total: int = 0
    punch_list_closed_pct: Optional[float] = None
    budget_variance_pct: Optional[float] = None
    schedule_on_track_pct: Optional[float] = None


class FinancialSummary(BaseModel):
    total_contract_value: Optional[int] = None  # cents
    total_approved_cos: Optional[int] = None  # cents
    total_paid: Optional[int] = None  # cents
    budget_original: Optional[int] = None  # cents
    budget_committed: Optional[int] = None  # cents
    budget_actuals: Optional[int] = None  # cents
    retention_held: Optional[int] = None  # cents


class ActivityDay(BaseModel):
    date: str
    count: int = 0


class ToolUsageStats(BaseModel):
    daily_logs: int = 0
    rfis: int = 0
    submittals: int = 0
    transmittals: int = 0
    change_orders: int = 0
    punch_list_items: int = 0
    inspections: int = 0
    pay_apps: int = 0
    bid_packages: int = 0
    schedule_tasks: int = 0
    drawings: int = 0
    meetings: int = 0
    todos: int = 0
    procurement_items: int = 0
    documents: int = 0


class OrgOverviewResponse(BaseModel):
    data: OrgOverview
    meta: dict = {}


class ProjectMetricsResponse(BaseModel):
    data: ProjectMetrics
    meta: dict = {}


class FinancialSummaryResponse(BaseModel):
    data: FinancialSummary
    meta: dict = {}


class ActivityTimelineResponse(BaseModel):
    data: list[ActivityDay]
    meta: dict = {}


class ToolUsageStatsResponse(BaseModel):
    data: ToolUsageStats
    meta: dict = {}
