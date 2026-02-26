import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drawing import Drawing, DrawingSheet
from app.models.event_log import EventLog
from app.schemas.drawing import DrawingSetCreate, DrawingSetUpdate, DrawingSheetCreate, DrawingSheetUpdate


async def create_set(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: DrawingSetCreate,
) -> Drawing:
    drawing = Drawing(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        set_number=data.set_number,
        title=data.title,
        discipline=data.discipline,
        description=data.description,
        received_from=data.received_from,
        is_current_set=True,
    )
    db.add(drawing)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="drawing_set_created",
        event_data={"set_number": data.set_number, "title": data.title},
    )
    db.add(event)

    await db.flush()
    return drawing


async def list_sets(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    discipline: str | None = None,
    is_current_set: bool | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[Drawing], int]:
    query = select(Drawing).where(Drawing.project_id == project_id, Drawing.deleted_at.is_(None))

    if discipline:
        query = query.where(Drawing.discipline == discipline)
    if is_current_set is not None:
        query = query.where(Drawing.is_current_set == is_current_set)
    if search:
        query = query.where(
            or_(
                Drawing.title.ilike(f"%{search}%"),
                Drawing.set_number.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Drawing, sort, Drawing.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_set(
    db: AsyncSession,
    drawing_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Drawing:
    result = await db.execute(
        select(Drawing).where(
            Drawing.id == drawing_id,
            Drawing.project_id == project_id,
            Drawing.deleted_at.is_(None),
        )
    )
    drawing = result.scalar_one_or_none()
    if not drawing:
        raise HTTPException(404, "Drawing set not found")
    return drawing


async def update_set(
    db: AsyncSession,
    drawing_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: DrawingSetUpdate,
) -> Drawing:
    drawing = await get_set(db, drawing_id, project_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(drawing, key):
            setattr(drawing, key, value)

    await db.flush()
    return drawing


async def delete_set(
    db: AsyncSession,
    drawing_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Drawing:
    drawing = await get_set(db, drawing_id, project_id)
    drawing.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return drawing


async def mark_current_set(
    db: AsyncSession,
    drawing_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Drawing:
    drawing = await get_set(db, drawing_id, project_id)

    # Unmark all other sets with the same set_number in this project
    result = await db.execute(
        select(Drawing).where(
            Drawing.project_id == project_id,
            Drawing.set_number == drawing.set_number,
            Drawing.deleted_at.is_(None),
        )
    )
    for d in result.scalars().all():
        d.is_current_set = False

    drawing.is_current_set = True
    await db.flush()
    return drawing


# ============================================================
# SHEETS
# ============================================================

async def list_sheets(
    db: AsyncSession,
    drawing_id: uuid.UUID,
) -> list[DrawingSheet]:
    result = await db.execute(
        select(DrawingSheet)
        .where(DrawingSheet.drawing_id == drawing_id)
        .order_by(DrawingSheet.sheet_number.asc())
    )
    return result.scalars().all()


async def get_sheet(
    db: AsyncSession,
    sheet_id: uuid.UUID,
) -> DrawingSheet:
    result = await db.execute(
        select(DrawingSheet).where(DrawingSheet.id == sheet_id)
    )
    sheet = result.scalar_one_or_none()
    if not sheet:
        raise HTTPException(404, "Drawing sheet not found")
    return sheet


async def add_sheet(
    db: AsyncSession,
    drawing_id: uuid.UUID,
    user: dict,
    data: DrawingSheetCreate,
) -> DrawingSheet:
    sheet = DrawingSheet(
        drawing_id=drawing_id,
        sheet_number=data.sheet_number,
        title=data.title,
        description=data.description,
        revision=data.revision,
        file_id=data.file_id,
        is_current=True,
        uploaded_by=user["user_id"],
    )
    db.add(sheet)
    await db.flush()
    return sheet


async def update_sheet(
    db: AsyncSession,
    sheet_id: uuid.UUID,
    user: dict,
    data: DrawingSheetUpdate,
) -> DrawingSheet:
    sheet = await get_sheet(db, sheet_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(sheet, key):
            setattr(sheet, key, value)

    await db.flush()
    return sheet


async def remove_sheet(
    db: AsyncSession,
    sheet_id: uuid.UUID,
    user: dict,
) -> None:
    sheet = await get_sheet(db, sheet_id)
    await db.delete(sheet)
    await db.flush()


async def upload_revision(
    db: AsyncSession,
    sheet_id: uuid.UUID,
    user: dict,
    new_revision: str,
    file_id: uuid.UUID | None = None,
) -> DrawingSheet:
    old_sheet = await get_sheet(db, sheet_id)
    old_sheet.is_current = False

    new_sheet = DrawingSheet(
        drawing_id=old_sheet.drawing_id,
        sheet_number=old_sheet.sheet_number,
        title=old_sheet.title,
        description=old_sheet.description,
        revision=new_revision,
        revision_date=datetime.now(timezone.utc),
        file_id=file_id or old_sheet.file_id,
        is_current=True,
        uploaded_by=user["user_id"],
    )
    db.add(new_sheet)
    await db.flush()
    return new_sheet


def format_sheet_response(sheet: DrawingSheet) -> dict:
    return {
        "id": sheet.id,
        "drawing_id": sheet.drawing_id,
        "sheet_number": sheet.sheet_number,
        "title": sheet.title,
        "description": sheet.description,
        "revision": sheet.revision,
        "revision_date": sheet.revision_date,
        "is_current": sheet.is_current,
        "file_id": sheet.file_id,
        "uploaded_by": sheet.uploaded_by,
        "created_at": sheet.created_at,
    }


async def format_drawing_set_response(
    db: AsyncSession,
    drawing: Drawing,
    created_by_name: str | None = None,
) -> dict:
    sheets = await list_sheets(db, drawing.id)

    return {
        "id": drawing.id,
        "project_id": drawing.project_id,
        "set_number": drawing.set_number,
        "title": drawing.title,
        "discipline": drawing.discipline,
        "description": drawing.description,
        "received_from": drawing.received_from,
        "is_current_set": drawing.is_current_set,
        "sheet_count": len(sheets),
        "sheets": [format_sheet_response(s) for s in sheets],
        "created_by": drawing.created_by,
        "created_by_name": created_by_name,
        "created_at": drawing.created_at,
        "updated_at": drawing.updated_at,
    }
