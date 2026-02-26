"""Tests for Punch List service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.punch_list_item import PunchListItem
from app.schemas.punch_list import (
    PunchListItemCreate,
    PunchListItemUpdate,
    PunchListCompleteRequest,
    PunchListVerifyRequest,
)
from app.services.punch_list_service import (
    close_punch_item,
    complete_punch_item,
    create_punch_item,
    dispute_punch_item,
    format_punch_item_response,
    get_punch_item,
    update_punch_item,
    verify_punch_item,
)
from app.services.numbering_service import format_number
from tests.conftest import (
    ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID,
    SUB_COMPANY_ID, SUB_USER_ID,
)


def _make_user(user_id=ADMIN_USER_ID, user_type="gc", permission_level="OWNER_ADMIN"):
    return {
        "user_type": user_type,
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_sub_user():
    return {
        "user_type": "sub",
        "user_id": SUB_USER_ID,
        "sub_company_id": SUB_COMPANY_ID,
        "permission_level": None,
    }


def _make_punch_item(status="OPEN", number=1, assigned_sub=SUB_COMPANY_ID):
    item = MagicMock(spec=PunchListItem)
    item.id = uuid.uuid4()
    item.organization_id = ORG_ID
    item.project_id = PROJECT_ID
    item.created_by = ADMIN_USER_ID
    item.number = number
    item.title = "Cracked drywall in Room 301"
    item.description = "Visible crack along ceiling joint"
    item.location = "Level 3, Room 301"
    item.category = "DEFICIENCY"
    item.trade = "Finishes"
    item.priority = "HIGH"
    item.assigned_sub_company_id = assigned_sub
    item.assigned_to_user_id = None
    item.due_date = datetime(2026, 3, 15)
    item.cost_code_id = None
    item.drawing_reference = "A-301"
    item.before_photo_ids = []
    item.after_photo_ids = []
    item.verification_photo_ids = []
    item.completion_notes = None
    item.completed_by = None
    item.completed_at = None
    item.verification_notes = None
    item.verified_by = None
    item.verified_at = None
    item.status = status
    item.created_at = datetime(2026, 2, 20, 10, 0)
    item.updated_at = datetime(2026, 2, 20, 10, 0)
    item.deleted_at = None
    return item


# ============================================================
# create_punch_item
# ============================================================

class TestCreatePunchItem:
    @pytest.mark.asyncio
    @patch("app.services.punch_list_service.get_next_number", new_callable=AsyncMock)
    async def test_create_with_sub_assignment(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = PunchListItemCreate(
            title="Cracked drywall",
            location="Level 3, Room 301",
            category="DEFICIENCY",
            priority="HIGH",
            assigned_to_sub_id=SUB_COMPANY_ID,
            due_date=date(2026, 3, 15),
        )

        result = await create_punch_item(db, PROJECT_ID, ORG_ID, user, data)

        # PunchItem + Notification (assigned sub) + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.punch_list_service.get_next_number", new_callable=AsyncMock)
    async def test_create_without_sub_no_notification(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        data = PunchListItemCreate(title="Missing outlet cover")

        await create_punch_item(db, PROJECT_ID, ORG_ID, user, data)

        # PunchItem + EventLog = 2
        assert db.add.call_count == 2


# ============================================================
# complete_punch_item (Sub)
# ============================================================

class TestCompletePunchItem:
    @pytest.mark.asyncio
    async def test_sub_marks_complete(self):
        db = AsyncMock()
        item = _make_punch_item(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_sub_user()
        data = PunchListCompleteRequest(completion_notes="Patched and painted")

        result = await complete_punch_item(db, item.id, PROJECT_ID, user, data)

        assert item.status == "COMPLETED"
        assert item.completion_notes == "Patched and painted"
        assert item.completed_by == SUB_USER_ID
        assert item.completed_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_in_progress(self):
        db = AsyncMock()
        item = _make_punch_item(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_sub_user()
        data = PunchListCompleteRequest()

        result = await complete_punch_item(db, item.id, PROJECT_ID, user, data)
        assert item.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_complete_verified_raises_400(self):
        db = AsyncMock()
        item = _make_punch_item(status="VERIFIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_sub_user()
        data = PunchListCompleteRequest()

        with pytest.raises(HTTPException) as exc_info:
            await complete_punch_item(db, item.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# verify_punch_item (GC)
# ============================================================

class TestVerifyPunchItem:
    @pytest.mark.asyncio
    async def test_gc_verifies_pass(self):
        db = AsyncMock()
        item = _make_punch_item(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user(user_id=MGMT_USER_ID, permission_level="MANAGEMENT")
        data = PunchListVerifyRequest(verified=True, verification_notes="Looks good")

        result = await verify_punch_item(db, item.id, PROJECT_ID, user, data)

        assert item.status == "VERIFIED"
        assert item.verified_by == MGMT_USER_ID
        assert item.verified_at is not None
        assert item.verification_notes == "Looks good"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_gc_rejects_reopens(self):
        db = AsyncMock()
        item = _make_punch_item(status="COMPLETED")
        item.completed_by = SUB_USER_ID
        item.completed_at = datetime(2026, 2, 25)
        item.completion_notes = "Done"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = PunchListVerifyRequest(verified=False, verification_notes="Patch is uneven")

        result = await verify_punch_item(db, item.id, PROJECT_ID, user, data)

        assert item.status == "OPEN"
        assert item.completed_at is None
        assert item.completed_by is None
        assert item.verification_notes == "Patch is uneven"

    @pytest.mark.asyncio
    async def test_verify_open_raises_400(self):
        db = AsyncMock()
        item = _make_punch_item(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        data = PunchListVerifyRequest(verified=True)

        with pytest.raises(HTTPException) as exc_info:
            await verify_punch_item(db, item.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# close_punch_item
# ============================================================

class TestClosePunchItem:
    @pytest.mark.asyncio
    async def test_close_verified(self):
        db = AsyncMock()
        item = _make_punch_item(status="VERIFIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        result = await close_punch_item(db, item.id, PROJECT_ID, user)

        assert item.status == "CLOSED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_open_raises_400(self):
        db = AsyncMock()
        item = _make_punch_item(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await close_punch_item(db, item.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# dispute_punch_item (Sub)
# ============================================================

class TestDisputePunchItem:
    @pytest.mark.asyncio
    async def test_sub_disputes_open(self):
        db = AsyncMock()
        item = _make_punch_item(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_sub_user()
        result = await dispute_punch_item(db, item.id, PROJECT_ID, user)

        assert item.status == "DISPUTED"
        # Notification + EventLog = 2
        assert db.add.call_count >= 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dispute_verified_raises_400(self):
        db = AsyncMock()
        item = _make_punch_item(status="VERIFIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        db.execute.return_value = mock_result

        user = _make_sub_user()
        with pytest.raises(HTTPException) as exc_info:
            await dispute_punch_item(db, item.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# format_punch_item_response
# ============================================================

class TestFormatPunchItemResponse:
    def test_basic_format(self):
        item = _make_punch_item(number=3)
        result = format_punch_item_response(
            item,
            created_by_name="John Admin",
            assigned_to_sub_name="Drywall Pro LLC",
            comments_count=2,
        )

        assert result["number"] == 3
        assert result["formatted_number"] == "PL-003"
        assert result["title"] == "Cracked drywall in Room 301"
        assert result["location"] == "Level 3, Room 301"
        assert result["category"] == "DEFICIENCY"
        assert result["priority"] == "HIGH"
        assert result["assigned_to_sub_name"] == "Drywall Pro LLC"
        assert result["comments_count"] == 2

    def test_numbering(self):
        assert format_number("punch_list_item", 1) == "PL-001"
        assert format_number("punch_list_item", 42) == "PL-042"
