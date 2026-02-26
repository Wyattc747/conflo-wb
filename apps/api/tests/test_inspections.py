"""Tests for Inspection service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.inspection import Inspection
from app.models.inspection_template import InspectionTemplate
from app.schemas.inspection import (
    ChecklistItemCreate,
    ChecklistResult,
    InspectionCreate,
    InspectionResultSubmit,
    InspectionTemplateCreate,
    InspectionTemplateUpdate,
    InspectionUpdate,
)
from app.services.inspection_service import (
    complete_inspection,
    create_inspection,
    create_template,
    format_inspection_response,
    format_template_response,
    start_inspection,
    update_inspection,
    update_template,
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


def _make_template():
    t = MagicMock(spec=InspectionTemplate)
    t.id = uuid.uuid4()
    t.organization_id = ORG_ID
    t.name = "Concrete Pour Inspection"
    t.fields = [
        {"label": "Rebar placement correct", "required": True, "order": 0},
        {"label": "Forms aligned", "required": True, "order": 1},
        {"label": "Moisture check", "required": False, "order": 2},
    ]
    t.is_default = False
    t.created_at = datetime(2026, 2, 20, 10, 0)
    t.updated_at = datetime(2026, 2, 20, 10, 0)
    return t


def _make_inspection(status="SCHEDULED", number=1, template_id=None):
    insp = MagicMock(spec=Inspection)
    insp.id = uuid.uuid4()
    insp.organization_id = ORG_ID
    insp.project_id = PROJECT_ID
    insp.created_by = ADMIN_USER_ID
    insp.number = number
    insp.title = "Level 3 Concrete Pour"
    insp.template_id = template_id
    insp.category = "CONCRETE"
    insp.scheduled_date = datetime(2026, 3, 10)
    insp.scheduled_time = "09:00"
    insp.location = "Level 3, Grid B-4"
    insp.inspector_name = "Mike Inspector"
    insp.inspector_company = "City Building Dept"
    insp.form_data = {"checklist": []}
    insp.checklist_results = []
    insp.overall_result = None
    insp.photo_ids = []
    insp.notes = None
    insp.status = status
    insp.completed_date = None
    insp.created_at = datetime(2026, 2, 20, 10, 0)
    insp.updated_at = datetime(2026, 2, 20, 10, 0)
    insp.deleted_at = None
    return insp


# ============================================================
# Templates
# ============================================================

class TestCreateTemplate:
    @pytest.mark.asyncio
    async def test_create_with_checklist(self):
        db = AsyncMock()
        data = InspectionTemplateCreate(
            name="Concrete Pour Inspection",
            checklist_items=[
                ChecklistItemCreate(label="Rebar placement correct", required=True, order=0),
                ChecklistItemCreate(label="Forms aligned", required=True, order=1),
            ],
        )

        result = await create_template(db, ORG_ID, data)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        template_obj = db.add.call_args[0][0]
        assert template_obj.name == "Concrete Pour Inspection"
        assert len(template_obj.fields) == 2
        assert template_obj.fields[0]["label"] == "Rebar placement correct"


class TestUpdateTemplate:
    @pytest.mark.asyncio
    async def test_update_name(self):
        db = AsyncMock()
        template = _make_template()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = template
        db.execute.return_value = mock_result

        data = InspectionTemplateUpdate(name="Updated Template Name")
        result = await update_template(db, template.id, data)

        db.flush.assert_awaited_once()


class TestFormatTemplateResponse:
    def test_basic_format(self):
        template = _make_template()
        result = format_template_response(template)

        assert result["name"] == "Concrete Pour Inspection"
        assert len(result["checklist_items"]) == 3
        assert result["is_default"] is False


# ============================================================
# Inspections
# ============================================================

class TestCreateInspection:
    @pytest.mark.asyncio
    @patch("app.services.inspection_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = InspectionCreate(
            title="Level 3 Concrete Pour",
            category="CONCRETE",
            scheduled_date=date(2026, 3, 10),
            scheduled_time="09:00",
            location="Level 3, Grid B-4",
            inspector_name="Mike Inspector",
        )

        result = await create_inspection(db, PROJECT_ID, ORG_ID, user, data)

        # Inspection + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "inspection")

    @pytest.mark.asyncio
    @patch("app.services.inspection_service.get_next_number", new_callable=AsyncMock)
    @patch("app.services.inspection_service.get_template", new_callable=AsyncMock)
    async def test_create_from_template(self, mock_get_template, mock_next_number):
        mock_next_number.return_value = 2
        template = _make_template()
        mock_get_template.return_value = template

        db = AsyncMock()
        user = _make_user()
        data = InspectionCreate(
            template_id=template.id,
            scheduled_date=date(2026, 3, 12),
        )

        result = await create_inspection(db, PROJECT_ID, ORG_ID, user, data)

        # Title should come from template
        insp_obj = db.add.call_args_list[0][0][0]
        assert insp_obj.title == "Concrete Pour Inspection"
        assert insp_obj.form_data["checklist"] == template.fields

    @pytest.mark.asyncio
    @patch("app.services.inspection_service.get_next_number", new_callable=AsyncMock)
    async def test_create_minimal(self, mock_next_number):
        mock_next_number.return_value = 3

        db = AsyncMock()
        user = _make_user()
        data = InspectionCreate(title="Quick Inspection")

        await create_inspection(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2


# ============================================================
# start_inspection
# ============================================================

class TestStartInspection:
    @pytest.mark.asyncio
    async def test_start_scheduled(self):
        db = AsyncMock()
        inspection = _make_inspection(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        result = await start_inspection(db, inspection.id, PROJECT_ID, user)

        assert inspection.status == "IN_PROGRESS"
        # EventLog = 1
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_non_scheduled_raises_400(self):
        db = AsyncMock()
        inspection = _make_inspection(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await start_inspection(db, inspection.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# complete_inspection
# ============================================================

class TestCompleteInspection:
    @pytest.mark.asyncio
    async def test_complete_pass(self):
        db = AsyncMock()
        inspection = _make_inspection(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionResultSubmit(
            results=[
                ChecklistResult(item_label="Rebar placement correct", result="PASS"),
                ChecklistResult(item_label="Forms aligned", result="PASS"),
            ],
            overall_result="PASSED",
        )

        result = await complete_inspection(db, inspection.id, PROJECT_ID, user, data)

        assert inspection.status == "PASSED"
        assert inspection.overall_result == "PASSED"
        assert len(inspection.checklist_results) == 2
        assert inspection.completed_date is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_fail(self):
        db = AsyncMock()
        inspection = _make_inspection(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionResultSubmit(
            results=[
                ChecklistResult(item_label="Rebar placement correct", result="FAIL", notes="Spacing off"),
            ],
            overall_result="FAILED",
            notes="Critical rebar issues",
        )

        await complete_inspection(db, inspection.id, PROJECT_ID, user, data)

        assert inspection.status == "FAILED"
        assert inspection.overall_result == "FAILED"
        assert inspection.notes == "Critical rebar issues"

    @pytest.mark.asyncio
    async def test_complete_conditional(self):
        db = AsyncMock()
        inspection = _make_inspection(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionResultSubmit(
            results=[
                ChecklistResult(item_label="Rebar placement correct", result="PASS"),
                ChecklistResult(item_label="Moisture check", result="FAIL"),
            ],
            overall_result="CONDITIONAL",
        )

        await complete_inspection(db, inspection.id, PROJECT_ID, user, data)
        assert inspection.status == "CONDITIONAL"

    @pytest.mark.asyncio
    async def test_complete_already_completed_raises_400(self):
        db = AsyncMock()
        inspection = _make_inspection(status="PASSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionResultSubmit(
            results=[],
            overall_result="PASSED",
        )

        with pytest.raises(HTTPException) as exc_info:
            await complete_inspection(db, inspection.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_overall_result_raises_400(self):
        db = AsyncMock()
        inspection = _make_inspection(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionResultSubmit(
            results=[],
            overall_result="INVALID",
        )

        with pytest.raises(HTTPException) as exc_info:
            await complete_inspection(db, inspection.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# update_inspection
# ============================================================

class TestUpdateInspection:
    @pytest.mark.asyncio
    async def test_update_scheduled(self):
        db = AsyncMock()
        inspection = _make_inspection(status="SCHEDULED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionUpdate(location="Level 2, Grid A-1")

        result = await update_inspection(db, inspection.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_completed_raises_400(self):
        db = AsyncMock()
        inspection = _make_inspection(status="PASSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inspection
        db.execute.return_value = mock_result

        user = _make_user()
        data = InspectionUpdate(location="Can't update")

        with pytest.raises(HTTPException) as exc_info:
            await update_inspection(db, inspection.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# format_inspection_response
# ============================================================

class TestFormatInspectionResponse:
    def test_basic_format(self):
        inspection = _make_inspection(number=5)
        result = format_inspection_response(
            inspection,
            created_by_name="John Admin",
            template_name="Concrete Pour Inspection",
            comments_count=3,
        )

        assert result["number"] == 5
        assert result["formatted_number"] == "INSP-005"
        assert result["title"] == "Level 3 Concrete Pour"
        assert result["status"] == "SCHEDULED"
        assert result["category"] == "CONCRETE"
        assert result["inspector_name"] == "Mike Inspector"
        assert result["template_name"] == "Concrete Pour Inspection"
        assert result["created_by_name"] == "John Admin"
        assert result["comments_count"] == 3

    def test_numbering(self):
        assert format_number("inspection", 1) == "INSP-001"
        assert format_number("inspection", 42) == "INSP-042"
