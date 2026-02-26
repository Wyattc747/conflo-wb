"""Daily Logs CRUD router."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.daily_log import (
    DailyLogCreate,
    DailyLogListResponse,
    DailyLogResponse,
    DailyLogUpdate,
)
from app.services.daily_log_service import (
    approve_daily_log,
    create_daily_log,
    delete_daily_log,
    format_daily_log_response,
    get_daily_log,
    list_daily_logs,
    submit_daily_log,
    update_daily_log,
)

router = APIRouter(prefix="/api/gc/projects/{project_id}/daily-logs", tags=["daily-logs"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# LIST DAILY LOGS
# ============================================================

@router.get("", response_model=DailyLogListResponse)
async def list_daily_logs_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("log_date"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List daily logs for a project."""
    _get_user(request)

    logs, total = await list_daily_logs(
        db,
        project_id=project_id,
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        sort=sort,
        order=order,
    )

    return DailyLogListResponse(
        data=[DailyLogResponse.model_validate(format_daily_log_response(log)) for log in logs],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


# ============================================================
# CREATE DAILY LOG
# ============================================================

@router.post("", response_model=dict, status_code=201)
async def create_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: DailyLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new daily log."""
    user = _get_user(request)

    log = await create_daily_log(
        db,
        project_id=project_id,
        organization_id=user["organization_id"],
        user=user,
        data=body,
    )

    return {
        "data": DailyLogResponse.model_validate(format_daily_log_response(log)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# GET DAILY LOG
# ============================================================

@router.get("/{daily_log_id}", response_model=dict)
async def get_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    daily_log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single daily log."""
    _get_user(request)

    log = await get_daily_log(db, daily_log_id, project_id)

    return {
        "data": DailyLogResponse.model_validate(format_daily_log_response(log)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# UPDATE DAILY LOG
# ============================================================

@router.patch("/{daily_log_id}", response_model=dict)
async def update_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    daily_log_id: uuid.UUID,
    body: DailyLogUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a daily log. Cannot edit approved logs."""
    user = _get_user(request)

    log = await update_daily_log(db, daily_log_id, project_id, user, body)

    return {
        "data": DailyLogResponse.model_validate(format_daily_log_response(log)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# DELETE DAILY LOG
# ============================================================

@router.delete("/{daily_log_id}", status_code=200)
async def delete_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    daily_log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a daily log. Cannot delete approved logs."""
    _get_user(request)

    await delete_daily_log(db, daily_log_id, project_id)

    return {"data": {"id": str(daily_log_id), "deleted": True}, "meta": {}}


# ============================================================
# SUBMIT DAILY LOG (DRAFT → SUBMITTED)
# ============================================================

@router.post("/{daily_log_id}/submit", response_model=dict)
async def submit_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    daily_log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Submit a daily log for approval. DRAFT → SUBMITTED."""
    user = _get_user(request)

    log = await submit_daily_log(db, daily_log_id, project_id, user)

    return {
        "data": DailyLogResponse.model_validate(format_daily_log_response(log)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# APPROVE DAILY LOG (SUBMITTED → APPROVED)
# ============================================================

@router.post("/{daily_log_id}/approve", response_model=dict)
async def approve_daily_log_endpoint(
    request: Request,
    project_id: uuid.UUID,
    daily_log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Approve a daily log. SUBMITTED → APPROVED. Management+ only."""
    user = _get_user(request)

    # Permission check: Management+ only
    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(status_code=403, detail="Only Management and above can approve daily logs")

    log = await approve_daily_log(db, daily_log_id, project_id, user)

    return {
        "data": DailyLogResponse.model_validate(format_daily_log_response(log)).model_dump(mode="json"),
        "meta": {},
    }
