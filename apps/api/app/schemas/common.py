from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class PaginationParams:
    """Reusable dependency for list endpoint query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        per_page: int = Query(25, ge=1, le=100),
        sort: str = Query("created_at"),
        order: str = Query("desc", pattern="^(asc|desc)$"),
        search: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
    ):
        self.page = page
        self.per_page = per_page
        self.sort = sort
        self.order = order
        self.search = search
        self.status = status

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    url: Optional[str] = None
