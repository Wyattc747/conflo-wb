"""Tests for Drawing service."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.drawing import Drawing, DrawingSheet
from app.schemas.drawing import DrawingSetCreate, DrawingSetUpdate, DrawingSheetCreate
from app.services.drawing_service import (
    create_set,
    get_set,
    update_set,
    delete_set,
    mark_current_set,
    add_sheet,
    upload_revision,
    format_drawing_set_response,
    format_sheet_response,
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


def _make_drawing(
    is_current_set=True,
    set_number="A",
    title="Structural Drawings",
    discipline="Structural",
):
    drawing = MagicMock(spec=Drawing)
    drawing.id = uuid.uuid4()
    drawing.organization_id = ORG_ID
    drawing.project_id = PROJECT_ID
    drawing.created_by = ADMIN_USER_ID
    drawing.set_number = set_number
    drawing.title = title
    drawing.discipline = discipline
    drawing.description = "Structural drawing set for Level 3"
    drawing.received_from = "Smith Engineering"
    drawing.is_current_set = is_current_set
    drawing.received_date = None
    drawing.created_at = datetime(2026, 2, 20, 10, 0)
    drawing.updated_at = datetime(2026, 2, 20, 10, 0)
    drawing.deleted_at = None
    return drawing


def _make_sheet(
    drawing_id=None,
    sheet_number="S-301",
    revision="0",
    is_current=True,
):
    sheet = MagicMock(spec=DrawingSheet)
    sheet.id = uuid.uuid4()
    sheet.drawing_id = drawing_id or uuid.uuid4()
    sheet.sheet_number = sheet_number
    sheet.title = "Foundation Plan"
    sheet.description = "Foundation plan Level 1"
    sheet.revision = revision
    sheet.revision_date = None
    sheet.is_current = is_current
    sheet.file_id = uuid.uuid4()
    sheet.uploaded_by = ADMIN_USER_ID
    sheet.created_at = datetime(2026, 2, 20, 10, 0)
    sheet.updated_at = datetime(2026, 2, 20, 10, 0)
    return sheet


# ============================================================
# create_set
# ============================================================

class TestCreateSet:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        data = DrawingSetCreate(
            set_number="A",
            title="Structural Drawings",
            discipline="Structural",
            description="Main structural set",
            received_from="Smith Engineering",
        )

        result = await create_set(db, PROJECT_ID, ORG_ID, user, data)

        # Drawing + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal(self):
        db = AsyncMock()
        user = _make_user()
        data = DrawingSetCreate(
            set_number="B",
            title="Architectural Drawings",
        )

        result = await create_set(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_set
# ============================================================

class TestGetSet:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        drawing = _make_drawing()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = drawing
        db.execute.return_value = mock_result

        result = await get_set(db, drawing.id, PROJECT_ID)
        assert result == drawing

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_set(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_set
# ============================================================

class TestUpdateSet:
    @pytest.mark.asyncio
    async def test_update_title(self):
        db = AsyncMock()
        drawing = _make_drawing()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = drawing
        db.execute.return_value = mock_result

        user = _make_user()
        data = DrawingSetUpdate(title="Updated Title")

        result = await update_set(db, drawing.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self):
        db = AsyncMock()
        drawing = _make_drawing()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = drawing
        db.execute.return_value = mock_result

        user = _make_user()
        data = DrawingSetUpdate(
            title="Revised Structural Set",
            discipline="Architecture",
            description="Updated description",
        )

        result = await update_set(db, drawing.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = DrawingSetUpdate(title="Won't work")

        with pytest.raises(HTTPException) as exc_info:
            await update_set(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# delete_set
# ============================================================

class TestDeleteSet:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        db = AsyncMock()
        drawing = _make_drawing()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = drawing
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_set(db, drawing.id, PROJECT_ID, user)

        assert drawing.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_set(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# mark_current_set
# ============================================================

class TestMarkCurrentSet:
    @pytest.mark.asyncio
    async def test_mark_current(self):
        db = AsyncMock()
        drawing = _make_drawing(is_current_set=False)

        # First call: get_set lookup
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = drawing

        # Second call: find all sets with same set_number
        other_drawing = _make_drawing(is_current_set=True, set_number=drawing.set_number)
        mock_siblings_result = MagicMock()
        mock_siblings_result.scalars.return_value.all.return_value = [other_drawing, drawing]

        db.execute.side_effect = [mock_get_result, mock_siblings_result]

        user = _make_user()
        result = await mark_current_set(db, drawing.id, PROJECT_ID, user)

        # Other drawing should be unmarked
        assert other_drawing.is_current_set is False
        # Target drawing should be marked current
        assert drawing.is_current_set is True
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_current_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await mark_current_set(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# add_sheet
# ============================================================

class TestAddSheet:
    @pytest.mark.asyncio
    async def test_add_sheet_success(self):
        db = AsyncMock()
        drawing = _make_drawing()
        user = _make_user()
        file_id = uuid.uuid4()
        data = DrawingSheetCreate(
            sheet_number="S-301",
            title="Foundation Plan",
            description="Foundation plan Level 1",
            revision="0",
            file_id=file_id,
        )

        result = await add_sheet(db, drawing.id, user, data)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_sheet_minimal(self):
        db = AsyncMock()
        drawing = _make_drawing()
        user = _make_user()
        data = DrawingSheetCreate(sheet_number="A-101")

        result = await add_sheet(db, drawing.id, user, data)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()


# ============================================================
# upload_revision (revise_sheet)
# ============================================================

class TestUploadRevision:
    @pytest.mark.asyncio
    async def test_revision_creates_new_sheet(self):
        db = AsyncMock()
        old_sheet = _make_sheet(revision="A", is_current=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = old_sheet
        db.execute.return_value = mock_result

        user = _make_user()
        new_file_id = uuid.uuid4()

        result = await upload_revision(db, old_sheet.id, user, "B", file_id=new_file_id)

        # Old sheet should be marked not current
        assert old_sheet.is_current is False
        # New sheet added
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revision_without_new_file(self):
        db = AsyncMock()
        old_sheet = _make_sheet(revision="0", is_current=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = old_sheet
        db.execute.return_value = mock_result

        user = _make_user()

        result = await upload_revision(db, old_sheet.id, user, "1")

        assert old_sheet.is_current is False
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revision_sheet_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await upload_revision(db, uuid.uuid4(), user, "B")
        assert exc_info.value.status_code == 404


# ============================================================
# format_drawing_set_response
# ============================================================

class TestFormatDrawingSetResponse:
    @pytest.mark.asyncio
    async def test_basic_format(self):
        db = AsyncMock()
        drawing = _make_drawing()
        sheet1 = _make_sheet(drawing_id=drawing.id, sheet_number="S-301")
        sheet2 = _make_sheet(drawing_id=drawing.id, sheet_number="S-302")

        # Mock list_sheets (called internally via db.execute)
        mock_sheets_result = MagicMock()
        mock_sheets_result.scalars.return_value.all.return_value = [sheet1, sheet2]
        db.execute.return_value = mock_sheets_result

        result = await format_drawing_set_response(
            db,
            drawing,
            created_by_name="John Smith",
        )

        assert result["id"] == drawing.id
        assert result["project_id"] == PROJECT_ID
        assert result["set_number"] == "A"
        assert result["title"] == "Structural Drawings"
        assert result["discipline"] == "Structural"
        assert result["is_current_set"] is True
        assert result["sheet_count"] == 2
        assert len(result["sheets"]) == 2
        assert result["created_by_name"] == "John Smith"
        assert result["created_at"] == drawing.created_at

    @pytest.mark.asyncio
    async def test_format_no_sheets(self):
        db = AsyncMock()
        drawing = _make_drawing()

        mock_sheets_result = MagicMock()
        mock_sheets_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_sheets_result

        result = await format_drawing_set_response(db, drawing)

        assert result["sheet_count"] == 0
        assert result["sheets"] == []
        assert result["created_by_name"] is None


# ============================================================
# format_sheet_response
# ============================================================

class TestFormatSheetResponse:
    def test_basic_format(self):
        sheet = _make_sheet(sheet_number="S-301", revision="A")
        result = format_sheet_response(sheet)

        assert result["id"] == sheet.id
        assert result["drawing_id"] == sheet.drawing_id
        assert result["sheet_number"] == "S-301"
        assert result["title"] == "Foundation Plan"
        assert result["revision"] == "A"
        assert result["is_current"] is True
        assert result["file_id"] == sheet.file_id
        assert result["uploaded_by"] == ADMIN_USER_ID
