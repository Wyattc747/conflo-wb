"""Document CRUD router — GC and Sub portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadNewVersion,
    FolderCreate,
    FolderListResponse,
    FolderResponse,
    FolderUpdate,
)
from app.services.document_service import (
    create_document,
    create_folder,
    delete_document,
    delete_folder,
    format_document_response,
    format_folder_response,
    get_document,
    get_folder,
    list_documents,
    list_folders,
    update_document,
    update_folder,
    upload_new_version,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/documents", tags=["documents"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# --- Folders ---

@gc_router.get("/folders", response_model=FolderListResponse)
async def list_folders_endpoint(
    request: Request, project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    folders = await list_folders(db, project_id)
    data = [FolderResponse.model_validate(format_folder_response(f)) for f in folders]
    return FolderListResponse(
        data=data,
        meta=PaginationMeta(page=1, per_page=100, total=len(data), total_pages=1),
    )


@gc_router.post("/folders", response_model=dict, status_code=201)
async def create_folder_endpoint(
    request: Request, project_id: uuid.UUID, body: FolderCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    folder = await create_folder(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": FolderResponse.model_validate(format_folder_response(folder)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/folders/{folder_id}", response_model=dict)
async def update_folder_endpoint(
    request: Request, project_id: uuid.UUID, folder_id: uuid.UUID, body: FolderUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    folder = await update_folder(db, folder_id, project_id, user, body)
    return {"data": FolderResponse.model_validate(format_folder_response(folder)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/folders/{folder_id}", status_code=200)
async def delete_folder_endpoint(
    request: Request, project_id: uuid.UUID, folder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_folder(db, folder_id, project_id, user)
    return {"data": {"id": str(folder_id), "deleted": True}, "meta": {}}


# --- Documents ---

@gc_router.get("", response_model=DocumentListResponse)
async def list_documents_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    folder_id: uuid.UUID | None = Query(None),
    category: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    docs, total = await list_documents(
        db, project_id=project_id, page=page, per_page=per_page,
        folder_id=folder_id, category=category, search=search, sort=sort, order=order,
    )
    data = [DocumentResponse.model_validate(format_document_response(d)) for d in docs]
    return DocumentListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_document_endpoint(
    request: Request, project_id: uuid.UUID, body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    doc = await create_document(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": DocumentResponse.model_validate(format_document_response(doc)).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{document_id}", response_model=dict)
async def get_document_endpoint(
    request: Request, project_id: uuid.UUID, document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    doc = await get_document(db, document_id, project_id)
    return {"data": DocumentResponse.model_validate(format_document_response(doc)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{document_id}", response_model=dict)
async def update_document_endpoint(
    request: Request, project_id: uuid.UUID, document_id: uuid.UUID, body: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    doc = await update_document(db, document_id, project_id, user, body)
    return {"data": DocumentResponse.model_validate(format_document_response(doc)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{document_id}", status_code=200)
async def delete_document_endpoint(
    request: Request, project_id: uuid.UUID, document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_document(db, document_id, project_id, user)
    return {"data": {"id": str(document_id), "deleted": True}, "meta": {}}


@gc_router.post("/{document_id}/new-version", response_model=dict)
async def upload_new_version_endpoint(
    request: Request, project_id: uuid.UUID, document_id: uuid.UUID,
    body: DocumentUploadNewVersion,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    doc = await upload_new_version(db, document_id, project_id, user, body)
    return {"data": DocumentResponse.model_validate(format_document_response(doc)).model_dump(mode="json"), "meta": {}}


# ============================================================
# SUB PORTAL — Read-only
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/documents", tags=["sub-documents"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("/folders", response_model=FolderListResponse)
async def sub_list_folders(
    request: Request, project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    folders = await list_folders(db, project_id)
    data = [FolderResponse.model_validate(format_folder_response(f)) for f in folders]
    return FolderListResponse(
        data=data,
        meta=PaginationMeta(page=1, per_page=100, total=len(data), total_pages=1),
    )


@sub_router.get("", response_model=DocumentListResponse)
async def sub_list_documents(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    folder_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    docs, total = await list_documents(db, project_id=project_id, page=page, per_page=per_page,
                                        folder_id=folder_id, search=search, sort=sort, order=order)
    data = [DocumentResponse.model_validate(format_document_response(d)) for d in docs]
    return DocumentListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@sub_router.get("/{document_id}", response_model=dict)
async def sub_get_document(
    request: Request, project_id: uuid.UUID, document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    doc = await get_document(db, document_id, project_id)
    return {"data": DocumentResponse.model_validate(format_document_response(doc)).model_dump(mode="json"), "meta": {}}
