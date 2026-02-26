"""Tests for Bid service (packages + submissions)."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.bid_package import BidPackage
from app.models.bid_submission import BidSubmission
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.bid_package import (
    AwardBidRequest,
    BidPackageCreate,
    BidPackageUpdate,
    BidSubmissionCreate,
    DistributeBidPackageRequest,
)
from app.services.bid_service import (
    award_bid,
    close_bidding,
    compare_bids,
    create_package,
    create_submission,
    delete_package,
    distribute_package,
    format_package_response,
    format_submission_response,
    get_package,
    submit_bid,
    update_package,
)
from app.services.numbering_service import format_number
from tests.conftest import (
    ADMIN_USER_ID,
    MGMT_USER_ID,
    ORG_ID,
    PROJECT_ID,
    SUB_COMPANY_ID,
    SUB_USER_ID,
)


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


def _make_sub_user(user_id=SUB_USER_ID, sub_company_id=SUB_COMPANY_ID):
    return {
        "user_type": "sub",
        "user_id": user_id,
        "sub_company_id": sub_company_id,
        "permission_level": None,
    }


def _make_package(
    status="DRAFT",
    number=1,
    created_by=ADMIN_USER_ID,
    trade="Concrete",
):
    pkg = MagicMock(spec=BidPackage)
    pkg.id = uuid.uuid4()
    pkg.organization_id = ORG_ID
    pkg.project_id = PROJECT_ID
    pkg.created_by = created_by
    pkg.number = number
    pkg.title = "Concrete Work - Building A"
    pkg.description = "Full concrete scope for Building A foundation and structure."
    pkg.trade = trade
    pkg.trades = ["Concrete", "Rebar"]
    pkg.bid_due_date = datetime(2026, 3, 15, 17, 0, tzinfo=timezone.utc)
    pkg.pre_bid_meeting_date = datetime(2026, 3, 10, 14, 0, tzinfo=timezone.utc)
    pkg.estimated_value = Decimal("500000.00")
    pkg.requirements = "Must provide bonding."
    pkg.scope_documents = []
    pkg.invited_sub_ids = []
    pkg.status = status
    pkg.awarded_sub_id = None
    pkg.awarded_at = None
    pkg.created_at = datetime(2026, 2, 20, 10, 0)
    pkg.updated_at = datetime(2026, 2, 20, 10, 0)
    pkg.deleted_at = None
    return pkg


def _make_submission(
    status="DRAFT",
    total_amount=Decimal("450000.00"),
    package_id=None,
    sub_company_id=SUB_COMPANY_ID,
):
    sub = MagicMock(spec=BidSubmission)
    sub.id = uuid.uuid4()
    sub.bid_package_id = package_id or uuid.uuid4()
    sub.sub_company_id = sub_company_id
    sub.total_amount = total_amount
    sub.line_items = [{"description": "Foundation", "amount_cents": 20000000}]
    sub.qualifications = "10 years experience"
    sub.schedule_duration_days = 90
    sub.exclusions = "Dewatering"
    sub.inclusions = "All rebar"
    sub.notes = "Earliest start March 2026"
    sub.status = status
    sub.submitted_at = None
    sub.created_at = datetime(2026, 2, 22, 10, 0)
    return sub


# ============================================================
# create_package
# ============================================================

class TestCreatePackage:
    @pytest.mark.asyncio
    @patch("app.services.bid_service.get_next_number", new_callable=AsyncMock)
    async def test_create_success(self, mock_next_number):
        mock_next_number.return_value = 1

        db = AsyncMock()
        user = _make_user()
        data = BidPackageCreate(
            title="Concrete Work",
            description="Full concrete scope",
            trade="Concrete",
            trades=["Concrete", "Rebar"],
            estimated_value_cents=50000000,
            requirements="Must provide bonding.",
        )

        result = await create_package(db, PROJECT_ID, ORG_ID, user, data)

        # BidPackage + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()
        mock_next_number.assert_awaited_once_with(db, PROJECT_ID, "bid_package")

    @pytest.mark.asyncio
    @patch("app.services.bid_service.get_next_number", new_callable=AsyncMock)
    async def test_create_minimal_fields(self, mock_next_number):
        mock_next_number.return_value = 2

        db = AsyncMock()
        user = _make_user()
        data = BidPackageCreate(title="Electrical Work")

        result = await create_package(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_package
# ============================================================

class TestGetPackage:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        pkg = _make_package()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        result = await get_package(db, pkg.id, PROJECT_ID)
        assert result == pkg

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_package(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_package
# ============================================================

class TestUpdatePackage:
    @pytest.mark.asyncio
    async def test_update_draft(self):
        db = AsyncMock()
        pkg = _make_package(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = BidPackageUpdate(title="Updated Title", description="New description")

        result = await update_package(db, pkg.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_published(self):
        """Published packages can still be edited (only CLOSED and AWARDED cannot)."""
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = BidPackageUpdate(title="Updated Title")

        result = await update_package(db, pkg.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_closed_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = BidPackageUpdate(title="Too late")

        with pytest.raises(HTTPException) as exc_info:
            await update_package(db, pkg.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_awarded_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="AWARDED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = BidPackageUpdate(title="Too late")

        with pytest.raises(HTTPException) as exc_info:
            await update_package(db, pkg.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# delete_package
# ============================================================

class TestDeletePackage:
    @pytest.mark.asyncio
    async def test_delete_draft(self):
        db = AsyncMock()
        pkg = _make_package(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_package(db, pkg.id, PROJECT_ID, user)

        assert pkg.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_published_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_package(db, pkg.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_closed_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_package(db, pkg.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# distribute_package
# ============================================================

class TestDistributePackage:
    @pytest.mark.asyncio
    async def test_distribute_draft(self):
        db = AsyncMock()
        pkg = _make_package(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        sub_id_1 = uuid.uuid4()
        sub_id_2 = uuid.uuid4()
        data = DistributeBidPackageRequest(invited_sub_ids=[sub_id_1, sub_id_2])

        result = await distribute_package(db, pkg.id, PROJECT_ID, user, data)

        assert pkg.status == "PUBLISHED"
        assert len(pkg.invited_sub_ids) == 2
        # 2 Notifications (one per sub) + 1 EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_distribute_published_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = DistributeBidPackageRequest(invited_sub_ids=[uuid.uuid4()])

        with pytest.raises(HTTPException) as exc_info:
            await distribute_package(db, pkg.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_distribute_closed_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = DistributeBidPackageRequest(invited_sub_ids=[uuid.uuid4()])

        with pytest.raises(HTTPException) as exc_info:
            await distribute_package(db, pkg.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400


# ============================================================
# close_bidding
# ============================================================

class TestCloseBidding:
    @pytest.mark.asyncio
    async def test_close_published(self):
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        result = await close_bidding(db, pkg.id, PROJECT_ID, user)

        assert pkg.status == "CLOSED"
        # EventLog added
        assert db.add.call_count >= 1
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_draft_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await close_bidding(db, pkg.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_close_already_closed_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await close_bidding(db, pkg.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# award_bid
# ============================================================

class TestAwardBid:
    @pytest.mark.asyncio
    async def test_award_closed_package(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        submission = _make_submission(
            status="SUBMITTED",
            total_amount=Decimal("450000.00"),
            package_id=pkg.id,
        )

        # First call: get_package (select BidPackage), second: get submission,
        # third: get all submissions for status update
        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = submission

        mock_all_subs = MagicMock()
        mock_all_subs.scalars.return_value.all.return_value = [submission]

        db.execute.side_effect = [mock_pkg_result, mock_sub_result, mock_all_subs]

        user = _make_user()
        data = AwardBidRequest(submission_id=submission.id)

        result = await award_bid(db, pkg.id, PROJECT_ID, ORG_ID, user, data)

        assert pkg.status == "AWARDED"
        assert pkg.awarded_sub_id == SUB_COMPANY_ID
        assert pkg.awarded_at is not None
        # ProjectAssignment + Notification + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_award_draft_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="DRAFT")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pkg
        db.execute.return_value = mock_result

        user = _make_user()
        data = AwardBidRequest(submission_id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await award_bid(db, pkg.id, PROJECT_ID, ORG_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_award_submission_not_found_raises_404(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = None

        db.execute.side_effect = [mock_pkg_result, mock_sub_result]

        user = _make_user()
        data = AwardBidRequest(submission_id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await award_bid(db, pkg.id, PROJECT_ID, ORG_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# create_submission
# ============================================================

class TestCreateSubmission:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        package_id = uuid.uuid4()
        user = _make_sub_user()
        data = BidSubmissionCreate(
            total_amount_cents=45000000,
            line_items=[{"description": "Foundation", "amount_cents": 20000000}],
            qualifications="10 years experience",
            schedule_duration_days=90,
            exclusions="Dewatering",
            inclusions="All rebar",
            notes="Earliest start March 2026",
        )

        result = await create_submission(db, package_id, SUB_COMPANY_ID, user, data)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal_submission(self):
        db = AsyncMock()
        package_id = uuid.uuid4()
        user = _make_sub_user()
        data = BidSubmissionCreate()

        result = await create_submission(db, package_id, SUB_COMPANY_ID, user, data)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()


# ============================================================
# submit_bid
# ============================================================

class TestSubmitBid:
    @pytest.mark.asyncio
    async def test_submit_draft(self):
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        pkg.bid_due_date = datetime(2027, 12, 31, tzinfo=timezone.utc)  # Far future
        submission = _make_submission(status="DRAFT", package_id=pkg.id)

        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = submission

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        db.execute.side_effect = [mock_sub_result, mock_pkg_result]

        user = _make_sub_user()
        result = await submit_bid(db, submission.id, user)

        assert submission.status == "SUBMITTED"
        assert submission.submitted_at is not None
        # Notification added
        assert db.add.call_count >= 1
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_already_submitted_raises_400(self):
        db = AsyncMock()
        submission = _make_submission(status="SUBMITTED")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = submission
        db.execute.return_value = mock_result

        user = _make_sub_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_bid(db, submission.id, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_submit_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_sub_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_bid(db, uuid.uuid4(), user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_submit_to_non_published_package_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        submission = _make_submission(status="DRAFT", package_id=pkg.id)

        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = submission

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        db.execute.side_effect = [mock_sub_result, mock_pkg_result]

        user = _make_sub_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_bid(db, submission.id, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_submit_past_due_date_raises_400(self):
        db = AsyncMock()
        pkg = _make_package(status="PUBLISHED")
        pkg.bid_due_date = datetime(2020, 1, 1, tzinfo=timezone.utc)  # Past
        submission = _make_submission(status="DRAFT", package_id=pkg.id)

        mock_sub_result = MagicMock()
        mock_sub_result.scalar_one_or_none.return_value = submission

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        db.execute.side_effect = [mock_sub_result, mock_pkg_result]

        user = _make_sub_user()
        with pytest.raises(HTTPException) as exc_info:
            await submit_bid(db, submission.id, user)
        assert exc_info.value.status_code == 400


# ============================================================
# compare_bids
# ============================================================

class TestCompareBids:
    @pytest.mark.asyncio
    async def test_compare_with_submissions(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")
        sub1 = _make_submission(status="SUBMITTED", total_amount=Decimal("400000.00"))
        sub2 = _make_submission(
            status="SUBMITTED",
            total_amount=Decimal("500000.00"),
            sub_company_id=uuid.uuid4(),
        )

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        mock_subs_result = MagicMock()
        mock_subs_result.scalars.return_value.all.return_value = [sub1, sub2]

        db.execute.side_effect = [mock_pkg_result, mock_subs_result]

        result = await compare_bids(db, pkg.id, PROJECT_ID)

        assert result["lowest_amount_cents"] == 40000000
        assert result["highest_amount_cents"] == 50000000
        assert result["average_amount_cents"] == 45000000
        assert result["recommended_submission_id"] == sub1.id
        assert len(result["submissions"]) == 2

    @pytest.mark.asyncio
    async def test_compare_no_submissions(self):
        db = AsyncMock()
        pkg = _make_package(status="CLOSED")

        mock_pkg_result = MagicMock()
        mock_pkg_result.scalar_one_or_none.return_value = pkg

        mock_subs_result = MagicMock()
        mock_subs_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [mock_pkg_result, mock_subs_result]

        result = await compare_bids(db, pkg.id, PROJECT_ID)

        assert result["lowest_amount_cents"] == 0
        assert result["highest_amount_cents"] == 0
        assert result["average_amount_cents"] == 0
        assert result["recommended_submission_id"] is None
        assert result["submissions"] == []


# ============================================================
# format_package_response
# ============================================================

class TestFormatPackageResponse:
    @pytest.mark.asyncio
    async def test_basic_format(self):
        db = AsyncMock()
        pkg = _make_package(number=3)

        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        db.execute.return_value = mock_count

        result = await format_package_response(db, pkg, created_by_name="John Smith")

        assert result["id"] == pkg.id
        assert result["project_id"] == PROJECT_ID
        assert result["number"] == 3
        assert result["formatted_number"] == "BP-003"
        assert result["title"] == "Concrete Work - Building A"
        assert result["status"] == "DRAFT"
        assert result["created_by_name"] == "John Smith"
        assert result["submission_count"] == 5
        assert result["estimated_value_cents"] == 50000000
        assert result["trades"] == ["Concrete", "Rebar"]

    @pytest.mark.asyncio
    async def test_format_with_zero_submissions(self):
        db = AsyncMock()
        pkg = _make_package(number=1)

        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        db.execute.return_value = mock_count

        result = await format_package_response(db, pkg)

        assert result["submission_count"] == 0
        assert result["created_by_name"] is None


# ============================================================
# format_submission_response
# ============================================================

class TestFormatSubmissionResponse:
    def test_basic_format(self):
        submission = _make_submission(
            status="SUBMITTED",
            total_amount=Decimal("450000.00"),
        )

        result = format_submission_response(
            submission,
            sub_company_name="Apex Concrete LLC",
        )

        assert result["id"] == submission.id
        assert result["total_amount_cents"] == 45000000
        assert result["sub_company_name"] == "Apex Concrete LLC"
        assert result["status"] == "SUBMITTED"
        assert result["schedule_duration_days"] == 90
        assert result["qualifications"] == "10 years experience"

    def test_format_without_sub_company_name(self):
        submission = _make_submission()
        result = format_submission_response(submission)
        assert result["sub_company_name"] is None


# ============================================================
# Numbering format verification
# ============================================================

class TestBidPackageNumbering:
    def test_first_package(self):
        assert format_number("bid_package", 1) == "BP-001"

    def test_double_digit(self):
        assert format_number("bid_package", 12) == "BP-012"

    def test_triple_digit(self):
        assert format_number("bid_package", 100) == "BP-100"
