"""Submittal service — CRUD, review, and revision logic."""
import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submittal import Submittal
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.submittal import (
    SubmittalCreate,
    SubmittalUpdate,
    SubmittalRevisionCreate,
    SubmittalReviewRequest,
)
from app.services.numbering_service import format_number, get_next_number, get_next_submittal_revision

REVIEW_DECISIONS = {"APPROVED", "APPROVED_AS_NOTED", "REVISE_AND_RESUBMIT", "REJECTED"}


async def create_submittal(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: SubmittalCreate,
) -> Submittal:
    base_number = await get_next_number(db, project_id, "submittal")

    submittal = Submittal(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=base_number,
        revision=0,
        title=data.title,
        spec_section=data.spec_section,
        description=data.description,
        submittal_type=data.submittal_type,
        submitted_by_sub_id=data.sub_company_id,
        assigned_to=data.assigned_to,
        due_date=datetime.combine(data.due_date, datetime.min.time()) if data.due_date else None,
        cost_code_id=data.cost_code_id,
        drawing_reference=data.drawing_reference,
        lead_time_days=data.lead_time_days,
        status="DRAFT",
    )
    db.add(submittal)

    if data.assigned_to:
        notification = Notification(
            user_type="GC_USER",
            user_id=data.assigned_to,
            type="submittal_assigned",
            title=f"New submittal {format_number('submittal', base_number, 0)}: {data.title}",
            body="You have been assigned to review this submittal.",
            source_type="submittal",
            source_id=submittal.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="submittal_created",
        event_data={"submittal_number": format_number("submittal", base_number, 0), "title": data.title},
    )
    db.add(event)

    await db.flush()
    return submittal


async def list_submittals(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    submittal_type: str | None = None,
    sub_company_id: uuid.UUID | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
    latest_only: bool = True,
) -> tuple[list[Submittal], int]:
    query = select(Submittal).where(
        Submittal.project_id == project_id,
        Submittal.deleted_at.is_(None),
    )

    if latest_only:
        # Subquery to get max revision per base number
        latest_sq = (
            select(
                Submittal.number,
                func.max(Submittal.revision).label("max_rev"),
            )
            .where(Submittal.project_id == project_id, Submittal.deleted_at.is_(None))
            .group_by(Submittal.number)
            .subquery()
        )
        query = query.join(
            latest_sq,
            (Submittal.number == latest_sq.c.number)
            & (Submittal.revision == latest_sq.c.max_rev),
        )

    if status:
        query = query.where(Submittal.status == status)
    if submittal_type:
        query = query.where(Submittal.submittal_type == submittal_type)
    if sub_company_id:
        query = query.where(Submittal.submitted_by_sub_id == sub_company_id)
    if search:
        query = query.where(
            or_(
                Submittal.title.ilike(f"%{search}%"),
                Submittal.spec_section.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Submittal, sort, Submittal.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_submittal(
    db: AsyncSession,
    submittal_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Submittal:
    result = await db.execute(
        select(Submittal).where(
            Submittal.id == submittal_id,
            Submittal.project_id == project_id,
            Submittal.deleted_at.is_(None),
        )
    )
    submittal = result.scalar_one_or_none()
    if not submittal:
        raise HTTPException(404, "Submittal not found")
    return submittal


async def update_submittal(
    db: AsyncSession,
    submittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: SubmittalUpdate,
) -> Submittal:
    submittal = await get_submittal(db, submittal_id, project_id)
    if submittal.status != "DRAFT":
        raise HTTPException(400, "Can only edit submittals in DRAFT status")

    update_data = data.model_dump(exclude_unset=True)

    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = datetime.combine(update_data["due_date"], datetime.min.time())

    # Map schema field to model field
    if "sub_company_id" in update_data:
        update_data["submitted_by_sub_id"] = update_data.pop("sub_company_id")

    for key, value in update_data.items():
        if hasattr(submittal, key):
            setattr(submittal, key, value)

    await db.flush()
    return submittal


async def submit_submittal(
    db: AsyncSession,
    submittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Submittal:
    """DRAFT → SUBMITTED."""
    submittal = await get_submittal(db, submittal_id, project_id)
    if submittal.status != "DRAFT":
        raise HTTPException(400, "Only DRAFT submittals can be submitted")

    submittal.status = "SUBMITTED"

    if submittal.assigned_to:
        notification = Notification(
            user_type="GC_USER",
            user_id=submittal.assigned_to,
            type="submittal_submitted",
            title=f"{format_number('submittal', submittal.number, submittal.revision)} submitted for review",
            body=f"Submittal '{submittal.title}' has been submitted.",
            source_type="submittal",
            source_id=submittal.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="submittal_submitted",
        event_data={"submittal_number": format_number("submittal", submittal.number, submittal.revision)},
    )
    db.add(event)

    await db.flush()
    return submittal


async def review_submittal(
    db: AsyncSession,
    submittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: SubmittalReviewRequest,
) -> Submittal:
    """Review decision: APPROVED, APPROVED_AS_NOTED, REVISE_AND_RESUBMIT, REJECTED."""
    submittal = await get_submittal(db, submittal_id, project_id)
    if submittal.status not in ("SUBMITTED", "IN_REVIEW"):
        raise HTTPException(400, "Submittal must be submitted or in review to make a decision")

    if data.decision not in REVIEW_DECISIONS:
        raise HTTPException(400, f"Invalid decision. Must be one of: {REVIEW_DECISIONS}")

    submittal.status = data.decision
    submittal.reviewer_id = user["user_id"]
    submittal.reviewed_at = datetime.utcnow()
    submittal.review_notes = data.notes

    # Notify creator
    notification = Notification(
        user_type="GC_USER",
        user_id=submittal.created_by,
        type="submittal_decision",
        title=f"{format_number('submittal', submittal.number, submittal.revision)}: {data.decision.replace('_', ' ').title()}",
        body=data.notes or f"Submittal has been {data.decision.lower().replace('_', ' ')}.",
        source_type="submittal",
        source_id=submittal.id,
    )
    db.add(notification)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="submittal_reviewed",
        event_data={
            "submittal_number": format_number("submittal", submittal.number, submittal.revision),
            "decision": data.decision,
        },
    )
    db.add(event)

    await db.flush()
    return submittal


async def create_revision(
    db: AsyncSession,
    submittal_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: SubmittalRevisionCreate,
) -> Submittal:
    """Create a new revision after REVISE_AND_RESUBMIT."""
    original = await get_submittal(db, submittal_id, project_id)
    if original.status != "REVISE_AND_RESUBMIT":
        raise HTTPException(400, "Can only revise submittals marked for resubmission")

    next_rev = await get_next_submittal_revision(db, project_id, original.number)

    new_submittal = Submittal(
        organization_id=original.organization_id,
        project_id=original.project_id,
        created_by=user["user_id"],
        number=original.number,
        revision=next_rev,
        parent_submittal_id=original.id,
        title=original.title,
        spec_section=original.spec_section,
        description=data.description or original.description,
        submittal_type=original.submittal_type,
        submitted_by_sub_id=original.submitted_by_sub_id,
        assigned_to=original.assigned_to,
        due_date=original.due_date,
        cost_code_id=original.cost_code_id,
        drawing_reference=original.drawing_reference,
        lead_time_days=original.lead_time_days,
        status="DRAFT",
    )
    db.add(new_submittal)

    event = EventLog(
        organization_id=original.organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="submittal_revision_created",
        event_data={
            "submittal_number": format_number("submittal", original.number, next_rev),
            "original_id": str(original.id),
        },
    )
    db.add(event)

    await db.flush()
    return new_submittal


async def get_revision_history(
    db: AsyncSession,
    project_id: uuid.UUID,
    base_number: int,
) -> list[Submittal]:
    """Get all revisions of a submittal base number."""
    result = await db.execute(
        select(Submittal)
        .where(
            Submittal.project_id == project_id,
            Submittal.number == base_number,
            Submittal.deleted_at.is_(None),
        )
        .order_by(Submittal.revision.asc())
    )
    return result.scalars().all()


def format_submittal_response(
    submittal: Submittal,
    created_by_name: str | None = None,
    assigned_to_name: str | None = None,
    reviewed_by_name: str | None = None,
    sub_company_name: str | None = None,
    revision_history: list | None = None,
    comments_count: int = 0,
) -> dict:
    """Convert Submittal ORM model to response dict."""
    days_open = None
    if submittal.status not in ("APPROVED", "REJECTED") and submittal.created_at:
        days_open = (datetime.utcnow() - submittal.created_at).days

    due_date = submittal.due_date
    if hasattr(due_date, "date") and due_date:
        due_date = due_date.date()

    return {
        "id": submittal.id,
        "project_id": submittal.project_id,
        "number": submittal.number,
        "revision": submittal.revision,
        "formatted_number": format_number("submittal", submittal.number, submittal.revision),
        "title": submittal.title,
        "spec_section": submittal.spec_section,
        "description": submittal.description,
        "submittal_type": submittal.submittal_type,
        "status": submittal.status,
        "sub_company_id": submittal.submitted_by_sub_id,
        "sub_company_name": sub_company_name,
        "assigned_to": submittal.assigned_to,
        "assigned_to_name": assigned_to_name,
        "due_date": due_date,
        "days_open": days_open,
        "cost_code_id": submittal.cost_code_id,
        "drawing_reference": submittal.drawing_reference,
        "lead_time_days": submittal.lead_time_days,
        "review_notes": submittal.review_notes,
        "reviewed_by": submittal.reviewer_id,
        "reviewed_by_name": reviewed_by_name,
        "reviewed_at": submittal.reviewed_at,
        "revision_history": revision_history or [],
        "comments_count": comments_count,
        "created_by": submittal.created_by,
        "created_by_name": created_by_name,
        "created_at": submittal.created_at,
        "updated_at": submittal.updated_at,
    }
