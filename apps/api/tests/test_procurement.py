"""Tests for Procurement service."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.procurement_item import ProcurementItem
from app.schemas.procurement import ProcurementCreate, ProcurementUpdate, ProcurementTransition
from app.services.procurement_service import (
    create_procurement,
    delete_procurement,
    format_procurement_response,
    get_procurement,
    transition_procurement,
    update_procurement,
)
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID, SUB_COMPANY_ID


# ============================================================
# HELPERS
# ============================================================

def _make_user(user_id=ADMIN_USER_ID, permission_level="OWNER_ADMIN"):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_procurement_item(
    status="IDENTIFIED",
    item_name="Structural Steel W14x30",
    vendor="Nucor Steel",
):
    item = MagicMock(spec=ProcurementItem)
    item.id = uuid.uuid4()
    item.organization_id = ORG_ID
    item.project_id = PROJECT_ID
    item.created_by = ADMIN_USER_ID
    item.item_name = item_name
    item.name = item_name
    item.description = "Wide flange beams for Level 3 framing"
    item.status = status
    item.category = "STRUCTURAL_STEEL"
    item.spec_section = "05 12 00"
    item.quantity = 24
    item.unit = "EA"
    item.vendor = vendor
    item.vendor_contact = "Mike Nelson"
    item.vendor_phone = "303-555-1234"
    item.vendor_email = "mike@nucor.example.com"
    item.estimated_cost = Decimal("48000.00")
    item.actual_cost = None
    item.po_number = None
    item.lead_time_days = 45
    item.required_on_site_date = datetime(2026, 6, 1, tzinfo=timezone.utc)
    item.order_by_date = datetime(2026, 4, 17, tzinfo=timezone.utc)
    item.expected_delivery_date = None
    item.actual_delivery_date = None
    item.tracking_number = None
    item.assigned_to = MGMT_USER_ID
    item.sub_company_id = SUB_COMPANY_ID
    item.linked_schedule_task_id = None
    item.notes = "Confirm mill cert required"
    item.dates = {}
    item.created_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
    item.updated_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
    item.deleted_at = None
    return item


# ============================================================
# create_procurement
# ============================================================

class TestCreateProcurement:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        data = ProcurementCreate(
            item_name="Structural Steel W14x30",
            description="Wide flange beams for Level 3",
            category="STRUCTURAL_STEEL",
            vendor="Nucor Steel",
            quantity=24,
            unit="EA",
            estimated_cost_cents=4800000,
            lead_time_days=45,
            required_on_site_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )

        result = await create_procurement(db, PROJECT_ID, ORG_ID, user, data)

        # ProcurementItem + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal(self):
        db = AsyncMock()
        user = _make_user()
        data = ProcurementCreate(item_name="Misc hardware")

        result = await create_procurement(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_assigned_to(self):
        db = AsyncMock()
        user = _make_user()
        data = ProcurementCreate(
            item_name="Elevator Cab",
            assigned_to=MGMT_USER_ID,
            sub_company_id=SUB_COMPANY_ID,
        )

        result = await create_procurement(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_procurement
# ============================================================

class TestGetProcurement:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        item = _make_procurement_item()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        result = await get_procurement(db, item.id, PROJECT_ID)
        assert result == item

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_procurement(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_procurement
# ============================================================

class TestUpdateProcurement:
    @pytest.mark.asyncio
    async def test_update_vendor(self):
        db = AsyncMock()
        item = _make_procurement_item()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementUpdate(vendor="US Steel Corp")

        result = await update_procurement(db, item.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_cost_cents_converted(self):
        db = AsyncMock()
        item = _make_procurement_item()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementUpdate(estimated_cost_cents=5200000)

        result = await update_procurement(db, item.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementUpdate(vendor="New Vendor")

        with pytest.raises(HTTPException) as exc_info:
            await update_procurement(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# delete_procurement
# ============================================================

class TestDeleteProcurement:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        db = AsyncMock()
        item = _make_procurement_item()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_procurement(db, item.id, PROJECT_ID, user)

        assert item.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_procurement(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# transition_procurement
# ============================================================

class TestTransitionProcurement:
    @pytest.mark.asyncio
    async def test_quote_identified_to_quoted(self):
        db = AsyncMock()
        item = _make_procurement_item(status="IDENTIFIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "quote")

        assert item.status == "QUOTED"
        db.add.assert_called_once()  # EventLog
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_order_quoted_to_ordered(self):
        db = AsyncMock()
        item = _make_procurement_item(status="QUOTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementTransition(po_number="PO-2026-001")
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "order", data)

        assert item.status == "ORDERED"
        assert item.po_number == "PO-2026-001"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ship_ordered_to_in_transit(self):
        db = AsyncMock()
        item = _make_procurement_item(status="ORDERED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementTransition(tracking_number="1Z999AA10123456784")
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "ship", data)

        assert item.status == "IN_TRANSIT"
        assert item.tracking_number == "1Z999AA10123456784"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deliver_in_transit_to_delivered(self):
        db = AsyncMock()
        item = _make_procurement_item(status="IN_TRANSIT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        delivery_date = datetime(2026, 5, 28, tzinfo=timezone.utc)
        data = ProcurementTransition(actual_delivery_date=delivery_date)
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "deliver", data)

        assert item.status == "DELIVERED"
        assert item.actual_delivery_date == delivery_date
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_install_delivered_to_installed(self):
        db = AsyncMock()
        item = _make_procurement_item(status="DELIVERED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "install")

        assert item.status == "INSTALLED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_transition_wrong_status_raises_400(self):
        db = AsyncMock()
        item = _make_procurement_item(status="IDENTIFIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await transition_procurement(db, item.id, PROJECT_ID, user, "order")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_unknown_action_raises_400(self):
        db = AsyncMock()
        user = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await transition_procurement(db, uuid.uuid4(), PROJECT_ID, user, "invalid_action")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_deliver_without_date_defaults_to_now(self):
        db = AsyncMock()
        item = _make_procurement_item(status="IN_TRANSIT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = ProcurementTransition()  # No explicit date
        result = await transition_procurement(db, item.id, PROJECT_ID, user, "deliver", data)

        assert item.status == "DELIVERED"
        assert item.actual_delivery_date is not None
        db.flush.assert_awaited_once()


# ============================================================
# format_procurement_response
# ============================================================

class TestFormatProcurementResponse:
    def test_basic_format(self):
        item = _make_procurement_item()
        result = format_procurement_response(item)

        assert result["id"] == item.id
        assert result["project_id"] == PROJECT_ID
        assert result["item_name"] == "Structural Steel W14x30"
        assert result["status"] == "IDENTIFIED"
        assert result["category"] == "STRUCTURAL_STEEL"
        assert result["vendor"] == "Nucor Steel"
        assert result["quantity"] == 24
        assert result["unit"] == "EA"
        assert result["estimated_cost_cents"] == 4800000
        assert result["actual_cost_cents"] == 0
        assert result["lead_time_days"] == 45
        assert result["po_number"] is None
        assert result["tracking_number"] is None
        assert result["created_by"] == ADMIN_USER_ID
        assert result["created_at"] is not None

    def test_at_risk_false_for_delivered(self):
        item = _make_procurement_item(status="DELIVERED")
        result = format_procurement_response(item)

        assert result["is_at_risk"] is False

    def test_at_risk_false_for_installed(self):
        item = _make_procurement_item(status="INSTALLED")
        result = format_procurement_response(item)

        assert result["is_at_risk"] is False

    def test_cost_conversion_cents(self):
        item = _make_procurement_item()
        item.estimated_cost = Decimal("1234.56")
        item.actual_cost = Decimal("1300.00")
        result = format_procurement_response(item)

        assert result["estimated_cost_cents"] == 123456
        assert result["actual_cost_cents"] == 130000

    def test_null_costs_default_zero(self):
        item = _make_procurement_item()
        item.estimated_cost = None
        item.actual_cost = None
        result = format_procurement_response(item)

        assert result["estimated_cost_cents"] == 0
        assert result["actual_cost_cents"] == 0
