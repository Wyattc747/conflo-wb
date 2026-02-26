"""Todo CRUD router — GC and Sub portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.todo import (
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoUpdate,
)
from app.services.todo_service import (
    complete_todo,
    create_todo,
    delete_todo,
    format_todo_response,
    get_todo,
    list_todos,
    reopen_todo,
    start_todo,
    update_todo,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/todos", tags=["todos"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=TodoListResponse)
async def list_todos_endpoint(
    request: Request,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    category: str | None = Query(None),
    source_type: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    todos, total = await list_todos(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, priority=priority, assigned_to=assigned_to,
        category=category, source_type=source_type, search=search,
        sort=sort, order=order,
    )
    data = [TodoResponse.model_validate(format_todo_response(t)) for t in todos]
    return TodoListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_todo_endpoint(
    request: Request, project_id: uuid.UUID, body: TodoCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    todo = await create_todo(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{todo_id}", response_model=dict)
async def get_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    todo = await get_todo(db, todo_id, project_id)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{todo_id}", response_model=dict)
async def update_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID, body: TodoUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    todo = await update_todo(db, todo_id, project_id, user, body)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{todo_id}", status_code=200)
async def delete_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_todo(db, todo_id, project_id, user)
    return {"data": {"id": str(todo_id), "deleted": True}, "meta": {}}


@gc_router.post("/{todo_id}/start", response_model=dict)
async def start_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    todo = await start_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{todo_id}/complete", response_model=dict)
async def complete_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    todo = await complete_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{todo_id}/reopen", response_model=dict)
async def reopen_todo_endpoint(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    todo = await reopen_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


# ============================================================
# SUB PORTAL
# ============================================================

sub_router = APIRouter(prefix="/api/sub/projects/{project_id}/todos", tags=["sub-todos"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("", response_model=TodoListResponse)
async def sub_list_todos(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("created_at"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    todos, total = await list_todos(db, project_id=project_id, page=page, per_page=per_page,
                                     status=status, search=search, sort=sort, order=order)
    data = [TodoResponse.model_validate(format_todo_response(t)) for t in todos]
    return TodoListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@sub_router.get("/{todo_id}", response_model=dict)
async def sub_get_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    todo = await get_todo(db, todo_id, project_id)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@sub_router.post("", response_model=dict, status_code=201)
async def sub_create_todo(
    request: Request, project_id: uuid.UUID, body: TodoCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    todo = await create_todo(db, project_id=project_id, organization_id=user.get("organization_id"), user=user, data=body)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@sub_router.patch("/{todo_id}", response_model=dict)
async def sub_update_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID, body: TodoUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    todo = await update_todo(db, todo_id, project_id, user, body)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@sub_router.delete("/{todo_id}", status_code=200)
async def sub_delete_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    await delete_todo(db, todo_id, project_id, user)
    return {"data": {"id": str(todo_id), "deleted": True}, "meta": {}}


@sub_router.post("/{todo_id}/start", response_model=dict)
async def sub_start_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    todo = await start_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@sub_router.post("/{todo_id}/complete", response_model=dict)
async def sub_complete_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    todo = await complete_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}


@sub_router.post("/{todo_id}/reopen", response_model=dict)
async def sub_reopen_todo(
    request: Request, project_id: uuid.UUID, todo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    todo = await reopen_todo(db, todo_id, project_id, user)
    return {"data": TodoResponse.model_validate(format_todo_response(todo)).model_dump(mode="json"), "meta": {}}
