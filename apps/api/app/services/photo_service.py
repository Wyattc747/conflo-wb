import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.photo import Photo
from app.models.event_log import EventLog
from app.schemas.photo import PhotoCreate, PhotoUpdate


async def create_photo(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: PhotoCreate,
) -> Photo:
    photo = Photo(
        organization_id=organization_id,
        project_id=project_id,
        file_id=data.file_id,
        linked_type=data.linked_type,
        linked_id=data.linked_id,
        caption=data.caption,
        tags=data.tags or [],
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        uploaded_by=user["user_id"],
    )
    db.add(photo)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="photo_uploaded",
        event_data={"caption": data.caption},
    )
    db.add(event)

    await db.flush()
    return photo


async def list_photos(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    linked_type: str | None = None,
    linked_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[Photo], int]:
    query = select(Photo).where(Photo.project_id == project_id, Photo.deleted_at.is_(None))

    if linked_type:
        query = query.where(Photo.linked_type == linked_type)
    if linked_id:
        query = query.where(Photo.linked_id == linked_id)
    if date_from:
        query = query.where(Photo.created_at >= date_from)
    if date_to:
        query = query.where(Photo.created_at <= date_to)
    if search:
        query = query.where(
            or_(
                Photo.caption.ilike(f"%{search}%"),
                Photo.location.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Photo, sort, Photo.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_photo(
    db: AsyncSession,
    photo_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Photo:
    result = await db.execute(
        select(Photo).where(
            Photo.id == photo_id,
            Photo.project_id == project_id,
            Photo.deleted_at.is_(None),
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Photo not found")
    return photo


async def update_photo(
    db: AsyncSession,
    photo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: PhotoUpdate,
) -> Photo:
    photo = await get_photo(db, photo_id, project_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(photo, key):
            setattr(photo, key, value)

    await db.flush()
    return photo


async def delete_photo(
    db: AsyncSession,
    photo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Photo:
    photo = await get_photo(db, photo_id, project_id)
    photo.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return photo


def format_photo_response(
    photo: Photo,
    uploaded_by_name: str | None = None,
) -> dict:
    return {
        "id": photo.id,
        "project_id": photo.project_id,
        "file_id": photo.file_id,
        "linked_type": photo.linked_type,
        "linked_id": photo.linked_id,
        "caption": photo.caption,
        "tags": photo.tags if photo.tags else [],
        "location": photo.location,
        "latitude": photo.latitude,
        "longitude": photo.longitude,
        "uploaded_by": photo.uploaded_by,
        "uploaded_by_name": uploaded_by_name,
        "captured_at": photo.captured_at,
        "created_at": photo.created_at,
    }
