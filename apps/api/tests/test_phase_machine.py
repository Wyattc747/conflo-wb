"""Tests for the phase state machine."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.phase_machine import (
    VALID_TRANSITIONS,
    validate_transition_actor,
    transition_project,
)
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment


# ============================================================
# VALID TRANSITIONS
# ============================================================

class TestValidTransitions:
    def test_bidding_to_buyout(self):
        assert "BUYOUT" in VALID_TRANSITIONS["BIDDING"]

    def test_buyout_to_active(self):
        assert "ACTIVE" in VALID_TRANSITIONS["BUYOUT"]

    def test_active_to_closeout(self):
        assert "CLOSEOUT" in VALID_TRANSITIONS["ACTIVE"]

    def test_closeout_to_closed(self):
        assert "CLOSED" in VALID_TRANSITIONS["CLOSEOUT"]

    def test_closed_terminal(self):
        assert VALID_TRANSITIONS["CLOSED"] == []

    def test_no_backward_transitions(self):
        assert "BIDDING" not in VALID_TRANSITIONS.get("BUYOUT", [])
        assert "BUYOUT" not in VALID_TRANSITIONS.get("ACTIVE", [])
        assert "ACTIVE" not in VALID_TRANSITIONS.get("CLOSEOUT", [])
        assert "CLOSEOUT" not in VALID_TRANSITIONS.get("CLOSED", [])

    def test_no_skip_transitions(self):
        assert "ACTIVE" not in VALID_TRANSITIONS["BIDDING"]
        assert "CLOSEOUT" not in VALID_TRANSITIONS["BUYOUT"]
        assert "CLOSED" not in VALID_TRANSITIONS["ACTIVE"]


# ============================================================
# ACTOR VALIDATION
# ============================================================

class TestActorValidation:
    def test_owner_admin_can_do_any_transition(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN"}
        # Should not raise for any valid transition
        validate_transition_actor(user, "BIDDING", "BUYOUT")
        validate_transition_actor(user, "BUYOUT", "ACTIVE")
        validate_transition_actor(user, "ACTIVE", "CLOSEOUT")
        validate_transition_actor(user, "CLOSEOUT", "CLOSED")

    def test_management_can_do_any_transition(self):
        user = {"user_type": "gc", "permission_level": "MANAGEMENT"}
        validate_transition_actor(user, "BIDDING", "BUYOUT")
        validate_transition_actor(user, "BUYOUT", "ACTIVE")
        validate_transition_actor(user, "ACTIVE", "CLOSEOUT")
        validate_transition_actor(user, "CLOSEOUT", "CLOSED")

    def test_precon_only_bidding_to_buyout(self):
        user = {"user_type": "gc", "permission_level": "PRE_CONSTRUCTION"}
        validate_transition_actor(user, "BIDDING", "BUYOUT")
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "BUYOUT", "ACTIVE")
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "ACTIVE", "CLOSEOUT")

    def test_user_cannot_transition(self):
        user = {"user_type": "gc", "permission_level": "USER"}
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "BIDDING", "BUYOUT")

    def test_sub_cannot_transition(self):
        user = {"user_type": "sub", "permission_level": None}
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "BIDDING", "BUYOUT")

    def test_owner_can_award_only(self):
        user = {"user_type": "owner", "permission_level": None}
        validate_transition_actor(user, "BIDDING", "BUYOUT")
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "BUYOUT", "ACTIVE")
        with pytest.raises(HTTPException):
            validate_transition_actor(user, "ACTIVE", "CLOSEOUT")


# ============================================================
# TRANSITION FUNCTION
# ============================================================

class TestTransitionProject:
    @pytest.mark.asyncio
    async def test_successful_transition(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}
        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.phase = "BIDDING"
        project.name = "Test"
        project.deleted_at = None

        db = AsyncMock()
        db.get = AsyncMock(return_value=project)

        # Mock the side effects
        with patch("app.services.phase_machine.execute_side_effects", new_callable=AsyncMock):
            with patch("app.services.phase_machine.create_audit_log", new_callable=AsyncMock):
                with patch("app.services.phase_machine.create_event_log", new_callable=AsyncMock):
                    result = await transition_project(project.id, "BUYOUT", user, db)
                    assert result.phase == "BUYOUT"

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}
        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.phase = "ACTIVE"
        project.name = "Test"
        project.deleted_at = None

        db = AsyncMock()
        db.get = AsyncMock(return_value=project)

        with pytest.raises(HTTPException) as exc_info:
            await transition_project(project.id, "BIDDING", user, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_closed_cannot_transition(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}
        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.phase = "CLOSED"
        project.name = "Test"
        project.deleted_at = None

        db = AsyncMock()
        db.get = AsyncMock(return_value=project)

        with pytest.raises(HTTPException) as exc_info:
            await transition_project(project.id, "ACTIVE", user, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_deleted_project_not_found(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}
        project = MagicMock(spec=Project)
        project.deleted_at = "2026-01-01"

        db = AsyncMock()
        db.get = AsyncMock(return_value=project)

        with pytest.raises(HTTPException) as exc_info:
            await transition_project(uuid.uuid4(), "BUYOUT", user, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_nonexistent_project_not_found(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await transition_project(uuid.uuid4(), "BUYOUT", user, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_target_phase(self):
        user = {"user_type": "gc", "permission_level": "OWNER_ADMIN",
                "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}
        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.phase = "BIDDING"
        project.name = "Test"
        project.deleted_at = None

        db = AsyncMock()
        db.get = AsyncMock(return_value=project)

        with pytest.raises(HTTPException) as exc_info:
            await transition_project(project.id, "INVALID_PHASE", user, db)
        assert exc_info.value.status_code == 400


# ============================================================
# SIDE EFFECTS
# ============================================================

class TestSideEffects:
    @pytest.mark.asyncio
    async def test_bidding_to_buyout_notifies_subs(self):
        from app.services.phase_machine import on_bidding_to_buyout

        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.name = "Test Project"
        user = {"user_type": "gc", "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}

        sub_assignment = MagicMock(spec=ProjectAssignment)
        sub_assignment.assignee_id = uuid.uuid4()

        db = AsyncMock()
        with patch("app.services.phase_machine.get_sub_assignments",
                   new_callable=AsyncMock, return_value=[sub_assignment]):
            with patch("app.services.phase_machine.create_notification",
                      new_callable=AsyncMock) as mock_notify:
                await on_bidding_to_buyout(project, user, db)
                mock_notify.assert_called_once()
                call_kwargs = mock_notify.call_args
                assert call_kwargs[1]["notification_type"] == "project_awarded"

    @pytest.mark.asyncio
    async def test_closeout_to_closed_notifies_all(self):
        from app.services.phase_machine import on_closeout_to_closed

        project = MagicMock(spec=Project)
        project.id = uuid.uuid4()
        project.name = "Test"
        user = {"user_type": "gc", "user_id": uuid.uuid4(), "organization_id": uuid.uuid4()}

        assignments = [
            MagicMock(assignee_type="GC_USER", assignee_id=uuid.uuid4()),
            MagicMock(assignee_type="SUB_COMPANY", assignee_id=uuid.uuid4()),
            MagicMock(assignee_type="OWNER_ACCOUNT", assignee_id=uuid.uuid4()),
        ]
        db = AsyncMock()
        with patch("app.services.phase_machine.get_all_assignments",
                   new_callable=AsyncMock, return_value=assignments):
            with patch("app.services.phase_machine.create_notification",
                      new_callable=AsyncMock) as mock_notify:
                await on_closeout_to_closed(project, user, db)
                assert mock_notify.call_count == 3
