from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str
    body: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    project_id: Optional[str] = None
    metadata: Optional[dict] = None
    read: bool
    read_at: Optional[str] = None
    created_at: Optional[str] = None


class NotificationListResponse(BaseModel):
    data: list[NotificationResponse]
    meta: PaginationMeta


class UnreadCountResponse(BaseModel):
    count: int


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    email_categories: Optional[dict] = None
