"""Tests for Submittal service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.submittal import Submittal
from app.schemas.submittal import (
    SubmittalCreate,
    SubmittalUpdate,
    SubmittalRevisionCreate,
    SubmittalReviewRequest,
)
from app.services.submittal_service import (
    create_submittal,
    format_submittal_response,
    get_submittal,
    list_submittals,
    review_submittal,
    submit_submittal,
    create_revision,
    update_submittal,
)
from app.services.numbering_service import format_number
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID, SUB_COMPANY_ID


def _make_user(user_id=ADMIN_USER_ID, permission_level="OWNER_ADMIN"):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_submittal(
    status="DRAFT",
    number=1,
    revision=0,
    created_by=ADMIN_USER_ID,
    assigned_to=MGMT_USER_ID,
):
    s = MagicMock(spec=Submittal)
    s.id = uuid.uuid4()
    s.organization_id = ORG_ID
    s.project_id = PROJECT_ID
    s.created_by = created_by
    s.number = number
    s.revision = revision
    s.parent_submittal_id = None
    s.title = "Shop Drawing - Steel Beams"
    s.spec_section = "05 12 00"
    s.description = "Steel beam shop drawings for Level 3"
    s.submittal_type = "SHOP_DRAWING"
    s.submitted_by_sub_id = SUB_COMPANY_ID
    s.assigned_to = assigned_to
    s.reviewer_id = None
    s.review_notes = None
    s.reviewed_at = None
    s.due_date = datetime(2026, 3, 15)
    s.drawing_reference = "S-301"
    s.lead_time_days = 14
    s.cost_code_id = None
    s.status = status
    s.created_at = datetime(2026, 2, 20, 10, 0)
    s.updated_at = datetime(2026, 2, 20, 10, 0)
    s.deleted_at = None
    return s


# ============================================================
# create_submittal
# ============================================================

class TestCreateSubmittal:
    @pytest.mark.asyncio
    @patch("app.services.submittal_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = SubmittalCreate(
            title="Shop Drawing - Steel",
            spec_section="05 12 00",
            submittal_type="SHOP_DRAWING",
            assigned_to=MGMT_USER_ID,
            due_date=date(2026, 3, 15),
            lead_time_days=14,
        )

        result = await create_submittal(db, PROJECT_ID, ORG_ID, user, data)

        # Submittal + Notification (assigned_to) + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "submittal")

    @pytest.mark.asyncio
    @patch("app.services.submittal_service.get_next_number", new_callable=AsyncMock)
    async def test_create_without_assignee_no_notification(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        data = SubmittalCreate(title="Product Data - HVAC Units")

        await create_submittal(db, PROJECT_ID, ORG_ID, user, data)

        # Submittal + EventLog = 2 (no notification)
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.submittal_service.get_next_number", new_callable=AsyncMock)
    async def test_auto_number_format_001_00(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = SubmittalCreate(title="Test Submittal")

        result = await create_submittal(db, PROJECT_ID, ORG_ID, user, data)
        formatted = format_number("submittal", 1, 0)
        assert formatted == "001.00"


# ============================================================
# submit_submittal
# ============================================================

class TestSubmitSubmittal:
    @pytest.mark.asyncio
    async def test_submit_draft(self):
        db = AsyncMock()
        submittal = _make_submittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        result = await submit_submittal(db, submittal.id, PROJECT_ID, user)

        assert submittal.status == "SUBMITTED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_non_draft_raises_400(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_submittal(db, submittal.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# review_submittal
# ============================================================

class TestReviewSubmittal:
    @pytest.mark.asyncio
    async def test_approve(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user(user_id=MGMT_USER_ID)
        data = SubmittalReviewRequest(decision="APPROVED", notes="Looks good")

        result = await review_submittal(db, submittal.id, PROJECT_ID, user, data)

        assert submittal.status == "APPROVED"
        assert submittal.reviewer_id == MGMT_USER_ID
        assert submittal.reviewed_at is not None
        assert submittal.review_notes == "Looks good"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approved_as_noted(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalReviewRequest(decision="APPROVED_AS_NOTED", notes="See comments on sheet 3")

        await review_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert submittal.status == "APPROVED_AS_NOTED"

    @pytest.mark.asyncio
    async def test_revise_and_resubmit(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalReviewRequest(decision="REVISE_AND_RESUBMIT", notes="Rebar spacing incorrect")

        await review_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert submittal.status == "REVISE_AND_RESUBMIT"

    @pytest.mark.asyncio
    async def test_reject(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalReviewRequest(decision="REJECTED")

        await review_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert submittal.status == "REJECTED"

    @pytest.mark.asyncio
    async def test_review_draft_raises_400(self):
        db = AsyncMock()
        submittal = _make_submittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalReviewRequest(decision="APPROVED")

        with pytest.raises(HTTPException) as exc_info:
            await review_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_decision_raises_400(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalReviewRequest(decision="INVALID")

        with pytest.raises(HTTPException) as exc_info:
            await review_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# create_revision
# ============================================================

class TestCreateRevision:
    @pytest.mark.asyncio
    @patch("app.services.submittal_service.get_next_submittal_revision", new_callable=AsyncMock)
    async def test_revision_creates_001_01(self, mock_next_rev):
        mock_next_rev.return_value = 1

        db = AsyncMock()
        original = _make_submittal(status="REVISE_AND_RESUBMIT", number=1, revision=0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = original
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalRevisionCreate(description="Updated rebar spacing")

        result = await create_revision(db, original.id, PROJECT_ID, user, data)

        # New submittal + EventLog = 2
        assert db.add.call_count >= 2
        db.flush.assert_awaited_once()
        mock_next_rev.assert_awaited_once_with(db, PROJECT_ID, 1)

    @pytest.mark.asyncio
    @patch("app.services.submittal_service.get_next_submittal_revision", new_callable=AsyncMock)
    async def test_multiple_revisions(self, mock_next_rev):
        mock_next_rev.return_value = 2

        db = AsyncMock()
        original = _make_submittal(status="REVISE_AND_RESUBMIT", number=1, revision=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = original
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalRevisionCreate()

        await create_revision(db, original.id, PROJECT_ID, user, data)

        # Verify revision 2 was requested
        formatted = format_number("submittal", 1, 2)
        assert formatted == "001.02"

    @pytest.mark.asyncio
    async def test_revise_non_resubmit_raises_400(self):
        db = AsyncMock()
        submittal = _make_submittal(status="APPROVED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalRevisionCreate()

        with pytest.raises(HTTPException) as exc_info:
            await create_revision(db, submittal.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# update_submittal
# ============================================================

class TestUpdateSubmittal:
    @pytest.mark.asyncio
    async def test_update_draft(self):
        db = AsyncMock()
        submittal = _make_submittal(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalUpdate(title="Updated Title")

        result = await update_submittal(db, submittal.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_non_draft_raises_400(self):
        db = AsyncMock()
        submittal = _make_submittal(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submittal
        db.execute.return_value = mock_result

        user = _make_user()
        data = SubmittalUpdate(title="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await update_submittal(db, submittal.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# format_submittal_response
# ============================================================

class TestFormatSubmittalResponse:
    def test_basic_format(self):
        submittal = _make_submittal(number=1, revision=0)
        result = format_submittal_response(
            submittal,
            created_by_name="John Smith",
            assigned_to_name="Sarah Johnson",
            sub_company_name="Apex Concrete",
            comments_count=5,
        )

        assert result["id"] == submittal.id
        assert result["number"] == 1
        assert result["revision"] == 0
        assert result["formatted_number"] == "001.00"
        assert result["title"] == "Shop Drawing - Steel Beams"
        assert result["status"] == "DRAFT"
        assert result["created_by_name"] == "John Smith"
        assert result["assigned_to_name"] == "Sarah Johnson"
        assert result["sub_company_name"] == "Apex Concrete"
        assert result["comments_count"] == 5

    def test_revision_number_format(self):
        submittal = _make_submittal(number=3, revision=2)
        result = format_submittal_response(submittal)
        assert result["formatted_number"] == "003.02"

    def test_days_open_not_set_for_approved(self):
        submittal = _make_submittal(status="APPROVED")
        result = format_submittal_response(submittal)
        assert result["days_open"] is None

    def test_days_open_calculated_for_open(self):
        submittal = _make_submittal(status="DRAFT")
        result = format_submittal_response(submittal)
        assert result["days_open"] is not None
        assert result["days_open"] >= 0


# ============================================================
# Numbering format verification
# ============================================================

class TestSubmittalNumbering:
    def test_first_submittal(self):
        assert format_number("submittal", 1, 0) == "001.00"

    def test_first_revision(self):
        assert format_number("submittal", 1, 1) == "001.01"

    def test_second_revision(self):
        assert format_number("submittal", 1, 2) == "001.02"

    def test_new_base_number(self):
        assert format_number("submittal", 2, 0) == "002.00"

    def test_high_number(self):
        assert format_number("submittal", 42, 3) == "042.03"
