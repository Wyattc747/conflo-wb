"""Change Order router — GC, Sub, and Owner portals."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderListResponse,
    ChangeOrderResponse,
    ChangeOrderUpdate,
    OwnerDecision,
    SubPricingSubmit,
)
from app.schemas.common import PaginationMeta
from app.services.change_order_service import (
    create_change_order,
    delete_change_order,
    format_change_order_response,
    get_change_order,
    list_change_orders,
    owner_decision,
    submit_sub_pricing,
    submit_to_owner,
    update_change_order,
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/change-orders", tags=["change-orders"])


@gc_router.get("", response_model=ChangeOrderListResponse)
async def gc_list_cos(
    request: Request,
    project_id: uuid.UUID,
    status: str | None = Query(None),
    reason: str | None = Query(None),
    priority: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    cos, total = await list_change_orders(
        db, project_id, page=page, per_page=per_page,
        status=status, reason=reason, priority=priority, search=search, sort=sort, order=order,
    )
    return ChangeOrderListResponse(
        data=[ChangeOrderResponse.model_validate(format_change_order_response(co)) for co in cos],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def gc_create_co(
    request: Request,
    project_id: uuid.UUID,
    body: ChangeOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    co = await create_change_order(db, project_id, user["organization_id"], user, body)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{co_id}", response_model=dict)
async def gc_get_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    co = await get_change_order(db, co_id, project_id)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{co_id}", response_model=dict)
async def gc_update_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    body: ChangeOrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    co = await update_change_order(db, co_id, project_id, user, body)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{co_id}", status_code=200)
async def gc_delete_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(403, "Only Owner/Admin can delete change orders")
    await delete_change_order(db, co_id, project_id)
    return {"data": {"id": str(co_id), "deleted": True}, "meta": {}}


@gc_router.post("/{co_id}/submit-to-owner", response_model=dict)
async def gc_submit_co_to_owner(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    co = await submit_to_owner(db, co_id, project_id, user)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# SUB PORTAL
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/change-orders", tags=["sub-change-orders"])


@sub_router.get("", response_model=ChangeOrderListResponse)
async def sub_list_cos(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    cos, total = await list_change_orders(db, project_id, page=page, per_page=per_page)
    return ChangeOrderListResponse(
        data=[ChangeOrderResponse.model_validate(format_change_order_response(co)) for co in cos],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@sub_router.get("/{co_id}", response_model=dict)
async def sub_get_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    co = await get_change_order(db, co_id, project_id)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{co_id}/submit-pricing", response_model=dict)
async def sub_submit_pricing(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    body: SubPricingSubmit,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    sub_company_id = user.get("sub_company_id")
    if not sub_company_id:
        raise HTTPException(403, "Sub company ID required")
    co = await submit_sub_pricing(db, co_id, project_id, sub_company_id, body)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# OWNER PORTAL
# ============================================================

owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/change-orders", tags=["owner-change-orders"])


@owner_router.get("", response_model=ChangeOrderListResponse)
async def owner_list_cos(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    cos, total = await list_change_orders(
        db, project_id, status="SUBMITTED_TO_OWNER", page=page, per_page=per_page,
    )
    # Also include approved/rejected for history
    all_cos, all_total = await list_change_orders(
        db, project_id, page=page, per_page=per_page,
    )
    owner_cos = [co for co in all_cos if co.status in ("SUBMITTED_TO_OWNER", "APPROVED", "REJECTED")]

    return ChangeOrderListResponse(
        data=[ChangeOrderResponse.model_validate(format_change_order_response(co)) for co in owner_cos],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=len(owner_cos),
            total_pages=1,
        ),
    )


@owner_router.get("/{co_id}", response_model=dict)
async def owner_get_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    co = await get_change_order(db, co_id, project_id)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@owner_router.post("/{co_id}/approve", response_model=dict)
async def owner_approve_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    body: OwnerDecision | None = None,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    notes = body.notes if body else None
    co = await owner_decision(db, co_id, project_id, user, "APPROVED", notes)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }


@owner_router.post("/{co_id}/reject", response_model=dict)
async def owner_reject_co(
    request: Request,
    project_id: uuid.UUID,
    co_id: uuid.UUID,
    body: OwnerDecision,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    co = await owner_decision(db, co_id, project_id, user, "REJECTED", body.notes)
    return {
        "data": ChangeOrderResponse.model_validate(format_change_order_response(co)).model_dump(mode="json"),
        "meta": {},
    }
