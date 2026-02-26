"""Submittal CRUD router — GC and Sub portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comment import Comment
from app.schemas.common import PaginationMeta
from app.schemas.submittal import (
    SubmittalCreate,
    SubmittalListResponse,
    SubmittalResponse,
    SubmittalRevisionCreate,
    SubmittalReviewRequest,
    SubmittalUpdate,
)
from app.services.submittal_service import (
    create_revision,
    create_submittal,
    format_submittal_response,
    get_revision_history,
    get_submittal,
    list_submittals,
    review_submittal,
    submit_submittal,
    update_submittal,
)
from app.services.numbering_service import format_number

# ============================================================
# GC PORTAL
# ============================================================

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/submittals", tags=["submittals"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def _comment_count(db: AsyncSession, submittal_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Comment).where(
            Comment.commentable_type == "submittal",
            Comment.commentable_id == submittal_id,
        )
    )
    return result.scalar() or 0


def _build_revision_history(revisions: list) -> list[dict]:
    return [
        {
            "revision": r.revision,
            "formatted_number": format_number("submittal", r.number, r.revision),
            "status": r.status,
            "created_at": r.created_at,
            "reviewed_at": r.reviewed_at,
        }
        for r in revisions
    ]


@gc_router.get("", response_model=SubmittalListResponse)
async def list_submittals_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    submittal_type: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("number"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List submittals for a project (latest revision per base number)."""
    _get_user(request)

    submittals, total = await list_submittals(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, submittal_type=submittal_type, search=search,
        sort=sort, order=order,
    )

    data = []
    for s in submittals:
        count = await _comment_count(db, s.id)
        data.append(SubmittalResponse.model_validate(format_submittal_response(s, comments_count=count)))

    return SubmittalListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: SubmittalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new submittal."""
    user = _get_user(request)

    submittal = await create_submittal(
        db, project_id=project_id,
        organization_id=user["organization_id"],
        user=user, data=body,
    )

    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.get("/{submittal_id}", response_model=dict)
async def get_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single submittal with revision history."""
    _get_user(request)

    submittal = await get_submittal(db, submittal_id, project_id)
    count = await _comment_count(db, submittal.id)
    revisions = await get_revision_history(db, project_id, submittal.number)
    rev_history = _build_revision_history(revisions)

    return {
        "data": SubmittalResponse.model_validate(
            format_submittal_response(submittal, revision_history=rev_history, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{submittal_id}", response_model=dict)
async def update_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    body: SubmittalUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a submittal (DRAFT only)."""
    user = _get_user(request)
    submittal = await update_submittal(db, submittal_id, project_id, user, body)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{submittal_id}", status_code=200)
async def delete_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a submittal."""
    user = _get_user(request)
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete submittals")

    submittal = await get_submittal(db, submittal_id, project_id)
    from datetime import datetime, timezone
    submittal.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    return {"data": {"id": str(submittal_id), "deleted": True}, "meta": {}}


@gc_router.post("/{submittal_id}/submit", response_model=dict)
async def submit_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Submit for review. DRAFT → SUBMITTED."""
    user = _get_user(request)
    submittal = await submit_submittal(db, submittal_id, project_id, user)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{submittal_id}/review", response_model=dict)
async def review_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    body: SubmittalReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Review a submittal. { decision, notes }."""
    user = _get_user(request)
    submittal = await review_submittal(db, submittal_id, project_id, user, body)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.post("/{submittal_id}/revise", response_model=dict, status_code=201)
async def revise_submittal_endpoint(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    body: SubmittalRevisionCreate = SubmittalRevisionCreate(),
    db: AsyncSession = Depends(get_db),
):
    """Create a new revision of a REVISE_AND_RESUBMIT submittal."""
    user = _get_user(request)
    new_submittal = await create_revision(db, submittal_id, project_id, user, body)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(new_submittal)).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# SUB PORTAL
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/submittals", tags=["sub-submittals"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=SubmittalListResponse)
async def sub_list_submittals(
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
    """List submittals visible to sub user."""
    user = _get_sub_user(request)

    submittals, total = await list_submittals(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, search=search, sort=sort, order=order,
        sub_company_id=user.get("sub_company_id"),
    )

    data = []
    for s in submittals:
        count = await _comment_count(db, s.id)
        data.append(SubmittalResponse.model_validate(format_submittal_response(s, comments_count=count)))

    return SubmittalListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ).model_dump(),
    )


@sub_router.get("/{submittal_id}", response_model=dict)
async def sub_get_submittal(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single submittal (sub portal)."""
    _get_sub_user(request)
    submittal = await get_submittal(db, submittal_id, project_id)
    count = await _comment_count(db, submittal.id)
    revisions = await get_revision_history(db, project_id, submittal.number)
    rev_history = _build_revision_history(revisions)

    return {
        "data": SubmittalResponse.model_validate(
            format_submittal_response(submittal, revision_history=rev_history, comments_count=count)
        ).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("", response_model=dict, status_code=201)
async def sub_create_submittal(
    request: Request,
    project_id: uuid.UUID,
    body: SubmittalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Sub creates a new submittal."""
    user = _get_sub_user(request)
    submittal = await create_submittal(
        db, project_id=project_id,
        organization_id=user.get("organization_id"),
        user=user, data=body,
    )
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{submittal_id}/submit", response_model=dict)
async def sub_submit_submittal(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Sub submits a submittal to GC."""
    user = _get_sub_user(request)
    submittal = await submit_submittal(db, submittal_id, project_id, user)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(submittal)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{submittal_id}/revise", response_model=dict, status_code=201)
async def sub_revise_submittal(
    request: Request,
    project_id: uuid.UUID,
    submittal_id: uuid.UUID,
    body: SubmittalRevisionCreate = SubmittalRevisionCreate(),
    db: AsyncSession = Depends(get_db),
):
    """Sub creates a new revision."""
    user = _get_sub_user(request)
    new_submittal = await create_revision(db, submittal_id, project_id, user, body)
    return {
        "data": SubmittalResponse.model_validate(format_submittal_response(new_submittal)).model_dump(mode="json"),
        "meta": {},
    }
