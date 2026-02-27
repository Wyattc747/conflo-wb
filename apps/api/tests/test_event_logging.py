"""Tests for event logging middleware and event catalog."""
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.event_logging import (
    EventLoggingMiddleware,
    METHOD_ACTION_MAP,
    MUTATING_METHODS,
    SKIP_PATH_PREFIXES,
    TOOL_ENTITY_MAP,
    _get_client_ip,
    _is_valid_uuid,
    _parse_path,
)
from app.services.event_catalog import (
    EVENT_CATALOG,
    CRITICAL,
    INFO,
    WARNING,
    get_event_info,
    get_event_severity,
    get_events_by_entity,
    get_events_by_severity,
    log_event,
)
from app.models.event_log import EventLog
from tests.conftest import ORG_ID, ADMIN_USER_ID, PROJECT_ID


# ============================================================
# HELPERS
# ============================================================

def _make_request(path="/api/gc/projects", method="POST", user_ctx=None, ip="127.0.0.1", user_agent="TestAgent/1.0"):
    """Create a mock Starlette Request object."""
    request = MagicMock()
    request.url.path = path
    request.method = method
    # Use a MagicMock for headers so .get is assignable
    headers_dict = {
        "user-agent": user_agent,
        "x-forwarded-for": None,
    }
    headers = MagicMock()
    headers.get = lambda key, default="": headers_dict.get(key, default)
    request.headers = headers
    request.client = MagicMock()
    request.client.host = ip

    # Set up state
    state = MagicMock()
    if user_ctx:
        state.user = user_ctx
    else:
        state.user = None
    request.state = state
    return request


def _make_user_ctx():
    return {
        "user_type": "gc",
        "user_id": ADMIN_USER_ID,
        "organization_id": ORG_ID,
        "permission_level": "OWNER_ADMIN",
    }


# ============================================================
# _parse_path — project-scoped routes
# ============================================================

class TestParsePath:
    def test_post_rfis_creates_rfi(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/rfis", "POST")
        assert result["entity_type"] == "rfi"
        assert result["action"] == "create"
        assert result["project_id"] == pid
        assert result["entity_id"] is None

    def test_patch_rfi_updates_rfi(self):
        pid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/rfis/{rid}", "PATCH")
        assert result["entity_type"] == "rfi"
        assert result["action"] == "update"
        assert result["project_id"] == pid
        assert result["entity_id"] == rid

    def test_delete_rfi(self):
        pid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/rfis/{rid}", "DELETE")
        assert result["entity_type"] == "rfi"
        assert result["action"] == "delete"
        assert result["entity_id"] == rid

    def test_post_change_order_submit_to_owner(self):
        pid = str(uuid.uuid4())
        coid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/change-orders/{coid}/submit-to-owner", "POST")
        assert result["entity_type"] == "change_order"
        assert result["action"] == "submit_to_owner"
        assert result["project_id"] == pid
        assert result["entity_id"] == coid

    def test_post_daily_logs(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/daily-logs", "POST")
        assert result["entity_type"] == "daily_log"
        assert result["action"] == "create"

    def test_post_submittals(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/submittals", "POST")
        assert result["entity_type"] == "submittal"
        assert result["action"] == "create"

    def test_patch_transmittal(self):
        pid = str(uuid.uuid4())
        tid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/transmittals/{tid}", "PATCH")
        assert result["entity_type"] == "transmittal"
        assert result["action"] == "update"

    def test_post_punch_list(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/punch-list", "POST")
        assert result["entity_type"] == "punch_list_item"
        assert result["action"] == "create"

    def test_post_pay_apps(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/pay-apps", "POST")
        assert result["entity_type"] == "pay_app"
        assert result["action"] == "create"

    def test_post_meetings(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/meetings", "POST")
        assert result["entity_type"] == "meeting"
        assert result["action"] == "create"

    def test_post_inspections(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/inspections", "POST")
        assert result["entity_type"] == "inspection"
        assert result["action"] == "create"

    def test_post_todos(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/todos", "POST")
        assert result["entity_type"] == "todo"
        assert result["action"] == "create"

    def test_post_procurement(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/procurement", "POST")
        assert result["entity_type"] == "procurement_item"
        assert result["action"] == "create"

    def test_post_drawings(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/drawings", "POST")
        assert result["entity_type"] == "drawing"
        assert result["action"] == "create"

    def test_post_documents(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/documents", "POST")
        assert result["entity_type"] == "document"
        assert result["action"] == "create"

    def test_post_photos(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/photos", "POST")
        assert result["entity_type"] == "photo"
        assert result["action"] == "create"

    def test_sub_portal_rfi(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/sub/projects/{pid}/rfis", "POST")
        assert result["entity_type"] == "rfi"
        assert result["action"] == "create"

    def test_owner_portal_pay_app_action(self):
        pid = str(uuid.uuid4())
        paid = str(uuid.uuid4())
        result = _parse_path(f"/api/owner/projects/{pid}/pay-apps/{paid}/approve", "POST")
        assert result["entity_type"] == "pay_app"
        assert result["action"] == "approve"

    def test_post_create_project(self):
        result = _parse_path("/api/gc/projects", "POST")
        assert result["entity_type"] == "project"
        assert result["action"] == "create"

    def test_bid_packages_sub_non_project_scoped(self):
        bpid = str(uuid.uuid4())
        result = _parse_path(f"/api/sub/bid-packages/{bpid}/submit", "POST")
        assert result["entity_type"] == "bid_package"
        assert result["action"] == "submit"

    def test_unrecognized_path_returns_none_entity(self):
        result = _parse_path("/something/random", "POST")
        assert result["entity_type"] is None
        assert result["action"] == "create"

    def test_schedule_tool(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/schedule", "POST")
        assert result["entity_type"] == "schedule_task"

    def test_budget_tool(self):
        pid = str(uuid.uuid4())
        result = _parse_path(f"/api/gc/projects/{pid}/budget", "POST")
        assert result["entity_type"] == "budget"


# ============================================================
# _is_valid_uuid
# ============================================================

class TestIsValidUuid:
    def test_valid_uuid(self):
        assert _is_valid_uuid(str(uuid.uuid4())) is True

    def test_valid_uuid_uppercase(self):
        assert _is_valid_uuid(str(uuid.uuid4()).upper()) is True

    def test_invalid_uuid_short(self):
        assert _is_valid_uuid("not-a-uuid") is False

    def test_invalid_uuid_empty(self):
        assert _is_valid_uuid("") is False

    def test_invalid_uuid_none_type(self):
        # The function should handle AttributeError for None
        assert _is_valid_uuid(None) is False

    def test_valid_uuid_known_format(self):
        assert _is_valid_uuid("12345678-1234-5678-1234-567812345678") is True


# ============================================================
# _get_client_ip
# ============================================================

class TestGetClientIp:
    def test_with_x_forwarded_for(self):
        request = MagicMock()
        request.headers.get = lambda key, default=None: {
            "x-forwarded-for": "203.0.113.50, 70.41.3.18",
        }.get(key, default)
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        ip = _get_client_ip(request)
        assert ip == "203.0.113.50"

    def test_with_single_x_forwarded_for(self):
        request = MagicMock()
        request.headers.get = lambda key, default=None: {
            "x-forwarded-for": "198.51.100.23",
        }.get(key, default)
        request.client = MagicMock()

        ip = _get_client_ip(request)
        assert ip == "198.51.100.23"

    def test_without_x_forwarded_for_uses_client(self):
        request = MagicMock()
        request.headers.get = lambda key, default=None: {
            "x-forwarded-for": None,
        }.get(key, default)
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        ip = _get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_no_client_returns_none(self):
        request = MagicMock()
        request.headers.get = lambda key, default=None: None
        request.client = None

        ip = _get_client_ip(request)
        assert ip is None


# ============================================================
# TOOL_ENTITY_MAP completeness
# ============================================================

class TestToolEntityMap:
    def test_rfis_in_map(self):
        assert "rfis" in TOOL_ENTITY_MAP
        assert TOOL_ENTITY_MAP["rfis"] == "rfi"

    def test_daily_logs_variants(self):
        assert "daily-logs" in TOOL_ENTITY_MAP
        assert "daily_logs" in TOOL_ENTITY_MAP
        assert TOOL_ENTITY_MAP["daily-logs"] == "daily_log"

    def test_change_orders_variants(self):
        assert "change-orders" in TOOL_ENTITY_MAP
        assert "change_orders" in TOOL_ENTITY_MAP
        assert TOOL_ENTITY_MAP["change-orders"] == "change_order"

    def test_punch_list_variants(self):
        assert "punch-list" in TOOL_ENTITY_MAP
        assert "punch_list" in TOOL_ENTITY_MAP
        assert TOOL_ENTITY_MAP["punch-list"] == "punch_list_item"

    def test_all_major_tools_present(self):
        expected_tools = [
            "rfis", "submittals", "transmittals", "inspections",
            "meetings", "todos", "procurement", "documents", "photos",
            "drawings", "budget", "schedule", "files", "projects",
            "comments", "notifications",
        ]
        for tool in expected_tools:
            assert tool in TOOL_ENTITY_MAP, f"Missing tool: {tool}"


# ============================================================
# METHOD_ACTION_MAP and constants
# ============================================================

class TestConstants:
    def test_method_action_map(self):
        assert METHOD_ACTION_MAP["POST"] == "create"
        assert METHOD_ACTION_MAP["PUT"] == "update"
        assert METHOD_ACTION_MAP["PATCH"] == "update"
        assert METHOD_ACTION_MAP["DELETE"] == "delete"

    def test_mutating_methods(self):
        assert "POST" in MUTATING_METHODS
        assert "PUT" in MUTATING_METHODS
        assert "PATCH" in MUTATING_METHODS
        assert "DELETE" in MUTATING_METHODS
        assert "GET" not in MUTATING_METHODS

    def test_skip_path_prefixes(self):
        assert "/api/health" in SKIP_PATH_PREFIXES
        assert "/api/webhooks/" in SKIP_PATH_PREFIXES
        assert "/api/auth/" in SKIP_PATH_PREFIXES


# ============================================================
# EventLoggingMiddleware.dispatch
# ============================================================

class TestEventLoggingMiddlewareDispatch:
    @pytest.mark.asyncio
    async def test_get_request_passes_through(self):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(method="GET")

        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        call_next.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    @patch("app.middleware.event_logging._write_event_log", new_callable=AsyncMock)
    async def test_post_201_is_logged(self, mock_write, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        pid = str(uuid.uuid4())
        user_ctx = _make_user_ctx()
        request = _make_request(
            path=f"/api/gc/projects/{pid}/rfis",
            method="POST",
            user_ctx=user_ctx,
        )

        response = MagicMock()
        response.status_code = 201
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        assert result == response
        # Should have created a background task
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_failed_request_not_logged(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(
            path="/api/gc/projects",
            method="POST",
            user_ctx=_make_user_ctx(),
        )

        response = MagicMock()
        response.status_code = 400
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_500_error_not_logged(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(
            path="/api/gc/projects",
            method="POST",
            user_ctx=_make_user_ctx(),
        )

        response = MagicMock()
        response.status_code = 500
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_health_path_skipped(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(path="/api/health", method="POST")

        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_auth_path_skipped(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(path="/api/auth/login", method="POST")

        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_webhook_path_skipped(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        request = _make_request(path="/api/webhooks/stripe", method="POST")

        response = MagicMock()
        response.status_code = 200
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_delete_with_204_is_logged(self, mock_create_task):
        middleware = EventLoggingMiddleware(app=MagicMock())
        pid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        request = _make_request(
            path=f"/api/gc/projects/{pid}/rfis/{rid}",
            method="DELETE",
            user_ctx=_make_user_ctx(),
        )

        response = MagicMock()
        response.status_code = 204
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.middleware.event_logging.asyncio.create_task")
    async def test_no_user_context_still_logs(self, mock_create_task):
        """Requests without an authenticated user context should still be logged."""
        middleware = EventLoggingMiddleware(app=MagicMock())
        pid = str(uuid.uuid4())
        request = _make_request(
            path=f"/api/gc/projects/{pid}/rfis",
            method="POST",
            user_ctx=None,
        )

        response = MagicMock()
        response.status_code = 201
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        mock_create_task.assert_called_once()


# ============================================================
# EVENT CATALOG — get_event_info, get_event_severity
# ============================================================

class TestEventCatalog:
    def test_catalog_has_rfi_events(self):
        assert "rfi_created" in EVENT_CATALOG
        assert "rfi_updated" in EVENT_CATALOG
        assert "rfi_deleted" in EVENT_CATALOG
        assert "rfi_closed" in EVENT_CATALOG

    def test_catalog_has_daily_log_events(self):
        assert "daily_log_created" in EVENT_CATALOG
        assert "daily_log_submitted" in EVENT_CATALOG

    def test_catalog_has_change_order_events(self):
        assert "change_order_created" in EVENT_CATALOG
        assert "change_order_approved" in EVENT_CATALOG
        assert "change_order_submitted_to_owner" in EVENT_CATALOG

    def test_catalog_has_project_events(self):
        assert "project_created" in EVENT_CATALOG
        assert "project_deleted" in EVENT_CATALOG
        assert "project_transition" in EVENT_CATALOG

    def test_catalog_has_pay_app_events(self):
        assert "pay_app_created" in EVENT_CATALOG
        assert "pay_app_approved" in EVENT_CATALOG
        assert "pay_app_submitted" in EVENT_CATALOG

    def test_catalog_has_submittal_events(self):
        assert "submittal_created" in EVENT_CATALOG
        assert "submittal_approved" in EVENT_CATALOG
        assert "submittal_rejected" in EVENT_CATALOG

    def test_catalog_has_punch_list_events(self):
        assert "punch_list_item_created" in EVENT_CATALOG
        assert "punch_list_item_verified" in EVENT_CATALOG
        assert "punch_list_item_completed" in EVENT_CATALOG

    def test_catalog_has_schedule_events(self):
        assert "schedule_task_created" in EVENT_CATALOG
        assert "schedule_delay_created" in EVENT_CATALOG
        assert "schedule_delay_applied" in EVENT_CATALOG

    def test_catalog_has_bid_events(self):
        assert "bid_package_created" in EVENT_CATALOG
        assert "bid_package_awarded" in EVENT_CATALOG
        assert "bid_submission_created" in EVENT_CATALOG

    def test_catalog_has_inspection_events(self):
        assert "inspection_created" in EVENT_CATALOG
        assert "inspection_completed" in EVENT_CATALOG
        assert "inspection_failed" in EVENT_CATALOG

    def test_catalog_has_meeting_events(self):
        assert "meeting_created" in EVENT_CATALOG
        assert "meeting_completed" in EVENT_CATALOG

    def test_catalog_has_todo_events(self):
        assert "todo_created" in EVENT_CATALOG
        assert "todo_completed" in EVENT_CATALOG
        assert "todo_reopened" in EVENT_CATALOG

    def test_catalog_has_procurement_events(self):
        assert "procurement_item_created" in EVENT_CATALOG
        assert "procurement_item_delivered" in EVENT_CATALOG

    def test_catalog_has_document_events(self):
        assert "document_created" in EVENT_CATALOG
        assert "document_deleted" in EVENT_CATALOG

    def test_catalog_has_billing_events(self):
        assert "subscription_created" in EVENT_CATALOG
        assert "payment_failed" in EVENT_CATALOG

    def test_all_entries_have_description_and_severity(self):
        for event_type, entry in EVENT_CATALOG.items():
            assert "description" in entry, f"Missing description for {event_type}"
            assert "severity" in entry, f"Missing severity for {event_type}"
            assert entry["severity"] in (INFO, WARNING, CRITICAL), f"Invalid severity for {event_type}"

    def test_get_event_info_known_event(self):
        info = get_event_info("rfi_created")
        assert info["description"] == "An RFI was created"
        assert info["severity"] == INFO

    def test_get_event_info_unknown_event_returns_default(self):
        info = get_event_info("nonexistent_event_type")
        assert "description" in info
        assert info["severity"] == INFO
        assert "nonexistent_event_type" in info["description"]

    def test_get_event_severity_known(self):
        assert get_event_severity("rfi_created") == INFO
        assert get_event_severity("rfi_deleted") == WARNING
        assert get_event_severity("change_order_approved") == CRITICAL

    def test_get_event_severity_unknown(self):
        assert get_event_severity("totally_unknown") == INFO

    def test_get_events_by_entity_rfi(self):
        rfi_events = get_events_by_entity("rfi")
        assert "rfi_created" in rfi_events
        assert "rfi_updated" in rfi_events
        assert "rfi_deleted" in rfi_events
        # Should NOT contain non-rfi events
        assert "submittal_created" not in rfi_events

    def test_get_events_by_entity_change_order(self):
        co_events = get_events_by_entity("change_order")
        assert "change_order_created" in co_events
        assert "change_order_approved" in co_events
        assert "change_order_submitted_to_owner" in co_events

    def test_get_events_by_severity_critical(self):
        critical_events = get_events_by_severity(CRITICAL)
        assert "change_order_approved" in critical_events
        assert "pay_app_approved" in critical_events
        assert "project_deleted" in critical_events
        # INFO events should NOT appear
        assert "rfi_created" not in critical_events

    def test_get_events_by_severity_warning(self):
        warning_events = get_events_by_severity(WARNING)
        assert "rfi_deleted" in warning_events
        assert "submittal_rejected" in warning_events


# ============================================================
# log_event (event_catalog)
# ============================================================

class TestLogEvent:
    @pytest.mark.asyncio
    async def test_log_event_creates_entry(self):
        db = AsyncMock()
        user = _make_user_ctx()
        entity_id = uuid.uuid4()

        result = await log_event(
            db=db,
            user=user,
            project_id=PROJECT_ID,
            event_type="rfi_created",
            entity_type="rfi",
            entity_id=entity_id,
            event_data={"number": "RFI-001"},
        )

        db.add.assert_called_once()
        event = db.add.call_args[0][0]
        assert isinstance(event, EventLog)
        assert event.event_type == "rfi_created"
        assert event.entity_type == "rfi"
        assert event.entity_id == entity_id
        assert event.project_id == PROJECT_ID
        assert event.organization_id == ORG_ID
        assert event.user_type == "gc"
        assert event.user_id == ADMIN_USER_ID
        assert event.action == "created"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_log_event_derives_entity_type_from_event_type(self):
        db = AsyncMock()
        user = _make_user_ctx()

        await log_event(
            db=db,
            user=user,
            project_id=PROJECT_ID,
            event_type="submittal_approved",
        )

        event = db.add.call_args[0][0]
        assert event.entity_type == "submittal"
        assert event.action == "approved"

    @pytest.mark.asyncio
    async def test_log_event_derives_action_when_entity_provided(self):
        db = AsyncMock()
        user = _make_user_ctx()

        await log_event(
            db=db,
            user=user,
            project_id=PROJECT_ID,
            event_type="punch_list_item_created",
            entity_type="punch_list_item",
        )

        event = db.add.call_args[0][0]
        assert event.entity_type == "punch_list_item"
        assert event.action == "created"

    @pytest.mark.asyncio
    async def test_log_event_with_ip_and_user_agent(self):
        db = AsyncMock()
        user = _make_user_ctx()

        await log_event(
            db=db,
            user=user,
            project_id=None,
            event_type="project_created",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
        )

        event = db.add.call_args[0][0]
        assert event.ip_address == "10.0.0.1"
        assert event.user_agent == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_log_event_default_event_data(self):
        db = AsyncMock()
        user = _make_user_ctx()

        await log_event(
            db=db,
            user=user,
            project_id=PROJECT_ID,
            event_type="rfi_updated",
        )

        event = db.add.call_args[0][0]
        assert event.event_data == {}

    @pytest.mark.asyncio
    async def test_log_event_returns_event_log_instance(self):
        db = AsyncMock()
        user = _make_user_ctx()

        result = await log_event(
            db=db,
            user=user,
            project_id=PROJECT_ID,
            event_type="meeting_created",
        )

        assert isinstance(result, EventLog)
        assert result.event_type == "meeting_created"
