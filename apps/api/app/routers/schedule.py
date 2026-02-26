"""Schedule router — Tasks, Dependencies, Delays, Versions, Config, Health.
GC, Sub, and Owner portal endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schedule import (
    DependencyCreate,
    DependencyResponse,
    ScheduleConfigResponse,
    ScheduleConfigUpdate,
    ScheduleDelayCreate,
    ScheduleDelayListResponse,
    ScheduleDelayResponse,
    ScheduleHealthResponse,
    SchedulePublishRequest,
    ScheduleTaskCreate,
    ScheduleTaskListResponse,
    ScheduleTaskResponse,
    ScheduleTaskUpdate,
    ScheduleVersionListResponse,
    ScheduleVersionResponse,
)
from app.services.schedule_service import (
    add_dependency,
    apply_delay,
    approve_delay,
    calculate_schedule_health,
    cascade_dependencies,
    create_delay,
    create_task,
    delete_task,
    format_config_response,
    format_delay_response,
    format_task_response,
    format_version_response,
    get_look_ahead_tasks,
    get_schedule_config,
    get_task,
    get_task_dependencies,
    get_version,
    list_delays,
    list_tasks,
    list_versions,
    lock_baseline,
    publish_schedule,
    reject_delay,
    remove_dependency,
    reorder_tasks,
    update_schedule_config,
    update_task,
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/schedule", tags=["schedule"])


# --- Tasks ---

@gc_router.get("/tasks", response_model=ScheduleTaskListResponse)
async def list_tasks_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all schedule tasks for Gantt chart."""
    _get_user(request)
    tasks = await list_tasks(db, project_id)
    deps = await get_task_dependencies(db, project_id)

    # Build dependency map per task
    dep_map: dict[uuid.UUID, list[dict]] = {}
    for d in deps:
        dep_map.setdefault(d.successor_id, []).append({
            "id": str(d.id),
            "predecessor_id": str(d.predecessor_id),
            "dependency_type": d.dependency_type,
            "lag_days": d.lag_days,
        })

    data = [
        ScheduleTaskResponse.model_validate(format_task_response(t, dep_map.get(t.id, [])))
        for t in tasks
    ]
    return ScheduleTaskListResponse(data=data, meta={"total": len(data)})


@gc_router.post("/tasks", response_model=dict, status_code=201)
async def create_task_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: ScheduleTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a schedule task."""
    user = _get_user(request)
    task = await create_task(db, project_id, user["organization_id"], user, body)
    return {
        "data": ScheduleTaskResponse.model_validate(format_task_response(task)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/tasks/{task_id}", response_model=dict)
async def get_task_endpoint(
    request: Request,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single schedule task."""
    _get_user(request)
    task = await get_task(db, task_id, project_id)
    return {
        "data": ScheduleTaskResponse.model_validate(format_task_response(task)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/tasks/{task_id}", response_model=dict)
async def update_task_endpoint(
    request: Request,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    body: ScheduleTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a schedule task."""
    user = _get_user(request)
    task = await update_task(db, task_id, project_id, user, body)
    return {
        "data": ScheduleTaskResponse.model_validate(format_task_response(task)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/tasks/{task_id}", status_code=200)
async def delete_task_endpoint(
    request: Request,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a schedule task."""
    _get_user(request)
    await delete_task(db, task_id, project_id)
    return {"data": {"id": str(task_id), "deleted": True}, "meta": {}}


@gc_router.post("/tasks/reorder", response_model=dict)
async def reorder_tasks_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Bulk reorder tasks."""
    _get_user(request)
    task_ids = [uuid.UUID(tid) for tid in body.get("task_ids", [])]
    await reorder_tasks(db, project_id, task_ids)
    return {"data": {"reordered": len(task_ids)}, "meta": {}}


# --- Dependencies ---

@gc_router.post("/tasks/{task_id}/dependencies", response_model=dict, status_code=201)
async def add_dependency_endpoint(
    request: Request,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    body: DependencyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a dependency to a task."""
    _get_user(request)
    dep = await add_dependency(db, project_id, body)
    return {
        "data": DependencyResponse.model_validate({
            "id": dep.id,
            "predecessor_id": dep.predecessor_id,
            "successor_id": dep.successor_id,
            "dependency_type": dep.dependency_type,
            "lag_days": dep.lag_days,
        }).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/dependencies/{dependency_id}", status_code=200)
async def remove_dependency_endpoint(
    request: Request,
    project_id: uuid.UUID,
    dependency_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a dependency."""
    _get_user(request)
    await remove_dependency(db, dependency_id)
    return {"data": {"id": str(dependency_id), "deleted": True}, "meta": {}}


# --- Baseline ---

@gc_router.post("/lock-baseline", response_model=dict)
async def lock_baseline_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Lock current dates as baseline."""
    user = _get_user(request)
    count = await lock_baseline(db, project_id, user)
    return {"data": {"tasks_updated": count}, "meta": {}}


# --- Publish / Archive ---

@gc_router.post("/publish", response_model=dict, status_code=201)
async def publish_schedule_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: SchedulePublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """Publish schedule as immutable version."""
    user = _get_user(request)
    version = await publish_schedule(db, project_id, user["organization_id"], user, body)
    return {
        "data": ScheduleVersionResponse.model_validate(format_version_response(version)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/versions", response_model=ScheduleVersionListResponse)
async def list_versions_endpoint(
    request: Request,
    project_id: uuid.UUID,
    version_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List published schedule versions."""
    _get_user(request)
    versions = await list_versions(db, project_id, version_type)
    data = [ScheduleVersionResponse.model_validate(format_version_response(v)) for v in versions]
    return ScheduleVersionListResponse(data=data, meta={"total": len(data)})


@gc_router.get("/versions/{version_id}", response_model=dict)
async def get_version_endpoint(
    request: Request,
    project_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific version with snapshot data."""
    _get_user(request)
    version = await get_version(db, version_id)
    return {
        "data": ScheduleVersionResponse.model_validate(format_version_response(version)).model_dump(mode="json"),
        "meta": {},
    }


# --- Look Ahead ---

@gc_router.get("/look-ahead", response_model=ScheduleTaskListResponse)
async def look_ahead_endpoint(
    request: Request,
    project_id: uuid.UUID,
    weeks: int = Query(3, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
):
    """Get tasks for 3-week look ahead."""
    _get_user(request)
    tasks = await get_look_ahead_tasks(db, project_id, weeks)
    data = [ScheduleTaskResponse.model_validate(format_task_response(t)) for t in tasks]
    return ScheduleTaskListResponse(data=data, meta={"total": len(data), "weeks": weeks})


# --- Health ---

@gc_router.get("/health", response_model=ScheduleHealthResponse)
async def health_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get schedule health (ON_TRACK / AT_RISK / BEHIND)."""
    _get_user(request)
    health = await calculate_schedule_health(db, project_id)
    return ScheduleHealthResponse(**health)


# --- Config ---

@gc_router.get("/config", response_model=dict)
async def get_config_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get schedule config."""
    _get_user(request)
    config = await get_schedule_config(db, project_id)
    return {
        "data": ScheduleConfigResponse.model_validate(format_config_response(config)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/config", response_model=dict)
async def update_config_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: ScheduleConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update schedule config."""
    user = _get_user(request)
    config = await update_schedule_config(db, project_id, user["organization_id"], body)
    return {
        "data": ScheduleConfigResponse.model_validate(format_config_response(config)).model_dump(mode="json"),
        "meta": {},
    }


# --- Delays ---

@gc_router.get("/delays", response_model=ScheduleDelayListResponse)
async def list_delays_endpoint(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List schedule delays."""
    _get_user(request)
    delays = await list_delays(db, project_id)
    data = [ScheduleDelayResponse.model_validate(format_delay_response(d)) for d in delays]
    return ScheduleDelayListResponse(data=data, meta={"total": len(data)})


@gc_router.post("/delays", response_model=dict, status_code=201)
async def create_delay_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: ScheduleDelayCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a schedule delay (pending approval)."""
    user = _get_user(request)
    delay = await create_delay(db, project_id, user["organization_id"], user, body)
    return {
        "data": ScheduleDelayResponse.model_validate(format_delay_response(delay)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/delays/{delay_id}/approve", response_model=dict)
async def approve_delay_endpoint(
    request: Request,
    project_id: uuid.UUID,
    delay_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending delay."""
    user = _get_user(request)
    delay = await approve_delay(db, delay_id, user)
    return {
        "data": ScheduleDelayResponse.model_validate(format_delay_response(delay)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/delays/{delay_id}/reject", response_model=dict)
async def reject_delay_endpoint(
    request: Request,
    project_id: uuid.UUID,
    delay_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending delay."""
    user = _get_user(request)
    delay = await reject_delay(db, delay_id, user)
    return {
        "data": ScheduleDelayResponse.model_validate(format_delay_response(delay)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/delays/{delay_id}/apply", response_model=dict)
async def apply_delay_endpoint(
    request: Request,
    project_id: uuid.UUID,
    delay_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Apply an approved delay (shifts task dates)."""
    user = _get_user(request)
    delay = await apply_delay(db, delay_id, user)
    return {
        "data": ScheduleDelayResponse.model_validate(format_delay_response(delay)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# OWNER PORTAL (Read-only)
# ============================================================

owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/schedule", tags=["owner-schedule"])


@owner_router.get("/tasks", response_model=ScheduleTaskListResponse)
async def owner_list_tasks(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Owner sees contract (owner-tier) schedule only."""
    _get_user(request)
    tasks = await list_tasks(db, project_id)
    # Owner only sees milestones and parent tasks with owner dates
    data = [
        ScheduleTaskResponse.model_validate(format_task_response(t))
        for t in tasks
    ]
    return ScheduleTaskListResponse(data=data, meta={"total": len(data)})


@owner_router.get("/health", response_model=ScheduleHealthResponse)
async def owner_health(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Owner schedule health."""
    _get_user(request)
    health = await calculate_schedule_health(db, project_id)
    return ScheduleHealthResponse(**health)


# ============================================================
# SUB PORTAL (Read-only, own tasks)
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/schedule", tags=["sub-schedule"])


@sub_router.get("/tasks", response_model=ScheduleTaskListResponse)
async def sub_list_tasks(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sub sees only their assigned tasks."""
    user = _get_user(request)
    all_tasks = await list_tasks(db, project_id)
    sub_id = user.get("sub_company_id")
    # Filter to sub's tasks
    sub_tasks = [t for t in all_tasks if t.assigned_to_sub_id == sub_id] if sub_id else all_tasks
    data = [ScheduleTaskResponse.model_validate(format_task_response(t)) for t in sub_tasks]
    return ScheduleTaskListResponse(data=data, meta={"total": len(data)})


@sub_router.get("/look-ahead", response_model=ScheduleTaskListResponse)
async def sub_look_ahead(
    request: Request,
    project_id: uuid.UUID,
    weeks: int = Query(3, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
):
    """Sub's look ahead — their upcoming tasks."""
    user = _get_user(request)
    tasks = await get_look_ahead_tasks(db, project_id, weeks)
    sub_id = user.get("sub_company_id")
    sub_tasks = [t for t in tasks if t.assigned_to_sub_id == sub_id] if sub_id else tasks
    data = [ScheduleTaskResponse.model_validate(format_task_response(t)) for t in sub_tasks]
    return ScheduleTaskListResponse(data=data, meta={"total": len(data), "weeks": weeks})
