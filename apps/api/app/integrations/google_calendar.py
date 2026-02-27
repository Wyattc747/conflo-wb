"""Google Calendar integration — OAuth + meeting sync."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.integration_connection import IntegrationConnection
from app.models.meeting import Meeting
from app.models.user import User
from app.services.encryption_service import decrypt, encrypt

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


async def initiate_google_oauth(user: dict, redirect_uri: str) -> tuple[str, str]:
    """Start OAuth flow — returns (authorization_url, state)."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url, state


async def complete_google_oauth(
    db: AsyncSession, user: dict, code: str, state: str, redirect_uri: str,
) -> IntegrationConnection:
    """Exchange auth code for tokens, store encrypted."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Upsert connection
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.user_id == user["user_id"],
            IntegrationConnection.provider == "google_calendar",
        )
    )
    connection = result.scalar_one_or_none()

    if connection:
        connection.access_token_enc = encrypt(credentials.token)
        connection.refresh_token_enc = encrypt(credentials.refresh_token) if credentials.refresh_token else connection.refresh_token_enc
        connection.token_expiry = credentials.expiry
        connection.status = "CONNECTED"
    else:
        connection = IntegrationConnection(
            organization_id=user["organization_id"],
            user_id=user["user_id"],
            provider="google_calendar",
            access_token_enc=encrypt(credentials.token),
            refresh_token_enc=encrypt(credentials.refresh_token) if credentials.refresh_token else None,
            token_expiry=credentials.expiry,
            scopes=GOOGLE_SCOPES,
            status="CONNECTED",
        )
        db.add(connection)

    await db.flush()
    return connection


async def disconnect_google(db: AsyncSession, user: dict):
    """Revoke and remove Google Calendar connection."""
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.user_id == user["user_id"],
            IntegrationConnection.provider == "google_calendar",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(404, "Google Calendar not connected")

    # Try to revoke the token
    try:
        import httpx
        token = decrypt(connection.access_token_enc)
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token},
            )
    except Exception:
        pass  # Revocation failure is non-critical

    await db.delete(connection)
    await db.flush()


def _get_credentials(connection: IntegrationConnection):
    """Build Google credentials from stored connection."""
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=decrypt(connection.access_token_enc),
        refresh_token=decrypt(connection.refresh_token_enc) if connection.refresh_token_enc else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )


async def get_google_connection(db: AsyncSession, user_id: UUID) -> IntegrationConnection | None:
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == user_id,
            IntegrationConnection.provider == "google_calendar",
            IntegrationConnection.status == "CONNECTED",
        )
    )
    return result.scalar_one_or_none()


async def sync_meeting_to_google(db: AsyncSession, meeting: Meeting, user: dict) -> dict | None:
    """Push a Conflo meeting to Google Calendar."""
    connection = await get_google_connection(db, user["user_id"])
    if not connection:
        return None

    from googleapiclient.discovery import build

    credentials = _get_credentials(connection)
    service = build("calendar", "v3", credentials=credentials)

    attendees = []
    for att in (meeting.attendees or []):
        if isinstance(att, dict) and att.get("email"):
            attendees.append({"email": att["email"]})
        elif isinstance(att, str):
            u = await db.get(User, UUID(att)) if len(att) == 36 else None
            if u and u.email:
                attendees.append({"email": u.email})

    event = {
        "summary": meeting.title,
        "description": f"Conflo Meeting: {meeting.title}\n\n{meeting.agenda or ''}",
        "start": {
            "dateTime": meeting.start_time.isoformat() if meeting.start_time else meeting.scheduled_date.isoformat(),
            "timeZone": "America/Denver",
        },
        "end": {
            "dateTime": meeting.end_time.isoformat() if meeting.end_time else (meeting.start_time + timedelta(hours=1)).isoformat() if meeting.start_time else meeting.scheduled_date.isoformat(),
            "timeZone": "America/Denver",
        },
        "attendees": attendees,
        "reminders": {"useDefault": True},
    }

    if meeting.virtual_provider and meeting.virtual_provider.upper() == "GOOGLE_MEET":
        event["conferenceData"] = {
            "createRequest": {"requestId": str(meeting.id)},
        }

    result = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1 if meeting.virtual_provider and meeting.virtual_provider.upper() == "GOOGLE_MEET" else 0,
        sendUpdates="all",
    ).execute()

    # Store Google Calendar event ID in provider_metadata-style field
    # We use the meeting's existing fields to track the external ID
    if not hasattr(meeting, "_google_event_id"):
        # Store in meeting action_items metadata or a dedicated field
        pass

    return result


async def delete_google_event(db: AsyncSession, google_event_id: str, user: dict):
    """Delete Google Calendar event when meeting is cancelled."""
    if not google_event_id:
        return

    connection = await get_google_connection(db, user["user_id"])
    if not connection:
        return

    from googleapiclient.discovery import build

    credentials = _get_credentials(connection)
    service = build("calendar", "v3", credentials=credentials)

    try:
        service.events().delete(
            calendarId="primary",
            eventId=google_event_id,
            sendUpdates="all",
        ).execute()
    except Exception:
        pass  # Event may already be deleted
