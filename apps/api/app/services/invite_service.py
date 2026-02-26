import secrets
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invitation import Invitation
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser
from app.models.project_assignment import ProjectAssignment


async def create_invitation(
    db: AsyncSession,
    inviter,
    email: str,
    invite_type: str,
    organization_id: uuid.UUID,
    role: str = None,
    project_ids: list = [],
    sub_company_id: uuid.UUID = None,
    owner_account_id: uuid.UUID = None,
) -> Invitation:
    """Create a new invitation after validating no pending invite exists for the email."""
    # Check for existing pending invitation
    existing = await get_pending_invitation_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A pending invitation already exists for {email}",
        )

    # Check if the user already exists in the system
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=f"A user with email {email} already exists",
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)

    invitation = Invitation(
        organization_id=organization_id,
        email=email,
        invite_type=invite_type,
        permission_level=role,
        token=token,
        status="pending",
        project_ids=project_ids or [],
        sub_company_id=sub_company_id,
        owner_account_id=owner_account_id,
        invited_by=inviter.id if hasattr(inviter, "id") else inviter,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.flush()
    return invitation


async def accept_invitation(
    db: AsyncSession, token: str, clerk_user_id: str
):
    """Accept an invitation by token, creating the appropriate user record."""
    invitation = await get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Invitation is no longer pending (status: {invitation.status})",
        )

    if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")

    default_name = invitation.email.split("@")[0]

    if invitation.invite_type == "gc_user":
        user = User(
            clerk_user_id=clerk_user_id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            name=default_name,
            permission_level=invitation.permission_level or "USER",
            status="ACTIVE",
        )
        db.add(user)
        await db.flush()

        # Auto-assign to projects
        if invitation.project_ids:
            for project_id in invitation.project_ids:
                assignment = ProjectAssignment(
                    project_id=project_id,
                    assignee_type="user",
                    assignee_id=user.id,
                    assigned_by_user_id=invitation.invited_by,
                )
                db.add(assignment)

    elif invitation.invite_type == "sub_user":
        sub_user = SubUser(
            clerk_user_id=clerk_user_id,
            sub_company_id=invitation.sub_company_id,
            email=invitation.email,
            name=default_name,
            is_primary=False,
            status="ACTIVE",
        )
        db.add(sub_user)

    elif invitation.invite_type == "owner_user":
        owner_user = OwnerUser(
            clerk_user_id=clerk_user_id,
            owner_account_id=invitation.owner_account_id,
            email=invitation.email,
            name=default_name,
            status="ACTIVE",
        )
        db.add(owner_user)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown invite type: {invitation.invite_type}",
        )

    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)
    await db.commit()

    return invitation


async def get_invitation_by_token(
    db: AsyncSession, token: str
) -> Invitation | None:
    """Look up an invitation by its token."""
    result = await db.execute(
        select(Invitation).where(Invitation.token == token)
    )
    return result.scalar_one_or_none()


async def get_pending_invitation_by_email(
    db: AsyncSession, email: str
) -> Invitation | None:
    """Get pending invitations matching the given email."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.email == email,
            Invitation.status == "pending",
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    """Check for an existing user across User, SubUser, and OwnerUser tables."""
    # Check User table
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # Check SubUser table
    result = await db.execute(
        select(SubUser).where(SubUser.email == email)
    )
    sub_user = result.scalar_one_or_none()
    if sub_user:
        return sub_user

    # Check OwnerUser table
    result = await db.execute(
        select(OwnerUser).where(OwnerUser.email == email)
    )
    owner_user = result.scalar_one_or_none()
    if owner_user:
        return owner_user

    return None


async def list_invitations(
    db: AsyncSession, organization_id: uuid.UUID
) -> list[Invitation]:
    """List all invitations for an organization."""
    result = await db.execute(
        select(Invitation)
        .where(Invitation.organization_id == organization_id)
        .order_by(Invitation.created_at.desc())
    )
    return result.scalars().all()


async def cancel_invitation(
    db: AsyncSession, invitation_id: uuid.UUID, organization_id: uuid.UUID
) -> Invitation:
    """Revoke a pending invitation."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == organization_id,
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending invitations can be revoked",
        )

    invitation.status = "revoked"
    await db.commit()
    return invitation


async def resend_invitation(
    db: AsyncSession, invitation_id: uuid.UUID, organization_id: uuid.UUID
) -> Invitation:
    """Refresh expiry and re-send an invitation email."""
    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == organization_id,
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending invitations can be resent",
        )

    # Refresh the expiry
    invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    await db.commit()

    return invitation
