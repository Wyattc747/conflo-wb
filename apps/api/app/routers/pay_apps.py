"""Pay Application router — GC, Sub, and Owner portals."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.pay_app import (
    PayAppCreate,
    PayAppDecision,
    PayAppListResponse,
    PayAppResponse,
)
from app.services.pay_app_service import (
    approve_pay_app,
    create_pay_app,
    format_pay_app_response,
    get_pay_app,
    list_pay_apps,
    reject_pay_app,
    submit_pay_app,
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/pay-apps", tags=["pay-apps"])


@gc_router.get("", response_model=PayAppListResponse)
async def gc_list_pay_apps(
    request: Request,
    project_id: uuid.UUID,
    pay_app_type: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List pay apps. Filter by type (SUB_TO_GC or GC_TO_OWNER)."""
    _get_user(request)

    apps, total = await list_pay_apps(db, project_id, pay_app_type=pay_app_type, status=status, page=page, per_page=per_page)

    return PayAppListResponse(
        data=[PayAppResponse.model_validate(format_pay_app_response(pa)) for pa in apps],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def gc_create_pay_app(
    request: Request,
    project_id: uuid.UUID,
    body: PayAppCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a pay app (GC_TO_OWNER)."""
    user = _get_user(request)
    pa = await create_pay_app(db, project_id, user["organization_id"], user, body)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{pay_app_id}", response_model=dict)
async def gc_get_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    pa = await get_pay_app(db, pay_app_id, project_id)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{pay_app_id}/submit", response_model=dict)
async def gc_submit_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pa = await submit_pay_app(db, pay_app_id, project_id, user)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{pay_app_id}/approve", response_model=dict)
async def gc_approve_sub_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    body: PayAppDecision | None = None,
    db: AsyncSession = Depends(get_db),
):
    """GC approves a sub's pay app."""
    user = _get_user(request)
    notes = body.notes if body else None
    pa = await approve_pay_app(db, pay_app_id, project_id, user, notes)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{pay_app_id}/reject", response_model=dict)
async def gc_reject_sub_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    body: PayAppDecision | None = None,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    reason = body.notes if body else None
    pa = await reject_pay_app(db, pay_app_id, project_id, user, reason)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# SUB PORTAL
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/pay-apps", tags=["sub-pay-apps"])


@sub_router.get("", response_model=PayAppListResponse)
async def sub_list_pay_apps(
    request: Request,
    project_id: uuid.UUID,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    sub_company_id = user.get("sub_company_id")
    apps, total = await list_pay_apps(
        db, project_id, pay_app_type="SUB_TO_GC",
        sub_company_id=sub_company_id, status=status, page=page, per_page=per_page,
    )
    return PayAppListResponse(
        data=[PayAppResponse.model_validate(format_pay_app_response(pa)) for pa in apps],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@sub_router.post("", response_model=dict, status_code=201)
async def sub_create_pay_app(
    request: Request,
    project_id: uuid.UUID,
    body: PayAppCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    body.pay_app_type = "SUB_TO_GC"
    body.sub_company_id = user.get("sub_company_id")
    pa = await create_pay_app(db, project_id, user.get("organization_id"), user, body)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.get("/{pay_app_id}", response_model=dict)
async def sub_get_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    pa = await get_pay_app(db, pay_app_id, project_id)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{pay_app_id}/submit", response_model=dict)
async def sub_submit_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pa = await submit_pay_app(db, pay_app_id, project_id, user)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# OWNER PORTAL
# ============================================================

owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/pay-apps", tags=["owner-pay-apps"])


@owner_router.get("", response_model=PayAppListResponse)
async def owner_list_pay_apps(
    request: Request,
    project_id: uuid.UUID,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    apps, total = await list_pay_apps(
        db, project_id, pay_app_type="GC_TO_OWNER", status=status, page=page, per_page=per_page,
    )
    return PayAppListResponse(
        data=[PayAppResponse.model_validate(format_pay_app_response(pa)) for pa in apps],
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@owner_router.get("/{pay_app_id}", response_model=dict)
async def owner_get_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    pa = await get_pay_app(db, pay_app_id, project_id)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@owner_router.post("/{pay_app_id}/approve", response_model=dict)
async def owner_approve_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    body: PayAppDecision | None = None,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    notes = body.notes if body else None
    pa = await approve_pay_app(db, pay_app_id, project_id, user, notes)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }


@owner_router.post("/{pay_app_id}/reject", response_model=dict)
async def owner_reject_pay_app(
    request: Request,
    project_id: uuid.UUID,
    pay_app_id: uuid.UUID,
    body: PayAppDecision | None = None,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    reason = body.notes if body else None
    pa = await reject_pay_app(db, pay_app_id, project_id, user, reason)
    return {
        "data": PayAppResponse.model_validate(format_pay_app_response(pa)).model_dump(mode="json"),
        "meta": {},
    }
