"""Microsoft Graph integration — OAuth, Outlook Calendar, and Email."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.integration_connection import IntegrationConnection
from app.models.meeting import Meeting
from app.models.user import User
from app.services.encryption_service import decrypt, encrypt

MICROSOFT_SCOPES = [
    "Calendars.ReadWrite",
    "Mail.Send",
    "User.Read",
    "OnlineMeetings.ReadWrite",
]

AUTHORITY = "https://login.microsoftonline.com/common"
GRAPH_URL = "https://graph.microsoft.com/v1.0"


def _get_msal_app():
    import msal
    return msal.ConfidentialClientApplication(
        settings.MICROSOFT_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )


async def initiate_microsoft_oauth(user: dict, redirect_uri: str) -> str:
    """Start Microsoft OAuth flow — returns authorization URL."""
    app = _get_msal_app()
    auth_url = app.get_authorization_request_url(
        scopes=MICROSOFT_SCOPES,
        redirect_uri=redirect_uri,
        state=str(user["user_id"]),
    )
    return auth_url


async def complete_microsoft_oauth(
    db: AsyncSession, user: dict, code: str, redirect_uri: str,
) -> IntegrationConnection:
    """Exchange auth code for tokens."""
    app = _get_msal_app()
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=MICROSOFT_SCOPES,
        redirect_uri=redirect_uri,
    )

    if "access_token" not in result:
        raise HTTPException(400, f"OAuth failed: {result.get('error_description', 'Unknown error')}")

    # Upsert connection
    existing = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.user_id == user["user_id"],
            IntegrationConnection.provider == "microsoft",
        )
    )
    connection = existing.scalar_one_or_none()

    expiry = datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 3600))

    if connection:
        connection.access_token_enc = encrypt(result["access_token"])
        if result.get("refresh_token"):
            connection.refresh_token_enc = encrypt(result["refresh_token"])
        connection.token_expiry = expiry
        connection.status = "CONNECTED"
    else:
        connection = IntegrationConnection(
            organization_id=user["organization_id"],
            user_id=user["user_id"],
            provider="microsoft",
            access_token_enc=encrypt(result["access_token"]),
            refresh_token_enc=encrypt(result["refresh_token"]) if result.get("refresh_token") else None,
            token_expiry=expiry,
            scopes=MICROSOFT_SCOPES,
            status="CONNECTED",
        )
        db.add(connection)

    await db.flush()
    return connection


async def disconnect_microsoft(db: AsyncSession, user: dict):
    """Remove Microsoft connection."""
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.user_id == user["user_id"],
            IntegrationConnection.provider == "microsoft",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(404, "Microsoft not connected")

    await db.delete(connection)
    await db.flush()


async def get_microsoft_token(db: AsyncSession, user_id: UUID) -> str | None:
    """Get a valid access token, refreshing if needed."""
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == "microsoft",
            IntegrationConnection.status == "CONNECTED",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        return None

    # Check if token needs refresh
    if connection.token_expiry and connection.token_expiry < datetime.now(timezone.utc):
        if connection.refresh_token_enc:
            app = _get_msal_app()
            refresh_result = app.acquire_token_by_refresh_token(
                decrypt(connection.refresh_token_enc),
                scopes=MICROSOFT_SCOPES,
            )
            if "access_token" in refresh_result:
                connection.access_token_enc = encrypt(refresh_result["access_token"])
                connection.token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=refresh_result.get("expires_in", 3600)
                )
                await db.flush()
            else:
                connection.status = "EXPIRED"
                await db.flush()
                return None
        else:
            return None

    return decrypt(connection.access_token_enc)


async def sync_meeting_to_outlook(db: AsyncSession, meeting: Meeting, user: dict) -> dict | None:
    """Push a Conflo meeting to Outlook Calendar."""
    token = await get_microsoft_token(db, user["user_id"])
    if not token:
        return None

    attendees = []
    for att in (meeting.attendees or []):
        if isinstance(att, dict) and att.get("email"):
            attendees.append({
                "emailAddress": {"address": att["email"], "name": att.get("name", "")},
                "type": "required",
            })

    is_teams = meeting.virtual_provider and meeting.virtual_provider.upper() == "TEAMS"

    event = {
        "subject": meeting.title,
        "body": {
            "contentType": "HTML",
            "content": f"<p>Conflo Meeting: {meeting.title}</p><p>{meeting.agenda or ''}</p>",
        },
        "start": {
            "dateTime": meeting.start_time.strftime("%Y-%m-%dT%H:%M:%S") if meeting.start_time else meeting.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "Mountain Standard Time",
        },
        "end": {
            "dateTime": meeting.end_time.strftime("%Y-%m-%dT%H:%M:%S") if meeting.end_time else (meeting.start_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S") if meeting.start_time else meeting.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "Mountain Standard Time",
        },
        "attendees": attendees,
        "isOnlineMeeting": is_teams,
    }

    if is_teams:
        event["onlineMeetingProvider"] = "teamsForBusiness"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRAPH_URL}/me/events",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=event,
        )
        response.raise_for_status()
        return response.json()


async def delete_outlook_event(db: AsyncSession, outlook_event_id: str, user: dict):
    """Delete Outlook event on meeting cancellation."""
    if not outlook_event_id:
        return

    token = await get_microsoft_token(db, user["user_id"])
    if not token:
        return

    async with httpx.AsyncClient() as client:
        try:
            await client.delete(
                f"{GRAPH_URL}/me/events/{outlook_event_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        except Exception:
            pass


async def send_via_outlook(db: AsyncSession, user_id: UUID, to_email: str, subject: str, html_body: str) -> bool:
    """Send email through user's Outlook account."""
    token = await get_microsoft_token(db, user_id)
    if not token:
        return False

    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRAPH_URL}/me/sendMail",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=message,
        )
        return response.status_code == 202
