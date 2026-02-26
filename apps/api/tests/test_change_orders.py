"""Tests for change order service."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.change_order import ChangeOrder
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderUpdate,
    SubPricingSubmit,
)
from app.services.change_order_service import (
    create_change_order,
    delete_change_order,
    format_change_order_response,
    get_change_order,
    owner_decision,
    submit_sub_pricing,
    submit_to_owner,
    update_change_order,
    _cents,
    _dollars,
)
from app.services.numbering_service import format_change_order_number
from tests.conftest import (
    ORG_ID,
    PROJECT_ID,
    ADMIN_USER_ID,
    MGMT_USER_ID,
    FIELD_USER_ID,
    SUB_COMPANY_ID,
    SUB_USER_ID,
    OWNER_USER_ID,
)


# ============================================================
# HELPERS
# ============================================================

def _make_user(user_id=ADMIN_USER_ID, permission_level="OWNER_ADMIN", user_type="gc"):
    return {
        "user_type": user_type,
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_change_order(
    status="DRAFT",
    number=1,
    order_type="PCO",
    title="Window spec change",
    total_amount=Decimal("25000.00"),
    gc_amount=Decimal("27500.00"),
    markup_percent=Decimal("10.00"),
    markup_amount=Decimal("2500.00"),
    sub_pricings=None,
    created_by=ADMIN_USER_ID,
    owner_decision_val=None,
    owner_decision_by=None,
    owner_decision_at=None,
    owner_decision_notes=None,
    submitted_to_owner_at=None,
):
    co = MagicMock(spec=ChangeOrder)
    co.id = uuid.uuid4()
    co.organization_id = ORG_ID
    co.project_id = PROJECT_ID
    co.created_by = created_by
    co.number = number
    co.title = title
    co.description = "Replace single-pane windows with double-pane."
    co.reason = "VALUE_ENGINEERING"
    co.cost_code_id = None
    co.priority = "NORMAL"
    co.drawing_reference = "A3.01"
    co.spec_section = "08 51 00"
    co.total_amount = total_amount
    co.markup_percent = markup_percent
    co.markup_amount = markup_amount
    co.gc_amount = gc_amount
    co.schedule_impact_days = 5
    co.cost_breakdown = []
    co.sub_pricings = sub_pricings or []
    co.related_rfi_ids = []
    co.submitted_to_owner_at = submitted_to_owner_at
    co.owner_decision = owner_decision_val
    co.owner_decision_by = owner_decision_by
    co.owner_decision_at = owner_decision_at
    co.owner_decision_notes = owner_decision_notes
    co.order_type = order_type
    co.status = status
    co.deleted_at = None
    co.created_at = datetime(2026, 2, 20, 10, 0)
    co.updated_at = datetime(2026, 2, 20, 10, 0)
    return co


# ============================================================
# create_change_order
# ============================================================

class TestCreateChangeOrder:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = ChangeOrderCreate(
            title="Window spec change",
            reason="VALUE_ENGINEERING",
            amount=2500000,  # $25,000 in cents
            schedule_impact_days=5,
        )

        result = await create_change_order(db, PROJECT_ID, ORG_ID, user, data)

        # Should add: ChangeOrder (via first flush), then EventLog = at least 2 adds
        assert db.add.call_count >= 2
        assert db.flush.await_count == 2
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "change_order")

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_next_number", new_callable=AsyncMock)
    async def test_create_with_sub_company_ids_creates_pricing_requests(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        sub_id_1 = uuid.uuid4()
        sub_id_2 = uuid.uuid4()
        data = ChangeOrderCreate(
            title="Foundation revision",
            reason="UNFORESEEN_CONDITIONS",
            amount=5000000,
            sub_company_ids=[sub_id_1, sub_id_2],
        )

        result = await create_change_order(db, PROJECT_ID, ORG_ID, user, data)

        # ChangeOrder + 2 Notifications + EventLog = 4 adds
        assert db.add.call_count >= 4
        # Verify notifications were created for each sub
        notification_calls = [
            call for call in db.add.call_args_list
            if isinstance(call[0][0], Notification)
        ]
        assert len(notification_calls) == 2
        # Verify the CO status was set to PRICING_REQUESTED
        co_call = db.add.call_args_list[0]
        co_obj = co_call[0][0]
        assert co_obj.status == "PRICING_REQUESTED"

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_next_number", new_callable=AsyncMock)
    async def test_create_without_subs_stays_draft(self, mock_next_number):
        mock_next_number.return_value = 3

        db = AsyncMock()
        user = _make_user()
        data = ChangeOrderCreate(
            title="Minor grading adjustment",
            reason="SCOPE_CHANGE",
            amount=100000,
        )

        result = await create_change_order(db, PROJECT_ID, ORG_ID, user, data)

        co_call = db.add.call_args_list[0]
        co_obj = co_call[0][0]
        assert co_obj.status == "DRAFT"


# ============================================================
# get_change_order
# ============================================================

class TestGetChangeOrder:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        co = _make_change_order()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = co
        db.execute.return_value = mock_result

        result = await get_change_order(db, co.id, PROJECT_ID)
        assert result == co

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_change_order(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_change_order
# ============================================================

class TestUpdateChangeOrder:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_update_title(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="DRAFT")
        mock_get.return_value = co

        user = _make_user()
        data = ChangeOrderUpdate(title="Updated window spec change")

        result = await update_change_order(db, co.id, PROJECT_ID, user, data)

        assert co.title == "Updated window spec change"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_update_amount_converts_cents_to_dollars(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="DRAFT")
        mock_get.return_value = co

        user = _make_user()
        data = ChangeOrderUpdate(amount=3000000)  # $30,000 in cents

        result = await update_change_order(db, co.id, PROJECT_ID, user, data)

        assert co.total_amount == Decimal("30000.00")
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_update_markup_recalculates_gc_amount(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(
            status="DRAFT",
            total_amount=Decimal("25000.00"),
        )
        mock_get.return_value = co

        user = _make_user()
        data = ChangeOrderUpdate(markup_percent=15.0)

        result = await update_change_order(db, co.id, PROJECT_ID, user, data)

        # 25000 * 15 / 100 = 3750 markup
        assert co.markup_percent == Decimal("15.0")
        assert co.markup_amount == Decimal("25000.00") * Decimal("15.0") / 100
        # gc_amount = total + markup = 25000 + 3750 = 28750
        expected_gc = Decimal("25000.00") + Decimal("25000.00") * Decimal("15.0") / 100
        assert co.gc_amount == expected_gc
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_update_finalized_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="APPROVED")
        mock_get.return_value = co

        user = _make_user()
        data = ChangeOrderUpdate(title="Should fail")

        with pytest.raises(HTTPException) as exc_info:
            await update_change_order(db, co.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_update_rejected_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="REJECTED")
        mock_get.return_value = co

        user = _make_user()
        data = ChangeOrderUpdate(title="Should also fail")

        with pytest.raises(HTTPException) as exc_info:
            await update_change_order(db, co.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# submit_sub_pricing
# ============================================================

class TestSubmitSubPricing:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_submit_success(self, mock_get):
        db = AsyncMock()
        sub_id = SUB_COMPANY_ID
        co = _make_change_order(
            status="PRICING_REQUESTED",
            sub_pricings=[
                {
                    "sub_company_id": str(sub_id),
                    "amount": None,
                    "description": None,
                    "schedule_impact_days": 0,
                    "status": "REQUESTED",
                    "submitted_at": None,
                },
            ],
        )
        mock_get.return_value = co

        data = SubPricingSubmit(
            amount=1500000,
            description="Window materials and labor",
            schedule_impact_days=3,
        )

        result = await submit_sub_pricing(db, co.id, PROJECT_ID, sub_id, data)

        pricing = co.sub_pricings[0]
        assert pricing["amount"] == 1500000
        assert pricing["description"] == "Window materials and labor"
        assert pricing["schedule_impact_days"] == 3
        assert pricing["status"] == "SUBMITTED"
        assert pricing["submitted_at"] is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_submit_already_submitted_raises_400(self, mock_get):
        db = AsyncMock()
        sub_id = SUB_COMPANY_ID
        co = _make_change_order(
            status="PRICING_REQUESTED",
            sub_pricings=[
                {
                    "sub_company_id": str(sub_id),
                    "amount": 1500000,
                    "description": "Already submitted",
                    "schedule_impact_days": 3,
                    "status": "SUBMITTED",
                    "submitted_at": "2026-02-20T10:00:00",
                },
            ],
        )
        mock_get.return_value = co

        data = SubPricingSubmit(
            amount=2000000,
            description="Updated pricing",
        )

        with pytest.raises(HTTPException) as exc_info:
            await submit_sub_pricing(db, co.id, PROJECT_ID, sub_id, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_submit_unknown_sub_raises_404(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(
            status="PRICING_REQUESTED",
            sub_pricings=[
                {
                    "sub_company_id": str(SUB_COMPANY_ID),
                    "amount": None,
                    "status": "REQUESTED",
                    "submitted_at": None,
                },
            ],
        )
        mock_get.return_value = co

        unknown_sub_id = uuid.uuid4()
        data = SubPricingSubmit(
            amount=1000000,
            description="From unknown sub",
        )

        with pytest.raises(HTTPException) as exc_info:
            await submit_sub_pricing(db, co.id, PROJECT_ID, unknown_sub_id, data)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_all_submitted_transitions_to_pricing_complete(self, mock_get):
        db = AsyncMock()
        sub_id_1 = SUB_COMPANY_ID
        sub_id_2 = uuid.uuid4()
        co = _make_change_order(
            status="PRICING_REQUESTED",
            sub_pricings=[
                {
                    "sub_company_id": str(sub_id_1),
                    "amount": None,
                    "description": None,
                    "schedule_impact_days": 0,
                    "status": "REQUESTED",
                    "submitted_at": None,
                },
                {
                    "sub_company_id": str(sub_id_2),
                    "amount": 2000000,
                    "description": "Already submitted",
                    "schedule_impact_days": 2,
                    "status": "SUBMITTED",
                    "submitted_at": "2026-02-19T10:00:00",
                },
            ],
        )
        mock_get.return_value = co

        data = SubPricingSubmit(
            amount=1500000,
            description="Last sub pricing",
            schedule_impact_days=1,
        )

        result = await submit_sub_pricing(db, co.id, PROJECT_ID, sub_id_1, data)

        assert co.status == "PRICING_COMPLETE"

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_partial_submissions_stay_pricing_requested(self, mock_get):
        db = AsyncMock()
        sub_id_1 = SUB_COMPANY_ID
        sub_id_2 = uuid.uuid4()
        co = _make_change_order(
            status="PRICING_REQUESTED",
            sub_pricings=[
                {
                    "sub_company_id": str(sub_id_1),
                    "amount": None,
                    "status": "REQUESTED",
                    "submitted_at": None,
                },
                {
                    "sub_company_id": str(sub_id_2),
                    "amount": None,
                    "status": "REQUESTED",
                    "submitted_at": None,
                },
            ],
        )
        mock_get.return_value = co

        data = SubPricingSubmit(
            amount=1500000,
            description="First sub pricing",
        )

        result = await submit_sub_pricing(db, co.id, PROJECT_ID, sub_id_1, data)

        # Still one REQUESTED, so should not transition
        assert co.status == "PRICING_REQUESTED"


# ============================================================
# submit_to_owner
# ============================================================

class TestSubmitToOwner:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_from_draft(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="DRAFT")
        mock_get.return_value = co

        user = _make_user()
        result = await submit_to_owner(db, co.id, PROJECT_ID, user)

        assert co.status == "SUBMITTED_TO_OWNER"
        assert co.submitted_to_owner_at is not None
        db.add.assert_called()  # EventLog added
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_from_pricing_complete(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="PRICING_COMPLETE")
        mock_get.return_value = co

        user = _make_user()
        result = await submit_to_owner(db, co.id, PROJECT_ID, user)

        assert co.status == "SUBMITTED_TO_OWNER"
        assert co.submitted_to_owner_at is not None

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_invalid_status_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="APPROVED")
        mock_get.return_value = co

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_to_owner(db, co.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_rejected_cannot_submit_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="REJECTED")
        mock_get.return_value = co

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_to_owner(db, co.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# owner_decision
# ============================================================

class TestOwnerDecision:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_approve_sets_status_approved_and_order_type_co(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="SUBMITTED_TO_OWNER")
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        result = await owner_decision(db, co.id, PROJECT_ID, user, "APPROVED", notes="Looks good")

        assert co.status == "APPROVED"
        assert co.order_type == "CO"
        assert co.owner_decision == "APPROVED"
        assert co.owner_decision_by == OWNER_USER_ID
        assert co.owner_decision_at is not None
        assert co.owner_decision_notes == "Looks good"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_reject_sets_status_rejected(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="SUBMITTED_TO_OWNER")
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        result = await owner_decision(db, co.id, PROJECT_ID, user, "REJECTED", notes="Too expensive")

        assert co.status == "REJECTED"
        assert co.owner_decision == "REJECTED"
        assert co.owner_decision_notes == "Too expensive"
        # order_type should NOT change to CO on rejection
        assert co.order_type == "PCO"

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_invalid_decision_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="SUBMITTED_TO_OWNER")
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        with pytest.raises(HTTPException) as exc_info:
            await owner_decision(db, co.id, PROJECT_ID, user, "MAYBE")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_not_submitted_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="DRAFT")
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        with pytest.raises(HTTPException) as exc_info:
            await owner_decision(db, co.id, PROJECT_ID, user, "APPROVED")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_approve_creates_notification_for_gc(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="SUBMITTED_TO_OWNER", created_by=ADMIN_USER_ID)
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        await owner_decision(db, co.id, PROJECT_ID, user, "APPROVED")

        # Should add: EventLog + Notification = 2
        assert db.add.call_count >= 2
        notification_calls = [
            call for call in db.add.call_args_list
            if isinstance(call[0][0], Notification)
        ]
        assert len(notification_calls) == 1
        notification = notification_calls[0][0][0]
        assert notification.user_type == "GC_USER"
        assert notification.user_id == ADMIN_USER_ID

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_approve_without_notes(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="SUBMITTED_TO_OWNER")
        mock_get.return_value = co

        user = _make_user(user_id=OWNER_USER_ID, user_type="owner")
        result = await owner_decision(db, co.id, PROJECT_ID, user, "APPROVED")

        assert co.owner_decision_notes is None
        assert co.status == "APPROVED"


# ============================================================
# delete_change_order
# ============================================================

class TestDeleteChangeOrder:
    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_soft_delete(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="DRAFT")
        co.deleted_at = None
        mock_get.return_value = co

        await delete_change_order(db, co.id, PROJECT_ID)

        assert co.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_delete_approved_raises_400(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="APPROVED")
        mock_get.return_value = co

        with pytest.raises(HTTPException) as exc_info:
            await delete_change_order(db, co.id, PROJECT_ID)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.change_order_service.get_change_order", new_callable=AsyncMock)
    async def test_delete_rejected_succeeds(self, mock_get):
        db = AsyncMock()
        co = _make_change_order(status="REJECTED")
        co.deleted_at = None
        mock_get.return_value = co

        await delete_change_order(db, co.id, PROJECT_ID)

        assert co.deleted_at is not None


# ============================================================
# format_change_order_response
# ============================================================

class TestFormatChangeOrderResponse:
    def test_pco_format(self):
        co = _make_change_order(number=3, status="DRAFT", order_type="PCO")
        result = format_change_order_response(co)

        assert result["formatted_number"] == "PCO-003"
        assert result["number"] == 3
        assert result["order_type"] == "PCO"

    def test_co_format(self):
        co = _make_change_order(number=3, status="APPROVED", order_type="CO")
        result = format_change_order_response(co)

        assert result["formatted_number"] == "CO-003"
        assert result["order_type"] == "CO"

    def test_cents_conversion(self):
        co = _make_change_order(
            total_amount=Decimal("25000.00"),
            gc_amount=Decimal("27500.00"),
            markup_amount=Decimal("2500.00"),
        )
        result = format_change_order_response(co)

        assert result["amount"] == 2500000  # $25,000 in cents
        assert result["gc_amount"] == 2750000  # $27,500 in cents
        assert result["markup_amount"] == 250000  # $2,500 in cents

    def test_includes_all_fields(self):
        co = _make_change_order()
        result = format_change_order_response(co)

        assert result["id"] == co.id
        assert result["project_id"] == PROJECT_ID
        assert result["title"] == "Window spec change"
        assert result["description"] == "Replace single-pane windows with double-pane."
        assert result["reason"] == "VALUE_ENGINEERING"
        assert result["status"] == "DRAFT"
        assert result["priority"] == "NORMAL"
        assert result["drawing_reference"] == "A3.01"
        assert result["spec_section"] == "08 51 00"
        assert result["schedule_impact_days"] == 5
        assert result["created_by"] == ADMIN_USER_ID
        assert result["created_at"] == co.created_at
        assert result["updated_at"] == co.updated_at
        assert result["comments_count"] == 0

    def test_sub_pricings_formatting(self):
        sub_id = str(SUB_COMPANY_ID)
        co = _make_change_order(
            sub_pricings=[
                {
                    "sub_company_id": sub_id,
                    "sub_company_name": "ABC Plumbing",
                    "amount": 1500000,
                    "description": "Pipe rerouting",
                    "schedule_impact_days": 3,
                    "status": "SUBMITTED",
                    "submitted_at": "2026-02-21T10:00:00",
                },
            ],
        )
        result = format_change_order_response(co)

        assert len(result["sub_pricings"]) == 1
        sp = result["sub_pricings"][0]
        assert sp["sub_company_id"] == sub_id
        assert sp["sub_company_name"] == "ABC Plumbing"
        assert sp["amount"] == 1500000
        assert sp["status"] == "SUBMITTED"

    def test_none_amounts_handled(self):
        co = _make_change_order(
            total_amount=None,
            gc_amount=None,
            markup_amount=None,
            markup_percent=None,
        )
        co.schedule_impact_days = None
        result = format_change_order_response(co)

        assert result["amount"] == 0
        assert result["gc_amount"] == 0
        assert result["markup_amount"] == 0
        assert result["markup_percent"] is None
        assert result["schedule_impact_days"] == 0

    def test_owner_decision_fields(self):
        owner_id = OWNER_USER_ID
        decision_time = datetime(2026, 2, 22, 14, 0)
        co = _make_change_order(
            status="APPROVED",
            order_type="CO",
            owner_decision_val="APPROVED",
            owner_decision_by=owner_id,
            owner_decision_at=decision_time,
            owner_decision_notes="Approved with conditions",
            submitted_to_owner_at=datetime(2026, 2, 21, 10, 0),
        )
        result = format_change_order_response(co)

        assert result["owner_decision"] == "APPROVED"
        assert result["owner_decision_by"] == owner_id
        assert result["owner_decision_at"] == decision_time
        assert result["owner_decision_notes"] == "Approved with conditions"
        assert result["submitted_to_owner_at"] == datetime(2026, 2, 21, 10, 0)
