"""Transmittal service — CRUD + send/confirm workflow."""
import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transmittal import Transmittal
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.transmittal import TransmittalCreate, TransmittalUpdate
from app.services.numbering_service import format_number, get_next_number


async def create_transmittal(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: TransmittalCreate,
) -> Transmittal:
    number = await get_next_number(db, project_id, "transmittal")

    transmittal = Transmittal(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        subject=data.subject,
        description=data.description,
        to_company=data.to_company,
        to_contact=data.to_contact,
        to_email=data.to_email,
        from_company=data.from_company,
        from_contact=data.from_contact,
        purpose=data.purpose,
        items=[item.model_dump() for item in data.items],
        due_date=datetime.combine(data.due_date, datetime.min.time()) if data.due_date else None,
        sent_via=data.sent_via,
        status="DRAFT",
    )
    db.add(transmittal)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="transmittal_created",
        event_data={"transmittal_number": number, "subject": data.subject},
    )
    db.add(event)

    await db.flush()
    return transmittal


async def list_transmittals(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    purpose: str | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[Transmittal], int]:
    query = select(Transmittal).where(
        Transmittal.project_id == project_id,
        Transmittal.deleted_at.is_(None),
    )

    if status:
        query = query.where(Transmittal.status == status)
    if purpose:
        query = query.where(Transmittal.purpose == purpose)
    if search:
        query = query.where(
            or_(
                Transmittal.subject.ilike(f"%{search}%"),
                Transmittal.to_company.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Transmittal, sort, Transmittal.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_transmittal(
    db: AsyncSession,
    transmittal_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Transmittal:
    result = await db.execute(
        select(Transmittal).where(
            Transmittal.id == transmittal_id,
            Transmittal.project_id == project_id,
            Transmittal.deleted_at.is_(None),
        )
    )
    transmittal = result.scalar_one_or_none()
    if not transmittal:
        raise HTTPException(404, "Transmittal not found")
    return transmittal


async def update_transmittal(
    db: AsyncSession,
    transmittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: TransmittalUpdate,
) -> Transmittal:
    transmittal = await get_transmittal(db, transmittal_id, project_id)
    if transmittal.status != "DRAFT":
        raise HTTPException(400, "Can only edit transmittals in DRAFT status")

    update_data = data.model_dump(exclude_unset=True)

    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = datetime.combine(update_data["due_date"], datetime.min.time())

    if "items" in update_data and update_data["items"] is not None:
        update_data["items"] = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in update_data["items"]
        ]

    for key, value in update_data.items():
        if hasattr(transmittal, key):
            setattr(transmittal, key, value)

    await db.flush()
    return transmittal


async def send_transmittal(
    db: AsyncSession,
    transmittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Transmittal:
    """DRAFT → SENT."""
    transmittal = await get_transmittal(db, transmittal_id, project_id)
    if transmittal.status != "DRAFT":
        raise HTTPException(400, "Only DRAFT transmittals can be sent")

    transmittal.status = "SENT"
    transmittal.sent_at = datetime.utcnow()

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="transmittal_sent",
        event_data={"transmittal_number": transmittal.number},
    )
    db.add(event)

    await db.flush()
    return transmittal


async def confirm_transmittal(
    db: AsyncSession,
    transmittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Transmittal:
    """SENT → RECEIVED."""
    transmittal = await get_transmittal(db, transmittal_id, project_id)
    if transmittal.status != "SENT":
        raise HTTPException(400, "Only SENT transmittals can be confirmed as received")

    transmittal.status = "RECEIVED"
    transmittal.received_at = datetime.utcnow()

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="transmittal_received",
        event_data={"transmittal_number": transmittal.number},
    )
    db.add(event)

    await db.flush()
    return transmittal


def format_transmittal_response(
    transmittal: Transmittal,
    created_by_name: str | None = None,
    comments_count: int = 0,
) -> dict:
    """Convert Transmittal ORM model to response dict."""
    due_date = transmittal.due_date
    if hasattr(due_date, "date") and due_date:
        due_date = due_date.date()

    return {
        "id": transmittal.id,
        "project_id": transmittal.project_id,
        "number": transmittal.number,
        "formatted_number": format_number("transmittal", transmittal.number),
        "subject": transmittal.subject,
        "to_company": transmittal.to_company,
        "to_contact": transmittal.to_contact,
        "to_email": getattr(transmittal, "to_email", None),
        "from_company": transmittal.from_company,
        "from_contact": transmittal.from_contact,
        "purpose": transmittal.purpose,
        "description": transmittal.description,
        "status": transmittal.status,
        "items": transmittal.items or [],
        "sent_via": transmittal.sent_via,
        "sent_at": transmittal.sent_at,
        "received_at": transmittal.received_at,
        "due_date": due_date,
        "comments_count": comments_count,
        "created_by": transmittal.created_by,
        "created_by_name": created_by_name,
        "created_at": transmittal.created_at,
        "updated_at": transmittal.updated_at,
    }
