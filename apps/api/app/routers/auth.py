import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.services.invite_service import (
    get_invitation_by_token,
    accept_invitation,
)
from app.config import settings
from app.services.billing_service import create_checkout_session


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    company_name: str
    tier: str


class InvitationAcceptRequest(BaseModel):
    clerk_user_id: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(tags=["auth"])


@router.post("/api/auth/signup")
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Create a new Organization + OWNER_ADMIN User and start a Stripe checkout session."""
    # Create the organization
    org = Organization(
        name=body.company_name,
        subscription_tier=body.tier,
        subscription_status="pending",
    )
    db.add(org)
    await db.flush()  # Need org.id before creating the user

    # Create the founding user (clerk_user_id set later by Clerk webhook)
    user = User(
        organization_id=org.id,
        clerk_user_id="",
        email=body.email,
        name=f"{body.first_name} {body.last_name}",
        permission_level="OWNER_ADMIN",
        status="ACTIVE",
    )
    db.add(user)
    await db.flush()

    # Create Stripe checkout session
    checkout_url = create_checkout_session(
        tier=body.tier,
        organization_id=org.id,
        user_email=body.email,
        success_url=f"{settings.FRONTEND_URL}/onboarding",
        cancel_url=f"{settings.FRONTEND_URL}/signup",
    )

    await db.commit()

    return {
        "checkout_url": checkout_url,
        "organization_id": str(org.id),
    }


@router.get("/api/auth/invitations/{token}")
async def get_invitation(token: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint — return invitation details for the invite acceptance page."""
    invitation = await get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Fetch organization name for display
    org = await db.get(Organization, invitation.organization_id)
    org_name = org.name if org else "Unknown Organization"

    # Map invite_type to a human-readable role label
    role_map = {
        "gc_user": invitation.permission_level or "USER",
        "sub_user": "Subcontractor",
        "owner_user": "Owner",
    }
    role = role_map.get(invitation.invite_type, invitation.invite_type)

    # Fetch project names if project_ids are set
    projects = []
    if invitation.project_ids:
        for pid in invitation.project_ids:
            try:
                project = await db.get(Project, uuid.UUID(str(pid)))
                if project:
                    projects.append({"id": str(project.id), "name": project.name})
            except (ValueError, TypeError):
                pass

    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "invite_type": invitation.invite_type,
        "organization_id": str(invitation.organization_id),
        "org_name": org_name,
        "role": role,
        "projects": projects,
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
    }


@router.post("/api/auth/invitations/{token}/accept")
async def accept_invite(
    token: str,
    body: InvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept an invitation using the Clerk user ID from the frontend."""
    invitation = await accept_invitation(db, token, body.clerk_user_id)
    return {
        "message": "Invitation accepted",
        "invite_type": invitation.invite_type,
        "organization_id": str(invitation.organization_id),
    }
