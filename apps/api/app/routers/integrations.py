"""Integration management router — connect/disconnect third-party services."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.integration_connection import IntegrationConnection
from app.schemas.integration import (
    IntegrationStatus,
    IntegrationsListResponse,
    OAuthCallbackRequest,
    OAuthUrlResponse,
)

gc_router = APIRouter(prefix="/api/gc/integrations", tags=["integrations"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


INTEGRATION_CATALOG = [
    {
        "provider": "google_calendar",
        "name": "Google Calendar",
        "description": "Sync meetings to your Google Calendar",
    },
    {
        "provider": "microsoft",
        "name": "Microsoft Outlook",
        "description": "Sync meetings and send emails via Outlook",
    },
    {
        "provider": "quickbooks",
        "name": "QuickBooks Online",
        "description": "Sync invoices and financial data",
    },
    {
        "provider": "zoom",
        "name": "Zoom",
        "description": "Create Zoom meetings automatically",
    },
    {
        "provider": "docusign",
        "name": "DocuSign",
        "description": "Send documents for electronic signature",
    },
]

COMING_SOON_PROVIDERS = {"zoom", "docusign"}


@gc_router.get("")
async def list_integrations(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all integrations with connection status."""
    user = _get_user(request)

    # Get all connections for this user
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.user_id == user["user_id"],
        )
    )
    connections = {c.provider: c for c in result.scalars().all()}

    integrations = []
    for catalog in INTEGRATION_CATALOG:
        provider = catalog["provider"]
        conn = connections.get(provider)
        if provider in COMING_SOON_PROVIDERS:
            status = "COMING_SOON"
        elif conn and conn.status == "CONNECTED":
            status = "CONNECTED"
        else:
            status = "DISCONNECTED"

        integrations.append(IntegrationStatus(
            provider=provider,
            name=catalog["name"],
            description=catalog["description"],
            status=status,
            connected_at=conn.created_at.isoformat() if conn and conn.status == "CONNECTED" else None,
        ))

    return IntegrationsListResponse(data=integrations)


# ── Google Calendar ──


@gc_router.post("/google-calendar/connect")
async def connect_google_calendar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/google-calendar/callback"

    from app.integrations.google_calendar import initiate_google_oauth
    auth_url, state = await initiate_google_oauth(user, redirect_uri)

    return {"data": OAuthUrlResponse(auth_url=auth_url, state=state).model_dump(), "meta": {}}


@gc_router.post("/google-calendar/callback")
async def google_calendar_callback(
    request: Request,
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/google-calendar/callback"

    from app.integrations.google_calendar import complete_google_oauth
    connection = await complete_google_oauth(db, user, body.code, body.state or "", redirect_uri)

    return {"data": {"status": "CONNECTED", "provider": "google_calendar"}, "meta": {}}


@gc_router.delete("/google-calendar/disconnect")
async def disconnect_google_calendar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)

    from app.integrations.google_calendar import disconnect_google
    await disconnect_google(db, user)

    return {"data": {"status": "DISCONNECTED", "provider": "google_calendar"}, "meta": {}}


# ── Microsoft ──


@gc_router.post("/microsoft/connect")
async def connect_microsoft(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/microsoft/callback"

    from app.integrations.microsoft_graph import initiate_microsoft_oauth
    auth_url = await initiate_microsoft_oauth(user, redirect_uri)

    return {"data": OAuthUrlResponse(auth_url=auth_url).model_dump(), "meta": {}}


@gc_router.post("/microsoft/callback")
async def microsoft_callback(
    request: Request,
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/microsoft/callback"

    from app.integrations.microsoft_graph import complete_microsoft_oauth
    connection = await complete_microsoft_oauth(db, user, body.code, redirect_uri)

    return {"data": {"status": "CONNECTED", "provider": "microsoft"}, "meta": {}}


@gc_router.delete("/microsoft/disconnect")
async def disconnect_microsoft(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)

    from app.integrations.microsoft_graph import disconnect_microsoft as _disconnect
    await _disconnect(db, user)

    return {"data": {"status": "DISCONNECTED", "provider": "microsoft"}, "meta": {}}


# ── QuickBooks ──


@gc_router.post("/quickbooks/connect")
async def connect_quickbooks(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/quickbooks/callback"

    from app.integrations.quickbooks import initiate_quickbooks_oauth
    auth_url = await initiate_quickbooks_oauth(user, redirect_uri)

    return {"data": OAuthUrlResponse(auth_url=auth_url).model_dump(), "meta": {}}


@gc_router.post("/quickbooks/callback")
async def quickbooks_callback(
    request: Request,
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    redirect_uri = f"{settings.FRONTEND_URL}/app/settings/integrations/quickbooks/callback"

    if not body.realm_id:
        raise HTTPException(400, "realm_id required for QuickBooks")

    from app.integrations.quickbooks import complete_quickbooks_oauth
    connection = await complete_quickbooks_oauth(db, user, body.code, body.realm_id, redirect_uri)

    return {"data": {"status": "CONNECTED", "provider": "quickbooks"}, "meta": {}}


@gc_router.delete("/quickbooks/disconnect")
async def disconnect_quickbooks(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)

    from app.integrations.quickbooks import disconnect_quickbooks as _disconnect
    await _disconnect(db, user)

    return {"data": {"status": "DISCONNECTED", "provider": "quickbooks"}, "meta": {}}
