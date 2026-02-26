import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfi import RFI
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.rfi import RfiCreate, RfiUpdate, RfiResponseCreate
from app.services.numbering_service import format_number, get_next_number


async def create_rfi(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: RfiCreate,
) -> RFI:
    number = await get_next_number(db, project_id, "rfi")

    rfi = RFI(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        subject=data.subject,
        question=data.question,
        assigned_to=data.assigned_to,
        due_date=datetime.combine(data.due_date, datetime.min.time()) if data.due_date else None,
        priority=data.priority,
        cost_impact=data.cost_impact or False,
        schedule_impact=data.schedule_impact or False,
        status="OPEN",
    )
    db.add(rfi)

    # Notify assigned user
    if data.assigned_to:
        notification = Notification(
            user_type="GC_USER",
            user_id=data.assigned_to,
            type="rfi_assigned",
            title=f"New {format_number('rfi', number)}: {data.subject}",
            body=f"You have been assigned to respond to this RFI.",
            source_type="rfi",
            source_id=rfi.id,
        )
        db.add(notification)

    # Event log
    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="rfi_created",
        event_data={"rfi_number": number, "subject": data.subject},
    )
    db.add(event)

    await db.flush()
    return rfi


async def list_rfis(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: uuid.UUID | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[RFI], int]:
    query = select(RFI).where(RFI.project_id == project_id)

    if status:
        query = query.where(RFI.status == status)
    if priority:
        query = query.where(RFI.priority == priority)
    if assigned_to:
        query = query.where(RFI.assigned_to == assigned_to)
    if search:
        query = query.where(
            or_(
                RFI.subject.ilike(f"%{search}%"),
                RFI.question.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(RFI, sort, RFI.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_rfi(
    db: AsyncSession,
    rfi_id: uuid.UUID,
    project_id: uuid.UUID,
) -> RFI:
    result = await db.execute(
        select(RFI).where(
            RFI.id == rfi_id,
            RFI.project_id == project_id,
        )
    )
    rfi = result.scalar_one_or_none()
    if not rfi:
        raise HTTPException(404, "RFI not found")
    return rfi


async def update_rfi(
    db: AsyncSession,
    rfi_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: RfiUpdate,
) -> RFI:
    rfi = await get_rfi(db, rfi_id, project_id)
    if rfi.status == "CLOSED":
        raise HTTPException(400, "Cannot edit a closed RFI")

    update_data = data.model_dump(exclude_unset=True)

    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = datetime.combine(
            update_data["due_date"], datetime.min.time()
        )

    for key, value in update_data.items():
        if hasattr(rfi, key):
            setattr(rfi, key, value)

    await db.flush()
    return rfi


async def respond_to_rfi(
    db: AsyncSession,
    rfi_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: RfiResponseCreate,
) -> RFI:
    """Submit official response. OPEN → RESPONDED."""
    rfi = await get_rfi(db, rfi_id, project_id)
    if rfi.status == "CLOSED":
        raise HTTPException(400, "Cannot respond to a closed RFI")

    rfi.official_response = data.response
    rfi.responded_by = user["user_id"]
    rfi.responded_at = datetime.utcnow()
    rfi.status = "RESPONDED"

    # Notify creator
    notification = Notification(
        user_type="GC_USER",
        user_id=rfi.created_by,
        type="rfi_response",
        title=f"{format_number('rfi', rfi.number)} has been answered",
        body="Your RFI has received an official response.",
        source_type="rfi",
        source_id=rfi.id,
    )
    db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="rfi_responded",
        event_data={"rfi_number": rfi.number},
    )
    db.add(event)

    await db.flush()
    return rfi


async def close_rfi(
    db: AsyncSession,
    rfi_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> RFI:
    """RESPONDED|OPEN → CLOSED."""
    rfi = await get_rfi(db, rfi_id, project_id)
    if rfi.status not in ("RESPONDED", "OPEN"):
        raise HTTPException(400, "RFI must be open or responded to close")
    rfi.status = "CLOSED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="rfi_closed",
        event_data={"rfi_number": rfi.number},
    )
    db.add(event)

    await db.flush()
    return rfi


async def reopen_rfi(
    db: AsyncSession,
    rfi_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> RFI:
    """CLOSED → OPEN."""
    rfi = await get_rfi(db, rfi_id, project_id)
    if rfi.status != "CLOSED":
        raise HTTPException(400, "Only closed RFIs can be reopened")
    rfi.status = "OPEN"
    rfi.official_response = None
    rfi.responded_by = None
    rfi.responded_at = None

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="rfi_reopened",
        event_data={"rfi_number": rfi.number},
    )
    db.add(event)

    await db.flush()
    return rfi


def format_rfi_response(
    rfi: RFI,
    created_by_name: str | None = None,
    assigned_to_name: str | None = None,
    responded_by_name: str | None = None,
    comments_count: int = 0,
) -> dict:
    """Convert RFI ORM model to response dict."""
    days_open = None
    if rfi.status != "CLOSED" and rfi.created_at:
        days_open = (datetime.utcnow() - rfi.created_at).days

    due_date = rfi.due_date
    if hasattr(due_date, "date") and due_date:
        due_date = due_date.date()

    return {
        "id": rfi.id,
        "project_id": rfi.project_id,
        "number": rfi.number,
        "formatted_number": format_number("rfi", rfi.number),
        "subject": rfi.subject,
        "question": rfi.question,
        "official_response": rfi.official_response,
        "status": rfi.status,
        "priority": rfi.priority,
        "assigned_to": rfi.assigned_to,
        "assigned_to_name": assigned_to_name,
        "due_date": due_date,
        "days_open": days_open,
        "cost_impact": rfi.cost_impact,
        "schedule_impact": rfi.schedule_impact,
        "drawing_reference": None,
        "spec_section": None,
        "location": None,
        "created_by": rfi.created_by,
        "created_by_name": created_by_name,
        "responded_by": rfi.responded_by,
        "responded_by_name": responded_by_name,
        "responded_at": rfi.responded_at,
        "created_at": rfi.created_at,
        "updated_at": rfi.updated_at,
        "comments_count": comments_count,
    }
