"""Tests for Schedule service — Tasks, Dependencies, Delays, Versions, Config, Health."""
import uuid
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from fastapi import HTTPException

from app.models.schedule_task import ScheduleTask
from app.models.schedule_dependency import ScheduleDependency
from app.models.schedule_delay import ScheduleDelay
from app.models.schedule_version import ScheduleVersion
from app.models.schedule_config import ScheduleConfig
from app.schemas.schedule import (
    DependencyCreate,
    ScheduleConfigUpdate,
    ScheduleDelayCreate,
    SchedulePublishRequest,
    ScheduleTaskCreate,
    ScheduleTaskUpdate,
)
from app.services.schedule_service import (
    DELAY_TIER_IMPACTS,
    apply_delay,
    approve_delay,
    calculate_schedule_health,
    create_delay,
    create_task,
    derive_tier_dates,
    format_config_response,
    format_delay_response,
    format_task_response,
    format_version_response,
    lock_baseline,
    publish_schedule,
    reject_delay,
)
from tests.conftest import (
    ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID,
    SUB_COMPANY_ID,
)


def _make_user(user_id=ADMIN_USER_ID):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": "OWNER_ADMIN",
    }


def _make_task(
    name="Foundation Pour",
    start_date=datetime(2026, 3, 1),
    end_date=datetime(2026, 3, 11),
    duration=10,
    is_critical=False,
    milestone=False,
    percent_complete=0,
    baseline_start=None,
    baseline_end=None,
    baseline_duration=None,
    owner_start_date=None,
    owner_end_date=None,
    sub_start_date=None,
    sub_end_date=None,
):
    task = MagicMock(spec=ScheduleTask)
    task.id = uuid.uuid4()
    task.organization_id = ORG_ID
    task.project_id = PROJECT_ID
    task.created_by = ADMIN_USER_ID
    task.name = name
    task.description = None
    task.wbs_code = None
    task.parent_task_id = None
    task.sort_order = 0
    task.start_date = start_date
    task.end_date = end_date
    task.duration = duration
    task.baseline_start = baseline_start
    task.baseline_end = baseline_end
    task.baseline_duration = baseline_duration
    task.owner_start_date = owner_start_date
    task.owner_end_date = owner_end_date
    task.sub_start_date = sub_start_date
    task.sub_end_date = sub_end_date
    task.percent_complete = percent_complete
    task.actual_start = None
    task.actual_end = None
    task.assigned_to = None
    task.assigned_to_sub_id = SUB_COMPANY_ID
    task.milestone = milestone
    task.is_critical = is_critical
    task.cost_code_id = None
    task.predecessors = []
    task.created_at = datetime(2026, 2, 20, 10, 0)
    task.updated_at = datetime(2026, 2, 20, 10, 0)
    task.deleted_at = None
    return task


def _make_config(
    schedule_mode="SINGLE",
    derivation_method="PERCENTAGE",
    owner_buffer=10,
    sub_compress=15,
    on_track=5,
    at_risk=15,
):
    config = MagicMock(spec=ScheduleConfig)
    config.id = uuid.uuid4()
    config.project_id = PROJECT_ID
    config.organization_id = ORG_ID
    config.schedule_mode = schedule_mode
    config.derivation_method = derivation_method
    config.owner_buffer_percent = owner_buffer
    config.sub_compress_percent = sub_compress
    config.health_on_track_max_days = on_track
    config.health_at_risk_max_days = at_risk
    config.sub_notify_intervals = [14, 7, 1]
    return config


def _make_delay(
    status="PENDING",
    reason="WEATHER",
    delay_days=3,
    task_ids=None,
    impacts_owner=False,
):
    delay = MagicMock(spec=ScheduleDelay)
    delay.id = uuid.uuid4()
    delay.organization_id = ORG_ID
    delay.project_id = PROJECT_ID
    delay.task_ids = task_ids or []
    delay.delay_days = delay_days
    delay.reason_category = reason
    delay.responsible_party = "GC"
    delay.description = "Rain delay"
    delay.impacts_gc_schedule = True
    delay.impacts_owner_schedule = impacts_owner
    delay.impacts_sub_schedule = True
    delay.daily_log_id = None
    delay.rfi_id = None
    delay.change_order_id = None
    delay.status = status
    delay.approved_by = None
    delay.approved_at = None
    delay.applied_at = None
    delay.created_by = ADMIN_USER_ID
    delay.created_at = datetime(2026, 2, 25, 10, 0)
    return delay


# ============================================================
# create_task
# ============================================================

class TestCreateTask:
    @pytest.mark.asyncio
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_create_task_single_mode(self, mock_get_config):
        config = _make_config(schedule_mode="SINGLE")
        mock_get_config.return_value = config

        db = AsyncMock()
        user = _make_user()
        data = ScheduleTaskCreate(
            name="Foundation Pour",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 11),
            duration=10,
            is_critical=True,
        )

        result = await create_task(db, PROJECT_ID, ORG_ID, user, data)

        # Task + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    @patch("app.services.schedule_service.derive_tier_dates")
    async def test_create_task_three_tier_auto(self, mock_derive, mock_get_config):
        config = _make_config(schedule_mode="THREE_TIER_AUTO")
        mock_get_config.return_value = config

        db = AsyncMock()
        user = _make_user()
        data = ScheduleTaskCreate(
            name="Steel Erection",
            start_date=date(2026, 3, 15),
            duration=20,
        )

        await create_task(db, PROJECT_ID, ORG_ID, user, data)

        # derive_tier_dates should be called for THREE_TIER_AUTO
        mock_derive.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    @patch("app.services.schedule_service.derive_tier_dates")
    async def test_create_task_three_tier_manual_no_derive(self, mock_derive, mock_get_config):
        config = _make_config(schedule_mode="THREE_TIER_MANUAL")
        mock_get_config.return_value = config

        db = AsyncMock()
        user = _make_user()
        data = ScheduleTaskCreate(name="Manual Task")

        await create_task(db, PROJECT_ID, ORG_ID, user, data)

        # derive_tier_dates should NOT be called for MANUAL
        mock_derive.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_create_milestone(self, mock_get_config):
        mock_get_config.return_value = _make_config(schedule_mode="SINGLE")

        db = AsyncMock()
        user = _make_user()
        data = ScheduleTaskCreate(name="Roof Dry-In", milestone=True)

        await create_task(db, PROJECT_ID, ORG_ID, user, data)

        task_obj = db.add.call_args_list[0][0][0]
        assert task_obj.milestone is True


# ============================================================
# derive_tier_dates
# ============================================================

class TestDeriveTierDates:
    def test_percentage_method(self):
        task = _make_task(
            start_date=datetime(2026, 3, 1),
            duration=10,
        )
        config = _make_config(
            derivation_method="PERCENTAGE",
            owner_buffer=10,   # 10% buffer → 11 days
            sub_compress=20,   # 20% compress → 8 days
        )

        derive_tier_dates(task, config)

        # Owner: 10 * 1.1 = 11 days
        assert task.owner_start_date == datetime(2026, 3, 1)
        assert task.owner_end_date == datetime(2026, 3, 1) + timedelta(days=11)

        # Sub: 10 * 0.8 = 8 days
        assert task.sub_start_date == datetime(2026, 3, 1)
        assert task.sub_end_date == datetime(2026, 3, 1) + timedelta(days=8)

    def test_no_start_date_skips_derivation(self):
        task = _make_task(start_date=None, duration=10)
        config = _make_config()

        derive_tier_dates(task, config)

        # Should not modify owner/sub dates
        assert task.owner_start_date is None
        assert task.sub_start_date is None

    def test_no_duration_skips_derivation(self):
        task = _make_task(duration=None)
        config = _make_config()

        derive_tier_dates(task, config)

        assert task.owner_start_date is None
        assert task.sub_start_date is None

    def test_sub_compress_min_one_day(self):
        """Sub duration should never go below 1 day."""
        task = _make_task(
            start_date=datetime(2026, 3, 1),
            duration=1,
        )
        config = _make_config(sub_compress=99)  # 99% compress on 1-day task

        derive_tier_dates(task, config)

        sub_duration = (task.sub_end_date - task.sub_start_date).days
        assert sub_duration >= 1


# ============================================================
# lock_baseline
# ============================================================

class TestLockBaseline:
    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    async def test_lock_baseline_copies_dates(self, mock_list_tasks):
        task1 = _make_task(
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 11),
            duration=10,
        )
        task2 = _make_task(
            name="Framing",
            start_date=datetime(2026, 3, 12),
            end_date=datetime(2026, 3, 22),
            duration=10,
        )
        mock_list_tasks.return_value = [task1, task2]

        db = AsyncMock()
        user = _make_user()

        count = await lock_baseline(db, PROJECT_ID, user)

        assert count == 2
        assert task1.baseline_start == datetime(2026, 3, 1)
        assert task1.baseline_end == datetime(2026, 3, 11)
        assert task1.baseline_duration == 10
        assert task2.baseline_start == datetime(2026, 3, 12)
        assert task2.baseline_end == datetime(2026, 3, 22)
        # EventLog
        db.add.assert_called_once()
        db.flush.assert_awaited_once()


# ============================================================
# Delays — Create, Approve, Reject, Apply
# ============================================================

class TestCreateDelay:
    @pytest.mark.asyncio
    async def test_create_weather_delay(self):
        db = AsyncMock()
        user = _make_user()
        task_id = uuid.uuid4()
        data = ScheduleDelayCreate(
            task_ids=[task_id],
            delay_days=3,
            reason_category="WEATHER",
            responsible_party="GC",
            description="Three days of rain",
        )

        result = await create_delay(db, PROJECT_ID, ORG_ID, user, data)

        # Delay + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        delay_obj = db.add.call_args_list[0][0][0]
        assert delay_obj.delay_days == 3
        assert delay_obj.status == "PENDING"
        # WEATHER: impacts GC + sub, NOT owner
        assert delay_obj.impacts_gc_schedule is True
        assert delay_obj.impacts_owner_schedule is False
        assert delay_obj.impacts_sub_schedule is True

    @pytest.mark.asyncio
    async def test_create_owner_change_delay(self):
        db = AsyncMock()
        user = _make_user()
        data = ScheduleDelayCreate(
            task_ids=[uuid.uuid4()],
            delay_days=5,
            reason_category="OWNER_CHANGE",
            responsible_party="OWNER",
            description="Owner requested layout change",
        )

        await create_delay(db, PROJECT_ID, ORG_ID, user, data)

        delay_obj = db.add.call_args_list[0][0][0]
        # OWNER_CHANGE: impacts ALL tiers
        assert delay_obj.impacts_gc_schedule is True
        assert delay_obj.impacts_owner_schedule is True
        assert delay_obj.impacts_sub_schedule is True


class TestApproveDelay:
    @pytest.mark.asyncio
    async def test_approve_pending(self):
        db = AsyncMock()
        delay = _make_delay(status="PENDING")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = delay
        db.execute.return_value = mock_result

        user = _make_user()
        result = await approve_delay(db, delay.id, user)

        assert delay.status == "APPROVED"
        assert delay.approved_by == ADMIN_USER_ID
        assert delay.approved_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_non_pending_raises_400(self):
        db = AsyncMock()
        delay = _make_delay(status="APPROVED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = delay
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await approve_delay(db, delay.id, user)
        assert exc_info.value.status_code == 400


class TestRejectDelay:
    @pytest.mark.asyncio
    async def test_reject_pending(self):
        db = AsyncMock()
        delay = _make_delay(status="PENDING")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = delay
        db.execute.return_value = mock_result

        user = _make_user()
        result = await reject_delay(db, delay.id, user)

        assert delay.status == "REJECTED"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reject_non_pending_raises_400(self):
        db = AsyncMock()
        delay = _make_delay(status="APPLIED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = delay
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reject_delay(db, delay.id, user)
        assert exc_info.value.status_code == 400


class TestApplyDelay:
    @pytest.mark.asyncio
    @patch("app.services.schedule_service.cascade_dependencies", new_callable=AsyncMock)
    async def test_apply_shifts_gc_and_sub_dates(self, mock_cascade):
        task = _make_task(
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 11),
            sub_end_date=datetime(2026, 3, 9),
            owner_end_date=datetime(2026, 3, 12),
        )
        task_id = task.id

        # WEATHER: gc=True, owner=False, sub=True
        delay = _make_delay(
            status="APPROVED",
            reason="WEATHER",
            delay_days=3,
            task_ids=[str(task_id)],
            impacts_owner=False,
        )

        db = AsyncMock()
        # First execute returns the delay, second returns the task
        delay_result = MagicMock()
        delay_result.scalar_one_or_none.return_value = delay
        task_result = MagicMock()
        task_result.scalar_one_or_none.return_value = task
        db.execute.side_effect = [delay_result, task_result]

        user = _make_user()
        result = await apply_delay(db, delay.id, user)

        # GC end shifted by 3 days
        assert task.end_date == datetime(2026, 3, 11) + timedelta(days=3)
        # Owner NOT shifted (WEATHER doesn't impact owner)
        assert task.owner_end_date == datetime(2026, 3, 12)
        # Sub shifted by 3 days
        assert task.sub_end_date == datetime(2026, 3, 9) + timedelta(days=3)

        assert delay.status == "APPLIED"
        assert delay.applied_at is not None
        mock_cascade.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.cascade_dependencies", new_callable=AsyncMock)
    async def test_apply_owner_change_shifts_all_tiers(self, mock_cascade):
        task = _make_task(
            end_date=datetime(2026, 3, 11),
            sub_end_date=datetime(2026, 3, 9),
            owner_end_date=datetime(2026, 3, 12),
        )
        task_id = task.id

        delay = _make_delay(
            status="APPROVED",
            reason="OWNER_CHANGE",
            delay_days=5,
            task_ids=[str(task_id)],
            impacts_owner=True,
        )

        db = AsyncMock()
        delay_result = MagicMock()
        delay_result.scalar_one_or_none.return_value = delay
        task_result = MagicMock()
        task_result.scalar_one_or_none.return_value = task
        db.execute.side_effect = [delay_result, task_result]

        user = _make_user()
        await apply_delay(db, delay.id, user)

        assert task.end_date == datetime(2026, 3, 11) + timedelta(days=5)
        assert task.owner_end_date == datetime(2026, 3, 12) + timedelta(days=5)
        assert task.sub_end_date == datetime(2026, 3, 9) + timedelta(days=5)

    @pytest.mark.asyncio
    async def test_apply_non_approved_raises_400(self):
        db = AsyncMock()
        delay = _make_delay(status="PENDING")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = delay
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await apply_delay(db, delay.id, user)
        assert exc_info.value.status_code == 400


# ============================================================
# Delay tier impact rules
# ============================================================

class TestDelayTierImpacts:
    def test_weather_no_owner_impact(self):
        impacts = DELAY_TIER_IMPACTS["WEATHER"]
        assert impacts["gc"] is True
        assert impacts["owner"] is False
        assert impacts["sub"] is True

    def test_owner_change_all_tiers(self):
        impacts = DELAY_TIER_IMPACTS["OWNER_CHANGE"]
        assert impacts["gc"] is True
        assert impacts["owner"] is True
        assert impacts["sub"] is True

    def test_force_majeure_all_tiers(self):
        impacts = DELAY_TIER_IMPACTS["FORCE_MAJEURE"]
        assert impacts["gc"] is True
        assert impacts["owner"] is True
        assert impacts["sub"] is True

    def test_sub_caused_no_owner_impact(self):
        impacts = DELAY_TIER_IMPACTS["SUB_CAUSED"]
        assert impacts["gc"] is True
        assert impacts["owner"] is False
        assert impacts["sub"] is True

    def test_design_error_all_tiers(self):
        impacts = DELAY_TIER_IMPACTS["DESIGN_ERROR"]
        assert impacts["gc"] is True
        assert impacts["owner"] is True
        assert impacts["sub"] is True


# ============================================================
# publish_schedule
# ============================================================

class TestPublishSchedule:
    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    async def test_publish_full_schedule(self, mock_list_tasks):
        task1 = _make_task(name="Foundation")
        task2 = _make_task(name="Framing")
        mock_list_tasks.return_value = [task1, task2]

        db = AsyncMock()
        # Mock for max version number query
        version_result = MagicMock()
        version_result.scalar.return_value = None  # No prior versions
        db.execute.return_value = version_result

        user = _make_user()
        data = SchedulePublishRequest(
            version_type="FULL_SCHEDULE",
            title="Week 8 Schedule",
            notes="Updated after delay",
        )

        result = await publish_schedule(db, PROJECT_ID, ORG_ID, user, data)

        # Version + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        version_obj = db.add.call_args_list[0][0][0]
        assert version_obj.version_number == 1
        assert version_obj.title == "Week 8 Schedule"
        assert len(version_obj.snapshot_data["tasks"]) == 2

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    async def test_publish_increments_version(self, mock_list_tasks):
        mock_list_tasks.return_value = []

        db = AsyncMock()
        version_result = MagicMock()
        version_result.scalar.return_value = 3  # Already have v3
        db.execute.return_value = version_result

        user = _make_user()
        data = SchedulePublishRequest(version_type="FULL_SCHEDULE")

        await publish_schedule(db, PROJECT_ID, ORG_ID, user, data)

        version_obj = db.add.call_args_list[0][0][0]
        assert version_obj.version_number == 4


# ============================================================
# calculate_schedule_health
# ============================================================

class TestCalculateScheduleHealth:
    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_on_track_no_slippage(self, mock_config, mock_list):
        mock_config.return_value = _make_config(on_track=5, at_risk=15)
        task = _make_task(
            is_critical=True,
            end_date=datetime(2026, 3, 11),
            baseline_end=datetime(2026, 3, 11),
        )
        mock_list.return_value = [task]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        assert result["status"] == "ON_TRACK"
        assert result["slippage_days"] == 0

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_on_track_small_slippage(self, mock_config, mock_list):
        mock_config.return_value = _make_config(on_track=5, at_risk=15)
        task = _make_task(
            is_critical=True,
            end_date=datetime(2026, 3, 14),       # 3 days behind
            baseline_end=datetime(2026, 3, 11),
        )
        mock_list.return_value = [task]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        assert result["status"] == "ON_TRACK"
        assert result["slippage_days"] == 3

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_at_risk(self, mock_config, mock_list):
        mock_config.return_value = _make_config(on_track=5, at_risk=15)
        task = _make_task(
            is_critical=True,
            end_date=datetime(2026, 3, 21),       # 10 days behind
            baseline_end=datetime(2026, 3, 11),
        )
        mock_list.return_value = [task]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        assert result["status"] == "AT_RISK"
        assert result["slippage_days"] == 10

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_behind(self, mock_config, mock_list):
        mock_config.return_value = _make_config(on_track=5, at_risk=15)
        task = _make_task(
            is_critical=True,
            end_date=datetime(2026, 3, 31),       # 20 days behind
            baseline_end=datetime(2026, 3, 11),
        )
        mock_list.return_value = [task]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        assert result["status"] == "BEHIND"
        assert result["slippage_days"] == 20

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_no_critical_tasks_defaults_on_track(self, mock_config, mock_list):
        mock_config.return_value = _make_config()
        task = _make_task(is_critical=False, baseline_end=None)
        mock_list.return_value = [task]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        assert result["status"] == "ON_TRACK"
        assert result["slippage_days"] == 0

    @pytest.mark.asyncio
    @patch("app.services.schedule_service.list_tasks", new_callable=AsyncMock)
    @patch("app.services.schedule_service.get_schedule_config", new_callable=AsyncMock)
    async def test_max_slippage_across_critical_tasks(self, mock_config, mock_list):
        mock_config.return_value = _make_config(on_track=5, at_risk=15)
        task1 = _make_task(
            is_critical=True,
            end_date=datetime(2026, 3, 14),       # 3 days
            baseline_end=datetime(2026, 3, 11),
        )
        task2 = _make_task(
            name="Critical Task 2",
            is_critical=True,
            end_date=datetime(2026, 3, 23),       # 12 days
            baseline_end=datetime(2026, 3, 11),
        )
        mock_list.return_value = [task1, task2]

        db = AsyncMock()
        result = await calculate_schedule_health(db, PROJECT_ID)

        # Uses max slippage
        assert result["status"] == "AT_RISK"
        assert result["slippage_days"] == 12


# ============================================================
# Format responses
# ============================================================

class TestFormatTaskResponse:
    def test_basic_format(self):
        task = _make_task()
        result = format_task_response(task, dependencies=[])

        assert result["name"] == "Foundation Pour"
        assert result["project_id"] == PROJECT_ID
        assert result["duration"] == 10
        assert result["milestone"] is False
        assert result["dependencies"] == []


class TestFormatDelayResponse:
    def test_basic_format(self):
        delay = _make_delay(delay_days=5)
        result = format_delay_response(delay)

        assert result["delay_days"] == 5
        assert result["reason_category"] == "WEATHER"
        assert result["status"] == "PENDING"


class TestFormatVersionResponse:
    def test_basic_format(self):
        version = MagicMock(spec=ScheduleVersion)
        version.id = uuid.uuid4()
        version.project_id = PROJECT_ID
        version.version_type = "FULL_SCHEDULE"
        version.version_number = 1
        version.title = "Week 8 Schedule"
        version.notes = None
        version.snapshot_data = {"tasks": []}
        version.published_by = ADMIN_USER_ID
        version.published_at = datetime(2026, 2, 25)

        result = format_version_response(version)

        assert result["version_number"] == 1
        assert result["title"] == "Week 8 Schedule"
        assert result["snapshot_data"]["tasks"] == []


class TestFormatConfigResponse:
    def test_basic_format(self):
        config = _make_config()
        result = format_config_response(config)

        assert result["schedule_mode"] == "SINGLE"
        assert result["derivation_method"] == "PERCENTAGE"
        assert result["health_on_track_max_days"] == 5
        assert result["health_at_risk_max_days"] == 15
        assert result["sub_notify_intervals"] == [14, 7, 1]
