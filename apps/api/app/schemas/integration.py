from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IntegrationStatus(BaseModel):
    provider: str
    name: str
    description: str
    status: str  # CONNECTED | DISCONNECTED | COMING_SOON
    connected_at: Optional[str] = None


class IntegrationsListResponse(BaseModel):
    data: list[IntegrationStatus]
    meta: dict = {}


class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None
    realm_id: Optional[str] = None  # QuickBooks only


class OAuthUrlResponse(BaseModel):
    auth_url: str
    state: Optional[str] = None
