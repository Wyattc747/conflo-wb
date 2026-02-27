"""Notification router — GC, Sub, Owner portals."""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import (
    dismiss_notification,
    format_notification_response,
    get_preferences,
    get_unread_count,
    list_notifications,
    mark_all_read,
    mark_read,
    update_preferences,
)

gc_router = APIRouter(prefix="/api/gc/notifications", tags=["notifications"])
sub_router = APIRouter(prefix="/api/sub/notifications", tags=["notifications"])
owner_router = APIRouter(prefix="/api/owner/notifications", tags=["notifications"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ── Shared logic ──


async def _list(request, page, per_page, unread_only, db):
    user = _get_user(request)
    notifications, total = await list_notifications(
        db, user["user_type"], user["user_id"], page, per_page, unread_only,
    )
    data = [NotificationResponse.model_validate(format_notification_response(n)) for n in notifications]
    return NotificationListResponse(
        data=data,
        meta=PaginationMeta(
            page=page, per_page=per_page, total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


async def _unread_count(request, db):
    user = _get_user(request)
    count = await get_unread_count(db, user["user_type"], user["user_id"])
    return {"data": UnreadCountResponse(count=count).model_dump(), "meta": {}}


async def _mark_read(request, notification_id, db):
    user = _get_user(request)
    n = await mark_read(db, notification_id, user["user_type"], user["user_id"])
    return {"data": format_notification_response(n), "meta": {}}


async def _mark_all_read(request, db):
    user = _get_user(request)
    count = await mark_all_read(db, user["user_type"], user["user_id"])
    return {"data": {"marked_read": count}, "meta": {}}


async def _dismiss(request, notification_id, db):
    user = _get_user(request)
    await dismiss_notification(db, notification_id, user["user_type"], user["user_id"])
    return {"data": {"id": str(notification_id), "dismissed": True}, "meta": {}}


async def _get_prefs(request, db):
    user = _get_user(request)
    prefs = await get_preferences(db, user["user_type"], user["user_id"])
    return {"data": prefs, "meta": {}}


async def _update_prefs(request, body, db):
    user = _get_user(request)
    current = await get_preferences(db, user["user_type"], user["user_id"])
    if body.email_enabled is not None:
        current["email_enabled"] = body.email_enabled
    if body.email_categories is not None:
        current.setdefault("email_categories", {}).update(body.email_categories)
    prefs = await update_preferences(db, user["user_type"], user["user_id"], current)
    return {"data": prefs, "meta": {}}


# ── GC Router ──


@gc_router.get("")
async def gc_list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await _list(request, page, per_page, unread_only, db)


@gc_router.get("/unread-count")
async def gc_unread_count(request: Request, db: AsyncSession = Depends(get_db)):
    return await _unread_count(request, db)


@gc_router.post("/{notification_id}/read")
async def gc_mark_read(
    request: Request, notification_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    return await _mark_read(request, notification_id, db)


@gc_router.post("/read-all")
async def gc_mark_all_read(request: Request, db: AsyncSession = Depends(get_db)):
    return await _mark_all_read(request, db)


@gc_router.delete("/{notification_id}")
async def gc_dismiss(
    request: Request, notification_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    return await _dismiss(request, notification_id, db)


@gc_router.get("/preferences")
async def gc_get_preferences(request: Request, db: AsyncSession = Depends(get_db)):
    return await _get_prefs(request, db)


@gc_router.patch("/preferences")
async def gc_update_preferences(
    request: Request, body: NotificationPreferencesUpdate, db: AsyncSession = Depends(get_db),
):
    return await _update_prefs(request, body, db)


# ── Sub Router ──


@sub_router.get("")
async def sub_list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await _list(request, page, per_page, unread_only, db)


@sub_router.get("/unread-count")
async def sub_unread_count(request: Request, db: AsyncSession = Depends(get_db)):
    return await _unread_count(request, db)


@sub_router.post("/{notification_id}/read")
async def sub_mark_read(
    request: Request, notification_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    return await _mark_read(request, notification_id, db)


@sub_router.post("/read-all")
async def sub_mark_all_read(request: Request, db: AsyncSession = Depends(get_db)):
    return await _mark_all_read(request, db)


# ── Owner Router ──


@owner_router.get("")
async def owner_list_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await _list(request, page, per_page, unread_only, db)


@owner_router.get("/unread-count")
async def owner_unread_count(request: Request, db: AsyncSession = Depends(get_db)):
    return await _unread_count(request, db)


@owner_router.post("/{notification_id}/read")
async def owner_mark_read(
    request: Request, notification_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    return await _mark_read(request, notification_id, db)


@owner_router.post("/read-all")
async def owner_mark_all_read(request: Request, db: AsyncSession = Depends(get_db)):
    return await _mark_all_read(request, db)
