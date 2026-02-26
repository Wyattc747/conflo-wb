from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: Optional[UUID] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_folder_id: Optional[UUID] = None


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    parent_folder_id: Optional[UUID] = None
    is_system: bool
    created_at: datetime


class FolderListResponse(BaseModel):
    data: list[FolderResponse]
    meta: PaginationMeta


class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    folder_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    tags: list[str] = []


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    folder_id: Optional[UUID] = None
    tags: Optional[list[str]] = None


class DocumentUploadNewVersion(BaseModel):
    file_id: UUID


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    folder_id: Optional[UUID] = None
    folder_name: Optional[str] = None
    file_id: Optional[UUID] = None
    tags: list[str] = []
    version: int
    uploaded_by: Optional[UUID] = None
    uploaded_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    data: list[DocumentResponse]
    meta: PaginationMeta
