"""Comments router — polymorphic threads for any commentable entity."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.comment import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
)
from app.schemas.common import PaginationMeta
from app.services.comment_service import (
    create_comment,
    delete_comment,
    format_comment_response,
    get_comment,
    list_comments,
    update_comment,
)

# ============================================================
# GC PORTAL — Comments
# ============================================================

gc_router = APIRouter(
    prefix="/api/gc/projects/{project_id}/comments",
    tags=["comments"],
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=CommentListResponse)
async def list_comments_endpoint(
    request: Request,
    project_id: uuid.UUID,
    commentable_type: str = Query(...),
    commentable_id: uuid.UUID = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a commentable entity."""
    _get_user(request)

    comments, total = await list_comments(
        db,
        commentable_type=commentable_type,
        commentable_id=commentable_id,
        page=page,
        per_page=per_page,
    )

    return CommentListResponse(
        data=[
            CommentResponse.model_validate(format_comment_response(c))
            for c in comments
        ],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_comment_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a comment on a commentable entity."""
    user = _get_user(request)

    comment = await create_comment(
        db,
        organization_id=user["organization_id"],
        project_id=project_id,
        user=user,
        data=body,
    )

    return {
        "data": CommentResponse.model_validate(format_comment_response(comment)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.patch("/{comment_id}", response_model=dict)
async def update_comment_endpoint(
    request: Request,
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: CommentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update your own comment."""
    user = _get_user(request)

    comment = await update_comment(db, comment_id, user, body)

    return {
        "data": CommentResponse.model_validate(format_comment_response(comment)).model_dump(mode="json"),
        "meta": {},
    }


@gc_router.delete("/{comment_id}", status_code=200)
async def delete_comment_endpoint(
    request: Request,
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete your own comment."""
    user = _get_user(request)

    await delete_comment(db, comment_id, user)

    return {"data": {"id": str(comment_id), "deleted": True}, "meta": {}}


# ============================================================
# SUB PORTAL — Comments
# ============================================================

sub_router = APIRouter(
    prefix="/api/sub/projects/{project_id}/comments",
    tags=["sub-comments"],
)


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=CommentListResponse)
async def sub_list_comments(
    request: Request,
    project_id: uuid.UUID,
    commentable_type: str = Query(...),
    commentable_id: uuid.UUID = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List comments (sub portal)."""
    _get_sub_user(request)

    comments, total = await list_comments(
        db,
        commentable_type=commentable_type,
        commentable_id=commentable_id,
        page=page,
        per_page=per_page,
    )

    return CommentListResponse(
        data=[
            CommentResponse.model_validate(format_comment_response(c))
            for c in comments
        ],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


@sub_router.post("", response_model=dict, status_code=201)
async def sub_create_comment(
    request: Request,
    project_id: uuid.UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a comment (sub portal)."""
    user = _get_sub_user(request)

    comment = await create_comment(
        db,
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user=user,
        data=body,
    )

    return {
        "data": CommentResponse.model_validate(format_comment_response(comment)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.patch("/{comment_id}", response_model=dict)
async def sub_update_comment(
    request: Request,
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: CommentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update own comment (sub portal)."""
    user = _get_sub_user(request)

    comment = await update_comment(db, comment_id, user, body)

    return {
        "data": CommentResponse.model_validate(format_comment_response(comment)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.delete("/{comment_id}", status_code=200)
async def sub_delete_comment(
    request: Request,
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete own comment (sub portal)."""
    user = _get_sub_user(request)

    await delete_comment(db, comment_id, user)

    return {"data": {"id": str(comment_id), "deleted": True}, "meta": {}}
