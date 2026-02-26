import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.services.invite_service import (
    create_invitation,
    list_invitations,
    cancel_invitation,
    resend_invitation,
)
from app.services.email_service import send_invite_email


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InvitationCreate(BaseModel):
    email: EmailStr
    invite_type: str  # gc_user | sub_user | owner_user
    permission_level: str | None = None
    project_ids: list[uuid.UUID] | None = None
    sub_company_id: uuid.UUID | None = None
    owner_account_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_user(request: Request, db: AsyncSession) -> User:
    """Extract the authenticated GC user from request state."""
    user_ctx = getattr(request.state, "user", None)
    if not user_ctx:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(User).where(User.id == user_ctx["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _require_admin(user: User):
    """Ensure the user has OWNER_ADMIN permission level."""
    if user.permission_level != "OWNER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can manage invitations",
        )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/gc/invitations", tags=["invitations"])


@router.post("")
async def create_invite(
    body: InvitationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new invitation and send the email (Owner/Admin only)."""
    user = await _get_user(request, db)
    _require_admin(user)

    invitation = await create_invitation(
        db=db,
        inviter=user,
        email=body.email,
        invite_type=body.invite_type,
        organization_id=user.organization_id,
        role=body.permission_level,
        project_ids=[str(pid) for pid in body.project_ids] if body.project_ids else [],
        sub_company_id=body.sub_company_id,
        owner_account_id=body.owner_account_id,
    )

    # Fetch the organization name for the email
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()
    org_name = org.name if org else "Your organization"

    await db.commit()

    # Send invitation email (non-blocking failure is acceptable)
    try:
        await send_invite_email(
            invitation=invitation,
            inviter_name=user.name or user.email,
            organization_name=org_name,
        )
    except Exception:
        pass  # Email failure should not block invitation creation

    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "invite_type": invitation.invite_type,
        "status": invitation.status,
        "token": invitation.token,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
    }


@router.get("")
async def list_invites(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all invitations for the authenticated user's organization."""
    user = await _get_user(request, db)

    invitations = await list_invitations(db, user.organization_id)
    return [
        {
            "id": str(inv.id),
            "email": inv.email,
            "invite_type": inv.invite_type,
            "permission_level": inv.permission_level,
            "status": inv.status,
            "project_ids": inv.project_ids,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invitations
    ]


@router.delete("/{invitation_id}")
async def cancel_invite(
    invitation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Cancel/revoke a pending invitation."""
    user = await _get_user(request, db)
    _require_admin(user)

    invitation = await cancel_invitation(db, invitation_id, user.organization_id)
    return {
        "id": str(invitation.id),
        "status": invitation.status,
        "message": "Invitation revoked",
    }


@router.post("/{invitation_id}/resend")
async def resend_invite(
    invitation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Resend an invitation email with a refreshed expiry."""
    user = await _get_user(request, db)
    _require_admin(user)

    invitation = await resend_invitation(db, invitation_id, user.organization_id)

    # Fetch the organization name for the email
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()
    org_name = org.name if org else "Your organization"

    # Re-send the email
    try:
        await send_invite_email(
            invitation=invitation,
            inviter_name=user.name or user.email,
            organization_name=org_name,
        )
    except Exception:
        pass

    return {
        "id": str(invitation.id),
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
        "message": "Invitation resent",
    }
