import uuid
from datetime import datetime

from pydantic import BaseModel


class InvitationCreate(BaseModel):
    email: str
    invite_type: str  # gc_user | sub_user | owner_user
    permission_level: str | None = None  # For gc_user
    project_ids: list[uuid.UUID] = []
    sub_company_id: uuid.UUID | None = None
    owner_account_id: uuid.UUID | None = None


class InvitationListResponse(BaseModel):
    id: uuid.UUID
    email: str
    invite_type: str
    permission_level: str | None
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationListWrapper(BaseModel):
    data: list[InvitationListResponse]
    meta: dict = {}
