"""Billing management endpoints for GC portal."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import stripe

from app.config import settings
from app.database import get_db
from app.models.organization import Organization
from app.services.billing_service import (
    TIER_STRIPE_PRICES,
    create_billing_portal_session,
    create_checkout_session,
    get_billing_status,
)

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/api/gc/billing", tags=["billing"])


# ============================================================
# REQUEST / RESPONSE SCHEMAS
# ============================================================

class CheckoutRequest(BaseModel):
    tier: str


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class UpgradeRequest(BaseModel):
    new_tier: str


class UpgradeResponse(BaseModel):
    message: str
    new_tier: str


# ============================================================
# HELPERS
# ============================================================

def _get_user(request: Request) -> dict:
    """Extract authenticated user from request state."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _require_admin(user: dict) -> None:
    """Ensure the user is an OWNER_ADMIN."""
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Owner/Admin users can manage billing",
        )


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout session for the requested tier."""
    user = _get_user(request)
    _require_admin(user)

    valid_tiers = {"STARTER", "PROFESSIONAL", "SCALE"}
    if body.tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {body.tier}. Must be one of {', '.join(sorted(valid_tiers))}",
        )

    success_url = f"{settings.FRONTEND_URL}/app/settings/billing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.FRONTEND_URL}/app/settings/billing?cancelled=true"

    url = create_checkout_session(
        tier=body.tier,
        organization_id=user["organization_id"],
        user_email=user.get("email", ""),
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return CheckoutResponse(url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Billing Portal session."""
    user = _get_user(request)
    _require_admin(user)

    org = await db.get(Organization, user["organization_id"])
    if not org or not org.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer found. Please subscribe to a plan first.",
        )

    return_url = f"{settings.FRONTEND_URL}/app/settings/billing"

    url = create_billing_portal_session(
        stripe_customer_id=org.stripe_customer_id,
        return_url=return_url,
    )

    return PortalResponse(url=url)


@router.get("/status")
async def billing_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return current billing status for the organization."""
    user = _get_user(request)
    _require_admin(user)

    status = await get_billing_status(db, user["organization_id"])
    return {"data": status}


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_subscription(
    body: UpgradeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Upgrade or change the Stripe subscription to a new tier."""
    user = _get_user(request)
    _require_admin(user)

    valid_tiers = {"STARTER", "PROFESSIONAL", "SCALE"}
    if body.new_tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {body.new_tier}. Must be one of {', '.join(sorted(valid_tiers))}",
        )

    org = await db.get(Organization, user["organization_id"])
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found. Please create a subscription first.",
        )

    if org.subscription_tier == body.new_tier:
        raise HTTPException(
            status_code=400,
            detail=f"Already on the {body.new_tier} plan.",
        )

    new_price_id = TIER_STRIPE_PRICES.get(body.new_tier)
    if not new_price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No Stripe price configured for tier: {body.new_tier}",
        )

    # Retrieve current subscription and update the price
    subscription = stripe.Subscription.retrieve(org.stripe_subscription_id)
    stripe.Subscription.modify(
        org.stripe_subscription_id,
        items=[
            {
                "id": subscription["items"]["data"][0]["id"],
                "price": new_price_id,
            }
        ],
        proration_behavior="create_prorations",
    )

    # Update local org record
    org.subscription_tier = body.new_tier
    await db.commit()

    return UpgradeResponse(
        message=f"Successfully upgraded to {body.new_tier}",
        new_tier=body.new_tier,
    )
