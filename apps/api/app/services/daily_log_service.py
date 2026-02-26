import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog
from app.models.event_log import EventLog
from app.models.schedule_delay import ScheduleDelay
from app.schemas.daily_log import DailyLogCreate, DailyLogDelayEntry, DailyLogUpdate
from app.services.schedule_service import DELAY_TIER_IMPACTS


async def create_daily_log(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: DailyLogCreate,
) -> DailyLog:
    """Create a new daily log. One per date per project."""
    existing = await db.execute(
        select(DailyLog).where(
            DailyLog.project_id == project_id,
            DailyLog.log_date == datetime.combine(data.log_date, datetime.min.time()),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Daily log already exists for {data.log_date}")

    weather_data = {}
    if data.weather_condition:
        weather_data["condition"] = data.weather_condition
    if data.temp_high is not None:
        weather_data["temp_high"] = data.temp_high
    if data.temp_low is not None:
        weather_data["temp_low"] = data.temp_low
    if data.precipitation is not None:
        weather_data["precipitation"] = data.precipitation
    if data.wind_speed is not None:
        weather_data["wind_speed"] = data.wind_speed
    if data.humidity is not None:
        weather_data["humidity"] = data.humidity

    daily_log = DailyLog(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        log_date=datetime.combine(data.log_date, datetime.min.time()),
        weather_data=weather_data,
        work_performed=data.work_performed,
        manpower=data.manpower or [],
        delays=_build_delays(data.delays),
        status=data.status,
    )
    db.add(daily_log)

    # Event log
    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="daily_log_created",
        event_data={"log_date": str(data.log_date)},
    )
    db.add(event)

    await db.flush()

    # Create linked ScheduleDelay records for each schedule impact entry
    if data.schedule_delays:
        for entry in data.schedule_delays:
            await _create_schedule_delay_from_log(
                db, daily_log, project_id, organization_id, user, entry,
            )

    return daily_log


def _build_delays(delays_text: str | None) -> list:
    """Convert delay text to JSONB array format."""
    if not delays_text:
        return []
    return [{"description": delays_text}]


async def _create_schedule_delay_from_log(
    db,
    daily_log: DailyLog,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    entry: DailyLogDelayEntry,
) -> ScheduleDelay:
    """Create a ScheduleDelay linked back to a daily log."""
    impacts = DELAY_TIER_IMPACTS.get(
        entry.reason_category, {"gc": True, "owner": False, "sub": True}
    )
    delay = ScheduleDelay(
        organization_id=organization_id,
        project_id=project_id,
        task_ids=[str(tid) for tid in entry.task_ids],
        delay_days=entry.delay_days,
        reason_category=entry.reason_category,
        responsible_party=entry.responsible_party,
        description=entry.description,
        impacts_gc_schedule=impacts["gc"],
        impacts_owner_schedule=impacts["owner"],
        impacts_sub_schedule=impacts["sub"],
        daily_log_id=daily_log.id,
        status="PENDING",
        created_by=user["user_id"],
    )
    db.add(delay)
    await db.flush()
    return delay


async def list_daily_logs(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    sort: str = "log_date",
    order: str = "desc",
) -> tuple[list[DailyLog], int]:
    query = select(DailyLog).where(DailyLog.project_id == project_id)

    if status:
        query = query.where(DailyLog.status == status)
    if search:
        query = query.where(
            or_(
                DailyLog.work_performed.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(DailyLog, sort, DailyLog.log_date)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_daily_log(
    db: AsyncSession,
    daily_log_id: uuid.UUID,
    project_id: uuid.UUID,
) -> DailyLog:
    result = await db.execute(
        select(DailyLog).where(
            DailyLog.id == daily_log_id,
            DailyLog.project_id == project_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(404, "Daily log not found")
    return log


async def update_daily_log(
    db: AsyncSession,
    daily_log_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: DailyLogUpdate,
) -> DailyLog:
    log = await get_daily_log(db, daily_log_id, project_id)

    if log.status == "APPROVED":
        raise HTTPException(400, "Cannot edit an approved daily log")

    update_data = data.model_dump(exclude_unset=True)

    # Handle weather fields → weather_data JSONB
    weather_fields = ["weather_condition", "temp_high", "temp_low", "precipitation", "wind_speed", "humidity"]
    weather_updates = {}
    for field in weather_fields:
        if field in update_data:
            weather_updates[field.replace("weather_", "")] = update_data.pop(field)
    if weather_updates:
        current_weather = log.weather_data or {}
        current_weather.update(weather_updates)
        log.weather_data = current_weather

    if "delays" in update_data:
        log.delays = _build_delays(update_data.pop("delays"))

    if "manpower" in update_data:
        log.manpower = update_data.pop("manpower") or []

    for key, value in update_data.items():
        if hasattr(log, key):
            setattr(log, key, value)

    await db.flush()
    return log


async def submit_daily_log(
    db: AsyncSession,
    daily_log_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> DailyLog:
    """DRAFT → SUBMITTED."""
    log = await get_daily_log(db, daily_log_id, project_id)
    if log.status != "DRAFT":
        raise HTTPException(400, "Only draft daily logs can be submitted")
    log.status = "SUBMITTED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="daily_log_submitted",
        event_data={"daily_log_id": str(daily_log_id)},
    )
    db.add(event)

    await db.flush()
    return log


async def approve_daily_log(
    db: AsyncSession,
    daily_log_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> DailyLog:
    """SUBMITTED → APPROVED. Management+ only."""
    log = await get_daily_log(db, daily_log_id, project_id)
    if log.status != "SUBMITTED":
        raise HTTPException(400, "Only submitted daily logs can be approved")
    log.status = "APPROVED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="daily_log_approved",
        event_data={"daily_log_id": str(daily_log_id)},
    )
    db.add(event)

    await db.flush()
    return log


async def delete_daily_log(
    db: AsyncSession,
    daily_log_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    """Soft delete by removing the record (daily logs don't have deleted_at)."""
    log = await get_daily_log(db, daily_log_id, project_id)
    if log.status == "APPROVED":
        raise HTTPException(400, "Cannot delete an approved daily log")
    await db.delete(log)
    await db.flush()


def format_daily_log_response(
    log: DailyLog,
    created_by_name: str | None = None,
    schedule_delays: list | None = None,
) -> dict:
    """Convert DailyLog ORM model to response dict."""
    weather = log.weather_data or {}
    log_date = log.log_date
    if hasattr(log_date, "date"):
        log_date = log_date.date()

    return {
        "id": log.id,
        "project_id": log.project_id,
        "log_date": log_date,
        "number": f"DL-{log_date}",
        "weather_data": weather,
        "summary": weather.get("summary"),
        "work_performed": log.work_performed,
        "materials_received": None,
        "equipment_on_site": None,
        "visitors": None,
        "safety_incidents": None,
        "delays_text": log.delays[0].get("description") if log.delays else None,
        "schedule_delays": schedule_delays,
        "extra_work": None,
        "manpower": log.manpower,
        "status": log.status,
        "created_by": log.created_by,
        "created_by_name": created_by_name,
        "created_at": log.created_at,
        "updated_at": log.updated_at,
    }
