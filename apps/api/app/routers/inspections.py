"""Inspection CRUD router — Templates (org-level) + Inspections (project-level)."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comment import Comment
from app.schemas.common import PaginationMeta
from app.schemas.inspection import (
    InspectionCreate,
    InspectionListResponse,
    InspectionResponse,
    InspectionResultSubmit,
    InspectionTemplateCreate,
    InspectionTemplateListResponse,
    InspectionTemplateResponse,
    InspectionTemplateUpdate,
    InspectionUpdate,
)
from app.services.inspection_service import (
    complete_inspection,
    create_inspection,
    create_template,
    delete_template,
    format_inspection_response,
    format_template_response,
    get_inspection,
    get_template,
    list_inspections,
    list_templates,
    start_inspection,
    update_inspection,
    update_template,
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def _comment_count(db: AsyncSession, inspection_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Comment).where(
            Comment.commentable_type == "inspection",
            Comment.commentable_id == inspection_id,
        )
    )
    return result.scalar() or 0


# ============================================================
# TEMPLATES (org-level)
# ============================================================

template_router = APIRouter(prefix="/api/gc/inspection-templates", tags=["inspection-templates"])


@template_router.get("", response_model=InspectionTemplateListResponse)
async def list_templates_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List inspection templates for the org."""
    user = _get_user(request)
    templates = await list_templates(db, user["organization_id"])
    data = [InspectionTemplateResponse.model_validate(format_template_response(t)) for t in templates]
    return InspectionTemplateListResponse(data=data, meta={})


@template_router.post("", response_model=dict, status_code=201)
async def create_template_endpoint(
    request: Request,
    body: InspectionTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create an inspection template."""
    user = _get_user(request)
    template = await create_template(db, user["organization_id"], body)
    return {
        "data": InspectionTemplateResponse.model_validate(format_template_response(template)).model_dump(mode="json"),
        "meta": {},
    }


@template_router.get("/{template_id}", response_model=dict)
async def get_template_endpoint(
    request: Request,
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single inspection template."""
    _get_user(request)
    template = await get_template(db, template_id)
    return {
        "data": InspectionTemplateResponse.model_validate(format_template_response(template)).model_dump(mode="json"),
        "meta": {},
    }


@template_router.patch("/{template_id}", response_model=dict)
async def update_template_endpoint(
    request: Request,
    template_id: uuid.UUID,
    body: InspectionTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an inspection template."""
    _get_user(request)
    template = await update_template(db, template_id, body)
    return {
        "data": InspectionTemplateResponse.model_validate(format_template_response(template)).model_dump(mode="json"),
        "meta": {},
    }


@template_router.delete("/{template_id}", status_code=200)
async def delete_template_endpoint(
    request: Request,
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an inspection template."""
    _get_user(request)
    await delete_template(db, template_id)
    return {"data": {"id": str(template_id), "deleted": True}, "meta": {}}


# ============================================================
# INSPECTIONS (project-level)
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/inspections", tags=["inspections"])


@gc_router.get("", response_model=InspectionListResponse)
async def list_inspections_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List inspections for a project."""
    _get_user(request)
    inspections, total = await list_inspections(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, category=category, search=search, sort=sort, order=order,
    )

    data = []
    for insp in inspections:
        count = await _comment_count(db, insp.id)
        data.append(InspectionResponse.model_validate(format_inspection_response(insp, comments_count=count)))

    return InspectionListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: InspectionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new inspection."""
    user = _get_user(request)
    inspection = await create_inspection(
        db, project_id=project_id,
        organization_id=user["organization_id"],
        user=user, data=body,
    )
    return {
        "data": InspectionResponse.model_validate(format_inspection_response(inspection)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{inspection_id}", response_model=dict)
async def get_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single inspection."""
    _get_user(request)
    inspection = await get_inspection(db, inspection_id, project_id)
    count = await _comment_count(db, inspection.id)
    return {
        "data": InspectionResponse.model_validate(
            format_inspection_response(inspection, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{inspection_id}", response_model=dict)
async def update_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    inspection_id: uuid.UUID,
    body: InspectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an inspection."""
    user = _get_user(request)
    inspection = await update_inspection(db, inspection_id, project_id, user, body)
    return {
        "data": InspectionResponse.model_validate(format_inspection_response(inspection)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{inspection_id}", status_code=200)
async def delete_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an inspection."""
    user = _get_user(request)
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete inspections")
    inspection = await get_inspection(db, inspection_id, project_id)
    from datetime import datetime, timezone
    inspection.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"data": {"id": str(inspection_id), "deleted": True}, "meta": {}}


@gc_router.post("/{inspection_id}/start", response_model=dict)
async def start_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Start an inspection. SCHEDULED → IN_PROGRESS."""
    user = _get_user(request)
    inspection = await start_inspection(db, inspection_id, project_id, user)
    return {
        "data": InspectionResponse.model_validate(format_inspection_response(inspection)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{inspection_id}/complete", response_model=dict)
async def complete_inspection_endpoint(
    request: Request,
    project_id: uuid.UUID,
    inspection_id: uuid.UUID,
    body: InspectionResultSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit inspection results."""
    user = _get_user(request)
    inspection = await complete_inspection(db, inspection_id, project_id, user, body)
    return {
        "data": InspectionResponse.model_validate(format_inspection_response(inspection)).model_dump(mode="json"),
        "meta": {},
    }
