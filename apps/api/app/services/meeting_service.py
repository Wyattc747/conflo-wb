import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.todo import Todo
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.meeting import MeetingCreate, MeetingUpdate, PublishMinutesRequest
from app.services.numbering_service import format_number, get_next_number


async def create_meeting(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: MeetingCreate,
) -> Meeting:
    number = await get_next_number(db, project_id, "meeting")

    meeting = Meeting(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        title=data.title,
        meeting_type=data.meeting_type,
        scheduled_date=datetime.combine(data.scheduled_date, datetime.min.time()) if data.scheduled_date else None,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        virtual_provider=data.virtual_provider,
        virtual_link=data.virtual_link,
        attendees=data.attendees or [],
        agenda=data.agenda,
        status="SCHEDULED",
        recurring=data.recurring,
        recurrence_rule=data.recurrence_rule,
        recurrence_end_date=data.recurrence_end_date,
    )
    db.add(meeting)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="meeting_created",
        event_data={"meeting_number": number, "title": data.title},
    )
    db.add(event)

    await db.flush()
    return meeting


async def list_meetings(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    meeting_type: str | None = None,
    search: str | None = None,
    sort: str = "scheduled_date",
    order: str = "desc",
) -> tuple[list[Meeting], int]:
    query = select(Meeting).where(Meeting.project_id == project_id, Meeting.deleted_at.is_(None))

    if status:
        query = query.where(Meeting.status == status)
    if meeting_type:
        query = query.where(Meeting.meeting_type == meeting_type)
    if search:
        query = query.where(
            or_(
                Meeting.title.ilike(f"%{search}%"),
                Meeting.agenda.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Meeting, sort, Meeting.scheduled_date)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Meeting:
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.project_id == project_id,
            Meeting.deleted_at.is_(None),
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


async def update_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: MeetingUpdate,
) -> Meeting:
    meeting = await get_meeting(db, meeting_id, project_id)
    if meeting.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(400, "Cannot edit a completed or cancelled meeting")

    update_data = data.model_dump(exclude_unset=True)
    if "scheduled_date" in update_data and update_data["scheduled_date"]:
        update_data["scheduled_date"] = datetime.combine(
            update_data["scheduled_date"], datetime.min.time()
        )
    # Convert action_items from Pydantic models to dicts
    if "action_items" in update_data and update_data["action_items"] is not None:
        update_data["action_items"] = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in update_data["action_items"]
        ]

    for key, value in update_data.items():
        if hasattr(meeting, key):
            setattr(meeting, key, value)

    await db.flush()
    return meeting


async def delete_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Meeting:
    meeting = await get_meeting(db, meeting_id, project_id)
    meeting.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return meeting


async def start_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Meeting:
    """SCHEDULED -> IN_PROGRESS"""
    meeting = await get_meeting(db, meeting_id, project_id)
    if meeting.status != "SCHEDULED":
        raise HTTPException(400, "Only scheduled meetings can be started")
    meeting.status = "IN_PROGRESS"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="meeting_started",
        event_data={"meeting_number": meeting.number},
    )
    db.add(event)

    await db.flush()
    return meeting


async def complete_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Meeting:
    """IN_PROGRESS -> COMPLETED"""
    meeting = await get_meeting(db, meeting_id, project_id)
    if meeting.status != "IN_PROGRESS":
        raise HTTPException(400, "Only in-progress meetings can be completed")
    meeting.status = "COMPLETED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="meeting_completed",
        event_data={"meeting_number": meeting.number},
    )
    db.add(event)

    await db.flush()
    return meeting


async def cancel_meeting(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Meeting:
    """SCHEDULED -> CANCELLED"""
    meeting = await get_meeting(db, meeting_id, project_id)
    if meeting.status != "SCHEDULED":
        raise HTTPException(400, "Only scheduled meetings can be cancelled")
    meeting.status = "CANCELLED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="meeting_cancelled",
        event_data={"meeting_number": meeting.number},
    )
    db.add(event)

    await db.flush()
    return meeting


async def publish_minutes(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: PublishMinutesRequest,
) -> Meeting:
    meeting = await get_meeting(db, meeting_id, project_id)
    if meeting.status not in ("IN_PROGRESS", "COMPLETED"):
        raise HTTPException(400, "Meeting must be in progress or completed to publish minutes")

    meeting.minutes_published = True
    meeting.minutes_published_at = datetime.now(timezone.utc)

    # Optionally create todos from action items
    if data.create_todos and meeting.action_items:
        for item in meeting.action_items:
            if isinstance(item, dict):
                todo = Todo(
                    organization_id=organization_id,
                    project_id=project_id,
                    created_by=user["user_id"],
                    title=item.get("description", "Action item from meeting"),
                    assigned_to=item.get("assigned_to"),
                    due_date=item.get("due_date"),
                    priority="MEDIUM",
                    status="OPEN",
                    source_type="meeting",
                    source_id=meeting.id,
                )
                db.add(todo)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="meeting_minutes_published",
        event_data={"meeting_number": meeting.number, "created_todos": data.create_todos},
    )
    db.add(event)

    await db.flush()
    return meeting


async def generate_recurring(
    db: AsyncSession,
    meeting_id: uuid.UUID,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    count: int = 4,
) -> list[Meeting]:
    """Generate child meetings from a recurring parent."""
    parent = await get_meeting(db, meeting_id, project_id)
    if not parent.recurring:
        raise HTTPException(400, "Meeting is not recurring")

    children = []
    for i in range(1, count + 1):
        number = await get_next_number(db, project_id, "meeting")
        child = Meeting(
            organization_id=organization_id,
            project_id=project_id,
            created_by=user["user_id"],
            number=number,
            title=f"{parent.title} (#{i})",
            meeting_type=parent.meeting_type,
            location=parent.location,
            virtual_provider=parent.virtual_provider,
            virtual_link=parent.virtual_link,
            attendees=parent.attendees or [],
            agenda=parent.agenda,
            status="SCHEDULED",
            parent_meeting_id=parent.id,
        )
        db.add(child)
        children.append(child)

    await db.flush()
    return children


def format_meeting_response(
    meeting: Meeting,
    created_by_name: str | None = None,
) -> dict:
    scheduled_date = meeting.scheduled_date
    if hasattr(scheduled_date, "date") and scheduled_date:
        scheduled_date = scheduled_date.date()

    return {
        "id": meeting.id,
        "project_id": meeting.project_id,
        "number": meeting.number,
        "formatted_number": format_number("meeting", meeting.number),
        "title": meeting.title,
        "meeting_type": meeting.meeting_type,
        "status": meeting.status,
        "scheduled_date": scheduled_date,
        "start_time": meeting.start_time,
        "end_time": meeting.end_time,
        "location": meeting.location,
        "virtual_provider": meeting.virtual_provider,
        "virtual_link": meeting.virtual_link,
        "attendees": meeting.attendees if meeting.attendees else [],
        "agenda": meeting.agenda,
        "minutes": meeting.minutes,
        "action_items": meeting.action_items if meeting.action_items else [],
        "recurring": meeting.recurring,
        "recurrence_rule": meeting.recurrence_rule,
        "recurrence_end_date": meeting.recurrence_end_date,
        "parent_meeting_id": meeting.parent_meeting_id,
        "minutes_published": meeting.minutes_published,
        "minutes_published_at": meeting.minutes_published_at,
        "created_by": meeting.created_by,
        "created_by_name": created_by_name,
        "created_at": meeting.created_at,
        "updated_at": meeting.updated_at,
    }
