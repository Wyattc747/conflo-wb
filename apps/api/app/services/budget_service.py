"""Budget management service.

All amounts stored as Decimal(15,2) in DB (dollars).
API layer converts to/from integer cents at the boundary.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget_line_item import BudgetLineItem
from app.models.change_order import ChangeOrder
from app.models.event_log import EventLog
from app.models.pay_app import PayApp
from app.schemas.budget import (
    BudgetLineItemCreate,
    BudgetLineItemResponse,
    BudgetLineItemUpdate,
    BudgetSummaryResponse,
)


def _cents(decimal_val) -> int:
    """Convert Decimal dollars to integer cents."""
    if decimal_val is None:
        return 0
    return int(Decimal(str(decimal_val)) * 100)


def _dollars(cents: int) -> Decimal:
    """Convert integer cents to Decimal dollars."""
    return Decimal(cents) / 100


async def get_budget_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> BudgetSummaryResponse:
    """Calculate complete budget summary with derived values."""
    result = await db.execute(
        select(BudgetLineItem)
        .where(
            BudgetLineItem.project_id == project_id,
            BudgetLineItem.deleted_at.is_(None),
        )
        .order_by(BudgetLineItem.cost_code)
    )
    items = result.scalars().all()

    # Get billed amounts per budget line from approved pay apps
    billed_map = await _get_billed_by_line(db, project_id)

    enriched = []
    for item in items:
        original = _cents(item.original_amount)
        changes = _cents(item.approved_changes)
        revised = original + changes
        billed = billed_map.get(str(item.id), 0)
        remaining = revised - billed
        pct = round(billed / revised * 100, 2) if revised > 0 else 0.0

        enriched.append(BudgetLineItemResponse(
            id=item.id,
            project_id=project_id,
            cost_code=item.cost_code,
            description=item.description,
            original_amount=original,
            approved_changes=changes,
            revised_amount=revised,
            billed_to_date=billed,
            remaining=remaining,
            percent_complete=pct,
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ))

    total_original = sum(i.original_amount for i in enriched)
    total_changes = sum(i.approved_changes for i in enriched)
    total_revised = sum(i.revised_amount for i in enriched)
    total_billed = sum(i.billed_to_date for i in enriched)
    total_remaining = total_revised - total_billed
    total_pct = round(total_billed / total_revised * 100, 2) if total_revised > 0 else 0.0

    # Pending COs
    pending_result = await db.execute(
        select(
            func.count(ChangeOrder.id),
            func.coalesce(func.sum(ChangeOrder.gc_amount), Decimal("0")),
        ).where(
            ChangeOrder.project_id == project_id,
            ChangeOrder.status.in_(["DRAFT", "PRICING_REQUESTED", "PRICING_COMPLETE", "SUBMITTED_TO_OWNER"]),
            ChangeOrder.deleted_at.is_(None),
        )
    )
    row = pending_result.one()
    pending_count = row[0] or 0
    pending_amount = _cents(row[1])

    return BudgetSummaryResponse(
        original_contract=total_original,
        approved_changes=total_changes,
        revised_contract=total_revised,
        billed_to_date=total_billed,
        remaining=total_remaining,
        percent_complete=total_pct,
        line_items=enriched,
        change_orders_pending=pending_count,
        change_orders_pending_amount=pending_amount,
    )


async def _get_billed_by_line(
    db: AsyncSession, project_id: uuid.UUID
) -> dict[str, int]:
    """Sum billed amounts from approved pay app SOV data, keyed by budget_line_item_id."""
    result = await db.execute(
        select(PayApp.sov_data).where(
            PayApp.project_id == project_id,
            PayApp.status == "APPROVED",
            PayApp.deleted_at.is_(None),
        )
    )
    billed: dict[str, int] = {}
    for (sov_data,) in result:
        if not sov_data:
            continue
        for line in sov_data:
            bli_id = line.get("budget_line_item_id")
            if bli_id:
                current = line.get("current_amount", 0)
                materials = line.get("materials_stored", 0)
                billed[bli_id] = billed.get(bli_id, 0) + current + materials
    return billed


async def create_budget_line_item(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: BudgetLineItemCreate,
) -> BudgetLineItem:
    item = BudgetLineItem(
        project_id=project_id,
        cost_code=data.cost_code,
        description=data.description,
        original_amount=_dollars(data.original_amount),
        notes=data.notes,
    )
    db.add(item)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="budget_line_item_created",
        event_data={"cost_code": data.cost_code, "amount_cents": data.original_amount},
    )
    db.add(event)

    await db.flush()
    return item


async def get_budget_line_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
) -> BudgetLineItem:
    result = await db.execute(
        select(BudgetLineItem).where(
            BudgetLineItem.id == item_id,
            BudgetLineItem.project_id == project_id,
            BudgetLineItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Budget line item not found")
    return item


async def update_budget_line_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    data: BudgetLineItemUpdate,
) -> BudgetLineItem:
    item = await get_budget_line_item(db, item_id, project_id)

    if data.description is not None:
        item.description = data.description
    if data.original_amount is not None:
        item.original_amount = _dollars(data.original_amount)
    if data.notes is not None:
        item.notes = data.notes

    await db.flush()
    return item


async def delete_budget_line_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    item = await get_budget_line_item(db, item_id, project_id)
    item.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def bulk_import_line_items(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    items: list[dict],
) -> list[BudgetLineItem]:
    """Import multiple line items from CSV data."""
    created = []
    for row in items:
        item = BudgetLineItem(
            project_id=project_id,
            cost_code=row["cost_code"],
            description=row["description"],
            original_amount=_dollars(row["amount"]),
        )
        db.add(item)
        created.append(item)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="budget_imported",
        event_data={"count": len(created)},
    )
    db.add(event)

    await db.flush()
    return created


def format_budget_line_item_response(
    item: BudgetLineItem,
    billed_cents: int = 0,
) -> dict:
    """Format a single line item for API response."""
    original = _cents(item.original_amount)
    changes = _cents(item.approved_changes)
    revised = original + changes
    remaining = revised - billed_cents
    pct = round(billed_cents / revised * 100, 2) if revised > 0 else 0.0

    return {
        "id": item.id,
        "project_id": item.project_id,
        "cost_code": item.cost_code,
        "description": item.description,
        "original_amount": original,
        "approved_changes": changes,
        "revised_amount": revised,
        "billed_to_date": billed_cents,
        "remaining": remaining,
        "percent_complete": pct,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
