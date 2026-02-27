"""Benchmark aggregation service — org-level performance metrics and project analytics."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_package import BidPackage
from app.models.budget_line_item import BudgetLineItem
from app.models.change_order import ChangeOrder
from app.models.daily_log import DailyLog
from app.models.document import Document
from app.models.drawing import Drawing
from app.models.event_log import EventLog
from app.models.inspection import Inspection
from app.models.meeting import Meeting
from app.models.organization import Organization
from app.models.pay_app import PayApp
from app.models.procurement_item import ProcurementItem
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.punch_list_item import PunchListItem
from app.models.rfi import RFI
from app.models.schedule_task import ScheduleTask
from app.models.submittal import Submittal
from app.models.todo import Todo
from app.models.transmittal import Transmittal
from app.models.user import User


# ============================================================
# HELPERS
# ============================================================

def _cents(value: Optional[Decimal]) -> Optional[int]:
    """Convert dollars (Decimal) to integer cents for the API."""
    if value is None:
        return None
    return int(value * 100)


# ============================================================
# ORG OVERVIEW
# ============================================================

async def get_org_overview(db: AsyncSession, organization_id: uuid.UUID) -> dict:
    """Return high-level org stats."""

    # Total / active / closed projects
    total_projects_q = select(func.count()).select_from(Project).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
    )
    active_projects_q = select(func.count()).select_from(Project).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
        Project.phase == "ACTIVE",
    )
    closed_projects_q = select(func.count()).select_from(Project).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
        Project.phase == "CLOSED",
    )

    # Total / active users
    total_users_q = select(func.count()).select_from(User).where(
        User.organization_id == organization_id,
        User.deleted_at.is_(None),
    )
    active_users_q = select(func.count()).select_from(User).where(
        User.organization_id == organization_id,
        User.deleted_at.is_(None),
        User.status == "ACTIVE",
    )

    # Total unique sub companies assigned
    total_subs_q = select(func.count(func.distinct(ProjectAssignment.assignee_id))).select_from(
        ProjectAssignment
    ).join(
        Project, ProjectAssignment.project_id == Project.id
    ).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
        ProjectAssignment.assignee_type == "SUB_COMPANY",
    )

    # Organization details
    org_q = select(
        Organization.subscription_tier,
        Organization.subscription_status,
    ).where(Organization.id == organization_id)

    # Execute all queries
    total_projects = (await db.execute(total_projects_q)).scalar() or 0
    active_projects = (await db.execute(active_projects_q)).scalar() or 0
    closed_projects = (await db.execute(closed_projects_q)).scalar() or 0
    total_users = (await db.execute(total_users_q)).scalar() or 0
    active_users = (await db.execute(active_users_q)).scalar() or 0
    total_subs = (await db.execute(total_subs_q)).scalar() or 0
    org_row = (await db.execute(org_q)).first()

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "closed_projects": closed_projects,
        "total_users": total_users,
        "active_users": active_users,
        "total_subs": total_subs,
        "subscription_tier": org_row.subscription_tier if org_row else None,
        "subscription_status": org_row.subscription_status if org_row else None,
    }


# ============================================================
# PROJECT METRICS
# ============================================================

async def get_project_metrics(
    db: AsyncSession,
    organization_id: uuid.UUID,
    project_id: Optional[uuid.UUID] = None,
) -> dict:
    """Return per-project or aggregate metrics across the org."""

    # Base filter: organization scoping
    def _org_filter(model):
        filters = [model.organization_id == organization_id]
        if project_id:
            filters.append(model.project_id == project_id)
        return filters

    # --- RFIs ---
    rfi_count = (await db.execute(
        select(func.count()).select_from(RFI).where(*_org_filter(RFI))
    )).scalar() or 0

    rfi_open_count = (await db.execute(
        select(func.count()).select_from(RFI).where(
            *_org_filter(RFI), RFI.status.in_(["DRAFT", "OPEN"])
        )
    )).scalar() or 0

    # Average close days: for CLOSED RFIs where responded_at exists
    rfi_avg_close_days_result = (await db.execute(
        select(func.avg(
            func.extract("epoch", RFI.responded_at - RFI.created_at) / 86400
        )).select_from(RFI).where(
            *_org_filter(RFI),
            RFI.status == "CLOSED",
            RFI.responded_at.isnot(None),
        )
    )).scalar()
    rfi_avg_close_days = round(float(rfi_avg_close_days_result), 1) if rfi_avg_close_days_result else None

    # --- Submittals ---
    submittal_count = (await db.execute(
        select(func.count()).select_from(Submittal).where(
            *_org_filter(Submittal), Submittal.deleted_at.is_(None)
        )
    )).scalar() or 0

    # Average review days: from created_at to reviewed_at
    submittal_avg_review_result = (await db.execute(
        select(func.avg(
            func.extract("epoch", Submittal.reviewed_at - Submittal.created_at) / 86400
        )).select_from(Submittal).where(
            *_org_filter(Submittal),
            Submittal.deleted_at.is_(None),
            Submittal.reviewed_at.isnot(None),
        )
    )).scalar()
    submittal_avg_review_days = (
        round(float(submittal_avg_review_result), 1) if submittal_avg_review_result else None
    )

    # Approval rate: APPROVED or APPROVED_AS_NOTED out of all reviewed
    approved_submittals = (await db.execute(
        select(func.count()).select_from(Submittal).where(
            *_org_filter(Submittal),
            Submittal.deleted_at.is_(None),
            Submittal.status.in_(["APPROVED", "APPROVED_AS_NOTED"]),
        )
    )).scalar() or 0
    reviewed_submittals = (await db.execute(
        select(func.count()).select_from(Submittal).where(
            *_org_filter(Submittal),
            Submittal.deleted_at.is_(None),
            Submittal.status.in_(["APPROVED", "APPROVED_AS_NOTED", "REVISE_AND_RESUBMIT", "REJECTED"]),
        )
    )).scalar() or 0
    submittal_approval_rate = (
        round(approved_submittals / reviewed_submittals * 100, 1)
        if reviewed_submittals > 0 else None
    )

    # --- Change Orders ---
    co_count = (await db.execute(
        select(func.count()).select_from(ChangeOrder).where(
            *_org_filter(ChangeOrder), ChangeOrder.deleted_at.is_(None)
        )
    )).scalar() or 0

    co_total_value = (await db.execute(
        select(func.sum(ChangeOrder.total_amount)).select_from(ChangeOrder).where(
            *_org_filter(ChangeOrder),
            ChangeOrder.deleted_at.is_(None),
            ChangeOrder.total_amount.isnot(None),
        )
    )).scalar()

    approved_cos = (await db.execute(
        select(func.count()).select_from(ChangeOrder).where(
            *_org_filter(ChangeOrder),
            ChangeOrder.deleted_at.is_(None),
            ChangeOrder.status == "APPROVED",
        )
    )).scalar() or 0
    decided_cos = (await db.execute(
        select(func.count()).select_from(ChangeOrder).where(
            *_org_filter(ChangeOrder),
            ChangeOrder.deleted_at.is_(None),
            ChangeOrder.status.in_(["APPROVED", "REJECTED"]),
        )
    )).scalar() or 0
    co_approval_rate = (
        round(approved_cos / decided_cos * 100, 1) if decided_cos > 0 else None
    )

    # --- Punch List ---
    punch_total = (await db.execute(
        select(func.count()).select_from(PunchListItem).where(
            *_org_filter(PunchListItem), PunchListItem.deleted_at.is_(None)
        )
    )).scalar() or 0
    punch_closed = (await db.execute(
        select(func.count()).select_from(PunchListItem).where(
            *_org_filter(PunchListItem),
            PunchListItem.deleted_at.is_(None),
            PunchListItem.status == "CLOSED",
        )
    )).scalar() or 0
    punch_closed_pct = (
        round(punch_closed / punch_total * 100, 1) if punch_total > 0 else None
    )

    # --- Budget Variance ---
    # BudgetLineItem only has project_id (no organization_id), so join to Project
    budget_base = select(
        func.sum(BudgetLineItem.original_amount).label("original"),
        func.sum(BudgetLineItem.committed).label("committed"),
    ).select_from(BudgetLineItem).join(
        Project, BudgetLineItem.project_id == Project.id
    ).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
        BudgetLineItem.deleted_at.is_(None),
    )
    if project_id:
        budget_base = budget_base.where(BudgetLineItem.project_id == project_id)
    budget_row = (await db.execute(budget_base)).first()
    budget_original = budget_row.original if budget_row else None
    budget_committed = budget_row.committed if budget_row else None
    budget_variance_pct = None
    if budget_original and budget_original != 0:
        budget_variance_pct = round(
            float((budget_committed - budget_original) / budget_original * 100), 1
        )

    # --- Schedule On-Track ---
    schedule_base_filters = [
        ScheduleTask.deleted_at.is_(None),
    ]
    if project_id:
        schedule_base_filters.append(ScheduleTask.project_id == project_id)
        schedule_base_filters.append(ScheduleTask.organization_id == organization_id)
    else:
        schedule_base_filters.append(ScheduleTask.organization_id == organization_id)

    schedule_total = (await db.execute(
        select(func.count()).select_from(ScheduleTask).where(*schedule_base_filters)
    )).scalar() or 0
    schedule_on_track = (await db.execute(
        select(func.count()).select_from(ScheduleTask).where(
            *schedule_base_filters,
            ScheduleTask.percent_complete >= 100,
        )
    )).scalar() or 0
    schedule_on_track_pct = (
        round(schedule_on_track / schedule_total * 100, 1)
        if schedule_total > 0 else None
    )

    return {
        "rfi_count": rfi_count,
        "rfi_avg_close_days": rfi_avg_close_days,
        "rfi_open_count": rfi_open_count,
        "submittal_count": submittal_count,
        "submittal_avg_review_days": submittal_avg_review_days,
        "submittal_approval_rate": submittal_approval_rate,
        "change_order_count": co_count,
        "change_order_total_value": _cents(co_total_value),
        "change_order_approval_rate": co_approval_rate,
        "punch_list_total": punch_total,
        "punch_list_closed_pct": punch_closed_pct,
        "budget_variance_pct": budget_variance_pct,
        "schedule_on_track_pct": schedule_on_track_pct,
    }


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

async def get_financial_summary(
    db: AsyncSession,
    organization_id: uuid.UUID,
    project_id: Optional[uuid.UUID] = None,
) -> dict:
    """Return financial overview for the org or a single project."""

    # Total contract value from projects
    contract_q = select(func.sum(Project.contract_value)).select_from(Project).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
    )
    if project_id:
        contract_q = contract_q.where(Project.id == project_id)
    total_contract_value = (await db.execute(contract_q)).scalar()

    # Total approved COs
    co_filters = [
        ChangeOrder.organization_id == organization_id,
        ChangeOrder.deleted_at.is_(None),
        ChangeOrder.status == "APPROVED",
        ChangeOrder.total_amount.isnot(None),
    ]
    if project_id:
        co_filters.append(ChangeOrder.project_id == project_id)
    total_approved_cos = (await db.execute(
        select(func.sum(ChangeOrder.total_amount)).select_from(ChangeOrder).where(*co_filters)
    )).scalar()

    # Total paid (sum of net_payment_due from approved pay apps)
    pa_filters = [
        PayApp.organization_id == organization_id,
        PayApp.deleted_at.is_(None),
        PayApp.status == "APPROVED",
        PayApp.net_payment_due.isnot(None),
    ]
    if project_id:
        pa_filters.append(PayApp.project_id == project_id)
    total_paid = (await db.execute(
        select(func.sum(PayApp.net_payment_due)).select_from(PayApp).where(*pa_filters)
    )).scalar()

    # Retention held
    ret_filters = [
        PayApp.organization_id == organization_id,
        PayApp.deleted_at.is_(None),
        PayApp.total_retainage.isnot(None),
    ]
    if project_id:
        ret_filters.append(PayApp.project_id == project_id)
    retention_held = (await db.execute(
        select(func.sum(PayApp.total_retainage)).select_from(PayApp).where(*ret_filters)
    )).scalar()

    # Budget aggregates (BudgetLineItem has no org_id, join through Project)
    budget_q = select(
        func.sum(BudgetLineItem.original_amount).label("original"),
        func.sum(BudgetLineItem.committed).label("committed"),
        func.sum(BudgetLineItem.actuals).label("actuals"),
    ).select_from(BudgetLineItem).join(
        Project, BudgetLineItem.project_id == Project.id
    ).where(
        Project.organization_id == organization_id,
        Project.deleted_at.is_(None),
        BudgetLineItem.deleted_at.is_(None),
    )
    if project_id:
        budget_q = budget_q.where(BudgetLineItem.project_id == project_id)
    budget_row = (await db.execute(budget_q)).first()

    return {
        "total_contract_value": _cents(total_contract_value),
        "total_approved_cos": _cents(total_approved_cos),
        "total_paid": _cents(total_paid),
        "budget_original": _cents(budget_row.original if budget_row else None),
        "budget_committed": _cents(budget_row.committed if budget_row else None),
        "budget_actuals": _cents(budget_row.actuals if budget_row else None),
        "retention_held": _cents(retention_held),
    }


# ============================================================
# ACTIVITY TIMELINE
# ============================================================

async def get_activity_timeline(
    db: AsyncSession,
    organization_id: uuid.UUID,
    days: int = 30,
) -> list:
    """Return daily event counts for the last N days from event_logs."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    q = (
        select(
            func.date(EventLog.created_at).label("day"),
            func.count().label("count"),
        )
        .select_from(EventLog)
        .where(
            EventLog.organization_id == organization_id,
            EventLog.created_at >= cutoff,
        )
        .group_by(func.date(EventLog.created_at))
        .order_by(func.date(EventLog.created_at))
    )
    result = await db.execute(q)
    rows = result.all()

    return [{"date": str(row.day), "count": row.count} for row in rows]


# ============================================================
# TOOL USAGE STATS
# ============================================================

async def get_tool_usage_stats(db: AsyncSession, organization_id: uuid.UUID) -> dict:
    """Count records per tool for the org."""

    async def _count(model, extra_filters=None):
        filters = [model.organization_id == organization_id]
        # Add deleted_at filter for models that support soft delete
        if hasattr(model, "deleted_at"):
            filters.append(model.deleted_at.is_(None))
        if extra_filters:
            filters.extend(extra_filters)
        result = await db.execute(
            select(func.count()).select_from(model).where(*filters)
        )
        return result.scalar() or 0

    return {
        "daily_logs": await _count(DailyLog),
        "rfis": await _count(RFI),
        "submittals": await _count(Submittal),
        "transmittals": await _count(Transmittal),
        "change_orders": await _count(ChangeOrder),
        "punch_list_items": await _count(PunchListItem),
        "inspections": await _count(Inspection),
        "pay_apps": await _count(PayApp),
        "bid_packages": await _count(BidPackage),
        "schedule_tasks": await _count(ScheduleTask),
        "drawings": await _count(Drawing),
        "meetings": await _count(Meeting),
        "todos": await _count(Todo),
        "procurement_items": await _count(ProcurementItem),
        "documents": await _count(Document),
    }
