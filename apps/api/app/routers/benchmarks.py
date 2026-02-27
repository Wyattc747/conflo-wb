"""Benchmark analytics router — GC portal, OWNER_ADMIN and MANAGEMENT only."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.benchmark import (
    ActivityTimelineResponse,
    FinancialSummaryResponse,
    OrgOverviewResponse,
    ProjectMetricsResponse,
    ToolUsageStatsResponse,
)
from app.services.benchmark_service import (
    get_activity_timeline,
    get_financial_summary,
    get_org_overview,
    get_project_metrics,
    get_tool_usage_stats,
)

gc_router = APIRouter(prefix="/api/gc/benchmarks", tags=["benchmarks"])

ALLOWED_LEVELS = ("OWNER_ADMIN", "MANAGEMENT")


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _require_management(user: dict) -> None:
    if user.get("permission_level") not in ALLOWED_LEVELS:
        raise HTTPException(
            status_code=403,
            detail="Benchmarks are restricted to Owner/Admin and Management users",
        )


# ============================================================
# ORG OVERVIEW
# ============================================================

@gc_router.get("/overview", response_model=OrgOverviewResponse)
async def overview_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return high-level org stats."""
    user = _get_user(request)
    _require_management(user)
    data = await get_org_overview(db, user["organization_id"])
    return {"data": data, "meta": {}}


# ============================================================
# PROJECT METRICS (aggregate)
# ============================================================

@gc_router.get("/projects", response_model=ProjectMetricsResponse)
async def project_metrics_aggregate_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate project metrics across the org."""
    user = _get_user(request)
    _require_management(user)
    data = await get_project_metrics(db, user["organization_id"])
    return {"data": data, "meta": {}}


# ============================================================
# PROJECT METRICS (single project)
# ============================================================

@gc_router.get("/projects/{project_id}", response_model=ProjectMetricsResponse)
async def project_metrics_detail_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return metrics for a single project."""
    user = _get_user(request)
    _require_management(user)
    data = await get_project_metrics(db, user["organization_id"], project_id=project_id)
    return {"data": data, "meta": {}}


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

@gc_router.get("/financials", response_model=FinancialSummaryResponse)
async def financials_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return financial summary for the org."""
    user = _get_user(request)
    _require_management(user)
    data = await get_financial_summary(db, user["organization_id"])
    return {"data": data, "meta": {}}


# ============================================================
# ACTIVITY TIMELINE
# ============================================================

@gc_router.get("/activity", response_model=ActivityTimelineResponse)
async def activity_endpoint(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Return daily event counts for the last N days."""
    user = _get_user(request)
    _require_management(user)
    data = await get_activity_timeline(db, user["organization_id"], days=days)
    return {"data": data, "meta": {}}


# ============================================================
# TOOL USAGE STATS
# ============================================================

@gc_router.get("/tool-usage", response_model=ToolUsageStatsResponse)
async def tool_usage_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return record counts per tool for the org."""
    user = _get_user(request)
    _require_management(user)
    data = await get_tool_usage_stats(db, user["organization_id"])
    return {"data": data, "meta": {}}
