"""Procurement CRUD router — GC portal only."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.procurement import (
    ProcurementCreate,
    ProcurementListResponse,
    ProcurementResponse,
    ProcurementTransition,
    ProcurementUpdate,
)
from app.services.procurement_service import (
    create_procurement,
    delete_procurement,
    format_procurement_response,
    get_procurement,
    list_procurement,
    transition_procurement,
    update_procurement,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/procurement", tags=["procurement"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=ProcurementListResponse)
async def list_procurement_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None), category: str | None = Query(None),
    vendor: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    items, total = await list_procurement(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, category=category, vendor=vendor, search=search,
        sort=sort, order=order,
    )
    data = [ProcurementResponse.model_validate(format_procurement_response(i)) for i in items]
    return ProcurementListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_procurement_endpoint(
    request: Request, project_id: uuid.UUID, body: ProcurementCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await create_procurement(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{item_id}", response_model=dict)
async def get_procurement_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    item = await get_procurement(db, item_id, project_id)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{item_id}", response_model=dict)
async def update_procurement_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID, body: ProcurementUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await update_procurement(db, item_id, project_id, user, body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{item_id}", status_code=200)
async def delete_procurement_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_procurement(db, item_id, project_id, user)
    return {"data": {"id": str(item_id), "deleted": True}, "meta": {}}


# --- Status Transitions ---

@gc_router.post("/{item_id}/quote", response_model=dict)
async def quote_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    body: ProcurementTransition = ProcurementTransition(),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await transition_procurement(db, item_id, project_id, user, "quote", body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{item_id}/order", response_model=dict)
async def order_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    body: ProcurementTransition = ProcurementTransition(),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await transition_procurement(db, item_id, project_id, user, "order", body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{item_id}/ship", response_model=dict)
async def ship_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    body: ProcurementTransition = ProcurementTransition(),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await transition_procurement(db, item_id, project_id, user, "ship", body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{item_id}/deliver", response_model=dict)
async def deliver_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    body: ProcurementTransition = ProcurementTransition(),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await transition_procurement(db, item_id, project_id, user, "deliver", body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{item_id}/install", response_model=dict)
async def install_endpoint(
    request: Request, project_id: uuid.UUID, item_id: uuid.UUID,
    body: ProcurementTransition = ProcurementTransition(),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    item = await transition_procurement(db, item_id, project_id, user, "install", body)
    return {"data": ProcurementResponse.model_validate(format_procurement_response(item)).model_dump(mode="json"), "meta": {}}
