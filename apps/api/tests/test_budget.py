"""Tests for budget service."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.budget_line_item import BudgetLineItem
from app.models.event_log import EventLog
from app.schemas.budget import BudgetLineItemCreate, BudgetLineItemUpdate
from app.services.budget_service import (
    bulk_import_line_items,
    create_budget_line_item,
    delete_budget_line_item,
    format_budget_line_item_response,
    get_budget_line_item,
    get_budget_summary,
    update_budget_line_item,
    _cents,
    _dollars,
)
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID, FIELD_USER_ID


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


def _make_budget_item(
    cost_code="03-100",
    description="Concrete Foundations",
    original_amount=Decimal("150000.00"),
    approved_changes=Decimal("5000.00"),
    committed=Decimal("120000.00"),
    actuals=Decimal("80000.00"),
    projected=Decimal("155000.00"),
    notes="Phase 1 footings",
):
    item = MagicMock(spec=BudgetLineItem)
    item.id = uuid.uuid4()
    item.project_id = PROJECT_ID
    item.cost_code = cost_code
    item.description = description
    item.original_amount = original_amount
    item.approved_changes = approved_changes
    item.committed = committed
    item.actuals = actuals
    item.projected = projected
    item.notes = notes
    item.deleted_at = None
    item.created_at = datetime(2026, 2, 20, 10, 0)
    item.updated_at = datetime(2026, 2, 20, 10, 0)
    return item


# ============================================================
# create_budget_line_item
# ============================================================

class TestCreateBudgetLineItem:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        data = BudgetLineItemCreate(
            cost_code="03-100",
            description="Concrete Foundations",
            original_amount=15000000,  # $150,000.00 in cents
            notes="Phase 1",
        )

        result = await create_budget_line_item(db, PROJECT_ID, ORG_ID, user, data)

        # Should add: BudgetLineItem + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_converts_cents_to_dollars(self):
        db = AsyncMock()
        user = _make_user()
        data = BudgetLineItemCreate(
            cost_code="03-200",
            description="Rebar",
            original_amount=5000000,  # $50,000.00 in cents
        )

        result = await create_budget_line_item(db, PROJECT_ID, ORG_ID, user, data)

        # Verify the first add call was the BudgetLineItem
        first_add_call = db.add.call_args_list[0]
        added_item = first_add_call[0][0]
        # The item should have been created with _dollars(5000000) = Decimal("50000.00")
        assert added_item.original_amount == Decimal("50000.00")

    @pytest.mark.asyncio
    async def test_create_logs_event(self):
        db = AsyncMock()
        user = _make_user()
        data = BudgetLineItemCreate(
            cost_code="03-100",
            description="Test",
            original_amount=10000,
        )

        await create_budget_line_item(db, PROJECT_ID, ORG_ID, user, data)

        # Second add call should be the EventLog
        second_add_call = db.add.call_args_list[1]
        event = second_add_call[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "budget_line_item_created"
        assert event.event_data["cost_code"] == "03-100"
        assert event.event_data["amount_cents"] == 10000


# ============================================================
# get_budget_line_item
# ============================================================

class TestGetBudgetLineItem:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        item = _make_budget_item()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        result = await get_budget_line_item(db, item.id, PROJECT_ID)
        assert result == item

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_budget_line_item(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_budget_line_item
# ============================================================

class TestUpdateBudgetLineItem:
    @pytest.mark.asyncio
    @patch("app.services.budget_service.get_budget_line_item", new_callable=AsyncMock)
    async def test_update_description(self, mock_get):
        db = AsyncMock()
        item = _make_budget_item()
        mock_get.return_value = item

        data = BudgetLineItemUpdate(description="Updated concrete work")

        result = await update_budget_line_item(db, item.id, PROJECT_ID, data)

        assert item.description == "Updated concrete work"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.budget_service.get_budget_line_item", new_callable=AsyncMock)
    async def test_update_amount_converts_cents_to_dollars(self, mock_get):
        db = AsyncMock()
        item = _make_budget_item()
        mock_get.return_value = item

        data = BudgetLineItemUpdate(original_amount=20000000)  # $200,000.00 in cents

        result = await update_budget_line_item(db, item.id, PROJECT_ID, data)

        assert item.original_amount == Decimal("200000.00")
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.budget_service.get_budget_line_item", new_callable=AsyncMock)
    async def test_update_notes(self, mock_get):
        db = AsyncMock()
        item = _make_budget_item()
        mock_get.return_value = item

        data = BudgetLineItemUpdate(notes="Updated notes")

        result = await update_budget_line_item(db, item.id, PROJECT_ID, data)

        assert item.notes == "Updated notes"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.budget_service.get_budget_line_item", new_callable=AsyncMock)
    async def test_update_no_changes(self, mock_get):
        db = AsyncMock()
        item = _make_budget_item()
        mock_get.return_value = item

        data = BudgetLineItemUpdate()  # No fields set

        result = await update_budget_line_item(db, item.id, PROJECT_ID, data)

        # Should still flush
        db.flush.assert_awaited_once()
        assert result == item


# ============================================================
# delete_budget_line_item
# ============================================================

class TestDeleteBudgetLineItem:
    @pytest.mark.asyncio
    @patch("app.services.budget_service.get_budget_line_item", new_callable=AsyncMock)
    async def test_soft_delete_sets_deleted_at(self, mock_get):
        db = AsyncMock()
        item = _make_budget_item()
        item.deleted_at = None
        mock_get.return_value = item

        await delete_budget_line_item(db, item.id, PROJECT_ID)

        assert item.deleted_at is not None
        db.flush.assert_awaited_once()


# ============================================================
# bulk_import_line_items
# ============================================================

class TestBulkImport:
    @pytest.mark.asyncio
    async def test_imports_multiple_items(self):
        db = AsyncMock()
        user = _make_user()
        items = [
            {"cost_code": "03-100", "description": "Concrete", "amount": 15000000},
            {"cost_code": "04-100", "description": "Masonry", "amount": 8000000},
            {"cost_code": "05-100", "description": "Metals", "amount": 12000000},
        ]

        result = await bulk_import_line_items(db, PROJECT_ID, ORG_ID, user, items)

        assert len(result) == 3
        # 3 BudgetLineItems + 1 EventLog = 4 add calls
        assert db.add.call_count == 4
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_import_converts_cents_to_dollars(self):
        db = AsyncMock()
        user = _make_user()
        items = [
            {"cost_code": "03-100", "description": "Concrete", "amount": 15000000},
        ]

        result = await bulk_import_line_items(db, PROJECT_ID, ORG_ID, user, items)

        first_add = db.add.call_args_list[0]
        added_item = first_add[0][0]
        assert added_item.original_amount == Decimal("150000.00")

    @pytest.mark.asyncio
    async def test_import_logs_event_with_count(self):
        db = AsyncMock()
        user = _make_user()
        items = [
            {"cost_code": "03-100", "description": "Concrete", "amount": 100},
            {"cost_code": "04-100", "description": "Masonry", "amount": 200},
        ]

        await bulk_import_line_items(db, PROJECT_ID, ORG_ID, user, items)

        # Last add call is the EventLog
        last_add = db.add.call_args_list[-1]
        event = last_add[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "budget_imported"
        assert event.event_data["count"] == 2


# ============================================================
# get_budget_summary
# ============================================================

class TestGetBudgetSummary:
    @pytest.mark.asyncio
    @patch("app.services.budget_service._get_billed_by_line", new_callable=AsyncMock)
    async def test_summary_calculation_with_items(self, mock_billed):
        mock_billed.return_value = {}

        db = AsyncMock()

        item1 = _make_budget_item(
            cost_code="03-100",
            original_amount=Decimal("100000.00"),
            approved_changes=Decimal("5000.00"),
        )
        item2 = _make_budget_item(
            cost_code="04-100",
            original_amount=Decimal("50000.00"),
            approved_changes=Decimal("2000.00"),
        )

        # Mock the first execute (select budget line items)
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [item1, item2]
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value = mock_scalars

        # Mock the second execute (pending COs)
        mock_co_row = (0, Decimal("0"))
        mock_co_result = MagicMock()
        mock_co_result.one.return_value = mock_co_row

        db.execute.side_effect = [mock_items_result, mock_co_result]

        result = await get_budget_summary(db, PROJECT_ID)

        # original: 100000 + 50000 = 150000 -> 15000000 cents
        assert result.original_contract == 15000000
        # changes: 5000 + 2000 = 7000 -> 700000 cents
        assert result.approved_changes == 700000
        # revised: 15000000 + 700000 = 15700000 cents
        assert result.revised_contract == 15700000
        assert result.billed_to_date == 0
        assert result.remaining == 15700000
        assert len(result.line_items) == 2
        assert result.change_orders_pending == 0
        assert result.change_orders_pending_amount == 0

    @pytest.mark.asyncio
    @patch("app.services.budget_service._get_billed_by_line", new_callable=AsyncMock)
    async def test_summary_with_billed_amounts(self, mock_billed):
        db = AsyncMock()

        item = _make_budget_item(
            cost_code="03-100",
            original_amount=Decimal("100000.00"),
            approved_changes=Decimal("0.00"),
        )
        # Return billed amounts for this item (in cents)
        mock_billed.return_value = {str(item.id): 5000000}  # $50,000 billed

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [item]
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value = mock_scalars

        mock_co_result = MagicMock()
        mock_co_result.one.return_value = (0, Decimal("0"))

        db.execute.side_effect = [mock_items_result, mock_co_result]

        result = await get_budget_summary(db, PROJECT_ID)

        assert result.original_contract == 10000000  # $100,000
        assert result.billed_to_date == 5000000  # $50,000
        assert result.remaining == 5000000  # $50,000
        assert result.percent_complete == 50.0

    @pytest.mark.asyncio
    @patch("app.services.budget_service._get_billed_by_line", new_callable=AsyncMock)
    async def test_summary_empty_budget(self, mock_billed):
        mock_billed.return_value = {}
        db = AsyncMock()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value = mock_scalars

        mock_co_result = MagicMock()
        mock_co_result.one.return_value = (0, Decimal("0"))

        db.execute.side_effect = [mock_items_result, mock_co_result]

        result = await get_budget_summary(db, PROJECT_ID)

        assert result.original_contract == 0
        assert result.approved_changes == 0
        assert result.revised_contract == 0
        assert result.percent_complete == 0.0
        assert len(result.line_items) == 0

    @pytest.mark.asyncio
    @patch("app.services.budget_service._get_billed_by_line", new_callable=AsyncMock)
    async def test_summary_with_pending_change_orders(self, mock_billed):
        mock_billed.return_value = {}
        db = AsyncMock()

        item = _make_budget_item(
            original_amount=Decimal("100000.00"),
            approved_changes=Decimal("0.00"),
        )

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [item]
        mock_items_result = MagicMock()
        mock_items_result.scalars.return_value = mock_scalars

        # 2 pending COs totaling $25,000
        mock_co_result = MagicMock()
        mock_co_result.one.return_value = (2, Decimal("25000.00"))

        db.execute.side_effect = [mock_items_result, mock_co_result]

        result = await get_budget_summary(db, PROJECT_ID)

        assert result.change_orders_pending == 2
        assert result.change_orders_pending_amount == 2500000  # $25,000 in cents


# ============================================================
# format_budget_line_item_response
# ============================================================

class TestFormatBudgetLineItemResponse:
    def test_cents_conversion(self):
        item = _make_budget_item(
            original_amount=Decimal("150000.00"),
            approved_changes=Decimal("5000.00"),
        )
        result = format_budget_line_item_response(item)

        assert result["original_amount"] == 15000000  # $150,000.00 in cents
        assert result["approved_changes"] == 500000  # $5,000.00 in cents
        assert result["revised_amount"] == 15500000  # $155,000.00 in cents

    def test_billed_and_remaining(self):
        item = _make_budget_item(
            original_amount=Decimal("100000.00"),
            approved_changes=Decimal("0.00"),
        )
        result = format_budget_line_item_response(item, billed_cents=3000000)

        assert result["billed_to_date"] == 3000000  # $30,000
        assert result["remaining"] == 7000000  # $70,000

    def test_percent_complete(self):
        item = _make_budget_item(
            original_amount=Decimal("100000.00"),
            approved_changes=Decimal("0.00"),
        )
        result = format_budget_line_item_response(item, billed_cents=5000000)

        assert result["percent_complete"] == 50.0

    def test_percent_complete_zero_revised(self):
        item = _make_budget_item(
            original_amount=Decimal("0.00"),
            approved_changes=Decimal("0.00"),
        )
        result = format_budget_line_item_response(item, billed_cents=0)

        assert result["percent_complete"] == 0.0

    def test_includes_all_fields(self):
        item = _make_budget_item()
        result = format_budget_line_item_response(item)

        assert result["id"] == item.id
        assert result["project_id"] == PROJECT_ID
        assert result["cost_code"] == "03-100"
        assert result["description"] == "Concrete Foundations"
        assert result["notes"] == "Phase 1 footings"
        assert result["created_at"] == item.created_at
        assert result["updated_at"] == item.updated_at

    def test_none_amounts_treated_as_zero(self):
        item = _make_budget_item(
            original_amount=None,
            approved_changes=None,
        )
        result = format_budget_line_item_response(item)

        assert result["original_amount"] == 0
        assert result["approved_changes"] == 0
        assert result["revised_amount"] == 0


# ============================================================
# _cents / _dollars helpers
# ============================================================

class TestCurrencyConversion:
    def test_cents_from_decimal(self):
        assert _cents(Decimal("150.00")) == 15000

    def test_cents_from_none(self):
        assert _cents(None) == 0

    def test_cents_from_zero(self):
        assert _cents(Decimal("0")) == 0

    def test_dollars_from_cents(self):
        assert _dollars(15000) == Decimal("150.00")

    def test_dollars_from_zero(self):
        assert _dollars(0) == Decimal("0")
