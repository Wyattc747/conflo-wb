"""Scheduled notification jobs — deadline checks and reminders.

Run via cron or management command:
    python -m app.services.scheduled_jobs daily
    python -m app.services.scheduled_jobs hourly
"""

import asyncio
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.rfi import RFI
from app.models.submittal import Submittal
from app.models.bid_package import BidPackage
from app.services.notification_service import create_notification


async def daily_deadline_check():
    """Check for approaching deadlines and send notifications."""
    async with async_session_factory() as db:
        today = date.today()

        # RFIs due in 2 days
        try:
            result = await db.execute(
                select(RFI).where(
                    RFI.status == "OPEN",
                    RFI.due_date == today + timedelta(days=2),
                    RFI.deleted_at.is_(None),
                )
            )
            for rfi in result.scalars():
                if rfi.assigned_to:
                    await create_notification(
                        db, "gc", rfi.assigned_to,
                        "rfi_due_approaching",
                        f"RFI-{rfi.number:03d} due in 2 days: {rfi.subject}",
                        body=f"RFI-{rfi.number:03d} '{rfi.subject}' is due on {rfi.due_date}.",
                        source_type="rfi", source_id=rfi.id,
                        project_id=rfi.project_id,
                    )
        except Exception:
            pass

        # Submittals due in 3 days
        try:
            result = await db.execute(
                select(Submittal).where(
                    Submittal.status.in_(["SUBMITTED", "UNDER_REVIEW"]),
                    Submittal.due_date == today + timedelta(days=3),
                    Submittal.deleted_at.is_(None),
                )
            )
            for sub in result.scalars():
                if sub.reviewer_id:
                    await create_notification(
                        db, "gc", sub.reviewer_id,
                        "submittal_due_approaching",
                        f"Submittal {sub.number:03d} review due in 3 days",
                        source_type="submittal", source_id=sub.id,
                        project_id=sub.project_id,
                    )
        except Exception:
            pass

        # Bid packages closing in 3 days
        try:
            result = await db.execute(
                select(BidPackage).where(
                    BidPackage.status == "PUBLISHED",
                    BidPackage.bid_due_date == today + timedelta(days=3),
                    BidPackage.deleted_at.is_(None),
                )
            )
            for bp in result.scalars():
                if bp.created_by:
                    await create_notification(
                        db, "gc", bp.created_by,
                        "bid_deadline_approaching",
                        f"Bid package {bp.number:03d} closes in 3 days",
                        source_type="bid_package", source_id=bp.id,
                        project_id=bp.project_id,
                    )
        except Exception:
            pass

        await db.commit()


async def hourly_sync_check():
    """Check for overdue items that need escalation."""
    async with async_session_factory() as db:
        today = date.today()

        # Overdue RFIs (past due date, still open)
        try:
            result = await db.execute(
                select(RFI).where(
                    RFI.status == "OPEN",
                    RFI.due_date < today,
                    RFI.deleted_at.is_(None),
                )
            )
            for rfi in result.scalars():
                if rfi.assigned_to:
                    await create_notification(
                        db, "gc", rfi.assigned_to,
                        "rfi_due_approaching",
                        f"OVERDUE: RFI-{rfi.number:03d} was due {rfi.due_date}",
                        source_type="rfi", source_id=rfi.id,
                        project_id=rfi.project_id,
                    )
        except Exception:
            pass

        await db.commit()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if command == "daily":
        asyncio.run(daily_deadline_check())
    elif command == "hourly":
        asyncio.run(hourly_sync_check())
    else:
        print(f"Unknown command: {command}. Use 'daily' or 'hourly'.")
