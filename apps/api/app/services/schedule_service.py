"""Schedule service — Tasks, Dependencies, Delays, Versions, Config, Health."""
import uuid
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule_task import ScheduleTask
from app.models.schedule_dependency import ScheduleDependency
from app.models.schedule_delay import ScheduleDelay
from app.models.schedule_version import ScheduleVersion
from app.models.schedule_config import ScheduleConfig
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.schedule import (
    ScheduleTaskCreate,
    ScheduleTaskUpdate,
    DependencyCreate,
    ScheduleDelayCreate,
    SchedulePublishRequest,
    ScheduleConfigUpdate,
)

# Default tier impact by reason category
DELAY_TIER_IMPACTS = {
    "WEATHER":               {"gc": True, "owner": False, "sub": True},
    "OWNER_CHANGE":          {"gc": True, "owner": True,  "sub": True},
    "DESIGN_ERROR":          {"gc": True, "owner": True,  "sub": True},
    "PERMITTING":            {"gc": True, "owner": False, "sub": True},
    "MATERIAL_DELIVERY":     {"gc": True, "owner": False, "sub": True},
    "LABOR_SHORTAGE":        {"gc": True, "owner": False, "sub": True},
    "UNFORESEEN_CONDITIONS": {"gc": True, "owner": False, "sub": True},
    "SUB_CAUSED":            {"gc": True, "owner": False, "sub": True},
    "FORCE_MAJEURE":         {"gc": True, "owner": True,  "sub": True},
    "OTHER":                 {"gc": True, "owner": False, "sub": True},
}


def _to_dt(d):
    """Convert date to datetime if needed."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    return datetime.combine(d, datetime.min.time())


def _to_date(d):
    """Convert datetime to date for response."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date()
    return d


# ============================================================
# CONFIG
# ============================================================

async def get_schedule_config(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> ScheduleConfig:
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        # Return a default config object (not persisted)
        config = ScheduleConfig(
            project_id=project_id,
            schedule_mode="SINGLE",
            derivation_method="FIXED_DAYS",
            health_on_track_max_days=5,
            health_at_risk_max_days=15,
            sub_notify_intervals=[14, 7, 1],
        )
    return config


async def update_schedule_config(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    data: ScheduleConfigUpdate,
) -> ScheduleConfig:
    result = await db.execute(
        select(ScheduleConfig).where(ScheduleConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = ScheduleConfig(
            project_id=project_id,
            organization_id=organization_id,
        )
        db.add(config)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(config, key):
            setattr(config, key, value)

    await db.flush()
    return config


# ============================================================
# TASKS
# ============================================================

async def create_task(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: ScheduleTaskCreate,
) -> ScheduleTask:
    task = ScheduleTask(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        name=data.name,
        description=data.description,
        wbs_code=data.wbs_code,
        parent_task_id=data.parent_task_id,
        start_date=_to_dt(data.start_date),
        end_date=_to_dt(data.end_date),
        duration=data.duration,
        assigned_to=data.assigned_to,
        assigned_to_sub_id=data.assigned_to_sub_id,
        milestone=data.milestone,
        is_critical=data.is_critical,
        cost_code_id=data.cost_code_id,
        sort_order=data.sort_order,
    )
    db.add(task)

    # If three-tier mode, derive owner/sub dates
    config = await get_schedule_config(db, project_id)
    if config.schedule_mode != "SINGLE" and config.schedule_mode != "THREE_TIER_MANUAL":
        derive_tier_dates(task, config)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="schedule_task_created",
        event_data={"task_name": data.name},
    )
    db.add(event)

    await db.flush()
    return task


def derive_tier_dates(task: ScheduleTask, config: ScheduleConfig):
    """Calculate owner and sub dates from GC dates."""
    if not task.start_date or not task.duration:
        return

    if config.derivation_method == "PERCENTAGE":
        owner_buffer = config.owner_buffer_percent or 0
        sub_compress = config.sub_compress_percent or 0

        # Owner: expand duration
        owner_duration = int(task.duration * (1 + owner_buffer / 100))
        task.owner_start_date = task.start_date
        task.owner_end_date = task.start_date + timedelta(days=owner_duration)

        # Sub: compress duration
        sub_duration = max(int(task.duration * (1 - sub_compress / 100)), 1)
        task.sub_start_date = task.start_date
        task.sub_end_date = task.start_date + timedelta(days=sub_duration)


async def list_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ScheduleTask]:
    result = await db.execute(
        select(ScheduleTask)
        .where(
            ScheduleTask.project_id == project_id,
            ScheduleTask.deleted_at.is_(None),
        )
        .order_by(ScheduleTask.sort_order, ScheduleTask.start_date)
    )
    return result.scalars().all()


async def get_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ScheduleTask:
    result = await db.execute(
        select(ScheduleTask).where(
            ScheduleTask.id == task_id,
            ScheduleTask.project_id == project_id,
            ScheduleTask.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Schedule task not found")
    return task


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: ScheduleTaskUpdate,
) -> ScheduleTask:
    task = await get_task(db, task_id, project_id)
    update_data = data.model_dump(exclude_unset=True)

    for date_field in ("start_date", "end_date"):
        if date_field in update_data and update_data[date_field]:
            update_data[date_field] = _to_dt(update_data[date_field])

    for key, value in update_data.items():
        if hasattr(task, key):
            setattr(task, key, value)

    # Re-derive tier dates if three-tier auto
    config = await get_schedule_config(db, project_id)
    if config.schedule_mode == "THREE_TIER_AUTO":
        derive_tier_dates(task, config)

    await db.flush()
    return task


async def delete_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    task = await get_task(db, task_id, project_id)
    task.deleted_at = datetime.utcnow()
    await db.flush()


async def reorder_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    task_ids: list[uuid.UUID],
) -> None:
    """Bulk reorder tasks by setting sort_order."""
    for idx, task_id in enumerate(task_ids):
        task = await get_task(db, task_id, project_id)
        task.sort_order = idx
    await db.flush()


# ============================================================
# DEPENDENCIES
# ============================================================

async def add_dependency(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: DependencyCreate,
) -> ScheduleDependency:
    dep = ScheduleDependency(
        project_id=project_id,
        predecessor_id=data.predecessor_id,
        successor_id=data.successor_id,
        dependency_type=data.dependency_type,
        lag_days=data.lag_days,
    )
    db.add(dep)
    await db.flush()
    return dep


async def remove_dependency(
    db: AsyncSession,
    dependency_id: uuid.UUID,
) -> None:
    result = await db.execute(
        select(ScheduleDependency).where(ScheduleDependency.id == dependency_id)
    )
    dep = result.scalar_one_or_none()
    if not dep:
        raise HTTPException(404, "Dependency not found")
    await db.delete(dep)
    await db.flush()


async def get_task_dependencies(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ScheduleDependency]:
    result = await db.execute(
        select(ScheduleDependency).where(ScheduleDependency.project_id == project_id)
    )
    return result.scalars().all()


# ============================================================
# BASELINE
# ============================================================

async def lock_baseline(
    db: AsyncSession,
    project_id: uuid.UUID,
    user: dict,
) -> int:
    """Snapshot current dates as baseline. Returns count of tasks updated."""
    tasks = await list_tasks(db, project_id)
    count = 0
    for task in tasks:
        task.baseline_start = task.start_date
        task.baseline_end = task.end_date
        task.baseline_duration = task.duration
        count += 1

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="schedule_baseline_locked",
        event_data={"tasks_count": count},
    )
    db.add(event)

    await db.flush()
    return count


# ============================================================
# DELAYS
# ============================================================

async def create_delay(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: ScheduleDelayCreate,
) -> ScheduleDelay:
    impacts = DELAY_TIER_IMPACTS.get(data.reason_category, {"gc": True, "owner": False, "sub": True})

    delay = ScheduleDelay(
        organization_id=organization_id,
        project_id=project_id,
        task_ids=[str(tid) for tid in data.task_ids],
        delay_days=data.delay_days,
        reason_category=data.reason_category,
        responsible_party=data.responsible_party,
        description=data.description,
        impacts_gc_schedule=impacts["gc"],
        impacts_owner_schedule=impacts["owner"],
        impacts_sub_schedule=impacts["sub"],
        daily_log_id=data.daily_log_id,
        rfi_id=data.rfi_id,
        change_order_id=data.change_order_id,
        status="PENDING",
        created_by=user["user_id"],
    )
    db.add(delay)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="schedule_delay_created",
        event_data={"delay_days": data.delay_days, "reason": data.reason_category},
    )
    db.add(event)

    await db.flush()
    return delay


async def list_delays(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ScheduleDelay]:
    result = await db.execute(
        select(ScheduleDelay)
        .where(ScheduleDelay.project_id == project_id)
        .order_by(ScheduleDelay.created_at.desc())
    )
    return result.scalars().all()


async def approve_delay(
    db: AsyncSession,
    delay_id: uuid.UUID,
    user: dict,
) -> ScheduleDelay:
    result = await db.execute(select(ScheduleDelay).where(ScheduleDelay.id == delay_id))
    delay = result.scalar_one_or_none()
    if not delay:
        raise HTTPException(404, "Delay not found")
    if delay.status != "PENDING":
        raise HTTPException(400, "Delay must be pending to approve")

    delay.status = "APPROVED"
    delay.approved_by = user["user_id"]
    delay.approved_at = datetime.utcnow()
    await db.flush()
    return delay


async def reject_delay(
    db: AsyncSession,
    delay_id: uuid.UUID,
    user: dict,
) -> ScheduleDelay:
    result = await db.execute(select(ScheduleDelay).where(ScheduleDelay.id == delay_id))
    delay = result.scalar_one_or_none()
    if not delay:
        raise HTTPException(404, "Delay not found")
    if delay.status != "PENDING":
        raise HTTPException(400, "Delay must be pending to reject")

    delay.status = "REJECTED"
    await db.flush()
    return delay


async def apply_delay(
    db: AsyncSession,
    delay_id: uuid.UUID,
    user: dict,
) -> ScheduleDelay:
    """Apply an approved delay to the schedule — shift task dates."""
    result = await db.execute(select(ScheduleDelay).where(ScheduleDelay.id == delay_id))
    delay = result.scalar_one_or_none()
    if not delay:
        raise HTTPException(404, "Delay not found")
    if delay.status != "APPROVED":
        raise HTTPException(400, "Delay must be approved before applying")

    delta = timedelta(days=delay.delay_days)

    for task_id_str in delay.task_ids:
        task_id = uuid.UUID(task_id_str)
        task_result = await db.execute(select(ScheduleTask).where(ScheduleTask.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            continue

        # Shift GC dates
        if delay.impacts_gc_schedule and task.end_date:
            task.end_date = task.end_date + delta

        # Shift owner dates ONLY if owner-caused
        if delay.impacts_owner_schedule and task.owner_end_date:
            task.owner_end_date = task.owner_end_date + delta

        # Shift sub dates
        if delay.impacts_sub_schedule and task.sub_end_date:
            task.sub_end_date = task.sub_end_date + delta

    # Cascade through dependencies
    await cascade_dependencies(db, delay.project_id, [uuid.UUID(tid) for tid in delay.task_ids])

    delay.status = "APPLIED"
    delay.applied_at = datetime.utcnow()

    event = EventLog(
        organization_id=delay.organization_id,
        project_id=delay.project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="schedule_delay_applied",
        event_data={"delay_days": delay.delay_days, "task_count": len(delay.task_ids)},
    )
    db.add(event)

    await db.flush()
    return delay


async def cascade_dependencies(
    db: AsyncSession,
    project_id: uuid.UUID,
    changed_task_ids: list[uuid.UUID],
) -> None:
    """After task date changes, cascade forward through FS dependencies."""
    result = await db.execute(
        select(ScheduleDependency).where(
            ScheduleDependency.project_id == project_id,
            ScheduleDependency.predecessor_id.in_(changed_task_ids),
        )
    )
    deps = result.scalars().all()

    next_cascade = []
    for dep in deps:
        pred_result = await db.execute(select(ScheduleTask).where(ScheduleTask.id == dep.predecessor_id))
        predecessor = pred_result.scalar_one_or_none()
        succ_result = await db.execute(select(ScheduleTask).where(ScheduleTask.id == dep.successor_id))
        successor = succ_result.scalar_one_or_none()

        if not predecessor or not successor or not predecessor.end_date or not successor.start_date:
            continue

        if dep.dependency_type == "FS":
            min_start = predecessor.end_date + timedelta(days=dep.lag_days)
            if successor.start_date < min_start:
                duration = successor.duration or 0
                successor.start_date = min_start
                successor.end_date = min_start + timedelta(days=duration)
                next_cascade.append(successor.id)

    if next_cascade:
        await cascade_dependencies(db, project_id, next_cascade)


# ============================================================
# LOOK AHEAD
# ============================================================

async def get_look_ahead_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    weeks: int = 3,
) -> list[ScheduleTask]:
    """Tasks starting or ending within next N weeks."""
    today = datetime.utcnow()
    cutoff = today + timedelta(weeks=weeks)

    result = await db.execute(
        select(ScheduleTask).where(
            ScheduleTask.project_id == project_id,
            ScheduleTask.deleted_at.is_(None),
            or_(
                and_(ScheduleTask.start_date >= today, ScheduleTask.start_date <= cutoff),
                and_(ScheduleTask.end_date >= today, ScheduleTask.end_date <= cutoff),
                and_(ScheduleTask.sub_start_date >= today, ScheduleTask.sub_start_date <= cutoff),
                and_(ScheduleTask.sub_end_date >= today, ScheduleTask.sub_end_date <= cutoff),
            ),
        ).order_by(ScheduleTask.start_date)
    )
    return result.scalars().all()


# ============================================================
# VERSIONS / ARCHIVE
# ============================================================

def _serialize_task(task: ScheduleTask) -> dict:
    """Serialize a task for snapshot."""
    return {
        "id": str(task.id),
        "name": task.name,
        "wbs_code": task.wbs_code,
        "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        "start_date": _to_date(task.start_date).isoformat() if task.start_date else None,
        "end_date": _to_date(task.end_date).isoformat() if task.end_date else None,
        "duration": task.duration,
        "percent_complete": task.percent_complete,
        "milestone": task.milestone,
        "is_critical": task.is_critical,
        "assigned_to_sub_id": str(task.assigned_to_sub_id) if task.assigned_to_sub_id else None,
        "baseline_start": _to_date(task.baseline_start).isoformat() if task.baseline_start else None,
        "baseline_end": _to_date(task.baseline_end).isoformat() if task.baseline_end else None,
        "owner_start_date": _to_date(task.owner_start_date).isoformat() if task.owner_start_date else None,
        "owner_end_date": _to_date(task.owner_end_date).isoformat() if task.owner_end_date else None,
        "sub_start_date": _to_date(task.sub_start_date).isoformat() if task.sub_start_date else None,
        "sub_end_date": _to_date(task.sub_end_date).isoformat() if task.sub_end_date else None,
    }


async def publish_schedule(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: SchedulePublishRequest,
) -> ScheduleVersion:
    tasks = await list_tasks(db, project_id)
    snapshot = [_serialize_task(t) for t in tasks]

    # Get next version number
    last_version = await db.execute(
        select(func.max(ScheduleVersion.version_number)).where(
            ScheduleVersion.project_id == project_id,
            ScheduleVersion.version_type == data.version_type,
        )
    )
    next_num = (last_version.scalar() or 0) + 1

    title = data.title or f"{data.version_type.replace('_', ' ').title()} v{next_num}"

    version = ScheduleVersion(
        organization_id=organization_id,
        project_id=project_id,
        version_type=data.version_type,
        version_number=next_num,
        title=title,
        notes=data.notes,
        snapshot_data={"tasks": snapshot},
        published_by=user["user_id"],
    )
    db.add(version)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="schedule_published",
        event_data={"version_type": data.version_type, "version_number": next_num},
    )
    db.add(event)

    await db.flush()
    return version


async def list_versions(
    db: AsyncSession,
    project_id: uuid.UUID,
    version_type: str | None = None,
) -> list[ScheduleVersion]:
    query = select(ScheduleVersion).where(ScheduleVersion.project_id == project_id)
    if version_type:
        query = query.where(ScheduleVersion.version_type == version_type)
    query = query.order_by(ScheduleVersion.published_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_version(
    db: AsyncSession,
    version_id: uuid.UUID,
) -> ScheduleVersion:
    result = await db.execute(
        select(ScheduleVersion).where(ScheduleVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(404, "Schedule version not found")
    return version


# ============================================================
# HEALTH
# ============================================================

async def calculate_schedule_health(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict:
    """Calculate project health based on schedule slippage against baseline."""
    config = await get_schedule_config(db, project_id)
    tasks = await list_tasks(db, project_id)

    critical_tasks = [t for t in tasks if t.is_critical and t.baseline_end]
    if not critical_tasks:
        return {
            "status": "ON_TRACK",
            "slippage_days": 0,
            "on_track_threshold": config.health_on_track_max_days,
            "at_risk_threshold": config.health_at_risk_max_days,
        }

    max_slippage = 0
    for task in critical_tasks:
        end = _to_date(task.end_date)
        baseline_end = _to_date(task.baseline_end)
        if end and baseline_end and end > baseline_end:
            slippage = (end - baseline_end).days
            max_slippage = max(max_slippage, slippage)

    if max_slippage <= config.health_on_track_max_days:
        status = "ON_TRACK"
    elif max_slippage <= config.health_at_risk_max_days:
        status = "AT_RISK"
    else:
        status = "BEHIND"

    return {
        "status": status,
        "slippage_days": max_slippage,
        "on_track_threshold": config.health_on_track_max_days,
        "at_risk_threshold": config.health_at_risk_max_days,
    }


# ============================================================
# RESPONSE FORMATTING
# ============================================================

def format_task_response(
    task: ScheduleTask,
    dependencies: list[dict] | None = None,
) -> dict:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "name": task.name,
        "description": task.description,
        "wbs_code": task.wbs_code,
        "parent_task_id": task.parent_task_id,
        "sort_order": task.sort_order,
        "start_date": _to_date(task.start_date),
        "end_date": _to_date(task.end_date),
        "duration": task.duration,
        "baseline_start": _to_date(task.baseline_start),
        "baseline_end": _to_date(task.baseline_end),
        "baseline_duration": task.baseline_duration,
        "owner_start_date": _to_date(task.owner_start_date),
        "owner_end_date": _to_date(task.owner_end_date),
        "sub_start_date": _to_date(task.sub_start_date),
        "sub_end_date": _to_date(task.sub_end_date),
        "percent_complete": task.percent_complete,
        "actual_start": _to_date(task.actual_start),
        "actual_end": _to_date(task.actual_end),
        "assigned_to": task.assigned_to,
        "assigned_to_sub_id": task.assigned_to_sub_id,
        "milestone": task.milestone,
        "is_critical": task.is_critical,
        "cost_code_id": task.cost_code_id,
        "dependencies": dependencies or [],
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def format_delay_response(delay: ScheduleDelay) -> dict:
    return {
        "id": delay.id,
        "project_id": delay.project_id,
        "task_ids": delay.task_ids or [],
        "delay_days": delay.delay_days,
        "reason_category": delay.reason_category,
        "responsible_party": delay.responsible_party,
        "description": delay.description,
        "impacts_gc_schedule": delay.impacts_gc_schedule,
        "impacts_owner_schedule": delay.impacts_owner_schedule,
        "impacts_sub_schedule": delay.impacts_sub_schedule,
        "daily_log_id": delay.daily_log_id,
        "rfi_id": delay.rfi_id,
        "change_order_id": delay.change_order_id,
        "status": delay.status,
        "approved_by": delay.approved_by,
        "approved_at": delay.approved_at,
        "applied_at": delay.applied_at,
        "created_by": delay.created_by,
        "created_at": delay.created_at,
    }


def format_version_response(version: ScheduleVersion) -> dict:
    return {
        "id": version.id,
        "project_id": version.project_id,
        "version_type": version.version_type,
        "version_number": version.version_number,
        "title": version.title,
        "notes": version.notes,
        "snapshot_data": version.snapshot_data,
        "published_by": version.published_by,
        "published_at": version.published_at,
    }


def format_config_response(config: ScheduleConfig) -> dict:
    return {
        "id": getattr(config, "id", None),
        "project_id": config.project_id,
        "schedule_mode": config.schedule_mode,
        "derivation_method": config.derivation_method,
        "owner_buffer_percent": config.owner_buffer_percent,
        "sub_compress_percent": config.sub_compress_percent,
        "health_on_track_max_days": config.health_on_track_max_days,
        "health_at_risk_max_days": config.health_at_risk_max_days,
        "sub_notify_intervals": config.sub_notify_intervals or [14, 7, 1],
    }
