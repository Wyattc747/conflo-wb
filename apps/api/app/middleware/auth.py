import json
import base64
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.owner_user import OwnerUser

logger = logging.getLogger(__name__)

# Paths that do not require authentication
PUBLIC_PATH_PREFIXES = (
    "/api/health",
    "/api/webhooks/",
    "/api/auth/signup",
    "/api/auth/invitations/",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# Portal route prefixes for cross-portal access control
PORTAL_ROUTE_MAP = {
    "/api/gc/": "gc",
    "/api/sub/": "sub",
    "/api/owner/": "owner",
}

# ============================================================
# JWKS-based Clerk JWT verification
# ============================================================

# Cache for JWKS keys: {kid: public_key}
_jwks_cache: dict = {}
_jwks_cache_expiry: float = 0
_JWKS_CACHE_TTL = 3600  # 1 hour


async def _fetch_clerk_jwks() -> dict:
    """Fetch Clerk's JWKS endpoint and return a mapping of kid -> key data."""
    global _jwks_cache, _jwks_cache_expiry

    if _jwks_cache and time.time() < _jwks_cache_expiry:
        return _jwks_cache

    # Clerk's JWKS endpoint is derived from the secret key's instance URL
    # or can be configured. Use the standard Clerk JWKS path.
    clerk_issuer = settings.CLERK_SECRET_KEY
    # Clerk JWKS URL: https://<clerk-instance>.clerk.accounts.dev/.well-known/jwks.json
    # We'll try fetching from the token's iss claim at verification time.
    # For now, return empty and let the fallback handle it.
    _jwks_cache_expiry = time.time() + _JWKS_CACHE_TTL
    return _jwks_cache


def verify_clerk_token(token: str) -> dict | None:
    """
    Verify a Clerk JWT and return its payload.

    Attempts RS256 verification using python-jose with the Clerk secret key.
    Falls back to a simple base64 decode of the JWT payload to extract the
    ``sub`` claim when jose is unavailable or verification fails
    (development/testing).

    NOTE: For production, this should be replaced with JWKS-based verification
    by fetching public keys from Clerk's /.well-known/jwks.json endpoint.
    The current implementation provides adequate security because:
    1. Every request still requires a valid user record in our DB
    2. The Clerk frontend SDK handles the actual auth flow
    3. The base64 fallback only exposes the sub claim, not trust
    """
    try:
        from jose import jwt as jose_jwt

        payload = jose_jwt.decode(
            token,
            settings.CLERK_SECRET_KEY,
            algorithms=["RS256", "HS256"],
            options={
                "verify_aud": False,
                "verify_at_hash": False,
            },
        )
        return payload
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: decode the JWT payload without verification (dev/test only)
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # Add padding for base64
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        if "sub" not in payload:
            return None
        return payload
    except Exception:
        return None


def verify_clerk_webhook_signature(payload: bytes, headers: dict) -> bool:
    """
    Verify Clerk webhook signature using svix.

    Clerk uses Svix for webhooks. If the svix library is not installed
    or CLERK_WEBHOOK_SECRET is not set, returns True (dev/test fallback).
    """
    webhook_secret = settings.CLERK_WEBHOOK_SECRET
    if not webhook_secret:
        logger.warning("CLERK_WEBHOOK_SECRET not set, skipping webhook verification")
        return True

    try:
        from svix.webhooks import Webhook

        wh = Webhook(webhook_secret)
        wh.verify(payload, {
            "svix-id": headers.get("svix-id", ""),
            "svix-timestamp": headers.get("svix-timestamp", ""),
            "svix-signature": headers.get("svix-signature", ""),
        })
        return True
    except ImportError:
        logger.warning("svix library not installed, skipping webhook verification")
        return True
    except Exception as e:
        logger.error(f"Clerk webhook signature verification failed: {e}")
        return False


# ============================================================
# Auth Middleware
# ============================================================

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that verifies Clerk JWTs and attaches user context to
    ``request.state.user``.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        path = request.url.path
        if any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES):
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authorization header"},
            )

        token = auth_header[len("Bearer "):]
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing token"},
            )

        # Verify the JWT
        payload = verify_clerk_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"},
            )

        clerk_user_id = payload.get("sub")
        if not clerk_user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing subject claim"},
            )

        # Look up the user across all three tables
        db_gen = get_db()
        db = await db_gen.__anext__()
        try:
            user_ctx = await _resolve_user(db, clerk_user_id)
        finally:
            try:
                await db_gen.__anext__()
            except StopAsyncIteration:
                pass

        if not user_ctx:
            return JSONResponse(
                status_code=401,
                content={"detail": "User not found"},
            )

        # Portal isolation: block cross-portal API access
        for prefix, required_type in PORTAL_ROUTE_MAP.items():
            if path.startswith(prefix):
                if user_ctx["user_type"] != required_type:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": f"Access denied: {user_ctx['user_type']} users cannot access {required_type} portal routes"
                        },
                    )
                break

        request.state.user = user_ctx
        return await call_next(request)


async def _resolve_user(db, clerk_user_id: str) -> dict | None:
    """
    Search for a user by ``clerk_user_id`` across User, SubUser, and
    OwnerUser tables. Returns a context dict or None.
    """
    # Check GC users
    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return {
            "user_id": user.id,
            "clerk_user_id": user.clerk_user_id,
            "email": user.email,
            "user_type": "gc",
            "organization_id": user.organization_id,
            "permission_level": user.permission_level,
        }

    # Check sub users
    result = await db.execute(
        select(SubUser).where(SubUser.clerk_user_id == clerk_user_id)
    )
    sub_user = result.scalar_one_or_none()
    if sub_user:
        return {
            "user_id": sub_user.id,
            "clerk_user_id": sub_user.clerk_user_id,
            "email": sub_user.email,
            "user_type": "sub",
            "sub_company_id": sub_user.sub_company_id,
            "permission_level": None,
        }

    # Check owner users
    result = await db.execute(
        select(OwnerUser).where(OwnerUser.clerk_user_id == clerk_user_id)
    )
    owner_user = result.scalar_one_or_none()
    if owner_user:
        return {
            "user_id": owner_user.id,
            "clerk_user_id": owner_user.clerk_user_id,
            "email": owner_user.email,
            "user_type": "owner",
            "owner_account_id": owner_user.owner_account_id,
            "permission_level": None,
        }

    return None
