"""Event catalog — defines all auditable events and provides the log_event helper."""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import EventLog

logger = logging.getLogger(__name__)


# ── Severity levels ──

INFO = "info"
WARNING = "warning"
CRITICAL = "critical"


# ── Event Catalog ──
# Maps event_type to a description and severity.
# event_type follows the pattern: {entity_type}_{action}

EVENT_CATALOG: dict[str, dict] = {
    # ── Daily Logs ──
    "daily_log_created": {
        "description": "A daily log entry was created",
        "severity": INFO,
    },
    "daily_log_updated": {
        "description": "A daily log entry was updated",
        "severity": INFO,
    },
    "daily_log_deleted": {
        "description": "A daily log entry was deleted",
        "severity": WARNING,
    },
    "daily_log_submitted": {
        "description": "A daily log was submitted for review",
        "severity": INFO,
    },
    "daily_log_commented": {
        "description": "A comment was added to a daily log",
        "severity": INFO,
    },

    # ── RFIs ──
    "rfi_created": {
        "description": "An RFI was created",
        "severity": INFO,
    },
    "rfi_updated": {
        "description": "An RFI was updated",
        "severity": INFO,
    },
    "rfi_deleted": {
        "description": "An RFI was deleted",
        "severity": WARNING,
    },
    "rfi_status_changed": {
        "description": "An RFI status was changed",
        "severity": INFO,
    },
    "rfi_responded": {
        "description": "A response was submitted for an RFI",
        "severity": INFO,
    },
    "rfi_closed": {
        "description": "An RFI was closed",
        "severity": INFO,
    },
    "rfi_assigned": {
        "description": "An RFI was assigned to a user",
        "severity": INFO,
    },
    "rfi_commented": {
        "description": "A comment was added to an RFI",
        "severity": INFO,
    },
    "rfi_file_uploaded": {
        "description": "A file was uploaded to an RFI",
        "severity": INFO,
    },

    # ── Submittals ──
    "submittal_created": {
        "description": "A submittal was created",
        "severity": INFO,
    },
    "submittal_updated": {
        "description": "A submittal was updated",
        "severity": INFO,
    },
    "submittal_deleted": {
        "description": "A submittal was deleted",
        "severity": WARNING,
    },
    "submittal_submitted": {
        "description": "A submittal was submitted for review",
        "severity": INFO,
    },
    "submittal_status_changed": {
        "description": "A submittal status was changed",
        "severity": INFO,
    },
    "submittal_approved": {
        "description": "A submittal was approved",
        "severity": INFO,
    },
    "submittal_approved_as_noted": {
        "description": "A submittal was approved as noted",
        "severity": INFO,
    },
    "submittal_rejected": {
        "description": "A submittal was rejected",
        "severity": WARNING,
    },
    "submittal_revise_and_resubmit": {
        "description": "A submittal was returned for revision and resubmission",
        "severity": WARNING,
    },
    "submittal_revision_created": {
        "description": "A new revision was created for a submittal",
        "severity": INFO,
    },
    "submittal_commented": {
        "description": "A comment was added to a submittal",
        "severity": INFO,
    },
    "submittal_file_uploaded": {
        "description": "A file was uploaded to a submittal",
        "severity": INFO,
    },

    # ── Transmittals ──
    "transmittal_created": {
        "description": "A transmittal was created",
        "severity": INFO,
    },
    "transmittal_updated": {
        "description": "A transmittal was updated",
        "severity": INFO,
    },
    "transmittal_deleted": {
        "description": "A transmittal was deleted",
        "severity": WARNING,
    },
    "transmittal_sent": {
        "description": "A transmittal was sent to recipients",
        "severity": INFO,
    },
    "transmittal_acknowledged": {
        "description": "A transmittal was acknowledged by a recipient",
        "severity": INFO,
    },
    "transmittal_commented": {
        "description": "A comment was added to a transmittal",
        "severity": INFO,
    },

    # ── Change Orders ──
    "change_order_created": {
        "description": "A change order was created",
        "severity": INFO,
    },
    "change_order_updated": {
        "description": "A change order was updated",
        "severity": INFO,
    },
    "change_order_deleted": {
        "description": "A change order was deleted",
        "severity": WARNING,
    },
    "change_order_status_changed": {
        "description": "A change order status was changed",
        "severity": INFO,
    },
    "change_order_pricing_requested": {
        "description": "Sub pricing was requested for a change order",
        "severity": INFO,
    },
    "change_order_pricing_submitted": {
        "description": "Sub pricing was submitted for a change order",
        "severity": INFO,
    },
    "change_order_submitted_to_owner": {
        "description": "A change order was submitted to the owner for approval",
        "severity": INFO,
    },
    "change_order_approved": {
        "description": "A change order was approved",
        "severity": CRITICAL,
    },
    "change_order_rejected": {
        "description": "A change order was rejected",
        "severity": WARNING,
    },
    "change_order_revision": {
        "description": "A change order revision was requested",
        "severity": WARNING,
    },
    "change_order_commented": {
        "description": "A comment was added to a change order",
        "severity": INFO,
    },
    "change_order_file_uploaded": {
        "description": "A file was uploaded to a change order",
        "severity": INFO,
    },

    # ── Punch List ──
    "punch_list_item_created": {
        "description": "A punch list item was created",
        "severity": INFO,
    },
    "punch_list_item_updated": {
        "description": "A punch list item was updated",
        "severity": INFO,
    },
    "punch_list_item_deleted": {
        "description": "A punch list item was deleted",
        "severity": WARNING,
    },
    "punch_list_item_status_changed": {
        "description": "A punch list item status was changed",
        "severity": INFO,
    },
    "punch_list_item_assigned": {
        "description": "A punch list item was assigned to a sub",
        "severity": INFO,
    },
    "punch_list_item_completed": {
        "description": "A punch list item was marked as completed by the sub",
        "severity": INFO,
    },
    "punch_list_item_verified": {
        "description": "A punch list item was verified by the GC",
        "severity": INFO,
    },
    "punch_list_item_closed": {
        "description": "A punch list item was closed",
        "severity": INFO,
    },
    "punch_list_item_disputed": {
        "description": "A punch list item completion was disputed",
        "severity": WARNING,
    },
    "punch_list_item_commented": {
        "description": "A comment was added to a punch list item",
        "severity": INFO,
    },
    "punch_list_item_photo_uploaded": {
        "description": "A photo was uploaded to a punch list item",
        "severity": INFO,
    },

    # ── Inspections ──
    "inspection_created": {
        "description": "An inspection was created",
        "severity": INFO,
    },
    "inspection_updated": {
        "description": "An inspection was updated",
        "severity": INFO,
    },
    "inspection_deleted": {
        "description": "An inspection was deleted",
        "severity": WARNING,
    },
    "inspection_status_changed": {
        "description": "An inspection status was changed",
        "severity": INFO,
    },
    "inspection_completed": {
        "description": "An inspection was completed",
        "severity": INFO,
    },
    "inspection_failed": {
        "description": "An inspection failed",
        "severity": WARNING,
    },
    "inspection_commented": {
        "description": "A comment was added to an inspection",
        "severity": INFO,
    },
    "inspection_template_created": {
        "description": "An inspection template was created",
        "severity": INFO,
    },
    "inspection_template_updated": {
        "description": "An inspection template was updated",
        "severity": INFO,
    },
    "inspection_template_deleted": {
        "description": "An inspection template was deleted",
        "severity": WARNING,
    },

    # ── Pay Apps ──
    "pay_app_created": {
        "description": "A pay application was created",
        "severity": INFO,
    },
    "pay_app_updated": {
        "description": "A pay application was updated",
        "severity": INFO,
    },
    "pay_app_deleted": {
        "description": "A pay application was deleted",
        "severity": WARNING,
    },
    "pay_app_submitted": {
        "description": "A pay application was submitted for review",
        "severity": INFO,
    },
    "pay_app_status_changed": {
        "description": "A pay application status was changed",
        "severity": INFO,
    },
    "pay_app_approved": {
        "description": "A pay application was approved",
        "severity": CRITICAL,
    },
    "pay_app_rejected": {
        "description": "A pay application was rejected",
        "severity": WARNING,
    },
    "pay_app_revision": {
        "description": "A pay application revision was requested",
        "severity": WARNING,
    },
    "pay_app_commented": {
        "description": "A comment was added to a pay application",
        "severity": INFO,
    },
    "pay_app_file_uploaded": {
        "description": "A file was uploaded to a pay application",
        "severity": INFO,
    },

    # ── Bid Packages ──
    "bid_package_created": {
        "description": "A bid package was created",
        "severity": INFO,
    },
    "bid_package_updated": {
        "description": "A bid package was updated",
        "severity": INFO,
    },
    "bid_package_deleted": {
        "description": "A bid package was deleted",
        "severity": WARNING,
    },
    "bid_package_published": {
        "description": "A bid package was published and distributed to subs",
        "severity": INFO,
    },
    "bid_package_closed": {
        "description": "A bid package was closed for submissions",
        "severity": INFO,
    },
    "bid_package_awarded": {
        "description": "A bid package was awarded to a sub",
        "severity": CRITICAL,
    },
    "bid_package_distributed": {
        "description": "A bid package was distributed to invited subs",
        "severity": INFO,
    },
    "bid_submission_created": {
        "description": "A bid submission was received from a sub",
        "severity": INFO,
    },
    "bid_submission_updated": {
        "description": "A bid submission was updated by a sub",
        "severity": INFO,
    },
    "bid_package_commented": {
        "description": "A comment was added to a bid package",
        "severity": INFO,
    },

    # ── Schedule ──
    "schedule_task_created": {
        "description": "A schedule task was created",
        "severity": INFO,
    },
    "schedule_task_updated": {
        "description": "A schedule task was updated",
        "severity": INFO,
    },
    "schedule_task_deleted": {
        "description": "A schedule task was deleted",
        "severity": WARNING,
    },
    "schedule_task_progress_updated": {
        "description": "A schedule task progress percentage was updated",
        "severity": INFO,
    },
    "schedule_delay_created": {
        "description": "A schedule delay was reported",
        "severity": WARNING,
    },
    "schedule_delay_approved": {
        "description": "A schedule delay was approved",
        "severity": WARNING,
    },
    "schedule_delay_applied": {
        "description": "A schedule delay was applied to the schedule",
        "severity": CRITICAL,
    },
    "schedule_baseline_created": {
        "description": "A schedule baseline was created",
        "severity": INFO,
    },
    "schedule_version_created": {
        "description": "A schedule version snapshot was created",
        "severity": INFO,
    },

    # ── Drawings ──
    "drawing_created": {
        "description": "A drawing set was created",
        "severity": INFO,
    },
    "drawing_updated": {
        "description": "A drawing set was updated",
        "severity": INFO,
    },
    "drawing_deleted": {
        "description": "A drawing set was deleted",
        "severity": WARNING,
    },
    "drawing_current_set_changed": {
        "description": "The current drawing set was changed",
        "severity": INFO,
    },
    "drawing_sheet_created": {
        "description": "A drawing sheet was uploaded",
        "severity": INFO,
    },
    "drawing_sheet_updated": {
        "description": "A drawing sheet was updated",
        "severity": INFO,
    },
    "drawing_sheet_deleted": {
        "description": "A drawing sheet was deleted",
        "severity": WARNING,
    },
    "drawing_sheet_revision_uploaded": {
        "description": "A new revision of a drawing sheet was uploaded",
        "severity": INFO,
    },

    # ── Meetings ──
    "meeting_created": {
        "description": "A meeting was scheduled",
        "severity": INFO,
    },
    "meeting_updated": {
        "description": "A meeting was updated",
        "severity": INFO,
    },
    "meeting_deleted": {
        "description": "A meeting was deleted",
        "severity": WARNING,
    },
    "meeting_completed": {
        "description": "A meeting was marked as completed",
        "severity": INFO,
    },
    "meeting_minutes_published": {
        "description": "Meeting minutes were published",
        "severity": INFO,
    },
    "meeting_commented": {
        "description": "A comment was added to a meeting",
        "severity": INFO,
    },

    # ── Todos ──
    "todo_created": {
        "description": "A to-do item was created",
        "severity": INFO,
    },
    "todo_updated": {
        "description": "A to-do item was updated",
        "severity": INFO,
    },
    "todo_deleted": {
        "description": "A to-do item was deleted",
        "severity": WARNING,
    },
    "todo_status_changed": {
        "description": "A to-do item status was changed",
        "severity": INFO,
    },
    "todo_assigned": {
        "description": "A to-do item was assigned to a user",
        "severity": INFO,
    },
    "todo_completed": {
        "description": "A to-do item was completed",
        "severity": INFO,
    },
    "todo_reopened": {
        "description": "A to-do item was reopened",
        "severity": INFO,
    },

    # ── Procurement ──
    "procurement_item_created": {
        "description": "A procurement item was created",
        "severity": INFO,
    },
    "procurement_item_updated": {
        "description": "A procurement item was updated",
        "severity": INFO,
    },
    "procurement_item_deleted": {
        "description": "A procurement item was deleted",
        "severity": WARNING,
    },
    "procurement_item_status_changed": {
        "description": "A procurement item status was changed",
        "severity": INFO,
    },
    "procurement_item_ordered": {
        "description": "A procurement item was ordered",
        "severity": INFO,
    },
    "procurement_item_delivered": {
        "description": "A procurement item was delivered",
        "severity": INFO,
    },
    "procurement_item_installed": {
        "description": "A procurement item was installed",
        "severity": INFO,
    },
    "procurement_item_commented": {
        "description": "A comment was added to a procurement item",
        "severity": INFO,
    },

    # ── Documents ──
    "document_created": {
        "description": "A document was uploaded",
        "severity": INFO,
    },
    "document_updated": {
        "description": "A document was updated",
        "severity": INFO,
    },
    "document_deleted": {
        "description": "A document was deleted",
        "severity": WARNING,
    },
    "document_version_uploaded": {
        "description": "A new version of a document was uploaded",
        "severity": INFO,
    },
    "document_commented": {
        "description": "A comment was added to a document",
        "severity": INFO,
    },

    # ── Photos ──
    "photo_created": {
        "description": "A photo was uploaded",
        "severity": INFO,
    },
    "photo_updated": {
        "description": "A photo was updated",
        "severity": INFO,
    },
    "photo_deleted": {
        "description": "A photo was deleted",
        "severity": WARNING,
    },
    "photo_linked": {
        "description": "A photo was linked to an entity",
        "severity": INFO,
    },

    # ── Budget ──
    "budget_created": {
        "description": "A budget was created",
        "severity": INFO,
    },
    "budget_updated": {
        "description": "A budget was updated",
        "severity": INFO,
    },
    "budget_line_item_created": {
        "description": "A budget line item was added",
        "severity": INFO,
    },
    "budget_line_item_updated": {
        "description": "A budget line item was updated",
        "severity": INFO,
    },
    "budget_line_item_deleted": {
        "description": "A budget line item was deleted",
        "severity": WARNING,
    },
    "budget_threshold_exceeded": {
        "description": "A budget threshold was exceeded",
        "severity": CRITICAL,
    },

    # ── Comments (cross-tool) ──
    "comment_created": {
        "description": "A comment was added to an entity",
        "severity": INFO,
    },
    "comment_updated": {
        "description": "A comment was updated",
        "severity": INFO,
    },
    "comment_deleted": {
        "description": "A comment was deleted",
        "severity": INFO,
    },

    # ── Files (cross-tool) ──
    "file_uploaded": {
        "description": "A file was uploaded",
        "severity": INFO,
    },
    "file_deleted": {
        "description": "A file was deleted",
        "severity": WARNING,
    },

    # ── Projects ──
    "project_created": {
        "description": "A project was created",
        "severity": INFO,
    },
    "project_updated": {
        "description": "A project was updated",
        "severity": INFO,
    },
    "project_deleted": {
        "description": "A project was deleted",
        "severity": CRITICAL,
    },
    "project_phase_changed": {
        "description": "A project phase transition was triggered",
        "severity": CRITICAL,
    },
    "project_transition": {
        "description": "A project transitioned to a new phase",
        "severity": CRITICAL,
    },

    # ── Project Assignments ──
    "project_assignment_created": {
        "description": "A user or company was assigned to a project",
        "severity": INFO,
    },
    "project_assignment_updated": {
        "description": "A project assignment was updated",
        "severity": INFO,
    },
    "project_assignment_deleted": {
        "description": "A user or company was removed from a project",
        "severity": WARNING,
    },

    # ── Auth and Invitations ──
    "invitation_created": {
        "description": "An invitation was sent",
        "severity": INFO,
    },
    "invitation_accepted": {
        "description": "An invitation was accepted",
        "severity": INFO,
    },
    "invitation_revoked": {
        "description": "An invitation was revoked",
        "severity": WARNING,
    },

    # ── Billing ──
    "subscription_created": {
        "description": "A subscription was created",
        "severity": CRITICAL,
    },
    "subscription_updated": {
        "description": "A subscription was updated",
        "severity": CRITICAL,
    },
    "subscription_cancelled": {
        "description": "A subscription was cancelled",
        "severity": CRITICAL,
    },
    "payment_succeeded": {
        "description": "A payment was processed successfully",
        "severity": INFO,
    },
    "payment_failed": {
        "description": "A payment failed",
        "severity": CRITICAL,
    },

    # ── Integrations ──
    "integration_connected": {
        "description": "An external integration was connected",
        "severity": INFO,
    },
    "integration_disconnected": {
        "description": "An external integration was disconnected",
        "severity": WARNING,
    },
    "integration_synced": {
        "description": "An integration sync was completed",
        "severity": INFO,
    },
    "integration_sync_failed": {
        "description": "An integration sync failed",
        "severity": WARNING,
    },
}


def get_event_info(event_type: str) -> dict:
    """
    Look up description and severity for an event type.

    Returns the catalog entry if found, otherwise returns a default info entry.
    """
    return EVENT_CATALOG.get(event_type, {
        "description": f"Event: {event_type}",
        "severity": INFO,
    })


def get_event_severity(event_type: str) -> str:
    """Return the severity level for an event type."""
    return get_event_info(event_type).get("severity", INFO)


def get_events_by_entity(entity_type: str) -> dict[str, dict]:
    """Return all catalog entries for a given entity type."""
    prefix = f"{entity_type}_"
    return {k: v for k, v in EVENT_CATALOG.items() if k.startswith(prefix)}


def get_events_by_severity(severity: str) -> dict[str, dict]:
    """Return all catalog entries matching a severity level."""
    return {k: v for k, v in EVENT_CATALOG.items() if v.get("severity") == severity}


async def log_event(
    db: AsyncSession,
    user: dict,
    project_id: Optional[uuid.UUID],
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    event_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> EventLog:
    """
    Create an EventLog entry in the database.

    This is the primary helper for services to log domain events. It derives
    the action from the event_type (e.g., "rfi_created" -> "created") and
    populates all fields on the EventLog model.

    Args:
        db: The async database session.
        user: User context dict with user_id, user_type, organization_id.
        project_id: The project UUID (if project-scoped).
        event_type: The event type string (e.g., "rfi_created").
        entity_type: The entity type (e.g., "rfi"). Derived from event_type if omitted.
        entity_id: The UUID of the affected entity.
        event_data: Additional JSON data for the event.
        ip_address: The client IP address (optional).
        user_agent: The client user agent string (optional).

    Returns:
        The created EventLog instance.
    """
    # Derive action and entity_type from event_type if not provided
    action = None
    if entity_type is None and "_" in event_type:
        # Split on last underscore: "punch_list_item_created" -> entity="punch_list_item", action="created"
        # Try to find the matching catalog entry to determine the split point
        parts = event_type.rsplit("_", 1)
        if len(parts) == 2:
            action = parts[1]
            entity_type = parts[0]
    elif entity_type and "_" in event_type:
        # entity_type provided, derive action by stripping it
        prefix = f"{entity_type}_"
        if event_type.startswith(prefix):
            action = event_type[len(prefix):]

    # Get organization_id from user context
    organization_id = user.get("organization_id")

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type"),
        user_id=user.get("user_id"),
        event_type=event_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_data=event_data or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    await db.flush()
    return event


async def log_event_non_blocking(
    user: dict,
    project_id: Optional[uuid.UUID],
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    event_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Fire-and-forget version of log_event using its own session.

    Use this when logging should not participate in the caller's transaction
    or when the caller does not have a session available.
    """
    from app.database import async_session_factory

    try:
        async with async_session_factory() as session:
            await log_event(
                db=session,
                user=user,
                project_id=project_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to log event (non-blocking): %s", event_type)
