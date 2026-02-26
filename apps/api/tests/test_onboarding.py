"""Tests for onboarding wizard endpoints."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.models.cost_code_template import CostCodeTemplate
from app.routers.onboarding import (
    CSI_MASTERFORMAT,
    _get_user,
    _require_owner_admin,
)


ORG_ID = uuid.uuid4()
USER_ID = uuid.uuid4()

OWNER_ADMIN_CTX = {
    "user_id": USER_ID,
    "organization_id": ORG_ID,
    "permission_level": "OWNER_ADMIN",
    "user_type": "gc",
}


def _make_request(user_ctx: dict | None = None):
    """Create a mock request with user context on state."""
    request = MagicMock()
    request.state.user = user_ctx
    return request


# ============================================================
# AUTH HELPERS
# ============================================================

class TestAuthHelpers:
    def test_get_user_returns_context(self):
        request = _make_request(OWNER_ADMIN_CTX)
        user = _get_user(request)
        assert user["user_id"] == USER_ID

    def test_get_user_raises_401_when_missing(self):
        request = MagicMock(spec=[])
        request.state = MagicMock(spec=[])
        with pytest.raises(HTTPException) as exc_info:
            _get_user(request)
        assert exc_info.value.status_code == 401

    def test_require_owner_admin_passes_for_owner_admin(self):
        # Should not raise
        _require_owner_admin(OWNER_ADMIN_CTX)

    def test_require_owner_admin_rejects_user_level(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_owner_admin({"permission_level": "USER"})
        assert exc_info.value.status_code == 403

    def test_require_owner_admin_rejects_management(self):
        with pytest.raises(HTTPException) as exc_info:
            _require_owner_admin({"permission_level": "MANAGEMENT"})
        assert exc_info.value.status_code == 403


# ============================================================
# POST /company
# ============================================================

class TestUpdateCompany:
    @pytest.mark.asyncio
    async def test_updates_org_fields(self):
        from app.routers.onboarding import update_company_profile

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        db.get.return_value = org

        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.model_dump.return_value = {"name": "ACME Construction", "phone": "555-1234"}

        result = await update_company_profile(request, body, db)
        assert org.name == "ACME Construction"
        assert org.phone == "555-1234"
        assert "name" in result["data"]["updated_fields"]
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_org_not_found_raises_404(self):
        from app.routers.onboarding import update_company_profile

        db = AsyncMock()
        db.get.return_value = None

        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.model_dump.return_value = {"name": "Test"}

        with pytest.raises(HTTPException) as exc_info:
            await update_company_profile(request, body, db)
        assert exc_info.value.status_code == 404


# ============================================================
# POST /profile
# ============================================================

class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_user_fields(self):
        from app.routers.onboarding import update_user_profile

        db = AsyncMock()
        user = MagicMock(spec=User)
        db.get.return_value = user

        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.model_dump.return_value = {"name": "Jane Smith", "title": "PM"}

        result = await update_user_profile(request, body, db)
        assert user.name == "Jane Smith"
        assert user.title == "PM"
        assert "name" in result["data"]["updated_fields"]

    @pytest.mark.asyncio
    async def test_user_not_found_raises_404(self):
        from app.routers.onboarding import update_user_profile

        db = AsyncMock()
        db.get.return_value = None

        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.model_dump.return_value = {"name": "Nobody"}

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(request, body, db)
        assert exc_info.value.status_code == 404


# ============================================================
# POST /cost-codes
# ============================================================

class TestCostCodes:
    @pytest.mark.asyncio
    async def test_skip_returns_no_creation(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "skip"

        result = await select_cost_codes(request, body, db)
        assert result["data"]["template"] == "skip"
        assert result["data"]["created"] is False
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_case_insensitive(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "SKIP"

        result = await select_cost_codes(request, body, db)
        assert result["data"]["template"] == "skip"

    @pytest.mark.asyncio
    async def test_csi_masterformat_creates_template(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "CSI_MASTERFORMAT"  # Uppercase from frontend

        result = await select_cost_codes(request, body, db)
        assert result["data"]["code_count"] == len(CSI_MASTERFORMAT)
        db.add.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_csi_masterformat_lowercase_also_works(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "csi_masterformat"

        result = await select_cost_codes(request, body, db)
        assert result["data"]["code_count"] == len(CSI_MASTERFORMAT)

    @pytest.mark.asyncio
    async def test_custom_requires_codes(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "CUSTOM"
        body.custom_codes = None

        with pytest.raises(HTTPException) as exc_info:
            await select_cost_codes(request, body, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_custom_with_codes_creates_template(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "CUSTOM"
        body.custom_codes = [{"code": "A1", "description": "Custom code"}]

        result = await select_cost_codes(request, body, db)
        assert result["data"]["code_count"] == 1
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_template_raises_400(self):
        from app.routers.onboarding import select_cost_codes

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.template = "INVALID_VALUE"

        with pytest.raises(HTTPException) as exc_info:
            await select_cost_codes(request, body, db)
        assert exc_info.value.status_code == 400


# ============================================================
# POST /project
# ============================================================

class TestCreateFirstProject:
    @pytest.mark.asyncio
    async def test_creates_project_with_defaults(self):
        from app.routers.onboarding import create_first_project

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.name = "My First Project"
        body.project_number = "P-001"
        body.address = "123 Main St"
        body.project_type = "COMMERCIAL"
        body.contract_value = None
        body.phase = "ACTIVE"

        result = await create_first_project(request, body, db)
        assert result["data"]["name"] == "My First Project"
        assert result["data"]["phase"] == "ACTIVE"
        # Should add project + portal config + assignment = 3 adds
        assert db.add.call_count == 3
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch("app.routers.onboarding.check_tier_limit")
    async def test_major_project_triggers_tier_check(self, mock_check):
        from app.routers.onboarding import create_first_project

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.name = "Big Project"
        body.project_number = None
        body.address = None
        body.project_type = "COMMERCIAL"
        body.contract_value = 500000.0  # >= 250K
        body.phase = "BIDDING"

        await create_first_project(request, body, db)
        mock_check.assert_called_once_with(db, ORG_ID)

    @pytest.mark.asyncio
    async def test_minor_project_skips_tier_check(self):
        from app.routers.onboarding import create_first_project

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        body = MagicMock()
        body.name = "Small Project"
        body.project_number = None
        body.address = None
        body.project_type = "COMMERCIAL"
        body.contract_value = 100000.0  # < 250K
        body.phase = "ACTIVE"

        with patch("app.routers.onboarding.check_tier_limit") as mock_check:
            await create_first_project(request, body, db)
            mock_check.assert_not_called()


# ============================================================
# POST /invite-team
# ============================================================

class TestInviteTeam:
    @pytest.mark.asyncio
    @patch("app.routers.onboarding.create_invitation")
    async def test_invites_multiple_members(self, mock_invite):
        from app.routers.onboarding import invite_team_members

        inv = MagicMock()
        inv.id = uuid.uuid4()
        mock_invite.return_value = inv

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        member1 = MagicMock()
        member1.email = "alice@team.com"
        member1.permission_level = "MANAGEMENT"
        member2 = MagicMock()
        member2.email = "bob@team.com"
        member2.permission_level = "USER"
        body = MagicMock()
        body.members = [member1, member2]

        result = await invite_team_members(request, body, db)
        assert result["meta"]["total_invited"] == 2
        assert result["meta"]["total_errors"] == 0
        assert mock_invite.call_count == 2

    @pytest.mark.asyncio
    @patch("app.routers.onboarding.create_invitation")
    async def test_handles_individual_invite_errors(self, mock_invite):
        from app.routers.onboarding import invite_team_members

        mock_invite.side_effect = HTTPException(status_code=409, detail="Already exists")

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        member = MagicMock()
        member.email = "duplicate@team.com"
        member.permission_level = "USER"
        body = MagicMock()
        body.members = [member]

        result = await invite_team_members(request, body, db)
        assert result["meta"]["total_invited"] == 0
        assert result["meta"]["total_errors"] == 1


# ============================================================
# POST /invite-subs
# ============================================================

class TestInviteSubs:
    @pytest.mark.asyncio
    @patch("app.routers.onboarding.create_invitation")
    async def test_creates_sub_company_and_invites(self, mock_invite):
        from app.routers.onboarding import invite_subs

        inv = MagicMock()
        inv.id = uuid.uuid4()
        mock_invite.return_value = inv

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        entry = MagicMock()
        entry.company_name = "SubCo Electric"
        entry.contact_email = "contact@subco.com"
        entry.trade = "Electrical"
        body = MagicMock()
        body.subs = [entry]

        result = await invite_subs(request, body, db)
        assert result["meta"]["total_invited"] == 1
        # Should add SubCompany (at minimum)
        assert db.add.called

    @pytest.mark.asyncio
    @patch("app.routers.onboarding.create_invitation")
    async def test_handles_sub_invite_error(self, mock_invite):
        from app.routers.onboarding import invite_subs

        mock_invite.side_effect = HTTPException(status_code=409, detail="Exists")

        db = AsyncMock()
        request = _make_request(OWNER_ADMIN_CTX)
        entry = MagicMock()
        entry.company_name = "DupeCo"
        entry.contact_email = "dup@sub.com"
        entry.trade = "Plumbing"
        body = MagicMock()
        body.subs = [entry]

        result = await invite_subs(request, body, db)
        assert result["meta"]["total_errors"] == 1


# ============================================================
# POST /complete
# ============================================================

class TestCompleteOnboarding:
    @pytest.mark.asyncio
    async def test_marks_onboarding_completed(self):
        from app.routers.onboarding import complete_onboarding

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.onboarding_completed = False
        db.get.return_value = org

        request = _make_request(OWNER_ADMIN_CTX)

        result = await complete_onboarding(request, db)
        assert org.onboarding_completed is True
        assert result["data"]["onboarding_completed"] is True
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_org_not_found_raises_404(self):
        from app.routers.onboarding import complete_onboarding

        db = AsyncMock()
        db.get.return_value = None

        request = _make_request(OWNER_ADMIN_CTX)

        with pytest.raises(HTTPException) as exc_info:
            await complete_onboarding(request, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_non_owner_admin_rejected(self):
        from app.routers.onboarding import complete_onboarding

        db = AsyncMock()
        request = _make_request({
            "user_id": USER_ID,
            "organization_id": ORG_ID,
            "permission_level": "USER",
        })

        with pytest.raises(HTTPException) as exc_info:
            await complete_onboarding(request, db)
        assert exc_info.value.status_code == 403


# ============================================================
# CSI MASTERFORMAT DATA
# ============================================================

class TestCSIMasterFormat:
    def test_has_25_codes(self):
        assert len(CSI_MASTERFORMAT) == 25

    def test_each_code_has_required_fields(self):
        for entry in CSI_MASTERFORMAT:
            assert "code" in entry
            assert "description" in entry

    def test_contains_key_trades(self):
        descriptions = [c["description"] for c in CSI_MASTERFORMAT]
        assert "Concrete" in descriptions
        assert "Electrical" in descriptions
        assert "HVAC" in descriptions
        assert "Plumbing" in descriptions
