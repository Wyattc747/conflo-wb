"""Transmittal CRUD router — GC portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comment import Comment
from app.schemas.common import PaginationMeta
from app.schemas.transmittal import (
    TransmittalCreate,
    TransmittalListResponse,
    TransmittalResponse,
    TransmittalUpdate,
)
from app.services.transmittal_service import (
    confirm_transmittal,
    create_transmittal,
    format_transmittal_response,
    get_transmittal,
    list_transmittals,
    send_transmittal,
    update_transmittal,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/transmittals", tags=["transmittals"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def _comment_count(db: AsyncSession, transmittal_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Comment).where(
            Comment.commentable_type == "transmittal",
            Comment.commentable_id == transmittal_id,
        )
    )
    return result.scalar() or 0


@gc_router.get("", response_model=TransmittalListResponse)
async def list_transmittals_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    purpose: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List transmittals for a project."""
    _get_user(request)

    transmittals, total = await list_transmittals(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, purpose=purpose, search=search, sort=sort, order=order,
    )

    data = []
    for t in transmittals:
        count = await _comment_count(db, t.id)
        data.append(TransmittalResponse.model_validate(format_transmittal_response(t, comments_count=count)))

    return TransmittalListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: TransmittalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new transmittal."""
    user = _get_user(request)
    transmittal = await create_transmittal(
        db, project_id=project_id,
        organization_id=user["organization_id"],
        user=user, data=body,
    )
    return {
        "data": TransmittalResponse.model_validate(format_transmittal_response(transmittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{transmittal_id}", response_model=dict)
async def get_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    transmittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single transmittal."""
    _get_user(request)
    transmittal = await get_transmittal(db, transmittal_id, project_id)
    count = await _comment_count(db, transmittal.id)
    return {
        "data": TransmittalResponse.model_validate(
            format_transmittal_response(transmittal, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{transmittal_id}", response_model=dict)
async def update_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    transmittal_id: uuid.UUID,
    body: TransmittalUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a transmittal (DRAFT only)."""
    user = _get_user(request)
    transmittal = await update_transmittal(db, transmittal_id, project_id, user, body)
    return {
        "data": TransmittalResponse.model_validate(format_transmittal_response(transmittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{transmittal_id}", status_code=200)
async def delete_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    transmittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a transmittal."""
    user = _get_user(request)
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete transmittals")

    transmittal = await get_transmittal(db, transmittal_id, project_id)
    from datetime import datetime, timezone
    transmittal.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"data": {"id": str(transmittal_id), "deleted": True}, "meta": {}}


@gc_router.post("/{transmittal_id}/send", response_model=dict)
async def send_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    transmittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Send a transmittal. DRAFT → SENT."""
    user = _get_user(request)
    transmittal = await send_transmittal(db, transmittal_id, project_id, user)
    return {
        "data": TransmittalResponse.model_validate(format_transmittal_response(transmittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{transmittal_id}/confirm", response_model=dict)
async def confirm_transmittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    transmittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Confirm received. SENT → RECEIVED."""
    user = _get_user(request)
    transmittal = await confirm_transmittal(db, transmittal_id, project_id, user)
    return {
        "data": TransmittalResponse.model_validate(format_transmittal_response(transmittal)).model_dump(mode="json"),
        "meta": {},
    }
