"""Tests for admin portal — auth service, admin service, and router."""
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.admin_user import AdminUser
from app.models.organization import Organization
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser
from app.models.project import Project
from app.models.sub_company import SubCompany
from app.models.audit_log import AuditLog
from app.services.admin_auth_service import (
    hash_password,
    verify_password,
    create_admin_token,
    verify_admin_token,
    authenticate_admin,
)
from app.services.admin_service import (
    get_platform_stats,
    list_organizations,
    get_organization_detail,
    list_org_users,
    search_users,
    impersonate_user,
)
from tests.conftest import (
    ORG_ID, ADMIN_USER_ID, MGMT_USER_ID,
    SUB_COMPANY_ID, SUB_USER_ID, OWNER_ACCOUNT_ID, OWNER_USER_ID,
)


ADMIN_ID = uuid.uuid4()


# ============================================================
# HELPERS
# ============================================================

def _make_admin_user(
    admin_id=ADMIN_ID,
    email="admin@conflo.com",
    name="Admin User",
    role="admin",
    is_active=True,
):
    admin = MagicMock(spec=AdminUser)
    admin.id = admin_id
    admin.email = email
    admin.name = name
    admin.role = role
    admin.is_active = is_active
    admin.password_hash = hash_password("secret123")
    admin.last_login_at = None
    admin.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    admin.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return admin


def _make_org(
    org_id=ORG_ID,
    name="Test GC Corp",
    tier="PROFESSIONAL",
    status="ACTIVE",
):
    org = MagicMock(spec=Organization)
    org.id = org_id
    org.name = name
    org.logo_url = None
    org.address_line1 = "123 Main St"
    org.address_line2 = None
    org.city = "Denver"
    org.state = "CO"
    org.zip_code = "80202"
    org.phone = "303-555-1234"
    org.timezone = "America/Denver"
    org.subscription_tier = tier
    org.subscription_status = status
    org.stripe_customer_id = "cus_test123"
    org.stripe_subscription_id = "sub_test123"
    org.grace_period_end = None
    org.onboarding_completed = True
    org.contract_start_date = None
    org.contract_end_date = None
    org.created_at = datetime(2026, 1, 15, tzinfo=timezone.utc)
    org.updated_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
    return org


def _make_gc_user(user_id=ADMIN_USER_ID, email="pm@test.com", name="Project Manager"):
    user = MagicMock(spec=User)
    user.id = user_id
    user.organization_id = ORG_ID
    user.clerk_user_id = f"clerk_{user_id}"
    user.email = email
    user.name = name
    user.phone = "303-555-0001"
    user.title = "Project Manager"
    user.permission_level = "OWNER_ADMIN"
    user.status = "ACTIVE"
    user.last_active_at = datetime(2026, 2, 25, tzinfo=timezone.utc)
    user.created_at = datetime(2026, 1, 20, tzinfo=timezone.utc)
    user.deleted_at = None
    return user


def _make_sub_user(user_id=SUB_USER_ID, email="sub@subco.com", name="Sub User"):
    user = MagicMock(spec=SubUser)
    user.id = user_id
    user.sub_company_id = SUB_COMPANY_ID
    user.clerk_user_id = f"clerk_{user_id}"
    user.email = email
    user.name = name
    user.status = "ACTIVE"
    return user


def _make_owner_user(user_id=OWNER_USER_ID, email="owner@corp.com", name="Owner User"):
    user = MagicMock(spec=OwnerUser)
    user.id = user_id
    user.owner_account_id = OWNER_ACCOUNT_ID
    user.clerk_user_id = f"clerk_{user_id}"
    user.email = email
    user.name = name
    user.status = "ACTIVE"
    return user


def _make_project(
    project_id=None,
    name="Test Project",
    phase="ACTIVE",
    contract_value=500000,
    is_major=True,
):
    p = MagicMock(spec=Project)
    p.id = project_id or uuid.uuid4()
    p.organization_id = ORG_ID
    p.name = name
    p.project_number = "P-001"
    p.phase = phase
    p.project_type = "COMMERCIAL"
    p.contract_value = contract_value
    p.is_major = is_major
    p.created_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
    p.deleted_at = None
    return p


# ============================================================
# PASSWORD HASHING
# ============================================================

class TestPasswordHashing:
    def test_hash_password_returns_salted_hash(self):
        pw_hash = hash_password("mypassword")
        assert "$" in pw_hash
        parts = pw_hash.split("$")
        assert len(parts) == 2
        # Salt should be 64 hex chars (32 bytes)
        assert len(parts[0]) == 64
        # Hash should be 64 hex chars (sha256)
        assert len(parts[1]) == 64

    def test_same_password_different_hashes(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # Different salts

    def test_verify_password_correct(self):
        pw_hash = hash_password("correct_password")
        assert verify_password("correct_password", pw_hash) is True

    def test_verify_password_incorrect(self):
        pw_hash = hash_password("correct_password")
        assert verify_password("wrong_password", pw_hash) is False

    def test_verify_password_invalid_hash_format(self):
        assert verify_password("password", "nohashformat") is False

    def test_verify_password_empty_password(self):
        pw_hash = hash_password("")
        assert verify_password("", pw_hash) is True
        assert verify_password("notempty", pw_hash) is False


# ============================================================
# JWT TOKEN CREATION / VERIFICATION
# ============================================================

class TestAdminToken:
    def test_create_token_returns_string(self):
        token = create_admin_token(ADMIN_ID, "admin@conflo.com")
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_verify_valid_token(self):
        token = create_admin_token(ADMIN_ID, "admin@conflo.com")
        payload = verify_admin_token(token)
        assert payload is not None
        assert payload["sub"] == str(ADMIN_ID)
        assert payload["email"] == "admin@conflo.com"
        assert payload["type"] == "admin"

    def test_verify_expired_token(self):
        """Token with exp in the past should fail."""
        with patch("app.services.admin_auth_service.time") as mock_time:
            # Create token at time 0 with 24h expiry
            mock_time.time.return_value = 0
            token = create_admin_token(ADMIN_ID, "admin@conflo.com")

        # Verify at time way past expiry (25 hours later)
        payload = verify_admin_token(token)
        # Token was created at time=0, exp=86400, current time is real (2026) >> 86400
        assert payload is None

    def test_verify_tampered_token(self):
        token = create_admin_token(ADMIN_ID, "admin@conflo.com")
        # Tamper with the signature
        parts = token.split(".")
        parts[2] = parts[2][::-1]  # Reverse signature
        tampered = ".".join(parts)
        assert verify_admin_token(tampered) is None

    def test_verify_invalid_format(self):
        assert verify_admin_token("not.a.valid.token.at.all") is None
        assert verify_admin_token("garbage") is None
        assert verify_admin_token("") is None

    def test_verify_wrong_type(self):
        """Token with type != 'admin' should fail."""
        # Manually craft a token with wrong type by patching
        import json
        import base64
        import hashlib
        import hmac
        from app.services.admin_auth_service import _get_signing_key, _b64url_encode

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(ADMIN_ID),
            "email": "admin@conflo.com",
            "type": "not_admin",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,
        }
        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{header_b64}.{payload_b64}"
        sig = hmac.new(_get_signing_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
        sig_b64 = _b64url_encode(sig)
        token = f"{header_b64}.{payload_b64}.{sig_b64}"

        assert verify_admin_token(token) is None

    def test_token_contains_iat_and_exp(self):
        before = int(time.time())
        token = create_admin_token(ADMIN_ID, "admin@conflo.com")
        payload = verify_admin_token(token)
        after = int(time.time())
        assert before <= payload["iat"] <= after
        assert payload["exp"] == payload["iat"] + 86400


# ============================================================
# AUTHENTICATE ADMIN
# ============================================================

class TestAuthenticateAdmin:
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        db = AsyncMock()
        pw_hash = hash_password("secret123")
        admin = _make_admin_user()
        admin.password_hash = pw_hash

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin
        db.execute.return_value = mock_result

        result = await authenticate_admin(db, "admin@conflo.com", "secret123")
        assert result is not None
        assert result.email == "admin@conflo.com"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self):
        db = AsyncMock()
        pw_hash = hash_password("secret123")
        admin = _make_admin_user()
        admin.password_hash = pw_hash

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin
        db.execute.return_value = mock_result

        result = await authenticate_admin(db, "admin@conflo.com", "wrongpass")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await authenticate_admin(db, "missing@conflo.com", "secret123")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self):
        db = AsyncMock()
        # The query filters is_active == True, so inactive users won't be returned
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await authenticate_admin(db, "inactive@conflo.com", "secret123")
        assert result is None


# ============================================================
# PLATFORM STATS
# ============================================================

class TestPlatformStats:
    @pytest.mark.asyncio
    async def test_returns_all_metrics(self):
        db = AsyncMock()

        # Mock sequential scalar_one calls:
        # total_orgs, total_gc_users, total_sub_users, total_owner_users, total_projects, total_sub_companies
        scalar_values = [5, 20, 15, 3, 50, 10]
        call_count = 0

        def make_scalar_result(val):
            r = MagicMock()
            r.scalar_one.return_value = val
            return r

        # orgs_by_tier returns .all()
        tier_result = MagicMock()
        tier_result.all.return_value = [
            ("STARTER", 2),
            ("PROFESSIONAL", 2),
            ("SCALE", 1),
        ]

        results = [
            make_scalar_result(5),    # total_orgs
            make_scalar_result(20),   # total_gc_users
            make_scalar_result(15),   # total_sub_users
            make_scalar_result(3),    # total_owner_users
            make_scalar_result(50),   # total_projects
            make_scalar_result(10),   # total_sub_companies
            tier_result,              # orgs_by_tier
        ]
        db.execute.side_effect = results

        stats = await get_platform_stats(db)

        assert stats["total_organizations"] == 5
        assert stats["total_users"] == 38  # 20 + 15 + 3
        assert stats["total_projects"] == 50
        assert stats["total_sub_companies"] == 10
        assert stats["orgs_by_tier"]["STARTER"] == 2
        assert stats["orgs_by_tier"]["PROFESSIONAL"] == 2
        assert stats["orgs_by_tier"]["SCALE"] == 1
        # MRR: STARTER 2*349*100 + PROFESSIONAL 2*2500*100 + SCALE 1*4500*100
        expected_mrr = (2 * 349 * 100) + (2 * 2500 * 100) + (1 * 4500 * 100)
        assert stats["monthly_recurring_revenue"] == expected_mrr

    @pytest.mark.asyncio
    async def test_empty_platform(self):
        db = AsyncMock()

        def make_scalar_result(val):
            r = MagicMock()
            r.scalar_one.return_value = val
            return r

        tier_result = MagicMock()
        tier_result.all.return_value = []

        results = [
            make_scalar_result(0),
            make_scalar_result(0),
            make_scalar_result(0),
            make_scalar_result(0),
            make_scalar_result(0),
            make_scalar_result(0),
            tier_result,
        ]
        db.execute.side_effect = results

        stats = await get_platform_stats(db)
        assert stats["total_organizations"] == 0
        assert stats["total_users"] == 0
        assert stats["total_projects"] == 0
        assert stats["monthly_recurring_revenue"] == 0
        assert stats["orgs_by_tier"] == {}


# ============================================================
# LIST ORGANIZATIONS
# ============================================================

class TestListOrganizations:
    @pytest.mark.asyncio
    async def test_returns_paginated_list(self):
        db = AsyncMock()
        org1 = _make_org(uuid.uuid4(), "Acme GC", "STARTER", "ACTIVE")
        org2 = _make_org(uuid.uuid4(), "Builder Co", "PROFESSIONAL", "ACTIVE")

        # count query
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        # org list query
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [org1, org2]
        list_result = MagicMock()
        list_result.scalars.return_value = scalars_mock

        # user_count for org1
        uc1 = MagicMock()
        uc1.scalar_one.return_value = 5

        # project_count for org1
        pc1 = MagicMock()
        pc1.scalar_one.return_value = 3

        # user_count for org2
        uc2 = MagicMock()
        uc2.scalar_one.return_value = 10

        # project_count for org2
        pc2 = MagicMock()
        pc2.scalar_one.return_value = 8

        db.execute.side_effect = [count_result, list_result, uc1, pc1, uc2, pc2]

        result = await list_organizations(db, page=1, per_page=25)

        assert result["meta"]["total"] == 2
        assert result["meta"]["page"] == 1
        assert len(result["data"]) == 2
        assert result["data"][0]["name"] == "Acme GC"
        assert result["data"][0]["user_count"] == 5
        assert result["data"][0]["project_count"] == 3
        assert result["data"][1]["name"] == "Builder Co"
        assert result["data"][1]["user_count"] == 10

    @pytest.mark.asyncio
    async def test_search_filter(self):
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        list_result = MagicMock()
        list_result.scalars.return_value = scalars_mock

        db.execute.side_effect = [count_result, list_result]

        result = await list_organizations(db, page=1, per_page=25, search="nonexistent")
        assert result["data"] == []
        assert result["meta"]["total"] == 0

    @pytest.mark.asyncio
    async def test_pagination_meta(self):
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 50

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        list_result = MagicMock()
        list_result.scalars.return_value = scalars_mock

        db.execute.side_effect = [count_result, list_result]

        result = await list_organizations(db, page=2, per_page=10)
        assert result["meta"]["total"] == 50
        assert result["meta"]["total_pages"] == 5
        assert result["meta"]["page"] == 2
        assert result["meta"]["per_page"] == 10


# ============================================================
# GET ORGANIZATION DETAIL
# ============================================================

class TestGetOrganizationDetail:
    @pytest.mark.asyncio
    async def test_returns_full_detail(self):
        db = AsyncMock()
        org = _make_org()
        user = _make_gc_user()
        project = _make_project()

        db.get.return_value = org

        # users query
        users_scalars = MagicMock()
        users_scalars.all.return_value = [user]
        users_result = MagicMock()
        users_result.scalars.return_value = users_scalars

        # projects query
        projects_scalars = MagicMock()
        projects_scalars.all.return_value = [project]
        projects_result = MagicMock()
        projects_result.scalars.return_value = projects_scalars

        db.execute.side_effect = [users_result, projects_result]

        detail = await get_organization_detail(db, ORG_ID)

        assert detail is not None
        assert detail["id"] == str(ORG_ID)
        assert detail["name"] == "Test GC Corp"
        assert detail["subscription_tier"] == "PROFESSIONAL"
        assert len(detail["users"]) == 1
        assert detail["users"][0]["email"] == "pm@test.com"
        assert len(detail["projects"]) == 1
        assert detail["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self):
        db = AsyncMock()
        db.get.return_value = None

        detail = await get_organization_detail(db, uuid.uuid4())
        assert detail is None


# ============================================================
# LIST ORG USERS
# ============================================================

class TestListOrgUsers:
    @pytest.mark.asyncio
    async def test_returns_user_list(self):
        db = AsyncMock()
        user1 = _make_gc_user(uuid.uuid4(), "user1@test.com", "User One")
        user2 = _make_gc_user(uuid.uuid4(), "user2@test.com", "User Two")
        user2.permission_level = "MANAGEMENT"

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [user1, user2]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute.return_value = result_mock

        users = await list_org_users(db, ORG_ID)
        assert len(users) == 2
        assert users[0]["email"] == "user1@test.com"
        assert users[1]["permission_level"] == "MANAGEMENT"


# ============================================================
# SEARCH USERS
# ============================================================

class TestSearchUsers:
    @pytest.mark.asyncio
    async def test_search_finds_gc_users(self):
        db = AsyncMock()
        gc_user = _make_gc_user()

        gc_scalars = MagicMock()
        gc_scalars.all.return_value = [gc_user]
        gc_result = MagicMock()
        gc_result.scalars.return_value = gc_scalars

        sub_scalars = MagicMock()
        sub_scalars.all.return_value = []
        sub_result = MagicMock()
        sub_result.scalars.return_value = sub_scalars

        owner_scalars = MagicMock()
        owner_scalars.all.return_value = []
        owner_result = MagicMock()
        owner_result.scalars.return_value = owner_scalars

        db.execute.side_effect = [gc_result, sub_result, owner_result]

        results = await search_users(db, "pm@test")
        assert len(results) == 1
        assert results[0]["user_type"] == "gc"
        assert results[0]["email"] == "pm@test.com"

    @pytest.mark.asyncio
    async def test_search_finds_sub_users(self):
        db = AsyncMock()
        sub_user = _make_sub_user()

        gc_scalars = MagicMock()
        gc_scalars.all.return_value = []
        gc_result = MagicMock()
        gc_result.scalars.return_value = gc_scalars

        sub_scalars = MagicMock()
        sub_scalars.all.return_value = [sub_user]
        sub_result = MagicMock()
        sub_result.scalars.return_value = sub_scalars

        owner_scalars = MagicMock()
        owner_scalars.all.return_value = []
        owner_result = MagicMock()
        owner_result.scalars.return_value = owner_scalars

        db.execute.side_effect = [gc_result, sub_result, owner_result]

        results = await search_users(db, "sub@subco")
        assert len(results) == 1
        assert results[0]["user_type"] == "sub"
        assert results[0]["sub_company_id"] == str(SUB_COMPANY_ID)

    @pytest.mark.asyncio
    async def test_search_finds_owner_users(self):
        db = AsyncMock()
        owner_user = _make_owner_user()

        gc_scalars = MagicMock()
        gc_scalars.all.return_value = []
        gc_result = MagicMock()
        gc_result.scalars.return_value = gc_scalars

        sub_scalars = MagicMock()
        sub_scalars.all.return_value = []
        sub_result = MagicMock()
        sub_result.scalars.return_value = sub_scalars

        owner_scalars = MagicMock()
        owner_scalars.all.return_value = [owner_user]
        owner_result = MagicMock()
        owner_result.scalars.return_value = owner_scalars

        db.execute.side_effect = [gc_result, sub_result, owner_result]

        results = await search_users(db, "owner@corp")
        assert len(results) == 1
        assert results[0]["user_type"] == "owner"
        assert results[0]["owner_account_id"] == str(OWNER_ACCOUNT_ID)

    @pytest.mark.asyncio
    async def test_search_returns_combined_results(self):
        db = AsyncMock()
        gc_user = _make_gc_user()
        sub_user = _make_sub_user()
        owner_user = _make_owner_user()

        gc_scalars = MagicMock()
        gc_scalars.all.return_value = [gc_user]
        gc_result = MagicMock()
        gc_result.scalars.return_value = gc_scalars

        sub_scalars = MagicMock()
        sub_scalars.all.return_value = [sub_user]
        sub_result = MagicMock()
        sub_result.scalars.return_value = sub_scalars

        owner_scalars = MagicMock()
        owner_scalars.all.return_value = [owner_user]
        owner_result = MagicMock()
        owner_result.scalars.return_value = owner_scalars

        db.execute.side_effect = [gc_result, sub_result, owner_result]

        results = await search_users(db, "test")
        assert len(results) == 3
        types = {r["user_type"] for r in results}
        assert types == {"gc", "sub", "owner"}

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        db = AsyncMock()

        for _ in range(3):
            pass

        gc_scalars = MagicMock()
        gc_scalars.all.return_value = []
        gc_result = MagicMock()
        gc_result.scalars.return_value = gc_scalars

        sub_scalars = MagicMock()
        sub_scalars.all.return_value = []
        sub_result = MagicMock()
        sub_result.scalars.return_value = sub_scalars

        owner_scalars = MagicMock()
        owner_scalars.all.return_value = []
        owner_result = MagicMock()
        owner_result.scalars.return_value = owner_scalars

        db.execute.side_effect = [gc_result, sub_result, owner_result]

        results = await search_users(db, "nonexistent")
        assert len(results) == 0


# ============================================================
# IMPERSONATION
# ============================================================

class TestImpersonateUser:
    @pytest.mark.asyncio
    async def test_impersonate_gc_user(self):
        db = AsyncMock()
        gc_user = _make_gc_user()

        scalars_mock = MagicMock()
        scalars_mock.scalar_one_or_none.return_value = gc_user
        db.execute.return_value = scalars_mock

        ctx = await impersonate_user(db, ADMIN_ID, ADMIN_USER_ID, "gc")

        assert ctx is not None
        assert ctx["user_type"] == "gc"
        assert ctx["email"] == "pm@test.com"
        assert ctx["organization_id"] == str(ORG_ID)
        # Verify audit log was created
        db.add.assert_called_once()
        audit = db.add.call_args[0][0]
        assert isinstance(audit, AuditLog)
        assert audit.action == "admin_impersonate"
        assert audit.actor_id == ADMIN_ID

    @pytest.mark.asyncio
    async def test_impersonate_sub_user(self):
        db = AsyncMock()
        sub_user = _make_sub_user()

        scalars_mock = MagicMock()
        scalars_mock.scalar_one_or_none.return_value = sub_user
        db.execute.return_value = scalars_mock

        ctx = await impersonate_user(db, ADMIN_ID, SUB_USER_ID, "sub")

        assert ctx is not None
        assert ctx["user_type"] == "sub"
        assert ctx["sub_company_id"] == str(SUB_COMPANY_ID)
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_impersonate_owner_user(self):
        db = AsyncMock()
        owner_user = _make_owner_user()

        scalars_mock = MagicMock()
        scalars_mock.scalar_one_or_none.return_value = owner_user
        db.execute.return_value = scalars_mock

        ctx = await impersonate_user(db, ADMIN_ID, OWNER_USER_ID, "owner")

        assert ctx is not None
        assert ctx["user_type"] == "owner"
        assert ctx["owner_account_id"] == str(OWNER_ACCOUNT_ID)
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_impersonate_nonexistent_user(self):
        db = AsyncMock()

        scalars_mock = MagicMock()
        scalars_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = scalars_mock

        ctx = await impersonate_user(db, ADMIN_ID, uuid.uuid4(), "gc")
        assert ctx is None
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_impersonate_logs_audit(self):
        db = AsyncMock()
        gc_user = _make_gc_user()

        scalars_mock = MagicMock()
        scalars_mock.scalar_one_or_none.return_value = gc_user
        db.execute.return_value = scalars_mock

        await impersonate_user(db, ADMIN_ID, ADMIN_USER_ID, "gc")

        audit = db.add.call_args[0][0]
        assert audit.after_data["admin_id"] == str(ADMIN_ID)
        assert audit.after_data["target_user_id"] == str(ADMIN_USER_ID)
        assert audit.after_data["target_user_type"] == "gc"
        assert audit.after_data["target_email"] == "pm@test.com"
        assert audit.resource_type == "gc_user"


# ============================================================
# ADMIN ROUTER — get_admin_user DEPENDENCY
# ============================================================

class TestGetAdminUserDependency:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        from app.routers.admin import get_admin_user
        token = create_admin_token(ADMIN_ID, "admin@conflo.com")
        request = MagicMock()
        request.headers.get.return_value = f"Bearer {token}"

        result = await get_admin_user(request)
        assert result["admin_id"] == str(ADMIN_ID)
        assert result["email"] == "admin@conflo.com"

    @pytest.mark.asyncio
    async def test_missing_auth_header(self):
        from app.routers.admin import get_admin_user
        request = MagicMock()
        request.headers.get.return_value = ""

        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        from app.routers.admin import get_admin_user
        request = MagicMock()
        request.headers.get.return_value = "Bearer invalidtoken"

        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_bearer_prefix(self):
        from app.routers.admin import get_admin_user
        request = MagicMock()
        request.headers.get.return_value = "Token abc123"

        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(request)
        assert exc_info.value.status_code == 401


# ============================================================
# ADMIN MODEL
# ============================================================

class TestAdminUserModel:
    def test_table_name(self):
        assert AdminUser.__tablename__ == "admin_users"

    def test_columns_exist(self):
        columns = {c.name for c in AdminUser.__table__.columns}
        expected = {
            "id", "email", "password_hash", "name", "role",
            "is_active", "last_login_at", "created_at", "updated_at",
        }
        assert expected.issubset(columns)

    def test_email_unique(self):
        email_col = AdminUser.__table__.c.email
        assert email_col.unique is True

    def test_role_default(self):
        role_col = AdminUser.__table__.c.role
        assert role_col.server_default is not None


# ============================================================
# ADMIN SCHEMAS
# ============================================================

class TestAdminSchemas:
    def test_login_request(self):
        from app.schemas.admin import AdminLoginRequest
        req = AdminLoginRequest(email="admin@conflo.com", password="secret")
        assert req.email == "admin@conflo.com"
        assert req.password == "secret"

    def test_impersonate_request(self):
        from app.schemas.admin import ImpersonateRequest
        req = ImpersonateRequest(user_id=str(uuid.uuid4()), user_type="gc")
        assert req.user_type == "gc"

    def test_platform_stats_defaults(self):
        from app.schemas.admin import PlatformStats
        stats = PlatformStats()
        assert stats.total_organizations == 0
        assert stats.total_users == 0
        assert stats.monthly_recurring_revenue == 0
        assert stats.orgs_by_tier == {}

    def test_org_list_item(self):
        from app.schemas.admin import OrgListItem
        item = OrgListItem(
            id=str(uuid.uuid4()),
            name="Test Org",
            user_count=5,
            project_count=3,
        )
        assert item.name == "Test Org"
        assert item.user_count == 5
        assert item.subscription_tier is None


# ============================================================
# AUTH MIDDLEWARE — admin path exclusion
# ============================================================

class TestAuthMiddlewareAdminExclusion:
    def test_admin_in_public_paths(self):
        from app.middleware.auth import PUBLIC_PATH_PREFIXES
        assert any(p.startswith("/api/admin") for p in PUBLIC_PATH_PREFIXES)

    def test_admin_login_path_is_public(self):
        from app.middleware.auth import PUBLIC_PATH_PREFIXES
        path = "/api/admin/login"
        assert any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)

    def test_admin_stats_path_is_public(self):
        from app.middleware.auth import PUBLIC_PATH_PREFIXES
        path = "/api/admin/stats"
        assert any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)

    def test_gc_routes_not_public(self):
        from app.middleware.auth import PUBLIC_PATH_PREFIXES
        path = "/api/gc/projects"
        assert not any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)
