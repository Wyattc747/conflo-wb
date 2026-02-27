"""Event logging middleware — non-blocking capture of all mutating API requests."""

import asyncio
import logging
import re
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import async_session_factory
from app.models.event_log import EventLog

logger = logging.getLogger(__name__)

# HTTP method → action mapping
METHOD_ACTION_MAP = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# Only intercept mutating methods
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Paths that should not be logged (auth, health, webhooks, docs)
SKIP_PATH_PREFIXES = (
    "/api/health",
    "/api/webhooks/",
    "/api/auth/",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# Regex to parse API tool routes:
#   /api/{portal}/projects/{project_id}/{tool}
#   /api/{portal}/projects/{project_id}/{tool}/{entity_id}
#   /api/{portal}/projects/{project_id}/{tool}/{entity_id}/{sub_action}
# Also handles non-project-scoped routes like:
#   /api/{portal}/{tool}
#   /api/{portal}/{tool}/{entity_id}
_UUID_PATTERN = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

# Project-scoped tool routes
_PROJECT_TOOL_RE = re.compile(
    rf"^/api/(?:gc|sub|owner)/projects/(?P<project_id>{_UUID_PATTERN})"
    rf"/(?P<tool>[a-z][a-z0-9_-]+)"
    rf"(?:/(?P<entity_id>{_UUID_PATTERN}))?"
    rf"(?:/(?P<sub_action>[a-z][a-z0-9_-]+))?$"
)

# Non-project-scoped routes (e.g., /api/sub/bid-packages, /api/gc/billing)
_PORTAL_TOOL_RE = re.compile(
    rf"^/api/(?:gc|sub|owner)/(?P<tool>[a-z][a-z0-9_-]+)"
    rf"(?:/(?P<entity_id>{_UUID_PATTERN}))?"
    rf"(?:/(?P<sub_action>[a-z][a-z0-9_-]+))?$"
)

# Map URL tool segments to canonical entity type names
TOOL_ENTITY_MAP = {
    "rfis": "rfi",
    "daily-logs": "daily_log",
    "daily_logs": "daily_log",
    "submittals": "submittal",
    "transmittals": "transmittal",
    "change-orders": "change_order",
    "change_orders": "change_order",
    "punch-list": "punch_list_item",
    "punch_list": "punch_list_item",
    "inspections": "inspection",
    "inspection-templates": "inspection_template",
    "pay-apps": "pay_app",
    "pay_apps": "pay_app",
    "bid-packages": "bid_package",
    "bid_packages": "bid_package",
    "schedule": "schedule_task",
    "schedule-tasks": "schedule_task",
    "drawings": "drawing",
    "drawing-sheets": "drawing_sheet",
    "meetings": "meeting",
    "todos": "todo",
    "procurement": "procurement_item",
    "documents": "document",
    "photos": "photo",
    "budget": "budget",
    "budget-line-items": "budget_line_item",
    "files": "file",
    "projects": "project",
    "assignments": "project_assignment",
    "comments": "comment",
    "notifications": "notification",
    "integrations": "integration",
}


def _parse_path(path: str, method: str) -> dict:
    """
    Extract entity_type, entity_id, project_id, and action from a URL path.

    Returns a dict with keys: entity_type, entity_id, project_id, action.
    """
    result = {
        "entity_type": None,
        "entity_id": None,
        "project_id": None,
        "action": METHOD_ACTION_MAP.get(method, "unknown"),
    }

    # Try project-scoped route first
    match = _PROJECT_TOOL_RE.match(path)
    if match:
        groups = match.groupdict()
        result["project_id"] = groups.get("project_id")
        tool = groups.get("tool", "")
        result["entity_type"] = TOOL_ENTITY_MAP.get(tool, tool.replace("-", "_"))
        entity_id = groups.get("entity_id")
        if entity_id:
            result["entity_id"] = entity_id
        sub_action = groups.get("sub_action")
        if sub_action:
            # Sub-action overrides the HTTP method action
            result["action"] = sub_action.replace("-", "_")
        return result

    # Try non-project-scoped route
    match = _PORTAL_TOOL_RE.match(path)
    if match:
        groups = match.groupdict()
        tool = groups.get("tool", "")
        # Skip generic portal-level routes that are not tools
        if tool in ("projects",):
            result["entity_type"] = "project"
            entity_id = groups.get("entity_id")
            if entity_id:
                result["entity_id"] = entity_id
        else:
            result["entity_type"] = TOOL_ENTITY_MAP.get(tool, tool.replace("-", "_"))
            entity_id = groups.get("entity_id")
            if entity_id:
                result["entity_id"] = entity_id
        sub_action = groups.get("sub_action")
        if sub_action:
            result["action"] = sub_action.replace("-", "_")
        return result

    return result


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


class EventLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all mutating API requests to the event_logs table.

    Runs the log insertion as a fire-and-forget background task so it never
    blocks or delays the HTTP response. Errors are caught and logged to
    the Python logger rather than surfaced to the client.
    """

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # Only intercept mutating methods
        if method not in MUTATING_METHODS:
            return await call_next(request)

        # Skip paths that should not be logged
        if any(path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            return await call_next(request)

        # Process the request first
        response = await call_next(request)

        # Only log successful mutations (2xx status codes)
        if response.status_code < 200 or response.status_code >= 300:
            return response

        # Extract user context (set by AuthMiddleware)
        user_ctx = getattr(request.state, "user", None)

        # Extract path info
        path_info = _parse_path(path, method)

        # Build event type string: {entity_type}_{action}
        entity_type = path_info["entity_type"]
        action = path_info["action"]
        if entity_type and action:
            event_type = f"{entity_type}_{action}"
        elif entity_type:
            event_type = f"{entity_type}_{METHOD_ACTION_MAP.get(method, 'unknown')}"
        else:
            event_type = f"api_{METHOD_ACTION_MAP.get(method, 'unknown')}"

        # Extract request metadata
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]

        # Parse entity_id and project_id as UUIDs
        entity_id = None
        if path_info["entity_id"] and _is_valid_uuid(path_info["entity_id"]):
            entity_id = uuid.UUID(path_info["entity_id"])

        project_id = None
        if path_info["project_id"] and _is_valid_uuid(path_info["project_id"]):
            project_id = uuid.UUID(path_info["project_id"])

        # Build event data
        event_data = {
            "method": method,
            "path": path,
            "status_code": response.status_code,
        }
        if path_info.get("action") and path_info["action"] != METHOD_ACTION_MAP.get(method):
            event_data["sub_action"] = path_info["action"]

        # Fire-and-forget the log insertion
        asyncio.create_task(
            _write_event_log(
                organization_id=user_ctx.get("organization_id") if user_ctx else None,
                project_id=project_id,
                user_type=user_ctx.get("user_type") if user_ctx else None,
                user_id=user_ctx.get("user_id") if user_ctx else None,
                event_type=event_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        return response


def _get_client_ip(request: Request) -> Optional[str]:
    """
    Extract the client IP address, respecting X-Forwarded-For for proxied requests.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; the first is the client
        return forwarded.split(",")[0].strip()[:45]
    if request.client:
        return str(request.client.host)[:45]
    return None


async def _write_event_log(
    organization_id: Optional[uuid.UUID],
    project_id: Optional[uuid.UUID],
    user_type: Optional[str],
    user_id: Optional[uuid.UUID],
    event_type: str,
    action: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[uuid.UUID],
    event_data: dict,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> None:
    """
    Write an event log entry using its own database session.

    This runs as a fire-and-forget background task. Uses a dedicated session
    from the factory so it does not interfere with the request's session.
    Errors are caught and logged silently.
    """
    try:
        async with async_session_factory() as session:
            event = EventLog(
                organization_id=organization_id,
                project_id=project_id,
                user_type=user_type,
                user_id=user_id,
                event_type=event_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(event)
            await session.commit()
    except Exception:
        logger.exception("Failed to write event log for %s", event_type)
