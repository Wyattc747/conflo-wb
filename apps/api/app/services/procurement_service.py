import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement_item import ProcurementItem
from app.models.event_log import EventLog
from app.schemas.procurement import ProcurementCreate, ProcurementUpdate, ProcurementTransition


def _cents(val) -> int:
    if val is None:
        return 0
    return int(Decimal(str(val)) * 100)


def _dollars(cents: int) -> Decimal:
    return Decimal(cents) / 100


def _compute_order_by_date(required_on_site_date, lead_time_days):
    if required_on_site_date and lead_time_days:
        return required_on_site_date - timedelta(days=lead_time_days)
    return None


def _is_at_risk(item: ProcurementItem) -> bool:
    if item.status in ("DELIVERED", "INSTALLED"):
        return False
    order_date = _compute_order_by_date(item.required_on_site_date, item.lead_time_days)
    if order_date and order_date < datetime.now(timezone.utc):
        if item.status in ("IDENTIFIED", "QUOTED"):
            return True
    return False


VALID_TRANSITIONS = {
    "quote": ("IDENTIFIED", "QUOTED"),
    "order": ("QUOTED", "ORDERED"),
    "ship": ("ORDERED", "IN_TRANSIT"),
    "deliver": ("IN_TRANSIT", "DELIVERED"),
    "install": ("DELIVERED", "INSTALLED"),
}


async def create_procurement(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: ProcurementCreate,
) -> ProcurementItem:
    item = ProcurementItem(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        name=data.item_name,
        description=data.description,
        status="IDENTIFIED",
        category=data.category,
        spec_section=data.spec_section,
        quantity=data.quantity,
        unit=data.unit,
        vendor=data.vendor,
        vendor_contact=data.vendor_contact,
        vendor_phone=data.vendor_phone,
        vendor_email=data.vendor_email,
        estimated_cost=_dollars(data.estimated_cost_cents) if data.estimated_cost_cents else None,
        lead_time_days=data.lead_time_days,
        required_on_site_date=data.required_on_site_date,
        order_by_date=_compute_order_by_date(data.required_on_site_date, data.lead_time_days),
        assigned_to=data.assigned_to,
        sub_company_id=data.sub_company_id,
        linked_schedule_task_id=data.linked_schedule_task_id,
        notes=data.notes,
    )
    db.add(item)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="procurement_created",
        event_data={"item_name": data.item_name},
    )
    db.add(event)

    await db.flush()
    return item


async def list_procurement(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    category: str | None = None,
    vendor: str | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[ProcurementItem], int]:
    query = select(ProcurementItem).where(
        ProcurementItem.project_id == project_id,
        ProcurementItem.deleted_at.is_(None),
    )

    if status:
        query = query.where(ProcurementItem.status == status)
    if category:
        query = query.where(ProcurementItem.category == category)
    if vendor:
        query = query.where(ProcurementItem.vendor.ilike(f"%{vendor}%"))
    if search:
        query = query.where(
            or_(
                ProcurementItem.name.ilike(f"%{search}%"),
                ProcurementItem.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(ProcurementItem, sort, ProcurementItem.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_procurement(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ProcurementItem:
    result = await db.execute(
        select(ProcurementItem).where(
            ProcurementItem.id == item_id,
            ProcurementItem.project_id == project_id,
            ProcurementItem.deleted_at.is_(None),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Procurement item not found")
    return item


async def update_procurement(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: ProcurementUpdate,
) -> ProcurementItem:
    item = await get_procurement(db, item_id, project_id)

    update_data = data.model_dump(exclude_unset=True)

    # Map schema field to model field
    if "item_name" in update_data:
        update_data["name"] = update_data.pop("item_name")

    # Convert cents to dollars for storage
    if "estimated_cost_cents" in update_data:
        val = update_data.pop("estimated_cost_cents")
        update_data["estimated_cost"] = _dollars(val) if val else None
    if "actual_cost_cents" in update_data:
        val = update_data.pop("actual_cost_cents")
        update_data["actual_cost"] = _dollars(val) if val else None

    for key, value in update_data.items():
        if hasattr(item, key):
            setattr(item, key, value)

    # Recompute order_by_date
    item.order_by_date = _compute_order_by_date(item.required_on_site_date, item.lead_time_days)

    await db.flush()
    return item


async def delete_procurement(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> ProcurementItem:
    item = await get_procurement(db, item_id, project_id)
    item.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return item


async def transition_procurement(
    db: AsyncSession,
    item_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    action: str,
    data: ProcurementTransition | None = None,
) -> ProcurementItem:
    if action not in VALID_TRANSITIONS:
        raise HTTPException(400, f"Unknown transition: {action}")

    from_status, to_status = VALID_TRANSITIONS[action]
    item = await get_procurement(db, item_id, project_id)

    if item.status != from_status:
        raise HTTPException(400, f"Cannot {action}: item must be in {from_status} status (current: {item.status})")

    # Validate requirements
    if action == "order" and data:
        if data.po_number:
            item.po_number = data.po_number
    if action == "ship" and data:
        if data.tracking_number:
            item.tracking_number = data.tracking_number
    if action == "deliver" and data:
        if data.actual_delivery_date:
            item.actual_delivery_date = data.actual_delivery_date
        else:
            item.actual_delivery_date = datetime.now(timezone.utc)

    item.status = to_status

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type=f"procurement_{action}",
        event_data={"item_id": str(item_id), "new_status": to_status},
    )
    db.add(event)

    await db.flush()
    return item


def format_procurement_response(item: ProcurementItem) -> dict:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "item_name": item.name,
        "description": item.description,
        "status": item.status,
        "category": item.category,
        "spec_section": item.spec_section,
        "quantity": item.quantity,
        "unit": item.unit,
        "vendor": item.vendor,
        "vendor_contact": item.vendor_contact,
        "vendor_phone": item.vendor_phone,
        "vendor_email": item.vendor_email,
        "estimated_cost_cents": _cents(item.estimated_cost),
        "actual_cost_cents": _cents(item.actual_cost),
        "po_number": item.po_number,
        "lead_time_days": item.lead_time_days,
        "required_on_site_date": item.required_on_site_date,
        "order_by_date": item.order_by_date,
        "expected_delivery_date": item.expected_delivery_date,
        "actual_delivery_date": item.actual_delivery_date,
        "tracking_number": item.tracking_number,
        "is_at_risk": _is_at_risk(item),
        "assigned_to": item.assigned_to,
        "sub_company_id": item.sub_company_id,
        "linked_schedule_task_id": item.linked_schedule_task_id,
        "notes": item.notes,
        "created_by": item.created_by,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }
