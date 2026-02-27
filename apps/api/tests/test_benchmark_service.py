"""Tests for benchmark aggregation service."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.benchmark_service import (
    _cents,
    get_activity_timeline,
    get_financial_summary,
    get_org_overview,
    get_project_metrics,
    get_tool_usage_stats,
)
from tests.conftest import ORG_ID, PROJECT_ID


# ============================================================
# HELPERS
# ============================================================

def _scalar_result(value):
    """Create a mock db.execute result whose .scalar() returns the value."""
    r = MagicMock()
    r.scalar.return_value = value
    return r


def _scalar_one_result(value):
    """Create a mock result whose .scalar_one() returns the value (for count queries)."""
    r = MagicMock()
    r.scalar_one.return_value = value
    return r


def _first_result(**kwargs):
    """Create a mock result whose .first() returns a namedtuple-like row."""
    row = MagicMock()
    for k, v in kwargs.items():
        setattr(row, k, v)
    r = MagicMock()
    r.first.return_value = row
    return r


def _all_result(rows):
    """Create a mock result whose .all() returns a list of rows."""
    r = MagicMock()
    r.all.return_value = rows
    return r


# ============================================================
# _cents helper
# ============================================================

class TestCentsHelper:
    def test_converts_dollars_to_cents(self):
        assert _cents(Decimal("100.00")) == 10000

    def test_handles_fractional_cents(self):
        assert _cents(Decimal("99.99")) == 9999

    def test_handles_large_amounts(self):
        assert _cents(Decimal("1000000.50")) == 100000050

    def test_none_returns_none(self):
        assert _cents(None) is None

    def test_zero(self):
        assert _cents(Decimal("0.00")) == 0


# ============================================================
# get_org_overview
# ============================================================

class TestGetOrgOverview:
    @pytest.mark.asyncio
    async def test_returns_all_expected_keys(self):
        db = AsyncMock()

        # The function executes 7 queries:
        # total_projects, active_projects, closed_projects,
        # total_users, active_users, total_subs, org_row
        org_row = MagicMock()
        org_row.subscription_tier = "PROFESSIONAL"
        org_row.subscription_status = "ACTIVE"

        db.execute.side_effect = [
            _scalar_result(10),  # total_projects
            _scalar_result(5),   # active_projects
            _scalar_result(2),   # closed_projects
            _scalar_result(8),   # total_users
            _scalar_result(6),   # active_users
            _scalar_result(15),  # total_subs
            _first_result(subscription_tier="PROFESSIONAL", subscription_status="ACTIVE"),
        ]

        result = await get_org_overview(db, ORG_ID)

        expected_keys = {
            "total_projects", "active_projects", "closed_projects",
            "total_users", "active_users", "total_subs",
            "subscription_tier", "subscription_status",
        }
        assert expected_keys == set(result.keys())
        assert result["total_projects"] == 10
        assert result["active_projects"] == 5
        assert result["closed_projects"] == 2
        assert result["total_users"] == 8
        assert result["active_users"] == 6
        assert result["total_subs"] == 15
        assert result["subscription_tier"] == "PROFESSIONAL"
        assert result["subscription_status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_empty_org(self):
        db = AsyncMock()

        # All counts return 0 or None
        org_result = MagicMock()
        org_result.first.return_value = None

        db.execute.side_effect = [
            _scalar_result(0),   # total_projects
            _scalar_result(0),   # active_projects
            _scalar_result(0),   # closed_projects
            _scalar_result(0),   # total_users
            _scalar_result(0),   # active_users
            _scalar_result(0),   # total_subs
            org_result,          # org_row (None)
        ]

        result = await get_org_overview(db, ORG_ID)

        assert result["total_projects"] == 0
        assert result["active_projects"] == 0
        assert result["total_users"] == 0
        assert result["total_subs"] == 0
        assert result["subscription_tier"] is None
        assert result["subscription_status"] is None

    @pytest.mark.asyncio
    async def test_null_scalar_defaults_to_zero(self):
        db = AsyncMock()

        org_result = MagicMock()
        org_result.first.return_value = MagicMock(
            subscription_tier="STARTER",
            subscription_status="TRIALING",
        )

        db.execute.side_effect = [
            _scalar_result(None),  # total_projects (NULL)
            _scalar_result(None),  # active_projects
            _scalar_result(None),  # closed_projects
            _scalar_result(None),  # total_users
            _scalar_result(None),  # active_users
            _scalar_result(None),  # total_subs
            org_result,
        ]

        result = await get_org_overview(db, ORG_ID)

        # None or 0 → 0 because of `or 0`
        assert result["total_projects"] == 0
        assert result["active_projects"] == 0
        assert result["total_users"] == 0


# ============================================================
# get_project_metrics
# ============================================================

class TestGetProjectMetrics:
    @pytest.mark.asyncio
    async def test_returns_all_expected_keys(self):
        db = AsyncMock()

        # 13 db.execute calls for project metrics
        budget_row = MagicMock()
        budget_row.original = Decimal("500000.00")
        budget_row.committed = Decimal("520000.00")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(25),           # rfi_count
            _scalar_result(8),            # rfi_open_count
            _scalar_result(5.3),          # rfi_avg_close_days
            _scalar_result(40),           # submittal_count
            _scalar_result(7.2),          # submittal_avg_review_result
            _scalar_result(30),           # approved_submittals
            _scalar_result(35),           # reviewed_submittals
            _scalar_result(12),           # co_count
            _scalar_result(Decimal("150000.00")),  # co_total_value
            _scalar_result(8),            # approved_cos
            _scalar_result(10),           # decided_cos
            _scalar_result(45),           # punch_total
            _scalar_result(20),           # punch_closed
            budget_first_result,          # budget row
            _scalar_result(100),          # schedule_total
            _scalar_result(70),           # schedule_on_track
        ]

        result = await get_project_metrics(db, ORG_ID)

        expected_keys = {
            "rfi_count", "rfi_avg_close_days", "rfi_open_count",
            "submittal_count", "submittal_avg_review_days", "submittal_approval_rate",
            "change_order_count", "change_order_total_value", "change_order_approval_rate",
            "punch_list_total", "punch_list_closed_pct",
            "budget_variance_pct", "schedule_on_track_pct",
        }
        assert expected_keys == set(result.keys())
        assert result["rfi_count"] == 25
        assert result["rfi_open_count"] == 8

    @pytest.mark.asyncio
    async def test_empty_results(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = None
        budget_row.committed = None
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(0),     # rfi_count
            _scalar_result(0),     # rfi_open_count
            _scalar_result(None),  # rfi_avg_close_days (no closed RFIs)
            _scalar_result(0),     # submittal_count
            _scalar_result(None),  # submittal_avg_review
            _scalar_result(0),     # approved_submittals
            _scalar_result(0),     # reviewed_submittals
            _scalar_result(0),     # co_count
            _scalar_result(None),  # co_total_value
            _scalar_result(0),     # approved_cos
            _scalar_result(0),     # decided_cos
            _scalar_result(0),     # punch_total
            _scalar_result(0),     # punch_closed
            budget_first_result,   # budget (all None)
            _scalar_result(0),     # schedule_total
            _scalar_result(0),     # schedule_on_track
        ]

        result = await get_project_metrics(db, ORG_ID)

        assert result["rfi_count"] == 0
        assert result["rfi_avg_close_days"] is None
        assert result["submittal_count"] == 0
        assert result["submittal_avg_review_days"] is None
        assert result["submittal_approval_rate"] is None
        assert result["change_order_count"] == 0
        assert result["change_order_total_value"] is None
        assert result["change_order_approval_rate"] is None
        assert result["punch_list_total"] == 0
        assert result["punch_list_closed_pct"] is None
        assert result["budget_variance_pct"] is None
        assert result["schedule_on_track_pct"] is None

    @pytest.mark.asyncio
    async def test_with_project_id_filter(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = Decimal("200000.00")
        budget_row.committed = Decimal("210000.00")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(5),             # rfi_count
            _scalar_result(2),             # rfi_open_count
            _scalar_result(3.0),           # rfi_avg_close_days
            _scalar_result(10),            # submittal_count
            _scalar_result(4.0),           # submittal_avg_review
            _scalar_result(7),             # approved_submittals
            _scalar_result(8),             # reviewed_submittals
            _scalar_result(3),             # co_count
            _scalar_result(Decimal("50000.00")),  # co_total_value
            _scalar_result(2),             # approved_cos
            _scalar_result(3),             # decided_cos
            _scalar_result(20),            # punch_total
            _scalar_result(10),            # punch_closed
            budget_first_result,           # budget row
            _scalar_result(30),            # schedule_total
            _scalar_result(25),            # schedule_on_track
        ]

        result = await get_project_metrics(db, ORG_ID, project_id=PROJECT_ID)

        assert result["rfi_count"] == 5
        assert result["change_order_total_value"] == 5000000  # $50,000 -> 5_000_000 cents
        assert result["submittal_approval_rate"] == 87.5  # 7/8 * 100

    @pytest.mark.asyncio
    async def test_rfi_avg_close_days_rounding(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = None
        budget_row.committed = None
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(10),            # rfi_count
            _scalar_result(3),             # rfi_open_count
            _scalar_result(4.567),         # rfi_avg_close_days
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            budget_first_result,
            _scalar_result(0),
            _scalar_result(0),
        ]

        result = await get_project_metrics(db, ORG_ID)
        assert result["rfi_avg_close_days"] == 4.6  # rounded to 1 decimal

    @pytest.mark.asyncio
    async def test_budget_variance_calculation(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = Decimal("1000000.00")
        budget_row.committed = Decimal("1050000.00")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            budget_first_result,
            _scalar_result(0),
            _scalar_result(0),
        ]

        result = await get_project_metrics(db, ORG_ID)
        # (1050000 - 1000000) / 1000000 * 100 = 5.0
        assert result["budget_variance_pct"] == 5.0

    @pytest.mark.asyncio
    async def test_budget_variance_zero_original(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = Decimal("0")
        budget_row.committed = Decimal("0")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            budget_first_result,
            _scalar_result(0),
            _scalar_result(0),
        ]

        result = await get_project_metrics(db, ORG_ID)
        # Zero original should not cause division by zero
        assert result["budget_variance_pct"] is None

    @pytest.mark.asyncio
    async def test_punch_list_closed_percentage(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = None
        budget_row.committed = None
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(50),  # punch_total
            _scalar_result(35),  # punch_closed
            budget_first_result,
            _scalar_result(0),
            _scalar_result(0),
        ]

        result = await get_project_metrics(db, ORG_ID)
        assert result["punch_list_closed_pct"] == 70.0  # 35/50 * 100

    @pytest.mark.asyncio
    async def test_schedule_on_track_percentage(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = None
        budget_row.committed = None
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            budget_first_result,
            _scalar_result(80),   # schedule_total
            _scalar_result(60),   # schedule_on_track
        ]

        result = await get_project_metrics(db, ORG_ID)
        assert result["schedule_on_track_pct"] == 75.0  # 60/80 * 100


# ============================================================
# get_financial_summary
# ============================================================

class TestGetFinancialSummary:
    @pytest.mark.asyncio
    async def test_returns_all_expected_keys(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = Decimal("500000.00")
        budget_row.committed = Decimal("510000.00")
        budget_row.actuals = Decimal("300000.00")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(Decimal("2000000.00")),  # total_contract_value
            _scalar_result(Decimal("50000.00")),     # total_approved_cos
            _scalar_result(Decimal("800000.00")),    # total_paid
            _scalar_result(Decimal("100000.00")),    # retention_held
            budget_first_result,                      # budget row
        ]

        result = await get_financial_summary(db, ORG_ID)

        expected_keys = {
            "total_contract_value", "total_approved_cos", "total_paid",
            "budget_original", "budget_committed", "budget_actuals",
            "retention_held",
        }
        assert expected_keys == set(result.keys())
        assert result["total_contract_value"] == 200000000   # $2M = 200M cents
        assert result["total_approved_cos"] == 5000000       # $50K = 5M cents
        assert result["total_paid"] == 80000000              # $800K
        assert result["retention_held"] == 10000000          # $100K
        assert result["budget_original"] == 50000000
        assert result["budget_committed"] == 51000000
        assert result["budget_actuals"] == 30000000

    @pytest.mark.asyncio
    async def test_empty_financial_data(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = None
        budget_row.committed = None
        budget_row.actuals = None
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(None),   # total_contract_value
            _scalar_result(None),   # total_approved_cos
            _scalar_result(None),   # total_paid
            _scalar_result(None),   # retention_held
            budget_first_result,    # budget row
        ]

        result = await get_financial_summary(db, ORG_ID)

        assert result["total_contract_value"] is None
        assert result["total_approved_cos"] is None
        assert result["total_paid"] is None
        assert result["retention_held"] is None
        assert result["budget_original"] is None
        assert result["budget_committed"] is None
        assert result["budget_actuals"] is None

    @pytest.mark.asyncio
    async def test_with_project_id_filter(self):
        db = AsyncMock()

        budget_row = MagicMock()
        budget_row.original = Decimal("100000.00")
        budget_row.committed = Decimal("105000.00")
        budget_row.actuals = Decimal("50000.00")
        budget_first_result = MagicMock()
        budget_first_result.first.return_value = budget_row

        db.execute.side_effect = [
            _scalar_result(Decimal("500000.00")),   # total_contract_value
            _scalar_result(Decimal("10000.00")),    # total_approved_cos
            _scalar_result(Decimal("200000.00")),   # total_paid
            _scalar_result(Decimal("25000.00")),    # retention_held
            budget_first_result,
        ]

        result = await get_financial_summary(db, ORG_ID, project_id=PROJECT_ID)

        assert result["total_contract_value"] == 50000000
        assert result["budget_original"] == 10000000

    @pytest.mark.asyncio
    async def test_budget_row_none(self):
        db = AsyncMock()

        budget_first_result = MagicMock()
        budget_first_result.first.return_value = None

        db.execute.side_effect = [
            _scalar_result(Decimal("100000.00")),
            _scalar_result(None),
            _scalar_result(None),
            _scalar_result(None),
            budget_first_result,
        ]

        result = await get_financial_summary(db, ORG_ID)

        assert result["total_contract_value"] == 10000000
        assert result["budget_original"] is None
        assert result["budget_committed"] is None
        assert result["budget_actuals"] is None


# ============================================================
# get_activity_timeline
# ============================================================

class TestGetActivityTimeline:
    @pytest.mark.asyncio
    async def test_returns_list_of_day_count_dicts(self):
        db = AsyncMock()

        row1 = MagicMock()
        row1.day = "2026-02-20"
        row1.count = 15

        row2 = MagicMock()
        row2.day = "2026-02-21"
        row2.count = 22

        result_mock = MagicMock()
        result_mock.all.return_value = [row1, row2]
        db.execute.return_value = result_mock

        result = await get_activity_timeline(db, ORG_ID, days=30)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["date"] == "2026-02-20"
        assert result[0]["count"] == 15
        assert result[1]["date"] == "2026-02-21"
        assert result[1]["count"] == 22

    @pytest.mark.asyncio
    async def test_empty_timeline(self):
        db = AsyncMock()

        result_mock = MagicMock()
        result_mock.all.return_value = []
        db.execute.return_value = result_mock

        result = await get_activity_timeline(db, ORG_ID, days=7)

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_single_day_result(self):
        db = AsyncMock()

        row = MagicMock()
        row.day = "2026-02-25"
        row.count = 42

        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        db.execute.return_value = result_mock

        result = await get_activity_timeline(db, ORG_ID, days=1)

        assert len(result) == 1
        assert result[0]["count"] == 42


# ============================================================
# get_tool_usage_stats
# ============================================================

class TestGetToolUsageStats:
    @pytest.mark.asyncio
    async def test_returns_all_tool_counts(self):
        db = AsyncMock()

        # 15 sequential count queries
        counts = [12, 25, 18, 5, 8, 45, 6, 3, 2, 100, 7, 9, 20, 11, 14]
        db.execute.side_effect = [_scalar_result(c) for c in counts]

        result = await get_tool_usage_stats(db, ORG_ID)

        expected_keys = {
            "daily_logs", "rfis", "submittals", "transmittals",
            "change_orders", "punch_list_items", "inspections",
            "pay_apps", "bid_packages", "schedule_tasks",
            "drawings", "meetings", "todos", "procurement_items",
            "documents",
        }
        assert expected_keys == set(result.keys())
        assert result["daily_logs"] == 12
        assert result["rfis"] == 25
        assert result["submittals"] == 18
        assert result["schedule_tasks"] == 100

    @pytest.mark.asyncio
    async def test_all_zero_counts(self):
        db = AsyncMock()

        db.execute.side_effect = [_scalar_result(0) for _ in range(15)]

        result = await get_tool_usage_stats(db, ORG_ID)

        for key in result:
            assert result[key] == 0

    @pytest.mark.asyncio
    async def test_null_counts_default_to_zero(self):
        db = AsyncMock()

        db.execute.side_effect = [_scalar_result(None) for _ in range(15)]

        result = await get_tool_usage_stats(db, ORG_ID)

        for key in result:
            assert result[key] == 0
