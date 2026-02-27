"""Notification service — in-app + email notifications."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser

DEFAULT_PREFERENCES = {
    "email_enabled": True,
    "email_categories": {
        "assigned_to_me": True,
        "status_changes": True,
        "mentions": True,
        "approaching_deadlines": True,
        "bid_invitations": True,
        "pay_app_decisions": True,
        "meeting_scheduled": True,
        "meeting_minutes": True,
        "daily_summary": False,
    },
}

# Map notification types to email preference categories
CATEGORY_MAP = {
    "rfi_assigned": "assigned_to_me",
    "punch_assigned": "assigned_to_me",
    "todo_assigned": "assigned_to_me",
    "project_assigned": "assigned_to_me",
    "rfi_response": "status_changes",
    "submittal_decision": "status_changes",
    "co_approved": "status_changes",
    "co_rejected": "status_changes",
    "pay_app_approved": "status_changes",
    "pay_app_rejected": "status_changes",
    "punch_completed": "status_changes",
    "owner_pay_app_approved": "status_changes",
    "delay_pending_approval": "status_changes",
    "payment_failed": "status_changes",
    "closeout_docs_requested": "status_changes",
    "project_active": "status_changes",
    "project_closed": "status_changes",
    "comment_mention": "mentions",
    "rfi_due_approaching": "approaching_deadlines",
    "submittal_due_approaching": "approaching_deadlines",
    "bid_deadline_approaching": "approaching_deadlines",
    "milestone_approaching": "approaching_deadlines",
    "sub_mobilization": "approaching_deadlines",
    "invited_to_bid": "bid_invitations",
    "bid_received": "bid_invitations",
    "bid_awarded": "bid_invitations",
    "bid_not_awarded": "bid_invitations",
    "bid_recommendation": "bid_invitations",
    "sub_pay_app_submitted": "pay_app_decisions",
    "pay_app_ready": "pay_app_decisions",
    "meeting_scheduled": "meeting_scheduled",
    "meeting_minutes": "meeting_minutes",
}


async def create_notification(
    db: AsyncSession,
    user_type: str,
    recipient_id: UUID | None,
    notification_type: str,
    title: str,
    body: str | None = None,
    source_type: str | None = None,
    source_id: UUID | None = None,
    project_id: UUID | None = None,
    metadata: dict | None = None,
):
    """Create in-app notification and optionally send email."""
    if not recipient_id:
        return

    notification = Notification(
        user_type=user_type,
        user_id=recipient_id,
        type=notification_type,
        title=title,
        body=body,
        source_type=source_type,
        source_id=source_id,
        project_id=project_id,
        metadata_=metadata or {},
    )
    db.add(notification)
    await db.flush()

    # Send email notification if enabled
    recipient = await _resolve_recipient(db, user_type, recipient_id)
    if recipient:
        email_category = CATEGORY_MAP.get(notification_type, "status_changes")
        prefs = getattr(recipient, "notification_preferences", None) or DEFAULT_PREFERENCES

        if prefs.get("email_enabled") and prefs.get("email_categories", {}).get(email_category, True):
            link = _build_entity_link(source_type, source_id, project_id, user_type)
            await _send_notification_email(recipient.email, title, body, link, notification_type)

    return notification


async def create_bulk_notifications(
    db: AsyncSession,
    recipients: list[tuple[str, UUID]],  # [(user_type, user_id), ...]
    notification_type: str,
    title: str,
    body: str | None = None,
    source_type: str | None = None,
    source_id: UUID | None = None,
    project_id: UUID | None = None,
    metadata: dict | None = None,
):
    """Create notifications for multiple recipients."""
    for user_type, recipient_id in recipients:
        await create_notification(
            db, user_type, recipient_id, notification_type,
            title, body, source_type, source_id, project_id, metadata,
        )


async def list_notifications(
    db: AsyncSession,
    user_type: str,
    user_id: UUID,
    page: int = 1,
    per_page: int = 25,
    unread_only: bool = False,
) -> tuple[list[Notification], int]:
    """List notifications for a user, newest first."""
    query = select(Notification).where(
        Notification.user_type == user_type,
        Notification.user_id == user_id,
    )
    if unread_only:
        query = query.where(Notification.read_at.is_(None))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_unread_count(
    db: AsyncSession,
    user_type: str,
    user_id: UUID,
) -> int:
    """Get count of unread notifications."""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_type == user_type,
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )
    return result.scalar() or 0


async def mark_read(
    db: AsyncSession,
    notification_id: UUID,
    user_type: str,
    user_id: UUID,
) -> Notification:
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_type == user_type,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        from fastapi import HTTPException
        raise HTTPException(404, "Notification not found")

    notification.read_at = datetime.now(timezone.utc)
    await db.flush()
    return notification


async def mark_all_read(
    db: AsyncSession,
    user_type: str,
    user_id: UUID,
) -> int:
    """Mark all notifications as read. Returns count updated."""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_type == user_type,
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.flush()
    return result.rowcount


async def dismiss_notification(
    db: AsyncSession,
    notification_id: UUID,
    user_type: str,
    user_id: UUID,
):
    """Delete a notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_type == user_type,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        from fastapi import HTTPException
        raise HTTPException(404, "Notification not found")

    await db.delete(notification)
    await db.flush()


async def get_preferences(
    db: AsyncSession,
    user_type: str,
    user_id: UUID,
) -> dict:
    """Get notification preferences for a user."""
    user = await _resolve_recipient(db, user_type, user_id)
    if not user:
        return DEFAULT_PREFERENCES
    return getattr(user, "notification_preferences", None) or DEFAULT_PREFERENCES


async def update_preferences(
    db: AsyncSession,
    user_type: str,
    user_id: UUID,
    preferences: dict,
) -> dict:
    """Update notification preferences."""
    user = await _resolve_recipient(db, user_type, user_id)
    if user and hasattr(user, "notification_preferences"):
        user.notification_preferences = preferences
        await db.flush()
    return preferences


def format_notification_response(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "source_type": n.source_type,
        "source_id": str(n.source_id) if n.source_id else None,
        "project_id": str(n.project_id) if n.project_id else None,
        "metadata": n.metadata_,
        "read": n.read_at is not None,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


# ── Private helpers ──


async def _resolve_recipient(db: AsyncSession, user_type: str, user_id: UUID):
    """Resolve a recipient user record from any user type."""
    if user_type == "gc":
        return await db.get(User, user_id)
    elif user_type == "sub":
        return await db.get(SubUser, user_id)
    elif user_type == "owner":
        return await db.get(OwnerUser, user_id)
    return None


def _build_entity_link(source_type: str | None, source_id: UUID | None, project_id: UUID | None, user_type: str) -> str:
    """Build a deep link to the entity for email CTAs."""
    base = settings.FRONTEND_URL
    prefix_map = {"gc": "/app", "sub": "/sub", "owner": "/owner"}
    prefix = prefix_map.get(user_type, "/app")

    if not source_type or not project_id:
        return f"{base}{prefix}/notifications"

    entity_routes = {
        "rfi": f"{prefix}/projects/{project_id}/rfis/{source_id}",
        "submittal": f"{prefix}/projects/{project_id}/submittals/{source_id}",
        "change_order": f"{prefix}/projects/{project_id}/change-orders/{source_id}",
        "pay_app": f"{prefix}/projects/{project_id}/pay-apps/{source_id}",
        "punch_list_item": f"{prefix}/projects/{project_id}/punch-list/{source_id}",
        "daily_log": f"{prefix}/projects/{project_id}/daily-logs/{source_id}",
        "meeting": f"{prefix}/projects/{project_id}/meetings/{source_id}",
        "bid_package": f"{prefix}/projects/{project_id}/bid-packages/{source_id}",
        "todo": f"{prefix}/projects/{project_id}/todos/{source_id}",
        "inspection": f"{prefix}/projects/{project_id}/inspections/{source_id}",
        "schedule_delay": f"{prefix}/projects/{project_id}/schedule/delays",
        "project": f"{prefix}/projects/{project_id}",
        "organization": f"{prefix}/settings/billing",
    }

    path = entity_routes.get(source_type, f"{prefix}/notifications")
    return f"{base}{path}"


async def _send_notification_email(
    to_email: str,
    title: str,
    body: str | None,
    link: str,
    notification_type: str,
):
    """Send notification email via Resend."""
    if not settings.RESEND_API_KEY:
        return  # Skip in dev/test

    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY

        html = _render_notification_email(title, body, link)

        resend.Emails.send({
            "from": "Conflo <notifications@conflo.app>",
            "to": to_email,
            "subject": title,
            "html": html,
        })
    except Exception:
        pass  # Email failure is non-critical


def _render_notification_email(title: str, body: str | None, link: str) -> str:
    """Render notification email HTML."""
    body_html = f"<p style='margin:0 0 24px 0;font-size:16px;line-height:1.5;color:#374151;'>{body}</p>" if body else ""

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
          <tr>
            <td style="padding:32px 40px 24px 40px;border-bottom:1px solid #e5e7eb;">
              <span style="font-size:28px;font-weight:700;color:#1B2A4A;letter-spacing:-0.5px;">Conflo</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 40px;">
              <p style="margin:0 0 16px 0;font-size:18px;font-weight:600;line-height:1.4;color:#1B2A4A;">
                {title}
              </p>
              {body_html}
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px 0;">
                <tr>
                  <td style="border-radius:6px;background-color:#2E75B6;">
                    <a href="{link}" target="_blank"
                       style="display:inline-block;padding:14px 32px;font-size:16px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:6px;">
                      View Details
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0;font-size:14px;line-height:1.5;color:#6b7280;">
                You received this notification from Conflo.
                <a href="{link.rsplit('/', 1)[0] if '/' in link else link}" style="color:#2E75B6;">Manage notification preferences</a>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 40px;border-top:1px solid #e5e7eb;background-color:#f9fafb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                &copy; 2026 Conflo. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
