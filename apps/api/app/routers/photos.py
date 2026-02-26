"""Photo CRUD router — GC and Sub portal endpoints."""
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.photo import (
    PhotoCreate,
    PhotoListResponse,
    PhotoResponse,
    PhotoUpdate,
)
from app.services.photo_service import (
    create_photo,
    delete_photo,
    format_photo_response,
    get_photo,
    list_photos,
    update_photo,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/photos", tags=["photos"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=PhotoListResponse)
async def list_photos_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    linked_type: str | None = Query(None), linked_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None), date_to: datetime | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    photos, total = await list_photos(
        db, project_id=project_id, page=page, per_page=per_page,
        linked_type=linked_type, linked_id=linked_id,
        date_from=date_from, date_to=date_to, search=search,
        sort=sort, order=order,
    )
    data = [PhotoResponse.model_validate(format_photo_response(p)) for p in photos]
    return PhotoListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_photo_endpoint(
    request: Request, project_id: uuid.UUID, body: PhotoCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    photo = await create_photo(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": PhotoResponse.model_validate(format_photo_response(photo)).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{photo_id}", response_model=dict)
async def get_photo_endpoint(
    request: Request, project_id: uuid.UUID, photo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    photo = await get_photo(db, photo_id, project_id)
    return {"data": PhotoResponse.model_validate(format_photo_response(photo)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{photo_id}", response_model=dict)
async def update_photo_endpoint(
    request: Request, project_id: uuid.UUID, photo_id: uuid.UUID, body: PhotoUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    photo = await update_photo(db, photo_id, project_id, user, body)
    return {"data": PhotoResponse.model_validate(format_photo_response(photo)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{photo_id}", status_code=200)
async def delete_photo_endpoint(
    request: Request, project_id: uuid.UUID, photo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_photo(db, photo_id, project_id, user)
    return {"data": {"id": str(photo_id), "deleted": True}, "meta": {}}


# ============================================================
# SUB PORTAL — Read-only
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/photos", tags=["sub-photos"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=PhotoListResponse)
async def sub_list_photos(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    linked_type: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    photos, total = await list_photos(db, project_id=project_id, page=page, per_page=per_page,
                                       linked_type=linked_type, search=search, sort=sort, order=order)
    data = [PhotoResponse.model_validate(format_photo_response(p)) for p in photos]
    return PhotoListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@sub_router.get("/{photo_id}", response_model=dict)
async def sub_get_photo(
    request: Request, project_id: uuid.UUID, photo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    photo = await get_photo(db, photo_id, project_id)
    return {"data": PhotoResponse.model_validate(format_photo_response(photo)).model_dump(mode="json"), "meta": {}}
