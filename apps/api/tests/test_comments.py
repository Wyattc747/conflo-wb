"""Tests for comment service."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.comment import Comment
from app.models.notification import Notification
from app.models.event_log import EventLog
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.comment_service import (
    VALID_COMMENTABLE_TYPES,
    create_comment,
    delete_comment,
    format_comment_response,
    get_comment,
    update_comment,
)
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID


# ============================================================
# HELPERS
# ============================================================

def _make_user(user_id=ADMIN_USER_ID):
    return {
        "user_type": "GC_USER",
        "user_id": user_id,
        "organization_id": ORG_ID,
    }


def _make_comment(author_id=ADMIN_USER_ID, body="Test comment"):
    comment = MagicMock(spec=Comment)
    comment.id = uuid.uuid4()
    comment.organization_id = ORG_ID
    comment.commentable_type = "rfi"
    comment.commentable_id = uuid.uuid4()
    comment.author_type = "GC_USER"
    comment.author_id = author_id
    comment.body = body
    comment.is_official_response = False
    comment.mentioned_user_ids = []
    comment.attachment_ids = []
    comment.created_at = datetime(2026, 2, 25, 10, 0)
    comment.updated_at = datetime(2026, 2, 25, 10, 0)
    return comment


# ============================================================
# VALID_COMMENTABLE_TYPES
# ============================================================

class TestValidCommentableTypes:
    def test_contains_core_types(self):
        assert "rfi" in VALID_COMMENTABLE_TYPES
        assert "daily_log" in VALID_COMMENTABLE_TYPES
        assert "submittal" in VALID_COMMENTABLE_TYPES
        assert "transmittal" in VALID_COMMENTABLE_TYPES
        assert "change_order" in VALID_COMMENTABLE_TYPES
        assert "punch_list_item" in VALID_COMMENTABLE_TYPES
        assert "inspection" in VALID_COMMENTABLE_TYPES
        assert "pay_app" in VALID_COMMENTABLE_TYPES
        assert "meeting" in VALID_COMMENTABLE_TYPES

    def test_no_invalid_types(self):
        assert "project" not in VALID_COMMENTABLE_TYPES
        assert "user" not in VALID_COMMENTABLE_TYPES


# ============================================================
# create_comment
# ============================================================

class TestCreateComment:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        commentable_id = uuid.uuid4()
        data = CommentCreate(
            commentable_type="rfi",
            commentable_id=commentable_id,
            body="This is a test comment.",
            mentions=[],
            attachments=[],
        )

        result = await create_comment(db, ORG_ID, PROJECT_ID, user, data)

        # Comment + EventLog = 2 adds
        assert db.add.call_count >= 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_mentions_notifies(self):
        db = AsyncMock()
        user = _make_user()
        mentioned_id = uuid.uuid4()
        data = CommentCreate(
            commentable_type="rfi",
            commentable_id=uuid.uuid4(),
            body="Hey @someone check this out",
            mentions=[mentioned_id],
            attachments=[],
        )

        await create_comment(db, ORG_ID, PROJECT_ID, user, data)

        # Comment + Notification + EventLog = 3 adds
        assert db.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_create_invalid_type_raises_400(self):
        db = AsyncMock()
        user = _make_user()
        data = CommentCreate(
            commentable_type="invalid_type",
            commentable_id=uuid.uuid4(),
            body="Test",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_comment(db, ORG_ID, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_multiple_mentions(self):
        db = AsyncMock()
        user = _make_user()
        mention1 = uuid.uuid4()
        mention2 = uuid.uuid4()
        data = CommentCreate(
            commentable_type="daily_log",
            commentable_id=uuid.uuid4(),
            body="Tagging two people",
            mentions=[mention1, mention2],
        )

        await create_comment(db, ORG_ID, PROJECT_ID, user, data)

        # Comment + 2 Notifications + EventLog = 4 adds
        assert db.add.call_count >= 4


# ============================================================
# get_comment
# ============================================================

class TestGetComment:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        comment = _make_comment()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_result

        result = await get_comment(db, comment.id)
        assert result == comment

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_comment(db, uuid.uuid4())
        assert exc_info.value.status_code == 404


# ============================================================
# update_comment
# ============================================================

class TestUpdateComment:
    @pytest.mark.asyncio
    async def test_update_own_comment(self):
        db = AsyncMock()
        comment = _make_comment(author_id=ADMIN_USER_ID)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_result

        user = _make_user(user_id=ADMIN_USER_ID)
        data = CommentUpdate(body="Updated comment body")

        result = await update_comment(db, comment.id, user, data)
        assert comment.body == "Updated comment body"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_others_comment_raises_403(self):
        db = AsyncMock()
        other_user_id = uuid.uuid4()
        comment = _make_comment(author_id=other_user_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_result

        user = _make_user(user_id=ADMIN_USER_ID)
        data = CommentUpdate(body="Trying to edit someone else's comment")

        with pytest.raises(HTTPException) as exc_info:
            await update_comment(db, comment.id, user, data)
        assert exc_info.value.status_code == 403


# ============================================================
# delete_comment
# ============================================================

class TestDeleteComment:
    @pytest.mark.asyncio
    async def test_delete_own_comment(self):
        db = AsyncMock()
        comment = _make_comment(author_id=ADMIN_USER_ID)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_result

        user = _make_user(user_id=ADMIN_USER_ID)
        await delete_comment(db, comment.id, user)

        db.delete.assert_called_once_with(comment)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_others_comment_raises_403(self):
        db = AsyncMock()
        other_user_id = uuid.uuid4()
        comment = _make_comment(author_id=other_user_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = comment
        db.execute.return_value = mock_result

        user = _make_user(user_id=ADMIN_USER_ID)
        with pytest.raises(HTTPException) as exc_info:
            await delete_comment(db, comment.id, user)
        assert exc_info.value.status_code == 403


# ============================================================
# format_comment_response
# ============================================================

class TestFormatCommentResponse:
    def test_basic_format(self):
        comment = _make_comment(body="Hello world")
        result = format_comment_response(comment, author_name="John Smith")

        assert result["id"] == comment.id
        assert result["body"] == "Hello world"
        assert result["author_name"] == "John Smith"
        assert result["author_type"] == "GC_USER"
        assert result["is_official_response"] is False
        assert result["mentions"] == []
        assert result["attachments"] == []
        assert "created_at" in result
        assert "updated_at" in result

    def test_format_without_author_name(self):
        comment = _make_comment()
        result = format_comment_response(comment)
        assert result["author_name"] is None
