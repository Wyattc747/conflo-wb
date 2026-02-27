from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    admin: dict


class OrgListItem(BaseModel):
    id: str
    name: str
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    user_count: int = 0
    project_count: int = 0
    created_at: Optional[datetime] = None


class ImpersonateRequest(BaseModel):
    user_id: str
    user_type: str  # gc, sub, owner


class PlatformStats(BaseModel):
    total_organizations: int = 0
    total_users: int = 0
    total_projects: int = 0
    total_sub_companies: int = 0
    monthly_recurring_revenue: int = 0  # cents
    orgs_by_tier: dict = {}
