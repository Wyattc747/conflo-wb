import uuid
from datetime import datetime

from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    company_name: str
    tier: str  # STARTER | PROFESSIONAL | SCALE


class SignupResponse(BaseModel):
    checkout_url: str
    organization_id: str


class InvitationAcceptRequest(BaseModel):
    clerk_user_id: str


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    invite_type: str
    status: str
    organization_name: str | None = None
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
