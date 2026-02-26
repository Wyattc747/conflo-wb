"""RFI CRUD router — GC and Sub portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comment import Comment
from app.schemas.common import PaginationMeta
from app.schemas.rfi import (
    RfiCreate,
    RfiListResponse,
    RfiResponse,
    RfiResponseCreate,
    RfiUpdate,
)
from app.services.rfi_service import (
    close_rfi,
    create_rfi,
    format_rfi_response,
    get_rfi,
    list_rfis,
    reopen_rfi,
    respond_to_rfi,
    update_rfi,
)

# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/rfis", tags=["rfis"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def _comment_count(db: AsyncSession, rfi_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Comment).where(
            Comment.commentable_type == "rfi",
            Comment.commentable_id == rfi_id,
        )
    )
    return result.scalar() or 0


@gc_router.get("", response_model=RfiListResponse)
async def list_rfis_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List RFIs for a project."""
    _get_user(request)

    rfis, total = await list_rfis(
        db,
        project_id=project_id,
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        search=search,
        sort=sort,
        order=order,
    )

    data = []
    for rfi in rfis:
        count = await _comment_count(db, rfi.id)
        data.append(RfiResponse.model_validate(format_rfi_response(rfi, comments_count=count)))

    return RfiListResponse(
        data=data,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: RfiCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new RFI."""
    user = _get_user(request)

    rfi = await create_rfi(
        db,
        project_id=project_id,
        organization_id=user["organization_id"],
        user=user,
        data=body,
    )

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{rfi_id}", response_model=dict)
async def get_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single RFI."""
    _get_user(request)

    rfi = await get_rfi(db, rfi_id, project_id)
    count = await _comment_count(db, rfi.id)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi, comments_count=count)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{rfi_id}", response_model=dict)
async def update_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    body: RfiUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an RFI. Cannot edit closed RFIs."""
    user = _get_user(request)

    rfi = await update_rfi(db, rfi_id, project_id, user, body)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{rfi_id}", status_code=200)
async def delete_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an RFI. Owner/Admin only."""
    user = _get_user(request)

    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete RFIs")

    rfi = await get_rfi(db, rfi_id, project_id)
    # Soft delete — set deleted_at if the model supports it, otherwise hard delete
    if hasattr(rfi, "deleted_at"):
        from datetime import datetime, timezone
        rfi.deleted_at = datetime.now(timezone.utc)
    else:
        await db.delete(rfi)
    await db.flush()

    return {"data": {"id": str(rfi_id), "deleted": True}, "meta": {}}


# ============================================================
# RFI STATUS TRANSITIONS
# ============================================================

@gc_router.post("/{rfi_id}/respond", response_model=dict)
async def respond_to_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    body: RfiResponseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit an official response. OPEN → RESPONDED."""
    user = _get_user(request)

    rfi = await respond_to_rfi(db, rfi_id, project_id, user, body)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{rfi_id}/close", response_model=dict)
async def close_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Close an RFI. RESPONDED|OPEN → CLOSED."""
    user = _get_user(request)

    rfi = await close_rfi(db, rfi_id, project_id, user)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{rfi_id}/reopen", response_model=dict)
async def reopen_rfi_endpoint(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reopen a closed RFI. CLOSED → OPEN."""
    user = _get_user(request)

    rfi = await reopen_rfi(db, rfi_id, project_id, user)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# SUB PORTAL — RFIs
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/rfis", tags=["sub-rfis"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=RfiListResponse)
async def sub_list_rfis(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List RFIs visible to sub user on a project."""
    _get_sub_user(request)

    # Subs can see all RFIs on projects they're assigned to
    rfis, total = await list_rfis(
        db,
        project_id=project_id,
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        sort=sort,
        order=order,
    )

    data = []
    for rfi in rfis:
        count = await _comment_count(db, rfi.id)
        data.append(RfiResponse.model_validate(format_rfi_response(rfi, comments_count=count)))

    return RfiListResponse(
        data=data,
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@sub_router.get("/{rfi_id}", response_model=dict)
async def sub_get_rfi(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single RFI (sub portal)."""
    _get_sub_user(request)

    rfi = await get_rfi(db, rfi_id, project_id)
    count = await _comment_count(db, rfi.id)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi, comments_count=count)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("", response_model=dict, status_code=201)
async def sub_create_rfi(
    request: Request,
    project_id: uuid.UUID,
    body: RfiCreate,
    db: AsyncSession = Depends(get_db),
):
    """Sub creates a new RFI."""
    user = _get_sub_user(request)

    rfi = await create_rfi(
        db,
        project_id=project_id,
        organization_id=user.get("organization_id"),
        user=user,
        data=body,
    )

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{rfi_id}/respond", response_model=dict)
async def sub_respond_to_rfi(
    request: Request,
    project_id: uuid.UUID,
    rfi_id: uuid.UUID,
    body: RfiResponseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Sub responds to an assigned RFI."""
    user = _get_sub_user(request)

    rfi = await respond_to_rfi(db, rfi_id, project_id, user, body)

    return {
        "data": RfiResponse.model_validate(format_rfi_response(rfi)).model_dump(mode="json"),
        "meta": {},
    }
