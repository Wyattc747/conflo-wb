"""Tests for Meeting service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.meeting import Meeting
from app.schemas.meeting import MeetingCreate, MeetingUpdate, PublishMinutesRequest
from app.services.meeting_service import (
    create_meeting,
    get_meeting,
    update_meeting,
    delete_meeting,
    start_meeting,
    complete_meeting,
    cancel_meeting,
    publish_minutes,
    format_meeting_response,
)
from app.services.numbering_service import format_number
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID


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


def _make_meeting(
    status="SCHEDULED",
    meeting_type="OAC",
    number=1,
    created_by=ADMIN_USER_ID,
):
    m = MagicMock(spec=Meeting)
    m.id = uuid.uuid4()
    m.organization_id = ORG_ID
    m.project_id = PROJECT_ID
    m.created_by = created_by
    m.number = number
    m.title = "Weekly OAC Meeting"
    m.meeting_type = meeting_type
    m.status = status
    m.scheduled_date = datetime(2026, 3, 5)
    m.start_time = None
    m.end_time = None
    m.location = "Conference Room A"
    m.virtual_provider = "Zoom"
    m.virtual_link = "https://zoom.us/j/123456"
    m.attendees = [str(ADMIN_USER_ID), str(MGMT_USER_ID)]
    m.agenda = "1. Review schedule\n2. Review RFIs"
    m.minutes = None
    m.action_items = []
    m.recurring = False
    m.recurrence_rule = None
    m.recurrence_end_date = None
    m.parent_meeting_id = None
    m.minutes_published = False
    m.minutes_published_at = None
    m.created_at = datetime(2026, 2, 20, 10, 0)
    m.updated_at = datetime(2026, 2, 20, 10, 0)
    m.deleted_at = None
    return m


# ============================================================
# create_meeting
# ============================================================

class TestCreateMeeting:
    @pytest.mark.asyncio
    @patch("app.services.meeting_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = MeetingCreate(
            title="Weekly OAC Meeting",
            meeting_type="OAC",
            scheduled_date=date(2026, 3, 5),
            location="Conference Room A",
            attendees=[ADMIN_USER_ID, MGMT_USER_ID],
            agenda="1. Review schedule\n2. Review RFIs",
        )

        result = await create_meeting(db, PROJECT_ID, ORG_ID, user, data)

        # Meeting + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "meeting")

    @pytest.mark.asyncio
    @patch("app.services.meeting_service.get_next_number", new_callable=AsyncMock)
    async def test_create_minimal(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        data = MeetingCreate(title="Quick Standup")

        await create_meeting(db, PROJECT_ID, ORG_ID, user, data)

        # Meeting + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_meeting
# ============================================================

class TestGetMeeting:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        meeting = _make_meeting()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        result = await get_meeting(db, meeting.id, PROJECT_ID)
        assert result == meeting

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_meeting(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_meeting
# ============================================================

class TestUpdateMeeting:
    @pytest.mark.asyncio
    async def test_update_scheduled(self):
        db = AsyncMock()
        meeting = _make_meeting(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = MeetingUpdate(title="Updated Title")

        result = await update_meeting(db, meeting.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_completed_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = MeetingUpdate(title="Won't work")

        with pytest.raises(HTTPException) as exc_info:
            await update_meeting(db, meeting.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_cancelled_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="CANCELLED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = MeetingUpdate(title="Won't work")

        with pytest.raises(HTTPException) as exc_info:
            await update_meeting(db, meeting.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# delete_meeting
# ============================================================

class TestDeleteMeeting:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        db = AsyncMock()
        meeting = _make_meeting()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_meeting(db, meeting.id, PROJECT_ID, user)

        assert meeting.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_meeting(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# start_meeting
# ============================================================

class TestStartMeeting:
    @pytest.mark.asyncio
    async def test_start_scheduled(self):
        db = AsyncMock()
        meeting = _make_meeting(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        result = await start_meeting(db, meeting.id, PROJECT_ID, user)

        assert meeting.status == "IN_PROGRESS"
        # EventLog added
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_non_scheduled_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await start_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_start_completed_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await start_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# complete_meeting
# ============================================================

class TestCompleteMeeting:
    @pytest.mark.asyncio
    async def test_complete_in_progress(self):
        db = AsyncMock()
        meeting = _make_meeting(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        result = await complete_meeting(db, meeting.id, PROJECT_ID, user)

        assert meeting.status == "COMPLETED"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_scheduled_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await complete_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_already_completed_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await complete_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# cancel_meeting
# ============================================================

class TestCancelMeeting:
    @pytest.mark.asyncio
    async def test_cancel_scheduled(self):
        db = AsyncMock()
        meeting = _make_meeting(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        result = await cancel_meeting(db, meeting.id, PROJECT_ID, user)

        assert meeting.status == "CANCELLED"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_in_progress_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await cancel_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_completed_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await cancel_meeting(db, meeting.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# publish_minutes
# ============================================================

class TestPublishMinutes:
    @pytest.mark.asyncio
    async def test_publish_completed_meeting(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        meeting.action_items = []
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = PublishMinutesRequest(create_todos=False)

        result = await publish_minutes(db, meeting.id, PROJECT_ID, ORG_ID, user, data)

        assert meeting.minutes_published is True
        assert meeting.minutes_published_at is not None
        # EventLog added
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_publish_in_progress_meeting(self):
        db = AsyncMock()
        meeting = _make_meeting(status="IN_PROGRESS")
        meeting.action_items = []
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = PublishMinutesRequest(create_todos=False)

        result = await publish_minutes(db, meeting.id, PROJECT_ID, ORG_ID, user, data)

        assert meeting.minutes_published is True

    @pytest.mark.asyncio
    async def test_publish_scheduled_raises_400(self):
        db = AsyncMock()
        meeting = _make_meeting(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = PublishMinutesRequest(create_todos=False)

        with pytest.raises(HTTPException) as exc_info:
            await publish_minutes(db, meeting.id, PROJECT_ID, ORG_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_publish_with_action_items_creates_todos(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        meeting.action_items = [
            {"description": "Review submittal", "assigned_to": str(MGMT_USER_ID), "due_date": "2026-03-10"},
            {"description": "Order materials", "assigned_to": None, "due_date": None},
        ]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = PublishMinutesRequest(create_todos=True)

        result = await publish_minutes(db, meeting.id, PROJECT_ID, ORG_ID, user, data)

        assert meeting.minutes_published is True
        # 2 Todos + 1 EventLog = 3 adds
        assert db.add.call_count == 3
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_publish_without_creating_todos(self):
        db = AsyncMock()
        meeting = _make_meeting(status="COMPLETED")
        meeting.action_items = [
            {"description": "Review submittal", "assigned_to": str(MGMT_USER_ID)},
        ]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = meeting
        db.execute.return_value = mock_result

        user = _make_user()
        data = PublishMinutesRequest(create_todos=False)

        result = await publish_minutes(db, meeting.id, PROJECT_ID, ORG_ID, user, data)

        assert meeting.minutes_published is True
        # Only EventLog = 1 add (no todos)
        assert db.add.call_count == 1
        db.flush.assert_awaited_once()


# ============================================================
# format_meeting_response
# ============================================================

class TestFormatMeetingResponse:
    def test_basic_format(self):
        meeting = _make_meeting(number=1)
        result = format_meeting_response(
            meeting,
            created_by_name="John Smith",
        )

        assert result["id"] == meeting.id
        assert result["project_id"] == PROJECT_ID
        assert result["number"] == 1
        assert result["formatted_number"] == "MTG-001"
        assert result["title"] == "Weekly OAC Meeting"
        assert result["meeting_type"] == "OAC"
        assert result["status"] == "SCHEDULED"
        assert result["location"] == "Conference Room A"
        assert result["virtual_provider"] == "Zoom"
        assert result["attendees"] == [str(ADMIN_USER_ID), str(MGMT_USER_ID)]
        assert result["agenda"] == "1. Review schedule\n2. Review RFIs"
        assert result["minutes_published"] is False
        assert result["created_by_name"] == "John Smith"
        assert result["created_at"] == meeting.created_at

    def test_number_format(self):
        meeting = _make_meeting(number=42)
        result = format_meeting_response(meeting)
        assert result["formatted_number"] == "MTG-042"

    def test_format_with_no_name(self):
        meeting = _make_meeting()
        result = format_meeting_response(meeting)
        assert result["created_by_name"] is None

    def test_empty_attendees(self):
        meeting = _make_meeting()
        meeting.attendees = None
        result = format_meeting_response(meeting)
        assert result["attendees"] == []

    def test_empty_action_items(self):
        meeting = _make_meeting()
        meeting.action_items = None
        result = format_meeting_response(meeting)
        assert result["action_items"] == []


# ============================================================
# Numbering format verification
# ============================================================

class TestMeetingNumbering:
    def test_first_meeting(self):
        assert format_number("meeting", 1) == "MTG-001"

    def test_high_number(self):
        assert format_number("meeting", 42) == "MTG-042"

    def test_triple_digits(self):
        assert format_number("meeting", 100) == "MTG-100"
