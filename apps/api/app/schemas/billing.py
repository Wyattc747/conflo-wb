from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    tier: str  # STARTER | PROFESSIONAL | SCALE


class CheckoutResponse(BaseModel):
    url: str


class BillingPortalResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    tier: str
    subscription_status: str
    current_major_projects: int
    max_major_projects: int | None
    onboarding_completed: bool


class UpgradeRequest(BaseModel):
    new_tier: str
