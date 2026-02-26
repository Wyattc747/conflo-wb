from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class CommentCreate(BaseModel):
    commentable_type: str
    commentable_id: UUID
    body: str
    mentions: list[UUID] = []
    attachments: list[UUID] = []


class CommentUpdate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    commentable_type: str
    commentable_id: UUID
    body: str
    author_type: str
    author_id: UUID
    author_name: Optional[str] = None
    is_official_response: bool = False
    mentions: list[UUID] = []
    attachments: list[UUID] = []
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    data: list[CommentResponse]
    meta: PaginationMeta
