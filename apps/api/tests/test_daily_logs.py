"""Tests for daily log service."""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.daily_log import DailyLog
from app.models.event_log import EventLog
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate
from app.services.daily_log_service import (
    _build_delays,
    approve_daily_log,
    create_daily_log,
    delete_daily_log,
    format_daily_log_response,
    get_daily_log,
    submit_daily_log,
    update_daily_log,
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


def _make_daily_log(
    status="DRAFT",
    log_date=None,
    created_by=ADMIN_USER_ID,
    weather_data=None,
    manpower=None,
    delays=None,
):
    log = MagicMock(spec=DailyLog)
    log.id = uuid.uuid4()
    log.organization_id = ORG_ID
    log.project_id = PROJECT_ID
    log.created_by = created_by
    log.log_date = log_date or datetime(2026, 2, 25)
    log.weather_data = weather_data or {"condition": "Sunny", "temp_high": 72}
    log.work_performed = "Concrete pour"
    log.manpower = manpower or [{"trade": "Concrete", "workers": 8, "hours": 64}]
    log.delays = delays or []
    log.status = status
    log.created_at = datetime(2026, 2, 25, 8, 0)
    log.updated_at = datetime(2026, 2, 25, 16, 0)
    return log


# ============================================================
# _build_delays
# ============================================================

class TestBuildDelays:
    def test_none_input(self):
        assert _build_delays(None) == []

    def test_empty_string(self):
        assert _build_delays("") == []

    def test_text_input(self):
        result = _build_delays("Rain delay - 4 hours")
        assert result == [{"description": "Rain delay - 4 hours"}]


# ============================================================
# create_daily_log
# ============================================================

class TestCreateDailyLog:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        # Mock the duplicate check to return None (no existing log)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = DailyLogCreate(
            log_date=date(2026, 2, 25),
            weather_condition="Sunny",
            temp_high=72.0,
            temp_low=45.0,
            work_performed="Concrete pour for footings",
            manpower=[{"trade": "Concrete", "workers": 8, "hours": 64}],
        )

        result = await create_daily_log(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count >= 2  # DailyLog + EventLog
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_date_raises_409(self):
        db = AsyncMock()
        existing_log = MagicMock(spec=DailyLog)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_log
        db.execute.return_value = mock_result

        user = _make_user()
        data = DailyLogCreate(log_date=date(2026, 2, 25))

        with pytest.raises(HTTPException) as exc_info:
            await create_daily_log(db, PROJECT_ID, ORG_ID, user, data)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_with_weather_data(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = DailyLogCreate(
            log_date=date(2026, 3, 1),
            weather_condition="Rain",
            temp_high=50.0,
            temp_low=35.0,
            precipitation=0.5,
            wind_speed=15.0,
            humidity=80.0,
        )

        await create_daily_log(db, PROJECT_ID, ORG_ID, user, data)
        # Verify something was added to db
        assert db.add.called


# ============================================================
# get_daily_log
# ============================================================

class TestGetDailyLog:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        log = _make_daily_log()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        result = await get_daily_log(db, log.id, PROJECT_ID)
        assert result == log

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_daily_log(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_daily_log
# ============================================================

class TestUpdateDailyLog:
    @pytest.mark.asyncio
    async def test_update_success(self):
        db = AsyncMock()
        log = _make_daily_log(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        data = DailyLogUpdate(work_performed="Updated work")

        result = await update_daily_log(db, log.id, PROJECT_ID, user, data)
        assert result == log
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_approved_raises_400(self):
        db = AsyncMock()
        log = _make_daily_log(status="APPROVED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        data = DailyLogUpdate(work_performed="Updated work")

        with pytest.raises(HTTPException) as exc_info:
            await update_daily_log(db, log.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# submit_daily_log
# ============================================================

class TestSubmitDailyLog:
    @pytest.mark.asyncio
    async def test_submit_draft(self):
        db = AsyncMock()
        log = _make_daily_log(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        result = await submit_daily_log(db, log.id, PROJECT_ID, user)

        assert log.status == "SUBMITTED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_non_draft_raises_400(self):
        db = AsyncMock()
        log = _make_daily_log(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_daily_log(db, log.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# approve_daily_log
# ============================================================

class TestApproveDailyLog:
    @pytest.mark.asyncio
    async def test_approve_submitted(self):
        db = AsyncMock()
        log = _make_daily_log(status="SUBMITTED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        result = await approve_daily_log(db, log.id, PROJECT_ID, user)

        assert log.status == "APPROVED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_non_submitted_raises_400(self):
        db = AsyncMock()
        log = _make_daily_log(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await approve_daily_log(db, log.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# delete_daily_log
# ============================================================

class TestDeleteDailyLog:
    @pytest.mark.asyncio
    async def test_delete_draft(self):
        db = AsyncMock()
        log = _make_daily_log(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        await delete_daily_log(db, log.id, PROJECT_ID)
        db.delete.assert_called_once_with(log)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_approved_raises_400(self):
        db = AsyncMock()
        log = _make_daily_log(status="APPROVED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = log
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await delete_daily_log(db, log.id, PROJECT_ID)
        assert exc_info.value.status_code == 400


# ============================================================
# format_daily_log_response
# ============================================================

class TestFormatDailyLogResponse:
    def test_basic_format(self):
        log = _make_daily_log()
        result = format_daily_log_response(log, created_by_name="John Smith")

        assert result["id"] == log.id
        assert result["project_id"] == PROJECT_ID
        assert result["status"] == "DRAFT"
        assert result["created_by_name"] == "John Smith"
        assert result["weather_data"] == log.weather_data
        assert result["manpower"] == log.manpower

    def test_delays_text_extraction(self):
        log = _make_daily_log(delays=[{"description": "Rain delay"}])
        result = format_daily_log_response(log)
        assert result["delays_text"] == "Rain delay"

    def test_no_delays(self):
        log = _make_daily_log(delays=[])
        result = format_daily_log_response(log)
        assert result["delays_text"] is None

    def test_date_conversion(self):
        log = _make_daily_log()
        log.log_date = datetime(2026, 2, 25, 0, 0)
        result = format_daily_log_response(log)
        assert result["log_date"] == date(2026, 2, 25)
        assert "DL-" in result["number"]
