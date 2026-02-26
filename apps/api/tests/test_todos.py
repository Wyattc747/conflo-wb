"""Tests for Todo service."""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.services.todo_service import (
    complete_todo,
    create_todo,
    delete_todo,
    format_todo_response,
    get_todo,
    reopen_todo,
    start_todo,
    update_todo,
)
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID, MGMT_USER_ID


# ============================================================
# HELPERS
# ============================================================

def _make_user(user_id=ADMIN_USER_ID, permission_level="OWNER_ADMIN"):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_todo(
    status="OPEN",
    priority="MEDIUM",
    assigned_to=MGMT_USER_ID,
    title="Review steel shop drawings",
):
    todo = MagicMock(spec=Todo)
    todo.id = uuid.uuid4()
    todo.organization_id = ORG_ID
    todo.project_id = PROJECT_ID
    todo.created_by = ADMIN_USER_ID
    todo.title = title
    todo.description = "Review and approve before submittal deadline"
    todo.assigned_to = assigned_to
    todo.due_date = datetime(2026, 3, 15)
    todo.priority = priority
    todo.status = status
    todo.category = "SUBMITTALS"
    todo.cost_code_id = None
    todo.source_type = None
    todo.source_id = None
    todo.completed_at = None
    todo.created_at = datetime(2026, 2, 20, 10, 0)
    todo.updated_at = datetime(2026, 2, 20, 10, 0)
    todo.deleted_at = None
    return todo


# ============================================================
# create_todo
# ============================================================

class TestCreateTodo:
    @pytest.mark.asyncio
    async def test_create_with_assignee(self):
        db = AsyncMock()
        user = _make_user()
        data = TodoCreate(
            title="Review steel shop drawings",
            description="Review and approve before submittal deadline",
            assigned_to=MGMT_USER_ID,
            due_date=date(2026, 3, 15),
            priority="HIGH",
            category="SUBMITTALS",
        )

        result = await create_todo(db, PROJECT_ID, ORG_ID, user, data)

        # Todo + Notification (assigned_to) + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_without_assignee_no_notification(self):
        db = AsyncMock()
        user = _make_user()
        data = TodoCreate(
            title="General site cleanup",
        )

        await create_todo(db, PROJECT_ID, ORG_ID, user, data)

        # Todo + EventLog = 2 (no notification since no assignee)
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal(self):
        db = AsyncMock()
        user = _make_user()
        data = TodoCreate(title="Quick task")

        result = await create_todo(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_source_link(self):
        db = AsyncMock()
        user = _make_user()
        source_id = uuid.uuid4()
        data = TodoCreate(
            title="Follow up on RFI-005",
            source_type="rfi",
            source_id=source_id,
            assigned_to=MGMT_USER_ID,
        )

        result = await create_todo(db, PROJECT_ID, ORG_ID, user, data)

        # Todo + Notification + EventLog = 3
        assert db.add.call_count >= 3
        db.flush.assert_awaited_once()


# ============================================================
# get_todo
# ============================================================

class TestGetTodo:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        todo = _make_todo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        result = await get_todo(db, todo.id, PROJECT_ID)
        assert result == todo

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_todo(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_todo
# ============================================================

class TestUpdateTodo:
    @pytest.mark.asyncio
    async def test_update_open_todo(self):
        db = AsyncMock()
        todo = _make_todo(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        data = TodoUpdate(title="Updated task title")

        result = await update_todo(db, todo.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_in_progress_todo(self):
        db = AsyncMock()
        todo = _make_todo(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        data = TodoUpdate(priority="HIGH")

        result = await update_todo(db, todo.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_completed_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        data = TodoUpdate(title="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await update_todo(db, todo.id, PROJECT_ID, user, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = TodoUpdate(title="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await update_todo(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# delete_todo
# ============================================================

class TestDeleteTodo:
    @pytest.mark.asyncio
    async def test_soft_delete(self):
        db = AsyncMock()
        todo = _make_todo()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_todo(db, todo.id, PROJECT_ID, user)

        assert todo.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_todo(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# start_todo
# ============================================================

class TestStartTodo:
    @pytest.mark.asyncio
    async def test_start_open_todo(self):
        db = AsyncMock()
        todo = _make_todo(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await start_todo(db, todo.id, PROJECT_ID, user)

        assert todo.status == "IN_PROGRESS"
        db.add.assert_called_once()  # EventLog
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_non_open_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await start_todo(db, todo.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_start_completed_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await start_todo(db, todo.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# complete_todo
# ============================================================

class TestCompleteTodo:
    @pytest.mark.asyncio
    async def test_complete_in_progress(self):
        db = AsyncMock()
        todo = _make_todo(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await complete_todo(db, todo.id, PROJECT_ID, user)

        assert todo.status == "COMPLETED"
        assert todo.completed_at is not None
        db.add.assert_called_once()  # EventLog
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_open_directly(self):
        db = AsyncMock()
        todo = _make_todo(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await complete_todo(db, todo.id, PROJECT_ID, user)

        assert todo.status == "COMPLETED"
        assert todo.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_already_completed_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="COMPLETED")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await complete_todo(db, todo.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# reopen_todo
# ============================================================

class TestReopenTodo:
    @pytest.mark.asyncio
    async def test_reopen_completed(self):
        db = AsyncMock()
        todo = _make_todo(status="COMPLETED")
        todo.completed_at = datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        result = await reopen_todo(db, todo.id, PROJECT_ID, user)

        assert todo.status == "OPEN"
        assert todo.completed_at is None
        db.add.assert_called_once()  # EventLog
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reopen_open_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="OPEN")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reopen_todo(db, todo.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_reopen_in_progress_raises_400(self):
        db = AsyncMock()
        todo = _make_todo(status="IN_PROGRESS")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = todo
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await reopen_todo(db, todo.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400


# ============================================================
# format_todo_response
# ============================================================

class TestFormatTodoResponse:
    def test_basic_format(self):
        todo = _make_todo()
        result = format_todo_response(
            todo,
            created_by_name="John Smith",
            assigned_to_name="Sarah Johnson",
        )

        assert result["id"] == todo.id
        assert result["project_id"] == PROJECT_ID
        assert result["title"] == "Review steel shop drawings"
        assert result["description"] == "Review and approve before submittal deadline"
        assert result["status"] == "OPEN"
        assert result["priority"] == "MEDIUM"
        assert result["assigned_to"] == MGMT_USER_ID
        assert result["assigned_to_name"] == "Sarah Johnson"
        assert result["created_by"] == ADMIN_USER_ID
        assert result["created_by_name"] == "John Smith"
        assert result["category"] == "SUBMITTALS"
        assert result["completed_at"] is None
        assert result["created_at"] is not None

    def test_format_without_names(self):
        todo = _make_todo()
        result = format_todo_response(todo)

        assert result["created_by_name"] is None
        assert result["assigned_to_name"] is None

    def test_format_completed_todo(self):
        todo = _make_todo(status="COMPLETED")
        todo.completed_at = datetime(2026, 2, 25, 12, 0, tzinfo=timezone.utc)
        result = format_todo_response(todo)

        assert result["status"] == "COMPLETED"
        assert result["completed_at"] is not None

    def test_due_date_conversion(self):
        todo = _make_todo()
        todo.due_date = datetime(2026, 3, 15, 0, 0)
        result = format_todo_response(todo)
        assert result["due_date"] == date(2026, 3, 15)

    def test_source_fields_included(self):
        todo = _make_todo()
        source_id = uuid.uuid4()
        todo.source_type = "rfi"
        todo.source_id = source_id
        result = format_todo_response(todo)

        assert result["source_type"] == "rfi"
        assert result["source_id"] == source_id
