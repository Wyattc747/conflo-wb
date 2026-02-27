from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str
    category: str
    file_size_bytes: Optional[int] = None


class UploadUrlResponse(BaseModel):
    file_id: str
    upload_url: str
    key: str


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    category: str
    status: str
    thumbnail_key: Optional[str] = None
    exif_data: Optional[dict] = None
    uploaded_by: Optional[str] = None
    confirmed_at: Optional[str] = None
    created_at: Optional[str] = None


class FileListResponse(BaseModel):
    data: list[FileResponse]
    meta: PaginationMeta
