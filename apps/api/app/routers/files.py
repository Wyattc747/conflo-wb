"""File upload/download router — GC, Sub, Owner portals."""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.file import (
    FileListResponse,
    FileResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.services.file_service import (
    confirm_upload,
    delete_file,
    format_file_response,
    get_download_url,
    get_thumbnail_url,
    get_view_url,
    list_project_files,
    request_upload_url,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/files", tags=["files"])
sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/files", tags=["files"])
owner_router = APIRouter(prefix="/api/owner/projects/{project_id}/files", tags=["files"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ── Shared endpoint logic ──


async def _upload_url(request, project_id, body, db):
    user = _get_user(request)
    result = await request_upload_url(
        db, user, project_id, body.filename, body.content_type,
        body.category, body.file_size_bytes,
    )
    return {"data": result, "meta": {}}


async def _confirm(request, project_id, file_id, db):
    user = _get_user(request)
    result = await confirm_upload(db, file_id, user)
    return {"data": result, "meta": {}}


async def _download(request, project_id, file_id, db):
    user = _get_user(request)
    url = await get_download_url(db, file_id, user)
    return {"data": {"url": url}, "meta": {}}


async def _view(request, project_id, file_id, db):
    _get_user(request)
    url = await get_view_url(db, file_id)
    return {"data": {"url": url}, "meta": {}}


async def _thumbnail(request, project_id, file_id, db):
    _get_user(request)
    url = await get_thumbnail_url(db, file_id)
    if not url:
        raise HTTPException(404, "No thumbnail available")
    return {"data": {"url": url}, "meta": {}}


async def _delete(request, project_id, file_id, db):
    user = _get_user(request)
    result = await delete_file(db, file_id, user)
    return {"data": result, "meta": {}}


async def _list_files(request, project_id, category, page, per_page, db):
    _get_user(request)
    files, total = await list_project_files(db, project_id, category, page, per_page)
    data = [FileResponse.model_validate(format_file_response(f)) for f in files]
    return FileListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


# ── GC Router ──


@gc_router.get("")
async def gc_list_files(
    request: Request, project_id: uuid.UUID,
    category: str | None = Query(None),
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await _list_files(request, project_id, category, page, per_page, db)


@gc_router.post("/upload-url", status_code=201)
async def gc_upload_url(
    request: Request, project_id: uuid.UUID, body: UploadUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    return await _upload_url(request, project_id, body, db)


@gc_router.post("/{file_id}/confirm")
async def gc_confirm(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _confirm(request, project_id, file_id, db)


@gc_router.get("/{file_id}/download")
async def gc_download(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _download(request, project_id, file_id, db)


@gc_router.get("/{file_id}/view")
async def gc_view(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _view(request, project_id, file_id, db)


@gc_router.get("/{file_id}/thumbnail")
async def gc_thumbnail(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _thumbnail(request, project_id, file_id, db)


@gc_router.delete("/{file_id}")
async def gc_delete(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _delete(request, project_id, file_id, db)


# ── Sub Router ──


@sub_router.post("/upload-url", status_code=201)
async def sub_upload_url(
    request: Request, project_id: uuid.UUID, body: UploadUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    return await _upload_url(request, project_id, body, db)


@sub_router.post("/{file_id}/confirm")
async def sub_confirm(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _confirm(request, project_id, file_id, db)


@sub_router.get("/{file_id}/download")
async def sub_download(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _download(request, project_id, file_id, db)


@sub_router.get("/{file_id}/view")
async def sub_view(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _view(request, project_id, file_id, db)


# ── Owner Router ──


@owner_router.post("/upload-url", status_code=201)
async def owner_upload_url(
    request: Request, project_id: uuid.UUID, body: UploadUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    return await _upload_url(request, project_id, body, db)


@owner_router.post("/{file_id}/confirm")
async def owner_confirm(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _confirm(request, project_id, file_id, db)


@owner_router.get("/{file_id}/download")
async def owner_download(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _download(request, project_id, file_id, db)


@owner_router.get("/{file_id}/view")
async def owner_view(
    request: Request, project_id: uuid.UUID, file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await _view(request, project_id, file_id, db)
