"""Change Order service — three-party workflow (GC ↔ Sub ↔ Owner).

PCO (Potential Change Order) → pricing → submit to owner → CO (approved).
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
from app.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderUpdate,
    SubPricingSubmit,
)
from app.services.numbering_service import format_change_order_number, get_next_number


def _cents(val) -> int:
    if val is None:
        return 0
    return int(Decimal(str(val)) * 100)


def _dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


async def create_change_order(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: ChangeOrderCreate,
) -> ChangeOrder:
    number = await get_next_number(db, project_id, "change_order")

    co = ChangeOrder(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        title=data.title,
        description=data.description,
        reason=data.reason,
        cost_code_id=data.cost_code_id,
        total_amount=_dollars(data.amount),
        gc_amount=_dollars(data.amount),
        schedule_impact_days=data.schedule_impact_days,
        priority=data.priority,
        drawing_reference=data.drawing_reference,
        spec_section=data.spec_section,
        status="DRAFT",
    )
    db.add(co)
    await db.flush()

    # Request pricing from subs
    if data.sub_company_ids:
        sub_pricings = []
        for sub_id in data.sub_company_ids:
            sub_pricings.append({
                "sub_company_id": str(sub_id),
                "sub_company_name": None,
                "amount": None,
                "description": None,
                "schedule_impact_days": 0,
                "status": "REQUESTED",
                "submitted_at": None,
            })

            notification = Notification(
                user_type="SUB_USER",
                user_id=sub_id,
                type="co_pricing_requested",
                title=f"Pricing requested: {data.title}",
                body=f"Please submit pricing for this change order.",
                source_type="change_order",
                source_id=co.id,
            )
            db.add(notification)

        co.sub_pricings = sub_pricings
        co.status = "PRICING_REQUESTED"

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="change_order_created",
        event_data={"number": number, "title": data.title},
    )
    db.add(event)

    await db.flush()
    return co


async def list_change_orders(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    reason: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[ChangeOrder], int]:
    query = select(ChangeOrder).where(
        ChangeOrder.project_id == project_id,
        ChangeOrder.deleted_at.is_(None),
    )

    if status:
        query = query.where(ChangeOrder.status == status)
    if reason:
        query = query.where(ChangeOrder.reason == reason)
    if priority:
        query = query.where(ChangeOrder.priority == priority)
    if search:
        query = query.where(
            or_(
                ChangeOrder.title.ilike(f"%{search}%"),
                ChangeOrder.description.ilike(f"%{search}%"),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    sort_col = getattr(ChangeOrder, sort, ChangeOrder.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_change_order(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ChangeOrder:
    result = await db.execute(
        select(ChangeOrder).where(
            ChangeOrder.id == co_id,
            ChangeOrder.project_id == project_id,
            ChangeOrder.deleted_at.is_(None),
        )
    )
    co = result.scalar_one_or_none()
    if not co:
        raise HTTPException(404, "Change order not found")
    return co


async def update_change_order(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: ChangeOrderUpdate,
) -> ChangeOrder:
    co = await get_change_order(db, co_id, project_id)
    if co.status in ("APPROVED", "REJECTED"):
        raise HTTPException(400, "Cannot edit a finalized change order")

    update_data = data.model_dump(exclude_unset=True)

    if "amount" in update_data:
        co.total_amount = _dollars(update_data.pop("amount"))
    if "gc_amount" in update_data:
        co.gc_amount = _dollars(update_data.pop("gc_amount"))
    if "markup_percent" in update_data:
        pct = update_data.pop("markup_percent")
        co.markup_percent = Decimal(str(pct)) if pct is not None else None
        if co.markup_percent and co.total_amount:
            co.markup_amount = co.total_amount * co.markup_percent / 100
            co.gc_amount = co.total_amount + co.markup_amount

    for key, value in update_data.items():
        if hasattr(co, key):
            setattr(co, key, value)

    await db.flush()
    return co


async def submit_sub_pricing(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
    sub_company_id: uuid.UUID,
    data: SubPricingSubmit,
) -> ChangeOrder:
    co = await get_change_order(db, co_id, project_id)

    pricings = co.sub_pricings or []
    found = False
    all_submitted = True

    for p in pricings:
        if p.get("sub_company_id") == str(sub_company_id):
            if p.get("status") != "REQUESTED":
                raise HTTPException(400, "Pricing already submitted")
            p["amount"] = data.amount
            p["description"] = data.description
            p["schedule_impact_days"] = data.schedule_impact_days
            p["status"] = "SUBMITTED"
            p["submitted_at"] = datetime.now(timezone.utc).isoformat()
            found = True
        if p.get("status") == "REQUESTED":
            all_submitted = False

    if not found:
        raise HTTPException(404, "Pricing request not found for this sub")

    co.sub_pricings = pricings

    if all_submitted:
        co.status = "PRICING_COMPLETE"

    event = EventLog(
        organization_id=co.organization_id,
        project_id=project_id,
        user_type="SUB_USER",
        user_id=sub_company_id,
        event_type="co_pricing_submitted",
        event_data={"co_number": co.number, "amount_cents": data.amount},
    )
    db.add(event)

    await db.flush()
    return co


async def submit_to_owner(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> ChangeOrder:
    co = await get_change_order(db, co_id, project_id)
    if co.status not in ("DRAFT", "PRICING_COMPLETE", "PRICING_REQUESTED"):
        raise HTTPException(400, "Change order cannot be submitted to owner in current state")

    co.status = "SUBMITTED_TO_OWNER"
    co.submitted_to_owner_at = datetime.now(timezone.utc)

    event = EventLog(
        organization_id=co.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="co_submitted_to_owner",
        event_data={"co_number": co.number},
    )
    db.add(event)

    await db.flush()
    return co


async def owner_decision(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    decision: str,
    notes: str | None = None,
) -> ChangeOrder:
    co = await get_change_order(db, co_id, project_id)
    if co.status != "SUBMITTED_TO_OWNER":
        raise HTTPException(400, "Change order must be submitted to owner for a decision")

    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(400, "Decision must be APPROVED or REJECTED")

    co.owner_decision = decision
    co.owner_decision_by = user["user_id"]
    co.owner_decision_at = datetime.now(timezone.utc)
    co.owner_decision_notes = notes

    if decision == "APPROVED":
        co.status = "APPROVED"
        co.order_type = "CO"
    else:
        co.status = "REJECTED"

    event = EventLog(
        organization_id=co.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "OWNER_USER"),
        user_id=user["user_id"],
        event_type=f"co_{decision.lower()}",
        event_data={"co_number": co.number},
    )
    db.add(event)

    # Notify GC creator
    notification = Notification(
        user_type="GC_USER",
        user_id=co.created_by,
        type=f"co_{decision.lower()}",
        title=f"{format_change_order_number(co.number, decision == 'APPROVED')} {decision.lower()} by owner",
        body=notes or f"Change order has been {decision.lower()}.",
        source_type="change_order",
        source_id=co.id,
    )
    db.add(notification)

    await db.flush()
    return co


async def delete_change_order(
    db: AsyncSession,
    co_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    co = await get_change_order(db, co_id, project_id)
    if co.status == "APPROVED":
        raise HTTPException(400, "Cannot delete an approved change order")
    co.deleted_at = datetime.now(timezone.utc)
    await db.flush()


def format_change_order_response(co: ChangeOrder) -> dict:
    is_approved = co.status == "APPROVED"
    formatted = format_change_order_number(co.number, is_approved)

    sub_pricings = []
    for p in (co.sub_pricings or []):
        sub_pricings.append({
            "sub_company_id": p.get("sub_company_id"),
            "sub_company_name": p.get("sub_company_name"),
            "amount": p.get("amount"),
            "description": p.get("description"),
            "schedule_impact_days": p.get("schedule_impact_days", 0),
            "status": p.get("status", "REQUESTED"),
            "submitted_at": p.get("submitted_at"),
        })

    return {
        "id": co.id,
        "project_id": co.project_id,
        "number": co.number,
        "formatted_number": formatted,
        "title": co.title,
        "description": co.description,
        "reason": co.reason,
        "status": co.status,
        "order_type": co.order_type,
        "cost_code_id": co.cost_code_id,
        "cost_code": None,
        "amount": _cents(co.total_amount),
        "markup_percent": float(co.markup_percent) if co.markup_percent else None,
        "markup_amount": _cents(co.markup_amount),
        "gc_amount": _cents(co.gc_amount),
        "schedule_impact_days": co.schedule_impact_days or 0,
        "sub_pricings": sub_pricings,
        "created_by": co.created_by,
        "created_by_name": None,
        "submitted_to_owner_at": co.submitted_to_owner_at,
        "owner_decision": co.owner_decision,
        "owner_decision_by": co.owner_decision_by,
        "owner_decision_at": co.owner_decision_at,
        "owner_decision_notes": co.owner_decision_notes,
        "priority": co.priority,
        "drawing_reference": co.drawing_reference,
        "spec_section": co.spec_section,
        "comments_count": 0,
        "created_at": co.created_at,
        "updated_at": co.updated_at,
    }
