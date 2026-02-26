"""Punch List CRUD router — GC, Sub, and Owner portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comment import Comment
from app.schemas.common import PaginationMeta
from app.schemas.punch_list import (
    PunchListCompleteRequest,
    PunchListItemCreate,
    PunchListItemResponse,
    PunchListItemUpdate,
    PunchListListResponse,
    PunchListVerifyRequest,
)
from app.services.punch_list_service import (
    close_punch_item,
    complete_punch_item,
    create_punch_item,
    dispute_punch_item,
    format_punch_item_response,
    get_punch_item,
    list_punch_items,
    update_punch_item,
    verify_punch_item,
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def _comment_count(db: AsyncSession, item_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Comment).where(
            Comment.commentable_type == "punch_list_item",
            Comment.commentable_id == item_id,
        )
    )
    return result.scalar() or 0


# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/punch-list", tags=["punch-list"])


@gc_router.get("", response_model=PunchListListResponse)
async def list_punch_items_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    category: str | None = Query(None),
    assigned_sub_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List punch list items for a project."""
    _get_user(request)
    items, total = await list_punch_items(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, priority=priority, category=category,
        assigned_sub_id=assigned_sub_id, search=search, sort=sort, order=order,
    )

    data = []
    for item in items:
        count = await _comment_count(db, item.id)
        data.append(PunchListItemResponse.model_validate(format_punch_item_response(item, comments_count=count)))

    return PunchListListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: PunchListItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new punch list item."""
    user = _get_user(request)
    item = await create_punch_item(
        db, project_id=project_id,
        organization_id=user["organization_id"],
        user=user, data=body,
    )
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{item_id}", response_model=dict)
async def get_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single punch list item."""
    _get_user(request)
    item = await get_punch_item(db, item_id, project_id)
    count = await _comment_count(db, item.id)
    return {
        "data": PunchListItemResponse.model_validate(
            format_punch_item_response(item, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{item_id}", response_model=dict)
async def update_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    body: PunchListItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a punch list item."""
    user = _get_user(request)
    item = await update_punch_item(db, item_id, project_id, user, body)
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{item_id}", status_code=200)
async def delete_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a punch list item."""
    user = _get_user(request)
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete punch list items")
    item = await get_punch_item(db, item_id, project_id)
    from datetime import datetime, timezone
    item.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"data": {"id": str(item_id), "deleted": True}, "meta": {}}


@gc_router.post("/{item_id}/verify", response_model=dict)
async def verify_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    body: PunchListVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """GC verifies a completed punch item."""
    user = _get_user(request)
    item = await verify_punch_item(db, item_id, project_id, user, body)
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{item_id}/close", response_model=dict)
async def close_punch_item_endpoint(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Close a verified punch item. VERIFIED → CLOSED."""
    user = _get_user(request)
    item = await close_punch_item(db, item_id, project_id, user)
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# SUB PORTAL
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/punch-list", tags=["sub-punch-list"])


@sub_router.get("", response_model=PunchListListResponse)
async def sub_list_punch_items(
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
    """List punch items assigned to this sub."""
    user = _get_user(request)
    items, total = await list_punch_items(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, search=search, sort=sort, order=order,
        assigned_sub_id=user.get("sub_company_id"),
    )
    data = []
    for item in items:
        count = await _comment_count(db, item.id)
        data.append(PunchListItemResponse.model_validate(format_punch_item_response(item, comments_count=count)))

    return PunchListListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@sub_router.get("/{item_id}", response_model=dict)
async def sub_get_punch_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single punch list item (sub portal)."""
    _get_user(request)
    item = await get_punch_item(db, item_id, project_id)
    count = await _comment_count(db, item.id)
    return {
        "data": PunchListItemResponse.model_validate(
            format_punch_item_response(item, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{item_id}/complete", response_model=dict)
async def sub_complete_punch_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    body: PunchListCompleteRequest = PunchListCompleteRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Sub marks a punch item as completed."""
    user = _get_user(request)
    item = await complete_punch_item(db, item_id, project_id, user, body)
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{item_id}/dispute", response_model=dict)
async def sub_dispute_punch_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sub disputes a punch item."""
    user = _get_user(request)
    item = await dispute_punch_item(db, item_id, project_id, user)
    return {
        "data": PunchListItemResponse.model_validate(format_punch_item_response(item)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# OWNER PORTAL (Read-only)
# ============================================================

owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/punch-list", tags=["owner-punch-list"])


@owner_router.get("", response_model=PunchListListResponse)
async def owner_list_punch_items(
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
    """List punch items (owner portal — read-only)."""
    _get_user(request)
    items, total = await list_punch_items(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, search=search, sort=sort, order=order,
    )
    data = []
    for item in items:
        count = await _comment_count(db, item.id)
        data.append(PunchListItemResponse.model_validate(format_punch_item_response(item, comments_count=count)))

    return PunchListListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@owner_router.get("/{item_id}", response_model=dict)
async def owner_get_punch_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single punch list item (owner portal — read-only)."""
    _get_user(request)
    item = await get_punch_item(db, item_id, project_id)
    count = await _comment_count(db, item.id)
    return {
        "data": PunchListItemResponse.model_validate(
            format_punch_item_response(item, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }
