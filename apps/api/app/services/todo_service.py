import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.todo import TodoCreate, TodoUpdate


async def create_todo(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: TodoCreate,
) -> Todo:
    todo = Todo(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        due_date=datetime.combine(data.due_date, datetime.min.time()) if data.due_date else None,
        priority=data.priority,
        status="OPEN",
        category=data.category,
        cost_code_id=data.cost_code_id,
        source_type=data.source_type,
        source_id=data.source_id,
    )
    db.add(todo)

    if data.assigned_to:
        notification = Notification(
            user_type="GC_USER",
            user_id=data.assigned_to,
            type="todo_assigned",
            title=f"New task: {data.title}",
            body="You have been assigned a new task.",
            source_type="todo",
            source_id=todo.id,
        )
        db.add(notification)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="todo_created",
        event_data={"title": data.title},
    )
    db.add(event)

    await db.flush()
    return todo


async def list_todos(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: uuid.UUID | None = None,
    category: str | None = None,
    source_type: str | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[Todo], int]:
    query = select(Todo).where(Todo.project_id == project_id, Todo.deleted_at.is_(None))

    if status:
        query = query.where(Todo.status == status)
    if priority:
        query = query.where(Todo.priority == priority)
    if assigned_to:
        query = query.where(Todo.assigned_to == assigned_to)
    if category:
        query = query.where(Todo.category == category)
    if source_type:
        query = query.where(Todo.source_type == source_type)
    if search:
        query = query.where(
            or_(
                Todo.title.ilike(f"%{search}%"),
                Todo.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Todo, sort, Todo.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Todo:
    result = await db.execute(
        select(Todo).where(
            Todo.id == todo_id,
            Todo.project_id == project_id,
            Todo.deleted_at.is_(None),
        )
    )
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(404, "Task not found")
    return todo


async def update_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: TodoUpdate,
) -> Todo:
    todo = await get_todo(db, todo_id, project_id)
    if todo.status == "COMPLETED":
        raise HTTPException(400, "Cannot edit a completed task. Reopen first.")

    update_data = data.model_dump(exclude_unset=True)
    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = datetime.combine(
            update_data["due_date"], datetime.min.time()
        )

    for key, value in update_data.items():
        if hasattr(todo, key):
            setattr(todo, key, value)

    await db.flush()
    return todo


async def delete_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Todo:
    todo = await get_todo(db, todo_id, project_id)
    todo.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return todo


async def start_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Todo:
    """OPEN -> IN_PROGRESS"""
    todo = await get_todo(db, todo_id, project_id)
    if todo.status != "OPEN":
        raise HTTPException(400, "Only open tasks can be started")
    todo.status = "IN_PROGRESS"

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="todo_started",
        event_data={"todo_id": str(todo_id)},
    )
    db.add(event)

    await db.flush()
    return todo


async def complete_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Todo:
    """OPEN|IN_PROGRESS -> COMPLETED"""
    todo = await get_todo(db, todo_id, project_id)
    if todo.status not in ("OPEN", "IN_PROGRESS"):
        raise HTTPException(400, "Task must be open or in progress to complete")
    todo.status = "COMPLETED"
    todo.completed_at = datetime.now(timezone.utc)

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="todo_completed",
        event_data={"todo_id": str(todo_id)},
    )
    db.add(event)

    await db.flush()
    return todo


async def reopen_todo(
    db: AsyncSession,
    todo_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Todo:
    """COMPLETED -> OPEN"""
    todo = await get_todo(db, todo_id, project_id)
    if todo.status != "COMPLETED":
        raise HTTPException(400, "Only completed tasks can be reopened")
    todo.status = "OPEN"
    todo.completed_at = None

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="todo_reopened",
        event_data={"todo_id": str(todo_id)},
    )
    db.add(event)

    await db.flush()
    return todo


def format_todo_response(
    todo: Todo,
    created_by_name: str | None = None,
    assigned_to_name: str | None = None,
) -> dict:
    due_date = todo.due_date
    if hasattr(due_date, "date") and due_date:
        due_date = due_date.date()

    return {
        "id": todo.id,
        "project_id": todo.project_id,
        "title": todo.title,
        "description": todo.description,
        "status": todo.status,
        "priority": todo.priority,
        "assigned_to": todo.assigned_to,
        "assigned_to_name": assigned_to_name,
        "due_date": due_date,
        "category": todo.category,
        "cost_code_id": todo.cost_code_id,
        "source_type": todo.source_type,
        "source_id": todo.source_id,
        "completed_at": todo.completed_at,
        "created_by": todo.created_by,
        "created_by_name": created_by_name,
        "created_at": todo.created_at,
        "updated_at": todo.updated_at,
    }
