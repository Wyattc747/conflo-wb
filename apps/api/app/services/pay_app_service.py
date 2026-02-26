"""Pay Application service — G702/G703 AIA format.

Handles Sub→GC and GC→Owner pay app flows.
All amounts stored as Decimal(15,2) in DB, converted to cents at API boundary.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.change_order import ChangeOrder
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.models.pay_app import PayApp
from app.schemas.pay_app import PayAppCreate, PayAppLineItemCreate
from app.services.numbering_service import format_number, get_next_number


def _cents(val) -> int:
    if val is None:
        return 0
    return int(Decimal(str(val)) * 100)


def _dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


async def create_pay_app(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: PayAppCreate,
) -> PayApp:
    number = await get_next_number(db, project_id, "pay_app")

    # Build SOV line items
    sov_data = []
    total_scheduled = 0
    total_previous = 0
    total_current = 0
    total_materials = 0

    for li in data.line_items:
        total_scheduled += li.scheduled_value
        total_previous += li.previous_applications
        total_current += li.current_amount
        total_materials += li.materials_stored
        total_completed_line = li.previous_applications + li.current_amount + li.materials_stored

        sov_data.append({
            "budget_line_item_id": str(li.budget_line_item_id) if li.budget_line_item_id else None,
            "description": li.description,
            "scheduled_value": li.scheduled_value,
            "previous_applications": li.previous_applications,
            "current_amount": li.current_amount,
            "materials_stored": li.materials_stored,
            "total_completed": total_completed_line,
        })

    total_completed = total_previous + total_current + total_materials

    # Net change orders (approved COs for this project)
    net_co_cents = await _get_approved_co_total(db, project_id)

    # Retainage
    retainage_cents = int(total_completed * data.retainage_percent / 100)
    earned_less_retainage = total_completed - retainage_cents

    # Previous certificates
    prev_certs = await get_previous_certified_amount(
        db, project_id, data.pay_app_type, data.sub_company_id
    )

    current_due = earned_less_retainage - prev_certs
    balance = total_scheduled + net_co_cents - total_completed

    pay_app = PayApp(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        pay_app_type=data.pay_app_type,
        sub_company_id=data.sub_company_id,
        period_start=datetime.combine(data.period_from, datetime.min.time()),
        period_end=datetime.combine(data.period_to, datetime.min.time()),
        retention_rate=Decimal(str(data.retainage_percent)),
        sov_data=sov_data,
        original_contract_sum=_dollars(total_scheduled),
        net_change_orders=_dollars(net_co_cents),
        contract_sum_to_date=_dollars(total_scheduled + net_co_cents),
        total_completed=_dollars(total_completed),
        total_retainage=_dollars(retainage_cents),
        total_earned_less_retainage=_dollars(earned_less_retainage),
        previous_certificates=_dollars(prev_certs),
        net_payment_due=_dollars(current_due),
        balance_to_finish=_dollars(balance),
        status="DRAFT",
    )
    db.add(pay_app)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="pay_app_created",
        event_data={"number": number, "type": data.pay_app_type},
    )
    db.add(event)

    await db.flush()
    return pay_app


async def list_pay_apps(
    db: AsyncSession,
    project_id: uuid.UUID,
    pay_app_type: str | None = None,
    sub_company_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
) -> tuple[list[PayApp], int]:
    query = select(PayApp).where(
        PayApp.project_id == project_id,
        PayApp.deleted_at.is_(None),
    )

    if pay_app_type:
        query = query.where(PayApp.pay_app_type == pay_app_type)
    if sub_company_id:
        query = query.where(PayApp.sub_company_id == sub_company_id)
    if status:
        query = query.where(PayApp.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(PayApp.number.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_pay_app(
    db: AsyncSession,
    pay_app_id: uuid.UUID,
    project_id: uuid.UUID,
) -> PayApp:
    result = await db.execute(
        select(PayApp).where(
            PayApp.id == pay_app_id,
            PayApp.project_id == project_id,
            PayApp.deleted_at.is_(None),
        )
    )
    pa = result.scalar_one_or_none()
    if not pa:
        raise HTTPException(404, "Pay application not found")
    return pa


async def submit_pay_app(
    db: AsyncSession,
    pay_app_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> PayApp:
    pa = await get_pay_app(db, pay_app_id, project_id)
    if pa.status != "DRAFT":
        raise HTTPException(400, "Only draft pay apps can be submitted")

    pa.status = "SUBMITTED"
    pa.submitted_by_type = user.get("user_type", "GC_USER")
    pa.submitted_by_id = user["user_id"]
    pa.submitted_at = datetime.now(timezone.utc)

    event = EventLog(
        organization_id=pa.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="pay_app_submitted",
        event_data={"number": pa.number, "type": pa.pay_app_type},
    )
    db.add(event)

    await db.flush()
    return pa


async def approve_pay_app(
    db: AsyncSession,
    pay_app_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    notes: str | None = None,
) -> PayApp:
    pa = await get_pay_app(db, pay_app_id, project_id)
    if pa.status not in ("SUBMITTED", "IN_REVIEW"):
        raise HTTPException(400, "Pay app must be submitted or in review to approve")

    pa.status = "APPROVED"
    pa.reviewed_by = user["user_id"]
    pa.reviewed_at = datetime.now(timezone.utc)
    pa.review_notes = notes

    event = EventLog(
        organization_id=pa.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="pay_app_approved",
        event_data={"number": pa.number},
    )
    db.add(event)

    await db.flush()
    return pa


async def reject_pay_app(
    db: AsyncSession,
    pay_app_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    reason: str | None = None,
) -> PayApp:
    pa = await get_pay_app(db, pay_app_id, project_id)
    if pa.status not in ("SUBMITTED", "IN_REVIEW"):
        raise HTTPException(400, "Pay app must be submitted or in review to reject")

    pa.status = "REJECTED"
    pa.reviewed_by = user["user_id"]
    pa.reviewed_at = datetime.now(timezone.utc)
    pa.review_notes = reason

    event = EventLog(
        organization_id=pa.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="pay_app_rejected",
        event_data={"number": pa.number, "reason": reason},
    )
    db.add(event)

    await db.flush()
    return pa


async def get_previous_certified_amount(
    db: AsyncSession,
    project_id: uuid.UUID,
    pay_app_type: str,
    sub_company_id: uuid.UUID | None = None,
) -> int:
    """Sum of net_payment_due (cents) from all previously APPROVED pay apps."""
    query = select(func.coalesce(func.sum(PayApp.net_payment_due), Decimal("0"))).where(
        PayApp.project_id == project_id,
        PayApp.pay_app_type == pay_app_type,
        PayApp.status == "APPROVED",
        PayApp.deleted_at.is_(None),
    )
    if sub_company_id:
        query = query.where(PayApp.sub_company_id == sub_company_id)
    result = await db.execute(query)
    return _cents(result.scalar())


async def _get_approved_co_total(db: AsyncSession, project_id: uuid.UUID) -> int:
    """Sum of approved change order gc_amounts in cents."""
    result = await db.execute(
        select(func.coalesce(func.sum(ChangeOrder.gc_amount), Decimal("0"))).where(
            ChangeOrder.project_id == project_id,
            ChangeOrder.status == "APPROVED",
            ChangeOrder.deleted_at.is_(None),
        )
    )
    return _cents(result.scalar())


def format_pay_app_response(pa: PayApp) -> dict:
    """Convert PayApp ORM to response dict with cents."""
    period_from = pa.period_start
    period_to = pa.period_end
    if hasattr(period_from, "date"):
        period_from = period_from.date()
    if hasattr(period_to, "date"):
        period_to = period_to.date()

    # Build line item responses from sov_data
    line_items = []
    retainage_pct = float(pa.retention_rate or 10)
    for li in (pa.sov_data or []):
        scheduled = li.get("scheduled_value", 0)
        previous = li.get("previous_applications", 0)
        current = li.get("current_amount", 0)
        materials = li.get("materials_stored", 0)
        total = previous + current + materials
        pct = round(total / scheduled * 100, 2) if scheduled > 0 else 0.0
        balance = scheduled - total
        retainage = int(total * retainage_pct / 100)

        line_items.append({
            "budget_line_item_id": li.get("budget_line_item_id"),
            "cost_code": li.get("cost_code"),
            "description": li.get("description", ""),
            "scheduled_value": scheduled,
            "previous_applications": previous,
            "current_amount": current,
            "materials_stored": materials,
            "total_completed": total,
            "percent_complete": pct,
            "balance_to_finish": balance,
            "retainage": retainage,
        })

    return {
        "id": pa.id,
        "project_id": pa.project_id,
        "number": pa.number,
        "formatted_number": format_number("pay_app", pa.number),
        "pay_app_type": pa.pay_app_type,
        "period_from": period_from,
        "period_to": period_to,
        "status": pa.status,
        "original_contract_sum": _cents(pa.original_contract_sum),
        "net_change_orders": _cents(pa.net_change_orders),
        "contract_sum_to_date": _cents(pa.contract_sum_to_date),
        "total_completed_and_stored": _cents(pa.total_completed),
        "retainage_percent": float(pa.retention_rate or 10),
        "retainage_amount": _cents(pa.total_retainage),
        "total_earned_less_retainage": _cents(pa.total_earned_less_retainage),
        "previous_certificates": _cents(pa.previous_certificates),
        "current_payment_due": _cents(pa.net_payment_due),
        "balance_to_finish": _cents(pa.balance_to_finish),
        "sub_company_id": pa.sub_company_id,
        "sub_company_name": None,
        "submitted_by_name": None,
        "submitted_at": pa.submitted_at,
        "reviewed_by_name": None,
        "reviewed_at": pa.reviewed_at,
        "review_notes": pa.review_notes,
        "line_items": line_items,
        "comments_count": 0,
        "created_at": pa.created_at,
        "updated_at": pa.updated_at,
    }
