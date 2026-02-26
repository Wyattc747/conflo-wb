import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bid_package import BidPackage
from app.models.bid_submission import BidSubmission
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.models.project_assignment import ProjectAssignment
from app.schemas.bid_package import (
    AwardBidRequest,
    BidPackageCreate,
    BidPackageUpdate,
    BidSubmissionCreate,
    BidSubmissionUpdate,
    DistributeBidPackageRequest,
)
from app.services.numbering_service import format_number, get_next_number


def _cents(val) -> int:
    if val is None:
        return 0
    return int(Decimal(str(val)) * 100)


def _dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


async def create_package(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: BidPackageCreate,
) -> BidPackage:
    number = await get_next_number(db, project_id, "bid_package")

    pkg = BidPackage(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        title=data.title,
        description=data.description,
        trade=data.trade,
        trades=data.trades or [],
        bid_due_date=data.bid_due_date,
        pre_bid_meeting_date=data.pre_bid_meeting_date,
        estimated_value=_dollars(data.estimated_value_cents) if data.estimated_value_cents else None,
        requirements=data.requirements,
        scope_documents=data.scope_documents or [],
        status="DRAFT",
    )
    db.add(pkg)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="bid_package_created",
        event_data={"number": number, "title": data.title},
    )
    db.add(event)

    await db.flush()
    return pkg


async def list_packages(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[BidPackage], int]:
    query = select(BidPackage).where(
        BidPackage.project_id == project_id,
        BidPackage.deleted_at.is_(None),
    )

    if status:
        query = query.where(BidPackage.status == status)
    if search:
        query = query.where(
            or_(
                BidPackage.title.ilike(f"%{search}%"),
                BidPackage.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(BidPackage, sort, BidPackage.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_package(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
) -> BidPackage:
    result = await db.execute(
        select(BidPackage).where(
            BidPackage.id == package_id,
            BidPackage.project_id == project_id,
            BidPackage.deleted_at.is_(None),
        )
    )
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(404, "Bid package not found")
    return pkg


async def update_package(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: BidPackageUpdate,
) -> BidPackage:
    pkg = await get_package(db, package_id, project_id)
    if pkg.status in ("CLOSED", "AWARDED"):
        raise HTTPException(400, "Cannot edit a closed or awarded bid package")

    update_data = data.model_dump(exclude_unset=True)
    if "estimated_value_cents" in update_data:
        val = update_data.pop("estimated_value_cents")
        update_data["estimated_value"] = _dollars(val) if val else None

    for key, value in update_data.items():
        if hasattr(pkg, key):
            setattr(pkg, key, value)

    await db.flush()
    return pkg


async def delete_package(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> BidPackage:
    pkg = await get_package(db, package_id, project_id)
    if pkg.status != "DRAFT":
        raise HTTPException(400, "Only draft bid packages can be deleted")
    pkg.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return pkg


async def distribute_package(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: DistributeBidPackageRequest,
) -> BidPackage:
    """DRAFT -> PUBLISHED. Set invited_sub_ids, notify subs."""
    pkg = await get_package(db, package_id, project_id)
    if pkg.status != "DRAFT":
        raise HTTPException(400, "Only draft packages can be distributed")

    pkg.status = "PUBLISHED"
    pkg.invited_sub_ids = [str(sid) for sid in data.invited_sub_ids]

    # Notify each invited sub
    for sub_id in data.invited_sub_ids:
        notification = Notification(
            user_type="SUB_USER",
            user_id=sub_id,
            type="invited_to_bid",
            title=f"Invited to bid on {format_number('bid_package', pkg.number)}: {pkg.title}",
            body="You have been invited to submit a bid.",
            source_type="bid_package",
            source_id=pkg.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="bid_package_distributed",
        event_data={"package_number": pkg.number, "invited_count": len(data.invited_sub_ids)},
    )
    db.add(event)

    await db.flush()
    return pkg


async def close_bidding(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> BidPackage:
    """PUBLISHED -> CLOSED."""
    pkg = await get_package(db, package_id, project_id)
    if pkg.status != "PUBLISHED":
        raise HTTPException(400, "Only published packages can be closed")
    pkg.status = "CLOSED"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="bid_package_closed",
        event_data={"package_number": pkg.number},
    )
    db.add(event)

    await db.flush()
    return pkg


async def compare_bids(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
) -> dict:
    """Compare all submissions for a package."""
    pkg = await get_package(db, package_id, project_id)

    result = await db.execute(
        select(BidSubmission).where(
            BidSubmission.bid_package_id == package_id,
            BidSubmission.status == "SUBMITTED",
        )
    )
    submissions = result.scalars().all()

    if not submissions:
        return {
            "submissions": [],
            "lowest_amount_cents": 0,
            "highest_amount_cents": 0,
            "average_amount_cents": 0,
            "recommended_submission_id": None,
        }

    amounts = [_cents(s.total_amount) for s in submissions if s.total_amount]
    lowest = min(amounts) if amounts else 0
    highest = max(amounts) if amounts else 0
    average = int(sum(amounts) / len(amounts)) if amounts else 0

    # Recommend lowest bidder
    recommended = None
    if amounts:
        for s in submissions:
            if _cents(s.total_amount) == lowest:
                recommended = s.id
                break

    return {
        "submissions": [format_submission_response(s) for s in submissions],
        "lowest_amount_cents": lowest,
        "highest_amount_cents": highest,
        "average_amount_cents": average,
        "recommended_submission_id": recommended,
    }


async def award_bid(
    db: AsyncSession,
    package_id: uuid.UUID,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: AwardBidRequest,
) -> BidPackage:
    """CLOSED -> AWARDED. Create ProjectAssignment for winning sub."""
    pkg = await get_package(db, package_id, project_id)
    if pkg.status != "CLOSED":
        raise HTTPException(400, "Only closed packages can be awarded")

    # Get winning submission
    result = await db.execute(
        select(BidSubmission).where(BidSubmission.id == data.submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(404, "Submission not found")

    pkg.status = "AWARDED"
    pkg.awarded_sub_id = submission.sub_company_id
    pkg.awarded_at = datetime.now(timezone.utc)

    # Update submission statuses
    all_subs = await db.execute(
        select(BidSubmission).where(BidSubmission.bid_package_id == package_id)
    )
    for s in all_subs.scalars().all():
        if s.id == data.submission_id:
            s.status = "ACCEPTED"
        elif s.status == "SUBMITTED":
            s.status = "REJECTED"

    # Create ProjectAssignment for winning sub
    assignment = ProjectAssignment(
        project_id=project_id,
        assignee_type="SUB_COMPANY",
        assignee_id=submission.sub_company_id,
        trade=data.trade or (pkg.trade if pkg.trade else None),
        contract_value=submission.total_amount,
        assigned_by_user_id=user["user_id"],
    )
    db.add(assignment)

    # Notify winning sub
    notification = Notification(
        user_type="SUB_USER",
        user_id=submission.sub_company_id,
        type="bid_result",
        title=f"You have been awarded {format_number('bid_package', pkg.number)}: {pkg.title}",
        body="Congratulations! Your bid has been selected.",
        source_type="bid_package",
        source_id=pkg.id,
    )
    db.add(notification)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="bid_awarded",
        event_data={"package_number": pkg.number, "awarded_sub_id": str(submission.sub_company_id)},
    )
    db.add(event)

    await db.flush()
    return pkg


# ============================================================
# SUBMISSIONS
# ============================================================

async def create_submission(
    db: AsyncSession,
    package_id: uuid.UUID,
    sub_company_id: uuid.UUID,
    user: dict,
    data: BidSubmissionCreate,
) -> BidSubmission:
    submission = BidSubmission(
        bid_package_id=package_id,
        sub_company_id=sub_company_id,
        total_amount=_dollars(data.total_amount_cents) if data.total_amount_cents else None,
        line_items=data.line_items or [],
        qualifications=data.qualifications,
        schedule_duration_days=data.schedule_duration_days,
        exclusions=data.exclusions,
        inclusions=data.inclusions,
        notes=data.notes,
        status="DRAFT",
    )
    db.add(submission)
    await db.flush()
    return submission


async def update_submission(
    db: AsyncSession,
    submission_id: uuid.UUID,
    user: dict,
    data: BidSubmissionUpdate,
) -> BidSubmission:
    result = await db.execute(
        select(BidSubmission).where(BidSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(404, "Submission not found")
    if submission.status != "DRAFT":
        raise HTTPException(400, "Only draft submissions can be edited")

    update_data = data.model_dump(exclude_unset=True)
    if "total_amount_cents" in update_data:
        val = update_data.pop("total_amount_cents")
        update_data["total_amount"] = _dollars(val) if val else None

    for key, value in update_data.items():
        if hasattr(submission, key):
            setattr(submission, key, value)

    await db.flush()
    return submission


async def submit_bid(
    db: AsyncSession,
    submission_id: uuid.UUID,
    user: dict,
) -> BidSubmission:
    """DRAFT -> SUBMITTED."""
    result = await db.execute(
        select(BidSubmission).where(BidSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(404, "Submission not found")
    if submission.status != "DRAFT":
        raise HTTPException(400, "Only draft submissions can be submitted")

    # Validate package is published
    pkg_result = await db.execute(
        select(BidPackage).where(BidPackage.id == submission.bid_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if not pkg or pkg.status != "PUBLISHED":
        raise HTTPException(400, "Bid package is not accepting submissions")

    # Check due date
    if pkg.bid_due_date and pkg.bid_due_date < datetime.now(timezone.utc):
        raise HTTPException(400, "Bid due date has passed")

    submission.status = "SUBMITTED"
    submission.submitted_at = datetime.now(timezone.utc)

    # Notify GC
    notification = Notification(
        user_type="GC_USER",
        user_id=pkg.created_by,
        type="new_sub_bid",
        title=f"New bid received for {format_number('bid_package', pkg.number)}",
        body="A subcontractor has submitted a bid.",
        source_type="bid_package",
        source_id=pkg.id,
    )
    db.add(notification)

    await db.flush()
    return submission


async def list_submissions_for_package(
    db: AsyncSession,
    package_id: uuid.UUID,
) -> list[BidSubmission]:
    result = await db.execute(
        select(BidSubmission)
        .where(BidSubmission.bid_package_id == package_id)
        .order_by(BidSubmission.created_at.asc())
    )
    return result.scalars().all()


async def get_my_submission(
    db: AsyncSession,
    package_id: uuid.UUID,
    sub_company_id: uuid.UUID,
) -> BidSubmission | None:
    result = await db.execute(
        select(BidSubmission).where(
            BidSubmission.bid_package_id == package_id,
            BidSubmission.sub_company_id == sub_company_id,
        )
    )
    return result.scalar_one_or_none()


def format_submission_response(submission: BidSubmission, sub_company_name: str | None = None) -> dict:
    return {
        "id": submission.id,
        "bid_package_id": submission.bid_package_id,
        "sub_company_id": submission.sub_company_id,
        "sub_company_name": sub_company_name,
        "total_amount_cents": _cents(submission.total_amount),
        "line_items": submission.line_items if submission.line_items else [],
        "qualifications": submission.qualifications,
        "schedule_duration_days": submission.schedule_duration_days,
        "exclusions": submission.exclusions,
        "inclusions": submission.inclusions,
        "notes": submission.notes,
        "status": submission.status,
        "submitted_at": submission.submitted_at,
        "created_at": submission.created_at,
    }


async def format_package_response(
    db: AsyncSession,
    pkg: BidPackage,
    created_by_name: str | None = None,
) -> dict:
    # Count submissions
    count_result = await db.execute(
        select(func.count()).select_from(BidSubmission).where(
            BidSubmission.bid_package_id == pkg.id,
        )
    )
    submission_count = count_result.scalar() or 0

    return {
        "id": pkg.id,
        "project_id": pkg.project_id,
        "number": pkg.number,
        "formatted_number": format_number("bid_package", pkg.number),
        "title": pkg.title,
        "description": pkg.description,
        "trade": pkg.trade,
        "trades": pkg.trades if pkg.trades else [],
        "status": pkg.status,
        "bid_due_date": pkg.bid_due_date,
        "pre_bid_meeting_date": pkg.pre_bid_meeting_date,
        "estimated_value_cents": _cents(pkg.estimated_value),
        "requirements": pkg.requirements,
        "scope_documents": pkg.scope_documents if pkg.scope_documents else [],
        "invited_sub_ids": pkg.invited_sub_ids if pkg.invited_sub_ids else [],
        "submission_count": submission_count,
        "awarded_sub_id": pkg.awarded_sub_id,
        "awarded_at": pkg.awarded_at,
        "created_by": pkg.created_by,
        "created_by_name": created_by_name,
        "created_at": pkg.created_at,
        "updated_at": pkg.updated_at,
    }
