"""Punch List service — CRUD + complete/verify/dispute workflow."""
import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.punch_list_item import PunchListItem
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.punch_list import (
    PunchListItemCreate,
    PunchListItemUpdate,
    PunchListCompleteRequest,
    PunchListVerifyRequest,
)
from app.services.numbering_service import format_number, get_next_number


async def create_punch_item(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: PunchListItemCreate,
) -> PunchListItem:
    number = await get_next_number(db, project_id, "punch_list_item")

    item = PunchListItem(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        title=data.title,
        description=data.description,
        location=data.location,
        category=data.category,
        priority=data.priority,
        assigned_sub_company_id=data.assigned_to_sub_id,
        assigned_to_user_id=data.assigned_to_user_id,
        due_date=datetime.combine(data.due_date, datetime.min.time()) if data.due_date else None,
        cost_code_id=data.cost_code_id,
        drawing_reference=data.drawing_reference,
        status="OPEN",
    )
    db.add(item)

    if data.assigned_to_sub_id:
        notification = Notification(
            user_type="SUB_USER",
            user_id=data.assigned_to_sub_id,
            type="punch_assigned",
            title=f"New punch item {format_number('punch_list_item', number)}: {data.title}",
            body=f"You have been assigned a punch list item: {data.title}",
            source_type="punch_list_item",
            source_id=item.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="punch_item_created",
        event_data={"punch_number": number, "title": data.title},
    )
    db.add(event)

    await db.flush()
    return item


async def list_punch_items(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    assigned_sub_id: uuid.UUID | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[PunchListItem], int]:
    query = select(PunchListItem).where(
        PunchListItem.project_id == project_id,
        PunchListItem.deleted_at.is_(None),
    )

    if status:
        query = query.where(PunchListItem.status == status)
    if priority:
        query = query.where(PunchListItem.priority == priority)
    if category:
        query = query.where(PunchListItem.category == category)
    if assigned_sub_id:
        query = query.where(PunchListItem.assigned_sub_company_id == assigned_sub_id)
    if search:
        query = query.where(
            or_(
                PunchListItem.title.ilike(f"%{search}%"),
                PunchListItem.location.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(PunchListItem, sort, PunchListItem.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
) -> PunchListItem:
    result = await db.execute(
        select(PunchListItem).where(
            PunchListItem.id == item_id,
            PunchListItem.project_id == project_id,
            PunchListItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Punch list item not found")
    return item


async def update_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: PunchListItemUpdate,
) -> PunchListItem:
    item = await get_punch_item(db, item_id, project_id)
    if item.status in ("VERIFIED", "CLOSED"):
        raise HTTPException(400, "Cannot edit verified or closed items")

    update_data = data.model_dump(exclude_unset=True)
    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = datetime.combine(update_data["due_date"], datetime.min.time())
    if "assigned_to_sub_id" in update_data:
        update_data["assigned_sub_company_id"] = update_data.pop("assigned_to_sub_id")

    for key, value in update_data.items():
        if hasattr(item, key):
            setattr(item, key, value)

    await db.flush()
    return item


async def complete_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: PunchListCompleteRequest,
) -> PunchListItem:
    """Sub marks as completed with notes + after photos."""
    item = await get_punch_item(db, item_id, project_id)
    if item.status not in ("OPEN", "IN_PROGRESS"):
        raise HTTPException(400, "Item must be open or in progress to complete")

    item.status = "COMPLETED"
    item.completion_notes = data.completion_notes
    item.completed_by = user["user_id"]
    item.completed_at = datetime.utcnow()

    notification = Notification(
        user_type="GC_USER",
        user_id=item.created_by,
        type="punch_completed",
        title=f"{format_number('punch_list_item', item.number)} marked complete — verify",
        body=f"Punch item '{item.title}' has been marked as completed.",
        source_type="punch_list_item",
        source_id=item.id,
    )
    db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "SUB_USER"),
        user_id=user["user_id"],
        event_type="punch_item_completed",
        event_data={"punch_number": item.number},
    )
    db.add(event)

    await db.flush()
    return item


async def verify_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: PunchListVerifyRequest,
) -> PunchListItem:
    """GC verifies completion. Pass or reopen."""
    item = await get_punch_item(db, item_id, project_id)
    if item.status != "COMPLETED":
        raise HTTPException(400, "Item must be completed before verification")

    item.verified_by = user["user_id"]
    item.verified_at = datetime.utcnow()
    item.verification_notes = data.verification_notes

    if data.verified:
        item.status = "VERIFIED"
        event_type = "punch_item_verified"
    else:
        item.status = "OPEN"  # Reopen
        item.completed_at = None
        item.completed_by = None
        item.completion_notes = None
        event_type = "punch_item_rejected"

    if item.assigned_sub_company_id:
        notification = Notification(
            user_type="SUB_USER",
            user_id=item.assigned_sub_company_id,
            type=event_type,
            title=f"{format_number('punch_list_item', item.number)}: {'Verified' if data.verified else 'Reopened'}",
            body=data.verification_notes or f"Punch item has been {'verified' if data.verified else 'reopened'}.",
            source_type="punch_list_item",
            source_id=item.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type=event_type,
        event_data={"punch_number": item.number, "verified": data.verified},
    )
    db.add(event)

    await db.flush()
    return item


async def close_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> PunchListItem:
    """VERIFIED → CLOSED."""
    item = await get_punch_item(db, item_id, project_id)
    if item.status != "VERIFIED":
        raise HTTPException(400, "Only verified items can be closed")

    item.status = "CLOSED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="punch_item_closed",
        event_data={"punch_number": item.number},
    )
    db.add(event)

    await db.flush()
    return item


async def dispute_punch_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> PunchListItem:
    """Sub disputes an item."""
    item = await get_punch_item(db, item_id, project_id)
    if item.status in ("VERIFIED", "CLOSED"):
        raise HTTPException(400, "Cannot dispute verified or closed items")

    item.status = "DISPUTED"

    notification = Notification(
        user_type="GC_USER",
        user_id=item.created_by,
        type="punch_disputed",
        title=f"{format_number('punch_list_item', item.number)} disputed by sub",
        body=f"Punch item '{item.title}' has been disputed.",
        source_type="punch_list_item",
        source_id=item.id,
    )
    db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "SUB_USER"),
        user_id=user["user_id"],
        event_type="punch_item_disputed",
        event_data={"punch_number": item.number},
    )
    db.add(event)

    await db.flush()
    return item


def format_punch_item_response(
    item: PunchListItem,
    created_by_name: str | None = None,
    assigned_to_sub_name: str | None = None,
    assigned_to_user_name: str | None = None,
    comments_count: int = 0,
) -> dict:
    """Convert PunchListItem ORM model to response dict."""
    due_date = item.due_date
    if hasattr(due_date, "date") and due_date:
        due_date = due_date.date()

    return {
        "id": item.id,
        "project_id": item.project_id,
        "number": item.number,
        "formatted_number": format_number("punch_list_item", item.number),
        "title": item.title,
        "description": item.description,
        "location": item.location,
        "category": item.category,
        "priority": item.priority,
        "status": item.status,
        "assigned_to_sub_id": item.assigned_sub_company_id,
        "assigned_to_sub_name": assigned_to_sub_name,
        "assigned_to_user_id": item.assigned_to_user_id,
        "assigned_to_user_name": assigned_to_user_name,
        "due_date": due_date,
        "cost_code_id": item.cost_code_id,
        "drawing_reference": item.drawing_reference,
        "before_photo_ids": item.before_photo_ids or [],
        "after_photo_ids": item.after_photo_ids or [],
        "verification_photo_ids": getattr(item, "verification_photo_ids", []) or [],
        "completion_notes": item.completion_notes,
        "completed_by": item.completed_by,
        "completed_at": item.completed_at,
        "verification_notes": item.verification_notes,
        "verified_by": item.verified_by,
        "verified_at": item.verified_at,
        "comments_count": comments_count,
        "created_by": item.created_by,
        "created_by_name": created_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
