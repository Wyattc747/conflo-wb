"""Tests for notification service."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.notification import Notification
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser
from app.services.notification_service import (
    CATEGORY_MAP,
    DEFAULT_PREFERENCES,
    create_notification,
    dismiss_notification,
    format_notification_response,
    get_preferences,
    get_unread_count,
    list_notifications,
    mark_all_read,
    mark_read,
    update_preferences,
    _build_entity_link,
)
from tests.conftest import (
    ADMIN_USER_ID,
    MGMT_USER_ID,
    ORG_ID,
    OWNER_ACCOUNT_ID,
    OWNER_USER_ID,
    PROJECT_ID,
    SUB_COMPANY_ID,
    SUB_USER_ID,
)


# ============================================================
# HELPERS
# ============================================================

NOTIF_ID = uuid.uuid4()
SOURCE_ID = uuid.uuid4()


def _make_user(
    user_type="gc",
    user_id=ADMIN_USER_ID,
    organization_id=ORG_ID,
    permission_level="OWNER_ADMIN",
):
    return {
        "user_type": user_type,
        "user_id": user_id,
        "organization_id": organization_id,
        "permission_level": permission_level,
    }


def _make_notification(
    notif_id=None,
    user_type="gc",
    user_id=ADMIN_USER_ID,
    notification_type="rfi_assigned",
    title="Test Notification",
    body="Test body",
    source_type="rfi",
    source_id=None,
    project_id=PROJECT_ID,
    read_at=None,
    metadata_=None,
    created_at=None,
):
    n = MagicMock(spec=Notification)
    n.id = notif_id or uuid.uuid4()
    n.user_type = user_type
    n.user_id = user_id
    n.type = notification_type
    n.title = title
    n.body = body
    n.source_type = source_type
    n.source_id = source_id or SOURCE_ID
    n.project_id = project_id
    n.metadata_ = metadata_ or {}
    n.read_at = read_at
    n.created_at = created_at or datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc)
    return n


def _make_gc_recipient(
    user_id=ADMIN_USER_ID,
    email="admin@example.com",
    preferences=None,
):
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = email
    user.notification_preferences = preferences
    return user


def _make_sub_recipient(
    user_id=SUB_USER_ID,
    email="sub@example.com",
    preferences=None,
):
    user = MagicMock(spec=SubUser)
    user.id = user_id
    user.email = email
    user.notification_preferences = preferences
    return user


def _make_owner_recipient(
    user_id=OWNER_USER_ID,
    email="owner@example.com",
    preferences=None,
):
    user = MagicMock(spec=OwnerUser)
    user.id = user_id
    user.email = email
    user.notification_preferences = preferences
    return user


# ============================================================
# CATEGORY_MAP
# ============================================================

class TestCategoryMap:
    def test_assigned_types_map_to_assigned_to_me(self):
        assert CATEGORY_MAP["rfi_assigned"] == "assigned_to_me"
        assert CATEGORY_MAP["punch_assigned"] == "assigned_to_me"
        assert CATEGORY_MAP["todo_assigned"] == "assigned_to_me"
        assert CATEGORY_MAP["project_assigned"] == "assigned_to_me"

    def test_status_change_types(self):
        status_types = [
            "rfi_response", "submittal_decision", "co_approved", "co_rejected",
            "pay_app_approved", "pay_app_rejected", "punch_completed",
            "owner_pay_app_approved", "delay_pending_approval",
            "payment_failed", "closeout_docs_requested",
            "project_active", "project_closed",
        ]
        for t in status_types:
            assert CATEGORY_MAP[t] == "status_changes", f"{t} should map to status_changes"

    def test_mention_types(self):
        assert CATEGORY_MAP["comment_mention"] == "mentions"

    def test_deadline_types(self):
        deadline_types = [
            "rfi_due_approaching", "submittal_due_approaching",
            "bid_deadline_approaching", "milestone_approaching",
            "sub_mobilization",
        ]
        for t in deadline_types:
            assert CATEGORY_MAP[t] == "approaching_deadlines", f"{t} should map to approaching_deadlines"

    def test_bid_invitation_types(self):
        bid_types = [
            "invited_to_bid", "bid_received", "bid_awarded",
            "bid_not_awarded", "bid_recommendation",
        ]
        for t in bid_types:
            assert CATEGORY_MAP[t] == "bid_invitations", f"{t} should map to bid_invitations"

    def test_pay_app_decision_types(self):
        assert CATEGORY_MAP["sub_pay_app_submitted"] == "pay_app_decisions"
        assert CATEGORY_MAP["pay_app_ready"] == "pay_app_decisions"

    def test_meeting_types(self):
        assert CATEGORY_MAP["meeting_scheduled"] == "meeting_scheduled"
        assert CATEGORY_MAP["meeting_minutes"] == "meeting_minutes"

    def test_all_categories_exist_in_default_preferences(self):
        """Every category referenced in CATEGORY_MAP should exist in DEFAULT_PREFERENCES."""
        categories = set(CATEGORY_MAP.values())
        for cat in categories:
            assert cat in DEFAULT_PREFERENCES["email_categories"], (
                f"Category '{cat}' not in DEFAULT_PREFERENCES"
            )


# ============================================================
# create_notification
# ============================================================

class TestCreateNotification:
    @pytest.mark.asyncio
    async def test_creates_record_in_db(self):
        db = AsyncMock()
        recipient = _make_gc_recipient()
        db.get.return_value = recipient

        result = await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="New RFI Assigned",
            body="RFI-001 has been assigned to you.",
            source_type="rfi",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        db.add.assert_called_once()
        db.flush.assert_called()
        added = db.add.call_args[0][0]
        assert isinstance(added, Notification)
        assert added.user_type == "gc"
        assert added.user_id == ADMIN_USER_ID
        assert added.type == "rfi_assigned"
        assert added.title == "New RFI Assigned"
        assert added.body == "RFI-001 has been assigned to you."
        assert added.source_type == "rfi"
        assert added.source_id == SOURCE_ID
        assert added.project_id == PROJECT_ID

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_sends_email_when_preference_enabled(self, mock_send):
        db = AsyncMock()
        prefs = {
            "email_enabled": True,
            "email_categories": {"assigned_to_me": True},
        }
        recipient = _make_gc_recipient(preferences=prefs)
        db.get.return_value = recipient

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="New RFI",
            body="Assigned.",
            source_type="rfi",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "admin@example.com"
        assert call_args[0][1] == "New RFI"

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_does_not_send_email_when_preference_disabled(self, mock_send):
        db = AsyncMock()
        prefs = {
            "email_enabled": True,
            "email_categories": {"assigned_to_me": False},
        }
        recipient = _make_gc_recipient(preferences=prefs)
        db.get.return_value = recipient

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="New RFI",
            source_type="rfi",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_does_not_send_email_when_email_disabled(self, mock_send):
        db = AsyncMock()
        prefs = {
            "email_enabled": False,
            "email_categories": {"assigned_to_me": True},
        }
        recipient = _make_gc_recipient(preferences=prefs)
        db.get.return_value = recipient

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="New RFI",
        )

        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_recipient_id_is_none(self):
        db = AsyncMock()
        result = await create_notification(
            db,
            user_type="gc",
            recipient_id=None,
            notification_type="rfi_assigned",
            title="New RFI",
        )
        assert result is None
        db.add.assert_not_called()
        db.flush.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_email_subject_matches_title(self, mock_send):
        db = AsyncMock()
        prefs = {
            "email_enabled": True,
            "email_categories": {"status_changes": True},
        }
        recipient = _make_gc_recipient(preferences=prefs)
        db.get.return_value = recipient
        title = "Pay App #3 Approved"

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="pay_app_approved",
            title=title,
            body="Your pay app has been approved.",
            source_type="pay_app",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        mock_send.assert_called_once()
        # _send_notification_email(to_email, title, body, link, notification_type)
        sent_title = mock_send.call_args[0][1]
        assert sent_title == title

    @pytest.mark.asyncio
    async def test_with_all_fields_populates_metadata(self):
        db = AsyncMock()
        recipient = _make_gc_recipient()
        db.get.return_value = recipient
        meta = {"rfi_number": "RFI-042", "priority": "HIGH"}

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="RFI Assigned",
            body="Please respond.",
            source_type="rfi",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
            metadata=meta,
        )

        added = db.add.call_args[0][0]
        assert added.metadata_ == meta

    @pytest.mark.asyncio
    async def test_metadata_defaults_to_empty_dict(self):
        db = AsyncMock()
        recipient = _make_gc_recipient()
        db.get.return_value = recipient

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="RFI Assigned",
        )

        added = db.add.call_args[0][0]
        assert added.metadata_ == {}

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_uses_default_prefs_when_recipient_has_none(self, mock_send):
        """When notification_preferences is None, defaults should enable email."""
        db = AsyncMock()
        recipient = _make_gc_recipient(preferences=None)
        db.get.return_value = recipient

        await create_notification(
            db,
            user_type="gc",
            recipient_id=ADMIN_USER_ID,
            notification_type="rfi_assigned",
            title="RFI Assigned",
            source_type="rfi",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        # DEFAULT_PREFERENCES has email_enabled=True and assigned_to_me=True
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_resolves_sub_recipient(self, mock_send):
        db = AsyncMock()
        sub_recipient = _make_sub_recipient()
        db.get.return_value = sub_recipient

        await create_notification(
            db,
            user_type="sub",
            recipient_id=SUB_USER_ID,
            notification_type="invited_to_bid",
            title="New Bid Invitation",
            source_type="bid_package",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        db.get.assert_called_with(SubUser, SUB_USER_ID)

    @pytest.mark.asyncio
    @patch("app.services.notification_service._send_notification_email", new_callable=AsyncMock)
    async def test_resolves_owner_recipient(self, mock_send):
        db = AsyncMock()
        owner_recipient = _make_owner_recipient()
        db.get.return_value = owner_recipient

        await create_notification(
            db,
            user_type="owner",
            recipient_id=OWNER_USER_ID,
            notification_type="pay_app_ready",
            title="Pay App Ready for Review",
            source_type="pay_app",
            source_id=SOURCE_ID,
            project_id=PROJECT_ID,
        )

        db.get.assert_called_with(OwnerUser, OWNER_USER_ID)


# ============================================================
# list_notifications
# ============================================================

class TestListNotifications:
    @pytest.mark.asyncio
    async def test_returns_paginated_results(self):
        db = AsyncMock()
        notifications = [
            _make_notification(notification_type="rfi_assigned"),
            _make_notification(notification_type="punch_assigned"),
        ]

        # First execute: count query returns scalar
        # Second execute: data query returns scalars().all()
        count_result = MagicMock()
        count_result.scalar.return_value = 2

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = notifications

        db.execute.side_effect = [count_result, data_result]

        items, total = await list_notifications(db, "gc", ADMIN_USER_ID, page=1, per_page=25)

        assert total == 2
        assert len(items) == 2
        assert db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_unread_only_filters(self):
        db = AsyncMock()
        unread = [_make_notification(read_at=None)]

        count_result = MagicMock()
        count_result.scalar.return_value = 1

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = unread

        db.execute.side_effect = [count_result, data_result]

        items, total = await list_notifications(
            db, "gc", ADMIN_USER_ID, page=1, per_page=25, unread_only=True,
        )

        assert total == 1
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_empty_list(self):
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [count_result, data_result]

        items, total = await list_notifications(db, "gc", ADMIN_USER_ID)

        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_pagination_page_2(self):
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar.return_value = 30

        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = [_make_notification()] * 5

        db.execute.side_effect = [count_result, data_result]

        items, total = await list_notifications(
            db, "gc", ADMIN_USER_ID, page=2, per_page=25,
        )

        assert total == 30
        assert len(items) == 5


# ============================================================
# get_unread_count
# ============================================================

class TestGetUnreadCount:
    @pytest.mark.asyncio
    async def test_returns_correct_count(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = 7
        db.execute.return_value = result

        count = await get_unread_count(db, "gc", ADMIN_USER_ID)

        assert count == 7

    @pytest.mark.asyncio
    async def test_returns_zero_when_none(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = None
        db.execute.return_value = result

        count = await get_unread_count(db, "gc", ADMIN_USER_ID)

        assert count == 0

    @pytest.mark.asyncio
    async def test_sub_user_count(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar.return_value = 3
        db.execute.return_value = result

        count = await get_unread_count(db, "sub", SUB_USER_ID)

        assert count == 3


# ============================================================
# mark_read
# ============================================================

class TestMarkRead:
    @pytest.mark.asyncio
    async def test_sets_read_at_timestamp(self):
        db = AsyncMock()
        notif = _make_notification(notif_id=NOTIF_ID, user_id=ADMIN_USER_ID, read_at=None)

        result = MagicMock()
        result.scalar_one_or_none.return_value = notif
        db.execute.return_value = result

        returned = await mark_read(db, NOTIF_ID, "gc", ADMIN_USER_ID)

        assert returned.read_at is not None
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_404_for_wrong_user(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        other_user_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await mark_read(db, NOTIF_ID, "gc", other_user_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_for_nonexistent_notification(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        fake_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await mark_read(db, fake_id, "gc", ADMIN_USER_ID)

        assert exc_info.value.status_code == 404
        assert "Notification not found" in str(exc_info.value.detail)


# ============================================================
# mark_all_read
# ============================================================

class TestMarkAllRead:
    @pytest.mark.asyncio
    async def test_updates_all_unread(self):
        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 5
        db.execute.return_value = result

        count = await mark_all_read(db, "gc", ADMIN_USER_ID)

        assert count == 5
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_none_unread(self):
        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 0
        db.execute.return_value = result

        count = await mark_all_read(db, "gc", ADMIN_USER_ID)

        assert count == 0

    @pytest.mark.asyncio
    async def test_sub_user_mark_all(self):
        db = AsyncMock()
        result = MagicMock()
        result.rowcount = 12
        db.execute.return_value = result

        count = await mark_all_read(db, "sub", SUB_USER_ID)

        assert count == 12


# ============================================================
# dismiss_notification
# ============================================================

class TestDismissNotification:
    @pytest.mark.asyncio
    async def test_deletes_from_db(self):
        db = AsyncMock()
        notif = _make_notification(notif_id=NOTIF_ID, user_id=ADMIN_USER_ID)

        result = MagicMock()
        result.scalar_one_or_none.return_value = notif
        db.execute.return_value = result

        await dismiss_notification(db, NOTIF_ID, "gc", ADMIN_USER_ID)

        db.delete.assert_called_once_with(notif)
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_404_for_wrong_user(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        other_user_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await dismiss_notification(db, NOTIF_ID, "gc", other_user_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_404_for_nonexistent(self):
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        fake_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await dismiss_notification(db, fake_id, "gc", ADMIN_USER_ID)

        assert exc_info.value.status_code == 404


# ============================================================
# get_preferences
# ============================================================

class TestGetPreferences:
    @pytest.mark.asyncio
    async def test_returns_user_preferences(self):
        db = AsyncMock()
        custom_prefs = {
            "email_enabled": True,
            "email_categories": {
                "assigned_to_me": True,
                "status_changes": False,
                "mentions": True,
                "approaching_deadlines": False,
                "bid_invitations": True,
                "pay_app_decisions": True,
                "meeting_scheduled": True,
                "meeting_minutes": False,
                "daily_summary": False,
            },
        }
        recipient = _make_gc_recipient(preferences=custom_prefs)
        db.get.return_value = recipient

        result = await get_preferences(db, "gc", ADMIN_USER_ID)

        assert result == custom_prefs
        assert result["email_categories"]["status_changes"] is False

    @pytest.mark.asyncio
    async def test_returns_defaults_when_user_has_none(self):
        db = AsyncMock()
        recipient = _make_gc_recipient(preferences=None)
        db.get.return_value = recipient

        result = await get_preferences(db, "gc", ADMIN_USER_ID)

        assert result == DEFAULT_PREFERENCES

    @pytest.mark.asyncio
    async def test_returns_defaults_when_user_not_found(self):
        db = AsyncMock()
        db.get.return_value = None

        result = await get_preferences(db, "gc", uuid.uuid4())

        assert result == DEFAULT_PREFERENCES

    @pytest.mark.asyncio
    async def test_sub_user_preferences(self):
        db = AsyncMock()
        prefs = {"email_enabled": False, "email_categories": {}}
        recipient = _make_sub_recipient(preferences=prefs)
        db.get.return_value = recipient

        result = await get_preferences(db, "sub", SUB_USER_ID)

        assert result == prefs
        assert result["email_enabled"] is False


# ============================================================
# update_preferences
# ============================================================

class TestUpdatePreferences:
    @pytest.mark.asyncio
    async def test_saves_preferences(self):
        db = AsyncMock()
        recipient = _make_gc_recipient()
        db.get.return_value = recipient

        new_prefs = {
            "email_enabled": False,
            "email_categories": {"assigned_to_me": False},
        }

        result = await update_preferences(db, "gc", ADMIN_USER_ID, new_prefs)

        assert result == new_prefs
        assert recipient.notification_preferences == new_prefs
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_preferences_even_if_user_not_found(self):
        db = AsyncMock()
        db.get.return_value = None

        new_prefs = {"email_enabled": True, "email_categories": {}}

        result = await update_preferences(db, "gc", uuid.uuid4(), new_prefs)

        assert result == new_prefs

    @pytest.mark.asyncio
    async def test_sub_user_update(self):
        db = AsyncMock()
        recipient = _make_sub_recipient()
        db.get.return_value = recipient

        new_prefs = {
            "email_enabled": True,
            "email_categories": {"bid_invitations": True, "pay_app_decisions": False},
        }

        result = await update_preferences(db, "sub", SUB_USER_ID, new_prefs)

        assert recipient.notification_preferences == new_prefs
        assert result == new_prefs


# ============================================================
# format_notification_response
# ============================================================

class TestFormatNotificationResponse:
    def test_returns_correct_dict(self):
        source_id = uuid.uuid4()
        notif = _make_notification(
            notif_id=NOTIF_ID,
            notification_type="rfi_assigned",
            title="RFI Assigned",
            body="RFI-001 assigned to you.",
            source_type="rfi",
            source_id=source_id,
            project_id=PROJECT_ID,
            read_at=None,
            metadata_={"rfi_number": "RFI-001"},
            created_at=datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
        )

        result = format_notification_response(notif)

        assert result["id"] == str(NOTIF_ID)
        assert result["type"] == "rfi_assigned"
        assert result["title"] == "RFI Assigned"
        assert result["body"] == "RFI-001 assigned to you."
        assert result["source_type"] == "rfi"
        assert result["source_id"] == str(source_id)
        assert result["project_id"] == str(PROJECT_ID)
        assert result["metadata"] == {"rfi_number": "RFI-001"}
        assert result["read"] is False
        assert result["read_at"] is None
        assert result["created_at"] == "2026-02-26T12:00:00+00:00"

    def test_read_notification(self):
        read_time = datetime(2026, 2, 26, 14, 30, tzinfo=timezone.utc)
        notif = _make_notification(read_at=read_time)

        result = format_notification_response(notif)

        assert result["read"] is True
        assert result["read_at"] == "2026-02-26T14:30:00+00:00"

    def test_no_source(self):
        notif = _make_notification(source_type=None, source_id=None, project_id=None)
        notif.source_id = None
        notif.project_id = None

        result = format_notification_response(notif)

        assert result["source_id"] is None
        assert result["project_id"] is None

    def test_empty_metadata(self):
        notif = _make_notification(metadata_={})

        result = format_notification_response(notif)

        assert result["metadata"] == {}


# ============================================================
# _build_entity_link
# ============================================================

class TestBuildEntityLink:
    @patch("app.services.notification_service.settings")
    def test_gc_rfi_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("rfi", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/rfis/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_submittal_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("submittal", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/submittals/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_change_order_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("change_order", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/change-orders/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_pay_app_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("pay_app", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/pay-apps/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_punch_list_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("punch_list_item", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/punch-list/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_daily_log_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("daily_log", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/daily-logs/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_meeting_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("meeting", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/meetings/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_bid_package_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("bid_package", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/bid-packages/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_todo_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("todo", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/todos/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_inspection_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("inspection", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/inspections/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_schedule_delay_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("schedule_delay", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/schedule/delays"

    @patch("app.services.notification_service.settings")
    def test_gc_project_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("project", SOURCE_ID, PROJECT_ID, "gc")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}"

    @patch("app.services.notification_service.settings")
    def test_gc_organization_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("organization", SOURCE_ID, PROJECT_ID, "gc")
        assert result == "https://app.conflo.com/app/settings/billing"

    @patch("app.services.notification_service.settings")
    def test_sub_portal_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("rfi", SOURCE_ID, PROJECT_ID, "sub")
        assert result == f"https://app.conflo.com/sub/projects/{PROJECT_ID}/rfis/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_sub_portal_punch_list_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("punch_list_item", SOURCE_ID, PROJECT_ID, "sub")
        assert result == f"https://app.conflo.com/sub/projects/{PROJECT_ID}/punch-list/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_owner_portal_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("pay_app", SOURCE_ID, PROJECT_ID, "owner")
        assert result == f"https://app.conflo.com/owner/projects/{PROJECT_ID}/pay-apps/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_owner_portal_change_order_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("change_order", SOURCE_ID, PROJECT_ID, "owner")
        assert result == f"https://app.conflo.com/owner/projects/{PROJECT_ID}/change-orders/{SOURCE_ID}"

    @patch("app.services.notification_service.settings")
    def test_no_source_type_returns_notifications_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link(None, None, None, "gc")
        assert result == "https://app.conflo.com/app/notifications"

    @patch("app.services.notification_service.settings")
    def test_no_project_id_returns_notifications_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("rfi", SOURCE_ID, None, "gc")
        assert result == "https://app.conflo.com/app/notifications"

    @patch("app.services.notification_service.settings")
    def test_unknown_source_type_returns_notifications_link(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("unknown_entity", SOURCE_ID, PROJECT_ID, "gc")
        assert result == "https://app.conflo.com/app/notifications"

    @patch("app.services.notification_service.settings")
    def test_unknown_user_type_defaults_to_app_prefix(self, mock_settings):
        mock_settings.FRONTEND_URL = "https://app.conflo.com"
        result = _build_entity_link("rfi", SOURCE_ID, PROJECT_ID, "unknown")
        assert result == f"https://app.conflo.com/app/projects/{PROJECT_ID}/rfis/{SOURCE_ID}"


# ============================================================
# DEFAULT_PREFERENCES
# ============================================================

class TestDefaultPreferences:
    def test_email_enabled_by_default(self):
        assert DEFAULT_PREFERENCES["email_enabled"] is True

    def test_all_categories_present(self):
        expected_categories = [
            "assigned_to_me",
            "status_changes",
            "mentions",
            "approaching_deadlines",
            "bid_invitations",
            "pay_app_decisions",
            "meeting_scheduled",
            "meeting_minutes",
            "daily_summary",
        ]
        for cat in expected_categories:
            assert cat in DEFAULT_PREFERENCES["email_categories"]

    def test_daily_summary_disabled_by_default(self):
        assert DEFAULT_PREFERENCES["email_categories"]["daily_summary"] is False

    def test_most_categories_enabled_by_default(self):
        for cat, enabled in DEFAULT_PREFERENCES["email_categories"].items():
            if cat != "daily_summary":
                assert enabled is True, f"{cat} should be enabled by default"
