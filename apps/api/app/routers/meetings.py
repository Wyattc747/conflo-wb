"""Meeting CRUD router — GC portal only."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.meeting import (
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
    PublishMinutesRequest,
)
from app.services.meeting_service import (
    cancel_meeting,
    complete_meeting,
    create_meeting,
    delete_meeting,
    format_meeting_response,
    generate_recurring,
    get_meeting,
    list_meetings,
    publish_minutes,
    start_meeting,
    update_meeting,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/meetings", tags=["meetings"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=MeetingListResponse)
async def list_meetings_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None), meeting_type: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("scheduled_date"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    meetings, total = await list_meetings(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, meeting_type=meeting_type, search=search,
        sort=sort, order=order,
    )
    data = [MeetingResponse.model_validate(format_meeting_response(m)) for m in meetings]
    return MeetingListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_meeting_endpoint(
    request: Request, project_id: uuid.UUID, body: MeetingCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await create_meeting(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{meeting_id}", response_model=dict)
async def get_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    meeting = await get_meeting(db, meeting_id, project_id)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{meeting_id}", response_model=dict)
async def update_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID, body: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await update_meeting(db, meeting_id, project_id, user, body)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{meeting_id}", status_code=200)
async def delete_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_meeting(db, meeting_id, project_id, user)
    return {"data": {"id": str(meeting_id), "deleted": True}, "meta": {}}


@gc_router.post("/{meeting_id}/start", response_model=dict)
async def start_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await start_meeting(db, meeting_id, project_id, user)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{meeting_id}/complete", response_model=dict)
async def complete_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await complete_meeting(db, meeting_id, project_id, user)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{meeting_id}/cancel", response_model=dict)
async def cancel_meeting_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await cancel_meeting(db, meeting_id, project_id, user)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{meeting_id}/publish-minutes", response_model=dict)
async def publish_minutes_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    body: PublishMinutesRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    meeting = await publish_minutes(db, meeting_id, project_id, user["organization_id"], user, body)
    return {"data": MeetingResponse.model_validate(format_meeting_response(meeting)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{meeting_id}/generate-recurring", response_model=dict)
async def generate_recurring_endpoint(
    request: Request, project_id: uuid.UUID, meeting_id: uuid.UUID,
    count: int = Query(4, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    children = await generate_recurring(db, meeting_id, project_id, user["organization_id"], user, count)
    data = [MeetingResponse.model_validate(format_meeting_response(c)).model_dump(mode="json") for c in children]
    return {"data": data, "meta": {}}
