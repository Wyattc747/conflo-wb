"""Drawing CRUD router — GC, Sub, and Owner portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.drawing import (
    DrawingSetCreate,
    DrawingSetListResponse,
    DrawingSetResponse,
    DrawingSetUpdate,
    DrawingSheetCreate,
    DrawingSheetResponse,
    DrawingSheetUpdate,
)
from app.services.drawing_service import (
    add_sheet,
    create_set,
    delete_set,
    format_drawing_set_response,
    format_sheet_response,
    get_set,
    get_sheet,
    list_sets,
    mark_current_set,
    remove_sheet,
    update_set,
    update_sheet,
    upload_revision,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/drawings", tags=["drawings"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=DrawingSetListResponse)
async def list_sets_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    discipline: str | None = Query(None),
    is_current_set: bool | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    sets, total = await list_sets(
        db, project_id=project_id, page=page, per_page=per_page,
        discipline=discipline, is_current_set=is_current_set,
        search=search, sort=sort, order=order,
    )
    data = []
    for s in sets:
        resp = await format_drawing_set_response(db, s)
        data.append(DrawingSetResponse.model_validate(resp))
    return DrawingSetListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_set_endpoint(
    request: Request, project_id: uuid.UUID, body: DrawingSetCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    drawing = await create_set(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{drawing_id}", response_model=dict)
async def get_set_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    drawing = await get_set(db, drawing_id, project_id)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{drawing_id}", response_model=dict)
async def update_set_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID, body: DrawingSetUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    drawing = await update_set(db, drawing_id, project_id, user, body)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{drawing_id}", status_code=200)
async def delete_set_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_set(db, drawing_id, project_id, user)
    return {"data": {"id": str(drawing_id), "deleted": True}, "meta": {}}


@gc_router.post("/{drawing_id}/mark-current", response_model=dict)
async def mark_current_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    drawing = await mark_current_set(db, drawing_id, project_id, user)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


# --- Sheets ---

@gc_router.post("/{drawing_id}/sheets", response_model=dict, status_code=201)
async def add_sheet_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    body: DrawingSheetCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await get_set(db, drawing_id, project_id)  # Verify drawing exists
    sheet = await add_sheet(db, drawing_id, user, body)
    return {"data": DrawingSheetResponse.model_validate(format_sheet_response(sheet)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{drawing_id}/sheets/{sheet_id}", response_model=dict)
async def update_sheet_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID, sheet_id: uuid.UUID,
    body: DrawingSheetUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    sheet = await update_sheet(db, sheet_id, user, body)
    return {"data": DrawingSheetResponse.model_validate(format_sheet_response(sheet)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{drawing_id}/sheets/{sheet_id}", status_code=200)
async def remove_sheet_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID, sheet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await remove_sheet(db, sheet_id, user)
    return {"data": {"id": str(sheet_id), "deleted": True}, "meta": {}}


@gc_router.post("/{drawing_id}/sheets/{sheet_id}/revise", response_model=dict)
async def revise_sheet_endpoint(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID, sheet_id: uuid.UUID,
    revision: str = Query(...), file_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    sheet = await upload_revision(db, sheet_id, user, revision, file_id)
    return {"data": DrawingSheetResponse.model_validate(format_sheet_response(sheet)).model_dump(mode="json"), "meta": {}}


# ============================================================
# SUB PORTAL — Read-only
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/drawings", tags=["sub-drawings"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=DrawingSetListResponse)
async def sub_list_sets(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    discipline: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    sets, total = await list_sets(db, project_id=project_id, page=page, per_page=per_page,
                                   discipline=discipline, search=search, sort=sort, order=order)
    data = []
    for s in sets:
        resp = await format_drawing_set_response(db, s)
        data.append(DrawingSetResponse.model_validate(resp))
    return DrawingSetListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@sub_router.get("/{drawing_id}", response_model=dict)
async def sub_get_set(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    drawing = await get_set(db, drawing_id, project_id)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


# ============================================================
# OWNER PORTAL — Read-only
# ============================================================

owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/drawings", tags=["owner-drawings"])


def _get_owner_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@owner_router.get("", response_model=DrawingSetListResponse)
async def owner_list_sets(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    discipline: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_owner_user(request)
    sets, total = await list_sets(db, project_id=project_id, page=page, per_page=per_page,
                                   discipline=discipline, search=search, sort=sort, order=order)
    data = []
    for s in sets:
        resp = await format_drawing_set_response(db, s)
        data.append(DrawingSetResponse.model_validate(resp))
    return DrawingSetListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@owner_router.get("/{drawing_id}", response_model=dict)
async def owner_get_set(
    request: Request, project_id: uuid.UUID, drawing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_owner_user(request)
    drawing = await get_set(db, drawing_id, project_id)
    resp = await format_drawing_set_response(db, drawing)
    return {"data": DrawingSetResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}
