"""Tests for pay application service."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.pay_app import PayApp
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.pay_app import PayAppCreate, PayAppLineItemCreate
from app.services.pay_app_service import (
    approve_pay_app,
    create_pay_app,
    format_pay_app_response,
    get_pay_app,
    get_previous_certified_amount,
    reject_pay_app,
    submit_pay_app,
    _cents,
    _dollars,
)
from app.services.numbering_service import format_number
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


def _make_pay_app(
    status="DRAFT",
    number=1,
    pay_app_type="GC_TO_OWNER",
    sub_company_id=None,
    sov_data=None,
    original_contract_sum=Decimal("500000.00"),
    net_change_orders=Decimal("25000.00"),
    contract_sum_to_date=Decimal("525000.00"),
    total_completed=Decimal("200000.00"),
    total_retainage=Decimal("20000.00"),
    total_earned_less_retainage=Decimal("180000.00"),
    previous_certificates=Decimal("100000.00"),
    net_payment_due=Decimal("80000.00"),
    balance_to_finish=Decimal("325000.00"),
    retention_rate=Decimal("10.00"),
    created_by=ADMIN_USER_ID,
):
    pa = MagicMock(spec=PayApp)
    pa.id = uuid.uuid4()
    pa.organization_id = ORG_ID
    pa.project_id = PROJECT_ID
    pa.created_by = created_by
    pa.number = number
    pa.pay_app_type = pay_app_type
    pa.sub_company_id = sub_company_id
    pa.period_start = datetime(2026, 2, 1)
    pa.period_end = datetime(2026, 2, 28)
    pa.retention_rate = retention_rate
    if sov_data is not None:
        pa.sov_data = sov_data
    else:
        pa.sov_data = [
            {
                "budget_line_item_id": str(uuid.uuid4()),
                "description": "Concrete",
                "scheduled_value": 25000000,
                "previous_applications": 5000000,
                "current_amount": 3000000,
                "materials_stored": 1000000,
                "total_completed": 9000000,
            },
            {
                "budget_line_item_id": str(uuid.uuid4()),
                "description": "Masonry",
                "scheduled_value": 15000000,
                "previous_applications": 2000000,
                "current_amount": 2000000,
                "materials_stored": 500000,
                "total_completed": 4500000,
            },
        ]
    pa.original_contract_sum = original_contract_sum
    pa.net_change_orders = net_change_orders
    pa.contract_sum_to_date = contract_sum_to_date
    pa.total_completed = total_completed
    pa.total_retainage = total_retainage
    pa.total_earned_less_retainage = total_earned_less_retainage
    pa.previous_certificates = previous_certificates
    pa.net_payment_due = net_payment_due
    pa.balance_to_finish = balance_to_finish
    pa.status = status
    pa.submitted_by_type = None
    pa.submitted_by_id = None
    pa.submitted_at = None
    pa.reviewed_by = None
    pa.reviewed_at = None
    pa.review_notes = None
    pa.deleted_at = None
    pa.created_at = datetime(2026, 2, 20, 10, 0)
    pa.updated_at = datetime(2026, 2, 20, 10, 0)
    return pa


# ============================================================
# create_pay_app
# ============================================================

class TestCreatePayApp:
    @pytest.mark.asyncio
    @patch("app.services.pay_app_service._get_approved_co_total", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_previous_certified_amount", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success_with_line_items(self, mock_next_number, mock_prev_certs, mock_co_total):
        mock_next_number.return_value = 1
        mock_prev_certs.return_value = 0
        mock_co_total.return_value = 500000  # $5,000 in approved COs (cents)

        db = AsyncMock()
        user = _make_user()
        data = PayAppCreate(
            pay_app_type="GC_TO_OWNER",
            period_from=date(2026, 2, 1),
            period_to=date(2026, 2, 28),
            retainage_percent=10.0,
            line_items=[
                PayAppLineItemCreate(
                    description="Concrete",
                    scheduled_value=25000000,
                    previous_applications=5000000,
                    current_amount=3000000,
                    materials_stored=1000000,
                ),
                PayAppLineItemCreate(
                    description="Masonry",
                    scheduled_value=15000000,
                    previous_applications=2000000,
                    current_amount=2000000,
                    materials_stored=500000,
                ),
            ],
        )

        result = await create_pay_app(db, PROJECT_ID, ORG_ID, user, data)

        # PayApp + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "pay_app")

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service._get_approved_co_total", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_previous_certified_amount", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_next_number", new_callable=AsyncMock)
    async def test_sov_calculations(self, mock_next_number, mock_prev_certs, mock_co_total):
        mock_next_number.return_value = 1
        mock_prev_certs.return_value = 0
        mock_co_total.return_value = 0

        db = AsyncMock()
        user = _make_user()
        data = PayAppCreate(
            pay_app_type="GC_TO_OWNER",
            period_from=date(2026, 2, 1),
            period_to=date(2026, 2, 28),
            retainage_percent=10.0,
            line_items=[
                PayAppLineItemCreate(
                    description="Concrete",
                    scheduled_value=10000000,  # $100,000
                    previous_applications=2000000,  # $20,000
                    current_amount=3000000,  # $30,000
                    materials_stored=500000,  # $5,000
                ),
            ],
        )

        await create_pay_app(db, PROJECT_ID, ORG_ID, user, data)

        # Verify the PayApp was created with correct calculations
        pa_call = db.add.call_args_list[0]
        pa = pa_call[0][0]

        # total_completed = previous(2M) + current(3M) + materials(500k) = 5500000 cents
        # In dollars: 55000.00
        assert pa.total_completed == _dollars(5500000)

        # retainage = 5500000 * 10 / 100 = 550000 cents -> $5500.00
        assert pa.total_retainage == _dollars(550000)

        # earned_less_retainage = 5500000 - 550000 = 4950000 -> $49500.00
        assert pa.total_earned_less_retainage == _dollars(4950000)

        # With no previous certs and no COs: current_due = 4950000 - 0 = 4950000
        assert pa.net_payment_due == _dollars(4950000)

        # balance = scheduled(10M) + co(0) - completed(5.5M) = 4500000
        assert pa.balance_to_finish == _dollars(4500000)

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service._get_approved_co_total", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_previous_certified_amount", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_next_number", new_callable=AsyncMock)
    async def test_create_with_previous_certificates(self, mock_next_number, mock_prev_certs, mock_co_total):
        mock_next_number.return_value = 2
        mock_prev_certs.return_value = 4000000  # $40,000 previously certified (cents)
        mock_co_total.return_value = 0

        db = AsyncMock()
        user = _make_user()
        data = PayAppCreate(
            pay_app_type="GC_TO_OWNER",
            period_from=date(2026, 3, 1),
            period_to=date(2026, 3, 31),
            retainage_percent=10.0,
            line_items=[
                PayAppLineItemCreate(
                    description="Concrete",
                    scheduled_value=10000000,
                    previous_applications=5000000,
                    current_amount=2000000,
                    materials_stored=0,
                ),
            ],
        )

        await create_pay_app(db, PROJECT_ID, ORG_ID, user, data)

        pa_call = db.add.call_args_list[0]
        pa = pa_call[0][0]

        # total_completed = 5000000 + 2000000 + 0 = 7000000
        # retainage = 7000000 * 10 / 100 = 700000
        # earned_less = 7000000 - 700000 = 6300000
        # current_due = 6300000 - 4000000 = 2300000
        assert pa.net_payment_due == _dollars(2300000)
        assert pa.previous_certificates == _dollars(4000000)

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service._get_approved_co_total", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_previous_certified_amount", new_callable=AsyncMock)
    @patch("app.services.pay_app_service.get_next_number", new_callable=AsyncMock)
    async def test_create_sub_pay_app(self, mock_next_number, mock_prev_certs, mock_co_total):
        mock_next_number.return_value = 1
        mock_prev_certs.return_value = 0
        mock_co_total.return_value = 0

        db = AsyncMock()
        user = _make_user(user_id=SUB_USER_ID, user_type="sub")
        data = PayAppCreate(
            pay_app_type="SUB_TO_GC",
            sub_company_id=SUB_COMPANY_ID,
            period_from=date(2026, 2, 1),
            period_to=date(2026, 2, 28),
            retainage_percent=10.0,
            line_items=[
                PayAppLineItemCreate(
                    description="Plumbing rough-in",
                    scheduled_value=5000000,
                    current_amount=1000000,
                ),
            ],
        )

        await create_pay_app(db, PROJECT_ID, ORG_ID, user, data)

        pa_call = db.add.call_args_list[0]
        pa = pa_call[0][0]
        assert pa.pay_app_type == "SUB_TO_GC"
        assert pa.sub_company_id == SUB_COMPANY_ID


# ============================================================
# get_pay_app
# ============================================================

class TestGetPayApp:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        pa = _make_pay_app()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pa
        db.execute.return_value = mock_result

        result = await get_pay_app(db, pa.id, PROJECT_ID)
        assert result == pa

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_pay_app(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# submit_pay_app
# ============================================================

class TestSubmitPayApp:
    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_submit_from_draft(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="DRAFT")
        mock_get.return_value = pa

        user = _make_user()
        result = await submit_pay_app(db, pa.id, PROJECT_ID, user)

        assert pa.status == "SUBMITTED"
        assert pa.submitted_by_type == "gc"
        assert pa.submitted_by_id == ADMIN_USER_ID
        assert pa.submitted_at is not None
        db.add.assert_called()  # EventLog added
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_submit_non_draft_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="SUBMITTED")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_submit_approved_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="APPROVED")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_submit_logs_event(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="DRAFT")
        mock_get.return_value = pa

        user = _make_user()
        await submit_pay_app(db, pa.id, PROJECT_ID, user)

        event_call = db.add.call_args_list[0]
        event = event_call[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "pay_app_submitted"


# ============================================================
# approve_pay_app
# ============================================================

class TestApprovePayApp:
    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_approve_from_submitted(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="SUBMITTED")
        mock_get.return_value = pa

        user = _make_user()
        result = await approve_pay_app(db, pa.id, PROJECT_ID, user, notes="Approved for payment")

        assert pa.status == "APPROVED"
        assert pa.reviewed_by == ADMIN_USER_ID
        assert pa.reviewed_at is not None
        assert pa.review_notes == "Approved for payment"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_approve_from_in_review(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="IN_REVIEW")
        mock_get.return_value = pa

        user = _make_user()
        result = await approve_pay_app(db, pa.id, PROJECT_ID, user)

        assert pa.status == "APPROVED"

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_approve_non_submitted_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="DRAFT")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await approve_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_approve_already_approved_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="APPROVED")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await approve_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_approve_logs_event(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="SUBMITTED")
        mock_get.return_value = pa

        user = _make_user()
        await approve_pay_app(db, pa.id, PROJECT_ID, user)

        event_call = db.add.call_args_list[0]
        event = event_call[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "pay_app_approved"


# ============================================================
# reject_pay_app
# ============================================================

class TestRejectPayApp:
    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_reject_from_submitted_sets_notes(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="SUBMITTED")
        mock_get.return_value = pa

        user = _make_user()
        result = await reject_pay_app(db, pa.id, PROJECT_ID, user, reason="Incorrect line items")

        assert pa.status == "REJECTED"
        assert pa.reviewed_by == ADMIN_USER_ID
        assert pa.reviewed_at is not None
        assert pa.review_notes == "Incorrect line items"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_reject_from_in_review(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="IN_REVIEW")
        mock_get.return_value = pa

        user = _make_user()
        result = await reject_pay_app(db, pa.id, PROJECT_ID, user, reason="Needs revision")

        assert pa.status == "REJECTED"
        assert pa.review_notes == "Needs revision"

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_reject_non_submitted_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="DRAFT")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reject_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_reject_already_approved_raises_400(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="APPROVED")
        mock_get.return_value = pa

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reject_pay_app(db, pa.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("app.services.pay_app_service.get_pay_app", new_callable=AsyncMock)
    async def test_reject_logs_event(self, mock_get):
        db = AsyncMock()
        pa = _make_pay_app(status="SUBMITTED")
        mock_get.return_value = pa

        user = _make_user()
        await reject_pay_app(db, pa.id, PROJECT_ID, user, reason="Wrong amounts")

        event_call = db.add.call_args_list[0]
        event = event_call[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "pay_app_rejected"
        assert event.event_data["reason"] == "Wrong amounts"


# ============================================================
# get_previous_certified_amount
# ============================================================

class TestGetPreviousCertifiedAmount:
    @pytest.mark.asyncio
    async def test_sums_approved_pay_apps(self):
        db = AsyncMock()
        # Simulate sum of net_payment_due = $80,000
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("80000.00")
        db.execute.return_value = mock_result

        result = await get_previous_certified_amount(db, PROJECT_ID, "GC_TO_OWNER")

        assert result == 8000000  # $80,000 in cents

    @pytest.mark.asyncio
    async def test_no_approved_pay_apps_returns_zero(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("0")
        db.execute.return_value = mock_result

        result = await get_previous_certified_amount(db, PROJECT_ID, "GC_TO_OWNER")

        assert result == 0

    @pytest.mark.asyncio
    async def test_with_sub_company_filter(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = Decimal("15000.00")
        db.execute.return_value = mock_result

        result = await get_previous_certified_amount(
            db, PROJECT_ID, "SUB_TO_GC", sub_company_id=SUB_COMPANY_ID
        )

        assert result == 1500000  # $15,000 in cents


# ============================================================
# format_pay_app_response
# ============================================================

class TestFormatPayAppResponse:
    def test_cents_conversion(self):
        pa = _make_pay_app(
            original_contract_sum=Decimal("500000.00"),
            net_change_orders=Decimal("25000.00"),
            contract_sum_to_date=Decimal("525000.00"),
            total_completed=Decimal("200000.00"),
            total_retainage=Decimal("20000.00"),
            total_earned_less_retainage=Decimal("180000.00"),
            previous_certificates=Decimal("100000.00"),
            net_payment_due=Decimal("80000.00"),
            balance_to_finish=Decimal("325000.00"),
        )
        result = format_pay_app_response(pa)

        assert result["original_contract_sum"] == 50000000
        assert result["net_change_orders"] == 2500000
        assert result["contract_sum_to_date"] == 52500000
        assert result["total_completed_and_stored"] == 20000000
        assert result["retainage_amount"] == 2000000
        assert result["total_earned_less_retainage"] == 18000000
        assert result["previous_certificates"] == 10000000
        assert result["current_payment_due"] == 8000000
        assert result["balance_to_finish"] == 32500000

    def test_formatted_number(self):
        pa = _make_pay_app(number=3)
        result = format_pay_app_response(pa)

        assert result["formatted_number"] == "#3"
        assert result["number"] == 3

    def test_line_item_calculations(self):
        pa = _make_pay_app(
            retention_rate=Decimal("10.00"),
            sov_data=[
                {
                    "budget_line_item_id": str(uuid.uuid4()),
                    "description": "Concrete",
                    "scheduled_value": 10000000,  # $100,000
                    "previous_applications": 2000000,  # $20,000
                    "current_amount": 3000000,  # $30,000
                    "materials_stored": 500000,  # $5,000
                },
            ],
        )
        result = format_pay_app_response(pa)

        assert len(result["line_items"]) == 1
        li = result["line_items"][0]

        # total = 2000000 + 3000000 + 500000 = 5500000
        assert li["total_completed"] == 5500000
        # pct = 5500000 / 10000000 * 100 = 55.0
        assert li["percent_complete"] == 55.0
        # balance = 10000000 - 5500000 = 4500000
        assert li["balance_to_finish"] == 4500000
        # retainage = 5500000 * 10 / 100 = 550000
        assert li["retainage"] == 550000

    def test_line_item_zero_scheduled_value(self):
        pa = _make_pay_app(
            sov_data=[
                {
                    "description": "Placeholder",
                    "scheduled_value": 0,
                    "previous_applications": 0,
                    "current_amount": 0,
                    "materials_stored": 0,
                },
            ],
        )
        result = format_pay_app_response(pa)

        li = result["line_items"][0]
        assert li["percent_complete"] == 0.0
        assert li["total_completed"] == 0
        assert li["balance_to_finish"] == 0

    def test_includes_all_fields(self):
        pa = _make_pay_app()
        result = format_pay_app_response(pa)

        assert result["id"] == pa.id
        assert result["project_id"] == PROJECT_ID
        assert result["pay_app_type"] == "GC_TO_OWNER"
        assert result["status"] == "DRAFT"
        assert result["retainage_percent"] == 10.0
        assert result["sub_company_id"] is None
        assert result["sub_company_name"] is None
        assert result["submitted_by_name"] is None
        assert result["submitted_at"] is None
        assert result["reviewed_by_name"] is None
        assert result["reviewed_at"] is None
        assert result["review_notes"] is None
        assert result["comments_count"] == 0
        assert result["created_at"] == pa.created_at
        assert result["updated_at"] == pa.updated_at

    def test_period_date_conversion(self):
        pa = _make_pay_app()
        # period_start and period_end are datetimes that should be converted to dates
        pa.period_start = datetime(2026, 2, 1, 0, 0)
        pa.period_end = datetime(2026, 2, 28, 0, 0)

        result = format_pay_app_response(pa)

        assert result["period_from"] == date(2026, 2, 1)
        assert result["period_to"] == date(2026, 2, 28)

    def test_empty_sov_data(self):
        pa = _make_pay_app(sov_data=[])
        result = format_pay_app_response(pa)

        assert result["line_items"] == []

    def test_none_sov_data(self):
        pa = _make_pay_app(sov_data=None)
        pa.sov_data = None
        result = format_pay_app_response(pa)

        assert result["line_items"] == []

    def test_sub_pay_app_fields(self):
        pa = _make_pay_app(
            pay_app_type="SUB_TO_GC",
            sub_company_id=SUB_COMPANY_ID,
        )
        result = format_pay_app_response(pa)

        assert result["pay_app_type"] == "SUB_TO_GC"
        assert result["sub_company_id"] == SUB_COMPANY_ID

    def test_none_amounts_handled(self):
        pa = _make_pay_app(
            original_contract_sum=None,
            net_change_orders=None,
            contract_sum_to_date=None,
            total_completed=None,
            total_retainage=None,
            total_earned_less_retainage=None,
            previous_certificates=None,
            net_payment_due=None,
            balance_to_finish=None,
        )
        result = format_pay_app_response(pa)

        assert result["original_contract_sum"] == 0
        assert result["net_change_orders"] == 0
        assert result["contract_sum_to_date"] == 0
        assert result["total_completed_and_stored"] == 0
        assert result["retainage_amount"] == 0
        assert result["total_earned_less_retainage"] == 0
        assert result["previous_certificates"] == 0
        assert result["current_payment_due"] == 0
        assert result["balance_to_finish"] == 0
