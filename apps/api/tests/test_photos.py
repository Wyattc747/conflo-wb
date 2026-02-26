"""Tests for Photo service."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoUpdate
from app.services.photo_service import (
    create_photo,
    delete_photo,
    format_photo_response,
    get_photo,
    update_photo,
)
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


def _make_photo(
    caption="Concrete pour Level 3",
    location="Building A - Level 3",
    linked_type=None,
    linked_id=None,
):
    photo = MagicMock(spec=Photo)
    photo.id = uuid.uuid4()
    photo.organization_id = ORG_ID
    photo.project_id = PROJECT_ID
    photo.file_id = uuid.uuid4()
    photo.caption = caption
    photo.tags = ["concrete", "level3"]
    photo.location = location
    photo.latitude = Decimal("39.7392358")
    photo.longitude = Decimal("-104.9903305")
    photo.linked_type = linked_type
    photo.linked_id = linked_id
    photo.uploaded_by = ADMIN_USER_ID
    photo.captured_at = datetime(2026, 2, 20, 14, 30, tzinfo=timezone.utc)
    photo.device_info = "iPhone 15 Pro"
    photo.created_at = datetime(2026, 2, 20, 15, 0, tzinfo=timezone.utc)
    photo.deleted_at = None
    return photo


# ============================================================
# create_photo
# ============================================================

class TestCreatePhoto:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        file_id = uuid.uuid4()
        data = PhotoCreate(
            file_id=file_id,
            caption="Concrete pour Level 3",
            tags=["concrete", "level3"],
            location="Building A - Level 3",
            latitude=39.7392358,
            longitude=-104.9903305,
        )

        result = await create_photo(db, PROJECT_ID, ORG_ID, user, data)

        # Photo + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal(self):
        db = AsyncMock()
        user = _make_user()
        data = PhotoCreate()

        result = await create_photo(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_linked_entity(self):
        db = AsyncMock()
        user = _make_user()
        punch_id = uuid.uuid4()
        data = PhotoCreate(
            file_id=uuid.uuid4(),
            linked_type="punch_list_item",
            linked_id=punch_id,
            caption="Before photo",
        )

        result = await create_photo(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_photo
# ============================================================

class TestGetPhoto:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        photo = _make_photo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = photo
        db.execute.return_value = mock_result

        result = await get_photo(db, photo.id, PROJECT_ID)
        assert result == photo

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_photo(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_photo
# ============================================================

class TestUpdatePhoto:
    @pytest.mark.asyncio
    async def test_update_caption(self):
        db = AsyncMock()
        photo = _make_photo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = photo
        db.execute.return_value = mock_result

        user = _make_user()
        data = PhotoUpdate(caption="Updated caption - Level 3 rebar")

        result = await update_photo(db, photo.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_tags(self):
        db = AsyncMock()
        photo = _make_photo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = photo
        db.execute.return_value = mock_result

        user = _make_user()
        data = PhotoUpdate(tags=["rebar", "structural", "level3"])

        result = await update_photo(db, photo.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_location(self):
        db = AsyncMock()
        photo = _make_photo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = photo
        db.execute.return_value = mock_result

        user = _make_user()
        data = PhotoUpdate(location="Building B - Roof")

        result = await update_photo(db, photo.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = PhotoUpdate(caption="New caption")

        with pytest.raises(HTTPException) as exc_info:
            await update_photo(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# delete_photo
# ============================================================

class TestDeletePhoto:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        db = AsyncMock()
        photo = _make_photo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = photo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_photo(db, photo.id, PROJECT_ID, user)

        assert photo.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_photo(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# format_photo_response
# ============================================================

class TestFormatPhotoResponse:
    def test_basic_format(self):
        photo = _make_photo()
        result = format_photo_response(
            photo,
            uploaded_by_name="John Smith",
        )

        assert result["id"] == photo.id
        assert result["project_id"] == PROJECT_ID
        assert result["file_id"] == photo.file_id
        assert result["caption"] == "Concrete pour Level 3"
        assert result["tags"] == ["concrete", "level3"]
        assert result["location"] == "Building A - Level 3"
        assert result["latitude"] == Decimal("39.7392358")
        assert result["longitude"] == Decimal("-104.9903305")
        assert result["uploaded_by"] == ADMIN_USER_ID
        assert result["uploaded_by_name"] == "John Smith"
        assert result["captured_at"] is not None
        assert result["created_at"] is not None

    def test_format_without_name(self):
        photo = _make_photo()
        result = format_photo_response(photo)

        assert result["uploaded_by_name"] is None
        assert result["id"] == photo.id

    def test_format_with_empty_tags(self):
        photo = _make_photo()
        photo.tags = None
        result = format_photo_response(photo)

        assert result["tags"] == []

    def test_format_with_linked_entity(self):
        linked_id = uuid.uuid4()
        photo = _make_photo(linked_type="daily_log", linked_id=linked_id)
        result = format_photo_response(photo)

        assert result["linked_type"] == "daily_log"
        assert result["linked_id"] == linked_id
