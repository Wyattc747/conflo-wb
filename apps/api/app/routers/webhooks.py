"""Webhook handlers for Stripe and Clerk."""
import json
import logging
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.invitation import Invitation
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser
from app.models.user import User
from app.middleware.auth import verify_clerk_webhook_signature
from app.services.billing_service import get_org_admins, get_org_by_subscription

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

stripe.api_key = settings.STRIPE_SECRET_KEY


# ============================================================
# STRIPE WEBHOOK
# ============================================================

@router.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data_object)
    elif event_type == "invoice.payment_succeeded":
        await _handle_payment_succeeded(db, data_object)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(db, data_object)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data_object)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data_object)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return {"status": "ok"}


async def _handle_checkout_completed(db: AsyncSession, session: dict):
    """
    Process checkout.session.completed: update org with tier,
    stripe_customer_id, stripe_subscription_id, and set status active.
    """
    metadata = session.get("metadata", {})
    organization_id = metadata.get("organization_id")
    tier = metadata.get("tier")

    if not organization_id or not tier:
        logger.warning("checkout.session.completed missing metadata")
        return

    org = await db.get(Organization, organization_id)
    if not org:
        logger.warning(f"Organization {organization_id} not found for checkout")
        return

    org.subscription_tier = tier
    org.stripe_customer_id = session.get("customer")
    org.stripe_subscription_id = session.get("subscription")
    org.subscription_status = "ACTIVE"
    org.grace_period_end = None

    await db.commit()
    logger.info(f"Checkout completed: org={organization_id} tier={tier}")


async def _handle_payment_succeeded(db: AsyncSession, invoice: dict):
    """Process invoice.payment_succeeded: ensure subscription is active."""
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return

    org = await get_org_by_subscription(db, subscription_id)
    if not org:
        logger.warning(f"No org found for subscription {subscription_id}")
        return

    org.subscription_status = "ACTIVE"
    org.grace_period_end = None
    await db.commit()
    logger.info(f"Payment succeeded: org={org.id}")


async def _handle_payment_failed(db: AsyncSession, invoice: dict):
    """
    Process invoice.payment_failed: set past_due status,
    add 7-day grace period, notify admins.
    """
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return

    org = await get_org_by_subscription(db, subscription_id)
    if not org:
        logger.warning(f"No org found for subscription {subscription_id}")
        return

    org.subscription_status = "PAST_DUE"
    org.grace_period_end = datetime.now(timezone.utc) + timedelta(days=7)
    await db.flush()

    # Notify all OWNER_ADMIN users
    admins = await get_org_admins(db, org.id)
    for admin in admins:
        notification = Notification(
            user_type="GC_USER",
            user_id=admin.id,
            type="payment_failed",
            title="Payment Failed",
            body="Your subscription payment has failed. Please update your payment method "
                 "within 7 days to avoid service interruption.",
            source_type="organization",
            source_id=org.id,
        )
        db.add(notification)

    await db.commit()
    logger.info(f"Payment failed: org={org.id}, grace period set")


async def _handle_subscription_updated(db: AsyncSession, subscription: dict):
    """Process customer.subscription.updated: sync status."""
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    org = await get_org_by_subscription(db, subscription_id)
    if not org:
        logger.warning(f"No org found for subscription {subscription_id}")
        return

    status = subscription.get("status", "")
    status_map = {
        "active": "ACTIVE",
        "past_due": "PAST_DUE",
        "canceled": "CANCELLED",
        "trialing": "TRIALING",
        "unpaid": "PAST_DUE",
    }
    mapped_status = status_map.get(status)
    if mapped_status:
        org.subscription_status = mapped_status

    if mapped_status == "ACTIVE":
        org.grace_period_end = None

    await db.commit()
    logger.info(f"Subscription updated: org={org.id} status={mapped_status}")


async def _handle_subscription_deleted(db: AsyncSession, subscription: dict):
    """Process customer.subscription.deleted: mark cancelled."""
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    org = await get_org_by_subscription(db, subscription_id)
    if not org:
        logger.warning(f"No org found for subscription {subscription_id}")
        return

    org.subscription_status = "CANCELLED"
    await db.commit()
    logger.info(f"Subscription deleted: org={org.id}")


# ============================================================
# CLERK WEBHOOK
# ============================================================

@router.post("/api/webhooks/clerk")
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Clerk webhook events."""
    body = await request.body()

    # Verify Clerk webhook signature
    if not verify_clerk_webhook_signature(body, dict(request.headers)):
        raise HTTPException(status_code=400, detail="Invalid Clerk webhook signature")

    payload = json.loads(body)

    event_type = payload.get("type")
    data = payload.get("data", {})

    if event_type == "user.created":
        await _handle_clerk_user_created(db, data)
    elif event_type == "user.updated":
        await _handle_clerk_user_updated(db, data)
    elif event_type == "user.deleted":
        await _handle_clerk_user_deleted(db, data)
    else:
        logger.info(f"Unhandled Clerk event type: {event_type}")

    return {"status": "ok"}


async def _handle_clerk_user_created(db: AsyncSession, data: dict):
    """
    Handle user.created: look up pending invitation by email.
    If found, auto-accept the invitation.
    """
    clerk_user_id = data.get("id")
    email_addresses = data.get("email_addresses", [])
    if not email_addresses:
        return

    primary_email = None
    for addr in email_addresses:
        if addr.get("id") == data.get("primary_email_address_id"):
            primary_email = addr.get("email_address")
            break
    if not primary_email:
        primary_email = email_addresses[0].get("email_address")

    if not primary_email:
        return

    # Look up pending invitation by email
    result = await db.execute(
        select(Invitation).where(
            Invitation.email == primary_email,
            Invitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        logger.info(f"No pending invitation for email {primary_email}")
        return

    # Determine user name from Clerk data
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    name = f"{first_name} {last_name}".strip() or primary_email

    # Auto-accept based on invitation type
    if invitation.invite_type == "GC_USER":
        user = User(
            organization_id=invitation.organization_id,
            clerk_user_id=clerk_user_id,
            email=primary_email,
            name=name,
            permission_level=invitation.permission_level or "USER",
            status="ACTIVE",
        )
        db.add(user)
    elif invitation.invite_type == "SUB_USER" and invitation.sub_company_id:
        sub_user = SubUser(
            sub_company_id=invitation.sub_company_id,
            clerk_user_id=clerk_user_id,
            email=primary_email,
            name=name,
            status="ACTIVE",
        )
        db.add(sub_user)
    elif invitation.invite_type == "OWNER_USER" and invitation.owner_account_id:
        owner_user = OwnerUser(
            owner_account_id=invitation.owner_account_id,
            clerk_user_id=clerk_user_id,
            email=primary_email,
            name=name,
            status="ACTIVE",
        )
        db.add(owner_user)

    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)

    await db.commit()
    logger.info(f"Auto-accepted invitation for {primary_email} (type={invitation.invite_type})")


async def _handle_clerk_user_updated(db: AsyncSession, data: dict):
    """Handle user.updated: sync profile fields from Clerk."""
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return

    email_addresses = data.get("email_addresses", [])
    primary_email = None
    for addr in email_addresses:
        if addr.get("id") == data.get("primary_email_address_id"):
            primary_email = addr.get("email_address")
            break

    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    name = f"{first_name} {last_name}".strip()
    image_url = data.get("image_url")

    # Try to find user in each table
    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        if primary_email:
            user.email = primary_email
        if name:
            user.name = name
        if image_url:
            user.avatar_url = image_url
        await db.commit()
        return

    result = await db.execute(
        select(SubUser).where(SubUser.clerk_user_id == clerk_user_id)
    )
    sub_user = result.scalar_one_or_none()
    if sub_user:
        if primary_email:
            sub_user.email = primary_email
        if name:
            sub_user.name = name
        await db.commit()
        return

    result = await db.execute(
        select(OwnerUser).where(OwnerUser.clerk_user_id == clerk_user_id)
    )
    owner_user = result.scalar_one_or_none()
    if owner_user:
        if primary_email:
            owner_user.email = primary_email
        if name:
            owner_user.name = name
        await db.commit()
        return

    logger.info(f"No user found for clerk_user_id {clerk_user_id} during update sync")


async def _handle_clerk_user_deleted(db: AsyncSession, data: dict):
    """Handle user.deleted: soft-delete the user record."""
    clerk_user_id = data.get("id")
    if not clerk_user_id:
        return

    now = datetime.now(timezone.utc)

    # Try GC user
    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.deleted_at = now
        user.status = "INACTIVE"
        await db.commit()
        return

    # Try sub user (no deleted_at, use status)
    result = await db.execute(
        select(SubUser).where(SubUser.clerk_user_id == clerk_user_id)
    )
    sub_user = result.scalar_one_or_none()
    if sub_user:
        sub_user.status = "INACTIVE"
        await db.commit()
        return

    # Try owner user (no deleted_at, use status)
    result = await db.execute(
        select(OwnerUser).where(OwnerUser.clerk_user_id == clerk_user_id)
    )
    owner_user = result.scalar_one_or_none()
    if owner_user:
        owner_user.status = "INACTIVE"
        await db.commit()
        return

    logger.info(f"No user found for clerk_user_id {clerk_user_id} during delete")
