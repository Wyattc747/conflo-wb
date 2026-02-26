"""Tests for RFI service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.rfi import RFI
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.rfi import RfiCreate, RfiUpdate, RfiResponseCreate
from app.services.rfi_service import (
    close_rfi,
    create_rfi,
    format_rfi_response,
    get_rfi,
    reopen_rfi,
    respond_to_rfi,
    update_rfi,
)
from app.services.numbering_service import format_number
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


def _make_rfi(
    status="OPEN",
    number=1,
    created_by=ADMIN_USER_ID,
    assigned_to=MGMT_USER_ID,
):
    rfi = MagicMock(spec=RFI)
    rfi.id = uuid.uuid4()
    rfi.organization_id = ORG_ID
    rfi.project_id = PROJECT_ID
    rfi.created_by = created_by
    rfi.number = number
    rfi.subject = "Test RFI Subject"
    rfi.question = "What is the answer?"
    rfi.status = status
    rfi.priority = "NORMAL"
    rfi.assigned_to = assigned_to
    rfi.due_date = datetime(2026, 3, 1)
    rfi.cost_impact = False
    rfi.schedule_impact = False
    rfi.official_response = None
    rfi.responded_by = None
    rfi.responded_at = None
    rfi.created_at = datetime(2026, 2, 20, 10, 0)
    rfi.updated_at = datetime(2026, 2, 20, 10, 0)
    return rfi


# ============================================================
# create_rfi
# ============================================================

class TestCreateRFI:
    @pytest.mark.asyncio
    @patch("app.services.rfi_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = RfiCreate(
            subject="Test RFI",
            question="What should we do?",
            assigned_to=MGMT_USER_ID,
            priority="HIGH",
            due_date=date(2026, 3, 1),
        )

        result = await create_rfi(db, PROJECT_ID, ORG_ID, user, data)

        # Should add: RFI + Notification + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "rfi")

    @pytest.mark.asyncio
    @patch("app.services.rfi_service.get_next_number", new_callable=AsyncMock)
    async def test_create_without_assignee_no_notification(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        data = RfiCreate(
            subject="Test RFI",
            question="Question?",
        )

        await create_rfi(db, PROJECT_ID, ORG_ID, user, data)

        # Should add: RFI + EventLog = 2 (no notification since no assignee)
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_rfi
# ============================================================

class TestGetRFI:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        rfi = _make_rfi()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        result = await get_rfi(db, rfi.id, PROJECT_ID)
        assert result == rfi

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_rfi(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_rfi
# ============================================================

class TestUpdateRFI:
    @pytest.mark.asyncio
    async def test_update_open_rfi(self):
        db = AsyncMock()
        rfi = _make_rfi(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        data = RfiUpdate(subject="Updated subject")

        result = await update_rfi(db, rfi.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_closed_raises_400(self):
        db = AsyncMock()
        rfi = _make_rfi(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        data = RfiUpdate(subject="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await update_rfi(db, rfi.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# respond_to_rfi
# ============================================================

class TestRespondToRFI:
    @pytest.mark.asyncio
    async def test_respond_success(self):
        db = AsyncMock()
        rfi = _make_rfi(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user(user_id=MGMT_USER_ID)
        data = RfiResponseCreate(response="Use 4000 PSI per structural drawings.")

        result = await respond_to_rfi(db, rfi.id, PROJECT_ID, user, data)

        assert rfi.status == "RESPONDED"
        assert rfi.official_response == "Use 4000 PSI per structural drawings."
        assert rfi.responded_by == MGMT_USER_ID
        assert rfi.responded_at is not None
        # Notification + EventLog added
        assert db.add.call_count >= 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_respond_to_closed_raises_400(self):
        db = AsyncMock()
        rfi = _make_rfi(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        data = RfiResponseCreate(response="Too late")

        with pytest.raises(HTTPException) as exc_info:
            await respond_to_rfi(db, rfi.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# close_rfi
# ============================================================

class TestCloseRFI:
    @pytest.mark.asyncio
    async def test_close_responded(self):
        db = AsyncMock()
        rfi = _make_rfi(status="RESPONDED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        result = await close_rfi(db, rfi.id, PROJECT_ID, user)

        assert rfi.status == "CLOSED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_open(self):
        db = AsyncMock()
        rfi = _make_rfi(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        result = await close_rfi(db, rfi.id, PROJECT_ID, user)
        assert rfi.status == "CLOSED"

    @pytest.mark.asyncio
    async def test_close_already_closed_raises_400(self):
        db = AsyncMock()
        rfi = _make_rfi(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await close_rfi(db, rfi.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# reopen_rfi
# ============================================================

class TestReopenRFI:
    @pytest.mark.asyncio
    async def test_reopen_closed(self):
        db = AsyncMock()
        rfi = _make_rfi(status="CLOSED")
        rfi.official_response = "Previous response"
        rfi.responded_by = MGMT_USER_ID
        rfi.responded_at = datetime(2026, 2, 22)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        result = await reopen_rfi(db, rfi.id, PROJECT_ID, user)

        assert rfi.status == "OPEN"
        assert rfi.official_response is None
        assert rfi.responded_by is None
        assert rfi.responded_at is None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reopen_open_raises_400(self):
        db = AsyncMock()
        rfi = _make_rfi(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rfi
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reopen_rfi(db, rfi.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# format_rfi_response
# ============================================================

class TestFormatRFIResponse:
    def test_basic_format(self):
        rfi = _make_rfi()
        result = format_rfi_response(
            rfi,
            created_by_name="John Smith",
            assigned_to_name="Sarah Johnson",
            comments_count=3,
        )

        assert result["id"] == rfi.id
        assert result["project_id"] == PROJECT_ID
        assert result["number"] == 1
        assert result["formatted_number"] == "RFI-001"
        assert result["subject"] == "Test RFI Subject"
        assert result["status"] == "OPEN"
        assert result["created_by_name"] == "John Smith"
        assert result["assigned_to_name"] == "Sarah Johnson"
        assert result["comments_count"] == 3

    def test_days_open_calculation(self):
        rfi = _make_rfi(status="OPEN")
        result = format_rfi_response(rfi)
        assert result["days_open"] is not None
        assert result["days_open"] >= 0

    def test_days_open_none_when_closed(self):
        rfi = _make_rfi(status="CLOSED")
        result = format_rfi_response(rfi)
        assert result["days_open"] is None

    def test_due_date_conversion(self):
        rfi = _make_rfi()
        rfi.due_date = datetime(2026, 3, 1, 0, 0)
        result = format_rfi_response(rfi)
        assert result["due_date"] == date(2026, 3, 1)
