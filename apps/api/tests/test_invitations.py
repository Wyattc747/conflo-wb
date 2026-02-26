"""Tests for the invitation system."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.invite_service import (
    create_invitation,
    accept_invitation,
    get_invitation_by_token,
    get_pending_invitation_by_email,
    get_user_by_email,
    list_invitations,
    cancel_invitation,
    resend_invitation,
)
from app.models.invitation import Invitation
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser

ORG_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
SUB_COMPANY_ID = uuid.uuid4()
OWNER_ACCOUNT_ID = uuid.uuid4()


# ============================================================
# CREATE INVITATION
# ============================================================

class TestCreateInvitation:
    @pytest.mark.asyncio
    async def test_creates_invitation_with_token(self):
        db = AsyncMock()
        # No pending invitation exists
        result_pending = MagicMock()
        result_pending.scalar_one_or_none.return_value = None
        # No existing user
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = None

        db.execute.return_value = result_pending  # Both queries return None

        invitation = await create_invitation(
            db=db,
            inviter=USER_ID,
            email="new@example.com",
            invite_type="gc_user",
            organization_id=ORG_ID,
            role="MANAGEMENT",
        )

        assert invitation.email == "new@example.com"
        assert invitation.invite_type == "gc_user"
        assert invitation.permission_level == "MANAGEMENT"
        assert invitation.status == "pending"
        assert invitation.token is not None
        assert len(invitation.token) > 20  # token_urlsafe(32) is 43 chars
        db.add.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_pending_invitation_raises_409(self):
        from fastapi import HTTPException

        db = AsyncMock()
        existing = MagicMock(spec=Invitation)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await create_invitation(
                db=db,
                inviter=USER_ID,
                email="existing@example.com",
                invite_type="gc_user",
                organization_id=ORG_ID,
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_existing_user_raises_409(self):
        from fastapi import HTTPException

        db = AsyncMock()
        # No pending invitation
        result_pending = MagicMock()
        result_pending.scalar_one_or_none.return_value = None
        # Existing user found
        existing_user = MagicMock(spec=User)
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = existing_user

        # First call returns None (no pending), second returns existing user
        db.execute.side_effect = [result_pending, result_user]

        with pytest.raises(HTTPException) as exc_info:
            await create_invitation(
                db=db,
                inviter=USER_ID,
                email="existing@example.com",
                invite_type="gc_user",
                organization_id=ORG_ID,
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_creates_sub_invitation_with_company(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        invitation = await create_invitation(
            db=db,
            inviter=USER_ID,
            email="sub@company.com",
            invite_type="sub_user",
            organization_id=ORG_ID,
            sub_company_id=SUB_COMPANY_ID,
        )

        assert invitation.invite_type == "sub_user"
        assert invitation.sub_company_id == SUB_COMPANY_ID

    @pytest.mark.asyncio
    async def test_creates_owner_invitation(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        invitation = await create_invitation(
            db=db,
            inviter=USER_ID,
            email="owner@client.com",
            invite_type="owner_user",
            organization_id=ORG_ID,
            owner_account_id=OWNER_ACCOUNT_ID,
        )

        assert invitation.invite_type == "owner_user"
        assert invitation.owner_account_id == OWNER_ACCOUNT_ID

    @pytest.mark.asyncio
    async def test_invitation_has_14_day_expiry(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        invitation = await create_invitation(
            db=db,
            inviter=USER_ID,
            email="new@test.com",
            invite_type="gc_user",
            organization_id=ORG_ID,
        )

        now = datetime.now(timezone.utc)
        assert invitation.expires_at > now + timedelta(days=13)
        assert invitation.expires_at < now + timedelta(days=15)


# ============================================================
# ACCEPT INVITATION
# ============================================================

class TestAcceptInvitation:
    @pytest.mark.asyncio
    async def test_accept_gc_user_creates_user(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation.invite_type = "gc_user"
        invitation.email = "newuser@example.com"
        invitation.organization_id = ORG_ID
        invitation.permission_level = "MANAGEMENT"
        invitation.project_ids = []
        invitation.invited_by = USER_ID

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        result = await accept_invitation(db, "test_token", "clerk_abc123")

        assert result.status == "accepted"
        assert result.accepted_at is not None
        db.add.assert_called()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_accept_with_project_auto_assigns(self):
        db = AsyncMock()
        project_id = uuid.uuid4()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation.invite_type = "gc_user"
        invitation.email = "team@example.com"
        invitation.organization_id = ORG_ID
        invitation.permission_level = "USER"
        invitation.project_ids = [project_id]
        invitation.invited_by = USER_ID

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        await accept_invitation(db, "token123", "clerk_xyz")

        # Should have added User + ProjectAssignment
        assert db.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_accept_sub_user(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation.invite_type = "sub_user"
        invitation.email = "sub@company.com"
        invitation.sub_company_id = SUB_COMPANY_ID

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        result = await accept_invitation(db, "sub_token", "clerk_sub")
        assert result.status == "accepted"

    @pytest.mark.asyncio
    async def test_accept_owner_user(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation.invite_type = "owner_user"
        invitation.email = "owner@client.com"
        invitation.owner_account_id = OWNER_ACCOUNT_ID

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        result = await accept_invitation(db, "owner_token", "clerk_owner")
        assert result.status == "accepted"

    @pytest.mark.asyncio
    async def test_expired_invitation_rejected(self):
        from fastapi import HTTPException

        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await accept_invitation(db, "expired_token", "clerk_123")
        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_already_accepted_rejected(self):
        from fastapi import HTTPException

        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "accepted"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await accept_invitation(db, "used_token", "clerk_456")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        from fastapi import HTTPException

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await accept_invitation(db, "nonexistent_token", "clerk_789")
        assert exc_info.value.status_code == 404


# ============================================================
# CANCEL & RESEND
# ============================================================

class TestCancelInvitation:
    @pytest.mark.asyncio
    async def test_cancel_sets_revoked(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.organization_id = ORG_ID

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        inv_id = uuid.uuid4()
        result = await cancel_invitation(db, inv_id, ORG_ID)
        assert result.status == "revoked"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_non_pending_raises_400(self):
        from fastapi import HTTPException

        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "accepted"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await cancel_invitation(db, uuid.uuid4(), ORG_ID)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises_404(self):
        from fastapi import HTTPException

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await cancel_invitation(db, uuid.uuid4(), ORG_ID)
        assert exc_info.value.status_code == 404


class TestResendInvitation:
    @pytest.mark.asyncio
    async def test_resend_refreshes_expiry(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "pending"
        invitation.expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # expired

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        result = await resend_invitation(db, uuid.uuid4(), ORG_ID)

        # Expiry should be refreshed to ~14 days from now
        now = datetime.now(timezone.utc)
        assert result.expires_at > now + timedelta(days=13)
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_resend_non_pending_raises_400(self):
        from fastapi import HTTPException

        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        invitation.status = "accepted"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await resend_invitation(db, uuid.uuid4(), ORG_ID)
        assert exc_info.value.status_code == 400


# ============================================================
# LOOKUP HELPERS
# ============================================================

class TestLookupHelpers:
    @pytest.mark.asyncio
    async def test_get_invitation_by_token(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        found = await get_invitation_by_token(db, "some_token")
        assert found == invitation

    @pytest.mark.asyncio
    async def test_get_invitation_by_token_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        found = await get_invitation_by_token(db, "invalid_token")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_pending_by_email(self):
        db = AsyncMock()
        invitation = MagicMock(spec=Invitation)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = invitation
        db.execute.return_value = result_mock

        found = await get_pending_invitation_by_email(db, "test@example.com")
        assert found == invitation

    @pytest.mark.asyncio
    async def test_get_user_by_email_finds_gc_user(self):
        db = AsyncMock()
        user = MagicMock(spec=User)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute.return_value = result_mock

        found = await get_user_by_email(db, "gc@test.com")
        assert found == user

    @pytest.mark.asyncio
    async def test_get_user_by_email_finds_sub_user(self):
        db = AsyncMock()
        sub_user = MagicMock(spec=SubUser)
        # First call (User table) returns None, second (SubUser) returns user
        result_none = MagicMock()
        result_none.scalar_one_or_none.return_value = None
        result_found = MagicMock()
        result_found.scalar_one_or_none.return_value = sub_user
        db.execute.side_effect = [result_none, result_found]

        found = await get_user_by_email(db, "sub@test.com")
        assert found == sub_user

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        found = await get_user_by_email(db, "nobody@test.com")
        assert found is None

    @pytest.mark.asyncio
    async def test_list_invitations(self):
        db = AsyncMock()
        inv1 = MagicMock(spec=Invitation)
        inv2 = MagicMock(spec=Invitation)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [inv1, inv2]
        db.execute.return_value = result_mock

        invitations = await list_invitations(db, ORG_ID)
        assert len(invitations) == 2
