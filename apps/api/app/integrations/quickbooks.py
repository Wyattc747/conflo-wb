"""QuickBooks Online integration — OAuth + sync stubs."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.integration_connection import IntegrationConnection
from app.models.event_log import EventLog
from app.services.encryption_service import decrypt, encrypt


async def initiate_quickbooks_oauth(user: dict, redirect_uri: str) -> str:
    """Start QuickBooks OAuth flow — returns authorization URL."""
    from intuitlib.client import AuthClient
    from intuitlib.enums import Scopes

    auth_client = AuthClient(
        client_id=settings.QUICKBOOKS_CLIENT_ID,
        client_secret=settings.QUICKBOOKS_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        environment=settings.QUICKBOOKS_ENVIRONMENT,
    )
    auth_url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    return auth_url


async def complete_quickbooks_oauth(
    db: AsyncSession, user: dict, code: str, realm_id: str, redirect_uri: str,
) -> IntegrationConnection:
    """Exchange auth code for tokens."""
    from intuitlib.client import AuthClient

    auth_client = AuthClient(
        client_id=settings.QUICKBOOKS_CLIENT_ID,
        client_secret=settings.QUICKBOOKS_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        environment=settings.QUICKBOOKS_ENVIRONMENT,
    )
    auth_client.get_bearer_token(code, realm_id=realm_id)

    # Upsert connection
    existing = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.provider == "quickbooks",
        )
    )
    connection = existing.scalar_one_or_none()

    if connection:
        connection.access_token_enc = encrypt(auth_client.access_token)
        connection.refresh_token_enc = encrypt(auth_client.refresh_token) if auth_client.refresh_token else connection.refresh_token_enc
        connection.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        connection.provider_metadata = {"realm_id": realm_id}
        connection.status = "CONNECTED"
    else:
        connection = IntegrationConnection(
            organization_id=user["organization_id"],
            user_id=user["user_id"],
            provider="quickbooks",
            access_token_enc=encrypt(auth_client.access_token),
            refresh_token_enc=encrypt(auth_client.refresh_token) if auth_client.refresh_token else None,
            token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            provider_metadata={"realm_id": realm_id},
            scopes=["accounting"],
            status="CONNECTED",
        )
        db.add(connection)

    await db.flush()
    return connection


async def disconnect_quickbooks(db: AsyncSession, user: dict):
    """Remove QuickBooks connection."""
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.organization_id == user["organization_id"],
            IntegrationConnection.provider == "quickbooks",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(404, "QuickBooks not connected")

    await db.delete(connection)
    await db.flush()


# ── Sync Stubs (expanded post-MVP) ──


async def sync_invoice_to_quickbooks(db: AsyncSession, pay_app, user: dict):
    """Stub: Push approved pay app as invoice to QuickBooks."""
    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=pay_app.project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="qb_sync_stub",
        event_data={"action": "create_invoice", "pay_app_id": str(pay_app.id)},
    )
    db.add(event)
    await db.flush()


async def sync_vendor_from_quickbooks(db: AsyncSession, user: dict):
    """Stub: Pull vendors from QuickBooks -> SubCompanies."""
    pass


async def sync_chart_of_accounts(db: AsyncSession, user: dict):
    """Stub: Pull chart of accounts -> cost code templates."""
    pass
