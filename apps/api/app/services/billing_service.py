"""Billing service for Stripe integration and tier enforcement."""
import uuid
from typing import Optional

import stripe
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User

stripe.api_key = settings.STRIPE_SECRET_KEY

# ============================================================
# TIER CONFIGURATION
# ============================================================

TIER_CONFIG = {
    "STARTER": {
        "max_major_projects": 3,
        "price_monthly": 349,
        "stripe_price_id_env": "STRIPE_PRICE_STARTER",
    },
    "PROFESSIONAL": {
        "max_major_projects": 10,
        "price_monthly": 2500,
        "stripe_price_id_env": "STRIPE_PRICE_PROFESSIONAL",
    },
    "SCALE": {
        "max_major_projects": 25,
        "price_monthly": 4500,
        "stripe_price_id_env": "STRIPE_PRICE_SCALE",
    },
    "ENTERPRISE": {
        "max_major_projects": None,
        "price_monthly": None,
        "stripe_price_id_env": None,
    },
}

# Backward-compatible dict used by existing tests
TIER_LIMITS = {
    "STARTER": 3,
    "PROFESSIONAL": 10,
    "SCALE": 25,
    "ENTERPRISE": None,
}

# Map tier names to their Stripe price IDs from settings
TIER_STRIPE_PRICES = {
    "STARTER": settings.STRIPE_PRICE_STARTER,
    "PROFESSIONAL": settings.STRIPE_PRICE_PROFESSIONAL,
    "SCALE": settings.STRIPE_PRICE_SCALE,
}


# ============================================================
# CHECKOUT & PORTAL SESSIONS
# ============================================================

def create_checkout_session(
    tier: str,
    organization_id: uuid.UUID,
    user_email: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """
    Create a Stripe Checkout session for the given tier.
    Returns the checkout session URL.
    """
    price_id = TIER_STRIPE_PRICES.get(tier)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"No Stripe price configured for tier: {tier}",
        )

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "organization_id": str(organization_id),
            "tier": tier,
        },
    )
    return session.url


def create_billing_portal_session(
    stripe_customer_id: str,
    return_url: str,
) -> str:
    """
    Create a Stripe Billing Portal session.
    Returns the portal session URL.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


# ============================================================
# TIER LIMIT CHECK
# ============================================================

async def check_tier_limit(
    db: AsyncSession,
    organization_id: uuid.UUID,
    exclude_project_id: uuid.UUID | None = None,
) -> None:
    """
    Check if the organization can add another major project.
    Raises HTTPException(402) if at the tier limit.

    Major projects = is_major=True AND phase != 'CLOSED'
    """
    org = await db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    tier_info = TIER_CONFIG.get(org.subscription_tier)
    limit = tier_info["max_major_projects"] if tier_info else None
    if limit is None:
        return  # Enterprise = unlimited

    # Count current major projects (excluding CLOSED)
    query = (
        select(func.count())
        .select_from(Project)
        .where(
            Project.organization_id == organization_id,
            Project.is_major == True,
            Project.phase != "CLOSED",
            Project.deleted_at.is_(None),
        )
    )
    if exclude_project_id:
        query = query.where(Project.id != exclude_project_id)

    result = await db.execute(query)
    current_count = result.scalar_one()

    if current_count >= limit:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "TIER_LIMIT_REACHED",
                "message": f"Your {org.subscription_tier} plan allows {limit} major projects. "
                           f"You currently have {current_count}. Please upgrade to add more.",
                "current_count": current_count,
                "limit": limit,
                "tier": org.subscription_tier,
            },
        )


# ============================================================
# BILLING STATUS
# ============================================================

async def get_billing_status(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> dict:
    """
    Return the current billing status for an organization.
    """
    org = await db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    tier_info = TIER_CONFIG.get(org.subscription_tier, TIER_CONFIG["STARTER"])
    limit = tier_info["max_major_projects"]

    # Count current active major projects
    query = (
        select(func.count())
        .select_from(Project)
        .where(
            Project.organization_id == organization_id,
            Project.is_major == True,
            Project.phase != "CLOSED",
            Project.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    current_count = result.scalar_one()

    return {
        "tier": org.subscription_tier,
        "subscription_status": org.subscription_status,
        "current_major_project_count": current_count,
        "max_major_projects": limit,
        "price_monthly": tier_info["price_monthly"],
        "stripe_customer_id": org.stripe_customer_id,
        "stripe_subscription_id": org.stripe_subscription_id,
        "grace_period_end": org.grace_period_end.isoformat() if org.grace_period_end else None,
    }


# ============================================================
# HELPER LOOKUPS
# ============================================================

async def get_org_by_subscription(
    db: AsyncSession,
    subscription_id: str,
) -> Optional[Organization]:
    """Look up an organization by its stripe_subscription_id."""
    result = await db.execute(
        select(Organization).where(
            Organization.stripe_subscription_id == subscription_id
        )
    )
    return result.scalar_one_or_none()


async def get_org_admins(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> list[User]:
    """Return all OWNER_ADMIN users for an organization."""
    result = await db.execute(
        select(User).where(
            User.organization_id == organization_id,
            User.permission_level == "OWNER_ADMIN",
            User.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())
