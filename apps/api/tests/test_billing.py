"""Tests for billing service and Stripe integration."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.billing_service import (
    TIER_CONFIG,
    TIER_LIMITS,
    check_tier_limit,
    create_checkout_session,
    create_billing_portal_session,
    get_billing_status,
    get_org_by_subscription,
    get_org_admins,
)
from app.models.organization import Organization
from app.models.project import Project


ORG_ID = uuid.uuid4()


# ============================================================
# TIER CONFIG
# ============================================================

class TestTierConfig:
    def test_starter_limits(self):
        assert TIER_CONFIG["STARTER"]["max_major_projects"] == 3
        assert TIER_CONFIG["STARTER"]["price_monthly"] == 349

    def test_professional_limits(self):
        assert TIER_CONFIG["PROFESSIONAL"]["max_major_projects"] == 10
        assert TIER_CONFIG["PROFESSIONAL"]["price_monthly"] == 2500

    def test_scale_limits(self):
        assert TIER_CONFIG["SCALE"]["max_major_projects"] == 25
        assert TIER_CONFIG["SCALE"]["price_monthly"] == 4500

    def test_enterprise_unlimited(self):
        assert TIER_CONFIG["ENTERPRISE"]["max_major_projects"] is None

    def test_backward_compat_tier_limits(self):
        """TIER_LIMITS dict kept for backward compat with Sprint 2 tests."""
        assert TIER_LIMITS["STARTER"] == 3
        assert TIER_LIMITS["PROFESSIONAL"] == 10
        assert TIER_LIMITS["SCALE"] == 25
        assert TIER_LIMITS["ENTERPRISE"] is None

    def test_all_tiers_present(self):
        assert set(TIER_CONFIG.keys()) == {"STARTER", "PROFESSIONAL", "SCALE", "ENTERPRISE"}


# ============================================================
# CHECKOUT SESSION
# ============================================================

class TestCheckoutSession:
    @patch("app.services.billing_service.stripe")
    @patch("app.services.billing_service.TIER_STRIPE_PRICES", {"STARTER": "price_starter_test", "PROFESSIONAL": "price_pro_test", "SCALE": "price_scale_test"})
    def test_create_checkout_session_returns_url(self, mock_stripe):
        mock_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/test")
        url = create_checkout_session(
            tier="STARTER",
            organization_id=ORG_ID,
            user_email="test@example.com",
            success_url="http://localhost:3000/onboarding",
            cancel_url="http://localhost:3000/signup",
        )
        assert url == "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.assert_called_once()

    @patch("app.services.billing_service.stripe")
    @patch("app.services.billing_service.TIER_STRIPE_PRICES", {"STARTER": "price_starter_test", "PROFESSIONAL": "price_pro_test", "SCALE": "price_scale_test"})
    def test_create_checkout_session_passes_metadata(self, mock_stripe):
        mock_stripe.checkout.Session.create.return_value = MagicMock(url="https://test.com")
        create_checkout_session(
            tier="PROFESSIONAL",
            organization_id=ORG_ID,
            user_email="admin@gc.com",
            success_url="http://localhost:3000/onboarding",
            cancel_url="http://localhost:3000/signup",
        )
        call_kwargs = mock_stripe.checkout.Session.create.call_args
        assert call_kwargs.kwargs["metadata"]["tier"] == "PROFESSIONAL"
        assert call_kwargs.kwargs["metadata"]["organization_id"] == str(ORG_ID)

    def test_create_checkout_session_enterprise_raises(self):
        """Enterprise has no stripe price, should raise 400."""
        with pytest.raises(Exception):
            create_checkout_session(
                tier="ENTERPRISE",
                organization_id=ORG_ID,
                user_email="test@example.com",
                success_url="http://localhost:3000",
                cancel_url="http://localhost:3000",
            )


# ============================================================
# BILLING PORTAL
# ============================================================

class TestBillingPortal:
    @patch("app.services.billing_service.stripe")
    def test_create_billing_portal_session(self, mock_stripe):
        mock_stripe.billing_portal.Session.create.return_value = MagicMock(url="https://portal.stripe.com/test")
        url = create_billing_portal_session(
            stripe_customer_id="cus_test123",
            return_url="http://localhost:3000/settings/billing",
        )
        assert url == "https://portal.stripe.com/test"


# ============================================================
# TIER LIMIT ENFORCEMENT
# ============================================================

class TestTierLimit:
    @pytest.mark.asyncio
    async def test_enterprise_always_allowed(self):
        """Enterprise tier should never raise."""
        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "ENTERPRISE"
        db.get.return_value = org

        # Should not raise
        await check_tier_limit(db, ORG_ID)

    @pytest.mark.asyncio
    async def test_starter_under_limit_allowed(self):
        """Starter with 2 projects should be allowed."""
        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "STARTER"
        db.get.return_value = org

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 2
        db.execute.return_value = result_mock

        # Should not raise
        await check_tier_limit(db, ORG_ID)

    @pytest.mark.asyncio
    async def test_starter_at_limit_raises_402(self):
        """Starter with 3 projects should raise 402."""
        from fastapi import HTTPException

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "STARTER"
        db.get.return_value = org

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 3
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await check_tier_limit(db, ORG_ID)
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_professional_at_limit_raises_402(self):
        from fastapi import HTTPException

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "PROFESSIONAL"
        db.get.return_value = org

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 10
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await check_tier_limit(db, ORG_ID)
        assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_org_not_found_raises_404(self):
        from fastapi import HTTPException

        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await check_tier_limit(db, ORG_ID)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_exclude_project_id(self):
        """When updating contract_value, exclude the project itself from count."""
        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "STARTER"
        db.get.return_value = org

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 2  # Under limit after exclusion
        db.execute.return_value = result_mock

        exclude_id = uuid.uuid4()
        await check_tier_limit(db, ORG_ID, exclude_project_id=exclude_id)


# ============================================================
# BILLING STATUS
# ============================================================

class TestBillingStatus:
    @pytest.mark.asyncio
    async def test_returns_tier_info(self):
        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.subscription_tier = "PROFESSIONAL"
        org.subscription_status = "ACTIVE"
        org.stripe_customer_id = "cus_123"
        org.stripe_subscription_id = "sub_123"
        org.grace_period_end = None
        db.get.return_value = org

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 5
        db.execute.return_value = result_mock

        status = await get_billing_status(db, ORG_ID)
        assert status["tier"] == "PROFESSIONAL"
        assert status["subscription_status"] == "ACTIVE"
        assert status["current_major_project_count"] == 5
        assert status["max_major_projects"] == 10
        assert status["price_monthly"] == 2500


# ============================================================
# HELPER LOOKUPS
# ============================================================

class TestHelperLookups:
    @pytest.mark.asyncio
    async def test_get_org_by_subscription(self):
        db = AsyncMock()
        org = MagicMock(spec=Organization)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = org
        db.execute.return_value = result_mock

        found = await get_org_by_subscription(db, "sub_123")
        assert found == org

    @pytest.mark.asyncio
    async def test_get_org_by_subscription_not_found(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        found = await get_org_by_subscription(db, "sub_nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_org_admins(self):
        db = AsyncMock()
        admin1 = MagicMock()
        admin2 = MagicMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [admin1, admin2]
        db.execute.return_value = result_mock

        admins = await get_org_admins(db, ORG_ID)
        assert len(admins) == 2


# ============================================================
# WEBHOOK HANDLERS
# ============================================================

class TestWebhookHandlers:
    @pytest.mark.asyncio
    async def test_checkout_completed_activates_org(self):
        from app.routers.webhooks import _handle_checkout_completed

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        db.get.return_value = org

        session = {
            "metadata": {"organization_id": str(ORG_ID), "tier": "PROFESSIONAL"},
            "customer": "cus_123",
            "subscription": "sub_456",
        }
        await _handle_checkout_completed(db, session)

        assert org.subscription_tier == "PROFESSIONAL"
        assert org.stripe_customer_id == "cus_123"
        assert org.stripe_subscription_id == "sub_456"
        assert org.subscription_status == "ACTIVE"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_failed_sets_past_due(self):
        from app.routers.webhooks import _handle_payment_failed

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.id = ORG_ID

        with patch("app.routers.webhooks.get_org_by_subscription", return_value=org):
            with patch("app.routers.webhooks.get_org_admins", return_value=[]):
                await _handle_payment_failed(db, {"subscription": "sub_123"})

        assert org.subscription_status == "PAST_DUE"
        assert org.grace_period_end is not None

    @pytest.mark.asyncio
    async def test_payment_failed_notifies_admins(self):
        from app.routers.webhooks import _handle_payment_failed

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.id = ORG_ID

        admin = MagicMock()
        admin.id = uuid.uuid4()

        with patch("app.routers.webhooks.get_org_by_subscription", return_value=org):
            with patch("app.routers.webhooks.get_org_admins", return_value=[admin]):
                await _handle_payment_failed(db, {"subscription": "sub_123"})

        # Should have added at least one notification
        assert db.add.called

    @pytest.mark.asyncio
    async def test_subscription_deleted_sets_cancelled(self):
        from app.routers.webhooks import _handle_subscription_deleted

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.id = ORG_ID

        with patch("app.routers.webhooks.get_org_by_subscription", return_value=org):
            await _handle_subscription_deleted(db, {"id": "sub_123"})

        assert org.subscription_status == "CANCELLED"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_succeeded_reactivates(self):
        from app.routers.webhooks import _handle_payment_succeeded

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.id = ORG_ID
        org.subscription_status = "PAST_DUE"

        with patch("app.routers.webhooks.get_org_by_subscription", return_value=org):
            await _handle_payment_succeeded(db, {"subscription": "sub_123"})

        assert org.subscription_status == "ACTIVE"
        assert org.grace_period_end is None

    @pytest.mark.asyncio
    async def test_subscription_updated_syncs_status(self):
        from app.routers.webhooks import _handle_subscription_updated

        db = AsyncMock()
        org = MagicMock(spec=Organization)
        org.id = ORG_ID

        with patch("app.routers.webhooks.get_org_by_subscription", return_value=org):
            await _handle_subscription_updated(db, {"id": "sub_123", "status": "past_due"})

        assert org.subscription_status == "PAST_DUE"
