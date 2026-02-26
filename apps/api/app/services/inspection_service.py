"""Inspection service — Templates + Inspection CRUD + results submission."""
import uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inspection import Inspection
from app.models.inspection_template import InspectionTemplate
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.inspection import (
    InspectionCreate,
    InspectionUpdate,
    InspectionResultSubmit,
    InspectionTemplateCreate,
    InspectionTemplateUpdate,
)
from app.services.numbering_service import format_number, get_next_number


# ============================================================
# TEMPLATES
# ============================================================

async def create_template(
    db: AsyncSession,
    organization_id: uuid.UUID,
    data: InspectionTemplateCreate,
) -> InspectionTemplate:
    template = InspectionTemplate(
        organization_id=organization_id,
        name=data.name,
        fields=[item.model_dump() for item in data.checklist_items],
    )
    db.add(template)
    await db.flush()
    return template


async def list_templates(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> list[InspectionTemplate]:
    result = await db.execute(
        select(InspectionTemplate)
        .where(InspectionTemplate.organization_id == organization_id)
        .order_by(InspectionTemplate.name)
    )
    return result.scalars().all()


async def get_template(
    db: AsyncSession,
    template_id: uuid.UUID,
) -> InspectionTemplate:
    result = await db.execute(
        select(InspectionTemplate).where(InspectionTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Inspection template not found")
    return template


async def update_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    data: InspectionTemplateUpdate,
) -> InspectionTemplate:
    template = await get_template(db, template_id)
    update_data = data.model_dump(exclude_unset=True)

    if "checklist_items" in update_data and update_data["checklist_items"] is not None:
        update_data["fields"] = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in update_data.pop("checklist_items")
        ]
    else:
        update_data.pop("checklist_items", None)

    for key, value in update_data.items():
        if hasattr(template, key):
            setattr(template, key, value)

    await db.flush()
    return template


async def delete_template(
    db: AsyncSession,
    template_id: uuid.UUID,
) -> None:
    template = await get_template(db, template_id)
    await db.delete(template)
    await db.flush()


def format_template_response(template: InspectionTemplate) -> dict:
    return {
        "id": template.id,
        "organization_id": template.organization_id,
        "name": template.name,
        "description": None,
        "category": "GENERAL",
        "checklist_items": template.fields or [],
        "is_default": template.is_default,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


# ============================================================
# INSPECTIONS
# ============================================================

async def create_inspection(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: InspectionCreate,
) -> Inspection:
    number = await get_next_number(db, project_id, "inspection")

    title = data.title
    checklist = []
    if data.template_id:
        template = await get_template(db, data.template_id)
        if not title:
            title = template.name
        checklist = template.fields or []

    inspection = Inspection(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        number=number,
        title=title or "Inspection",
        template_id=data.template_id,
        category=data.category,
        scheduled_date=datetime.combine(data.scheduled_date, datetime.min.time()) if data.scheduled_date else None,
        scheduled_time=data.scheduled_time,
        location=data.location,
        inspector_name=data.inspector_name,
        inspector_company=data.inspector_company,
        notes=data.notes,
        form_data={"checklist": checklist},
        status="SCHEDULED",
    )
    db.add(inspection)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="inspection_created",
        event_data={"inspection_number": number, "title": title},
    )
    db.add(event)

    await db.flush()
    return inspection


async def list_inspections(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    sort: str = "number",
    order: str = "desc",
) -> tuple[list[Inspection], int]:
    query = select(Inspection).where(
        Inspection.project_id == project_id,
        Inspection.deleted_at.is_(None),
    )

    if status:
        query = query.where(Inspection.status == status)
    if category:
        query = query.where(Inspection.category == category)
    if search:
        query = query.where(Inspection.title.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Inspection, sort, Inspection.number)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Inspection:
    result = await db.execute(
        select(Inspection).where(
            Inspection.id == inspection_id,
            Inspection.project_id == project_id,
            Inspection.deleted_at.is_(None),
        )
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(404, "Inspection not found")
    return inspection


async def update_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: InspectionUpdate,
) -> Inspection:
    inspection = await get_inspection(db, inspection_id, project_id)
    if inspection.status in ("COMPLETED", "PASSED", "FAILED", "CONDITIONAL"):
        raise HTTPException(400, "Cannot edit completed inspections")

    update_data = data.model_dump(exclude_unset=True)
    if "scheduled_date" in update_data and update_data["scheduled_date"]:
        update_data["scheduled_date"] = datetime.combine(update_data["scheduled_date"], datetime.min.time())

    for key, value in update_data.items():
        if hasattr(inspection, key):
            setattr(inspection, key, value)

    await db.flush()
    return inspection


async def start_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Inspection:
    """SCHEDULED → IN_PROGRESS."""
    inspection = await get_inspection(db, inspection_id, project_id)
    if inspection.status != "SCHEDULED":
        raise HTTPException(400, "Only scheduled inspections can be started")

    inspection.status = "IN_PROGRESS"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="inspection_started",
        event_data={"inspection_number": inspection.number},
    )
    db.add(event)

    await db.flush()
    return inspection


async def complete_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: InspectionResultSubmit,
) -> Inspection:
    """Submit inspection results."""
    inspection = await get_inspection(db, inspection_id, project_id)
    if inspection.status not in ("SCHEDULED", "IN_PROGRESS"):
        raise HTTPException(400, "Inspection must be scheduled or in progress to submit results")

    if data.overall_result not in ("PASSED", "FAILED", "CONDITIONAL"):
        raise HTTPException(400, "Overall result must be PASSED, FAILED, or CONDITIONAL")

    inspection.checklist_results = [r.model_dump() for r in data.results]
    inspection.overall_result = data.overall_result
    inspection.status = data.overall_result
    inspection.completed_date = datetime.utcnow()
    if data.notes:
        inspection.notes = data.notes

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="inspection_completed",
        event_data={
            "inspection_number": inspection.number,
            "overall_result": data.overall_result,
        },
    )
    db.add(event)

    await db.flush()
    return inspection


def format_inspection_response(
    inspection: Inspection,
    created_by_name: str | None = None,
    template_name: str | None = None,
    comments_count: int = 0,
) -> dict:
    """Convert Inspection ORM model to response dict."""
    scheduled_date = inspection.scheduled_date
    if hasattr(scheduled_date, "date") and scheduled_date:
        scheduled_date = scheduled_date.date()

    return {
        "id": inspection.id,
        "project_id": inspection.project_id,
        "number": inspection.number,
        "formatted_number": format_number("inspection", inspection.number),
        "title": inspection.title,
        "template_id": inspection.template_id,
        "template_name": template_name,
        "category": inspection.category,
        "scheduled_date": scheduled_date,
        "scheduled_time": inspection.scheduled_time,
        "location": inspection.location,
        "inspector_name": inspection.inspector_name,
        "inspector_company": inspection.inspector_company,
        "status": inspection.status,
        "overall_result": inspection.overall_result,
        "checklist_results": inspection.checklist_results or [],
        "photo_ids": inspection.photo_ids or [],
        "notes": inspection.notes,
        "comments_count": comments_count,
        "created_by": inspection.created_by,
        "created_by_name": created_by_name,
        "created_at": inspection.created_at,
        "completed_at": inspection.completed_date,
        "updated_at": inspection.updated_at,
    }
