"""Tests for Transmittal service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.transmittal import Transmittal
from app.schemas.transmittal import TransmittalCreate, TransmittalUpdate
from app.services.transmittal_service import (
    confirm_transmittal,
    create_transmittal,
    format_transmittal_response,
    get_transmittal,
    send_transmittal,
    update_transmittal,
)
from app.services.numbering_service import format_number
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID


def _make_user(user_id=ADMIN_USER_ID):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": "OWNER_ADMIN",
    }


def _make_transmittal(status="DRAFT", number=1):
    t = MagicMock(spec=Transmittal)
    t.id = uuid.uuid4()
    t.organization_id = ORG_ID
    t.project_id = PROJECT_ID
    t.created_by = ADMIN_USER_ID
    t.number = number
    t.subject = "Concrete Mix Design Submittal Package"
    t.description = "Transmitting concrete mix design documents"
    t.to_company = "Smith Architecture"
    t.to_contact = "Robert Smith"
    t.to_email = "robert@smitharch.com"
    t.from_company = "Apex Construction"
    t.from_contact = "John Admin"
    t.purpose = "FOR_REVIEW"
    t.items = [
        {"description": "Concrete mix design report", "quantity": 2, "document_type": "REPORTS"},
        {"description": "Test cylinder results", "quantity": 1, "document_type": "REPORTS"},
    ]
    t.sent_via = "CONFLO"
    t.due_date = datetime(2026, 3, 1)
    t.to_contact_ids = []
    t.action_required = None
    t.notes = None
    t.status = status
    t.sent_at = None
    t.received_at = None
    t.created_at = datetime(2026, 2, 20, 10, 0)
    t.updated_at = datetime(2026, 2, 20, 10, 0)
    t.deleted_at = None
    return t


# ============================================================
# create_transmittal
# ============================================================

class TestCreateTransmittal:
    @pytest.mark.asyncio
    @patch("app.services.transmittal_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = TransmittalCreate(
            subject="Concrete Mix Design",
            to_company="Smith Architecture",
            to_contact="Robert Smith",
            purpose="FOR_REVIEW",
            items=[
                {"description": "Mix design report", "quantity": 2, "document_type": "REPORTS"},
            ],
            due_date=date(2026, 3, 1),
        )

        result = await create_transmittal(db, PROJECT_ID, ORG_ID, user, data)

        # Transmittal + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "transmittal")

    @pytest.mark.asyncio
    @patch("app.services.transmittal_service.get_next_number", new_callable=AsyncMock)
    async def test_auto_numbering(self, mock_next_number):
        mock_next_number.return_value = 3

        db = AsyncMock()
        user = _make_user()
        data = TransmittalCreate(subject="Test Transmittal")

        await create_transmittal(db, PROJECT_ID, ORG_ID, user, data)

        formatted = format_number("transmittal", 3)
        assert formatted == "TR-003"


# ============================================================
# send_transmittal
# ============================================================

class TestSendTransmittal:
    @pytest.mark.asyncio
    async def test_send_draft(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        result = await send_transmittal(db, transmittal.id, PROJECT_ID, user)

        assert transmittal.status == "SENT"
        assert transmittal.sent_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_non_draft_raises_400(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="SENT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await send_transmittal(db, transmittal.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# confirm_transmittal
# ============================================================

class TestConfirmTransmittal:
    @pytest.mark.asyncio
    async def test_confirm_sent(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="SENT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        result = await confirm_transmittal(db, transmittal.id, PROJECT_ID, user)

        assert transmittal.status == "RECEIVED"
        assert transmittal.received_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_confirm_draft_raises_400(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await confirm_transmittal(db, transmittal.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# update_transmittal
# ============================================================

class TestUpdateTransmittal:
    @pytest.mark.asyncio
    async def test_update_draft(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = TransmittalUpdate(subject="Updated Subject")

        result = await update_transmittal(db, transmittal.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_sent_raises_400(self):
        db = AsyncMock()
        transmittal = _make_transmittal(status="SENT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = transmittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = TransmittalUpdate(subject="Can't update")

        with pytest.raises(HTTPException) as exc_info:
            await update_transmittal(db, transmittal.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# Items stored correctly
# ============================================================

class TestTransmittalItems:
    @pytest.mark.asyncio
    @patch("app.services.transmittal_service.get_next_number", new_callable=AsyncMock)
    async def test_items_stored(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = TransmittalCreate(
            subject="Test",
            items=[
                {"description": "Drawing set A", "quantity": 3, "document_type": "DRAWINGS"},
                {"description": "Spec book", "quantity": 1, "document_type": "SPECS"},
            ],
        )

        await create_transmittal(db, PROJECT_ID, ORG_ID, user, data)

        # Verify items are passed as dicts
        add_calls = db.add.call_args_list
        transmittal_obj = add_calls[0][0][0]
        assert len(transmittal_obj.items) == 2
        assert transmittal_obj.items[0]["description"] == "Drawing set A"
        assert transmittal_obj.items[0]["quantity"] == 3


# ============================================================
# format_transmittal_response
# ============================================================

class TestFormatTransmittalResponse:
    def test_basic_format(self):
        transmittal = _make_transmittal(number=5)
        result = format_transmittal_response(
            transmittal,
            created_by_name="John Admin",
            comments_count=2,
        )

        assert result["number"] == 5
        assert result["formatted_number"] == "TR-005"
        assert result["subject"] == "Concrete Mix Design Submittal Package"
        assert result["status"] == "DRAFT"
        assert result["to_company"] == "Smith Architecture"
        assert result["purpose"] == "FOR_REVIEW"
        assert result["created_by_name"] == "John Admin"
        assert result["comments_count"] == 2
        assert len(result["items"]) == 2

    def test_numbering(self):
        assert format_number("transmittal", 1) == "TR-001"
        assert format_number("transmittal", 42) == "TR-042"
