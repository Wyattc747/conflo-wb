"""Admin authentication service — password hashing, JWT creation and verification."""
import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


# ============================================================
# PASSWORD HASHING (SHA-256 with per-password salt)
# ============================================================

_SALT_LENGTH = 32  # bytes


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a random salt.
    Returns '<salt_hex>$<hash_hex>'.
    """
    salt = secrets.token_hex(_SALT_LENGTH)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""
    if "$" not in password_hash:
        return False
    salt, stored_hash = password_hash.split("$", 1)
    candidate = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, stored_hash)


# ============================================================
# JWT TOKEN (HMAC-SHA256 signed)
# ============================================================

_TOKEN_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours


def _get_signing_key() -> bytes:
    """Return the key used for HMAC signing."""
    key = settings.CLERK_SECRET_KEY or "admin-dev-secret-key"
    return key.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_admin_token(admin_user_id: uuid.UUID, email: str) -> str:
    """
    Create a JWT-style token for an admin user.
    Header.Payload.Signature with HMAC-SHA256.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(admin_user_id),
        "email": email,
        "type": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + _TOKEN_EXPIRY_SECONDS,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        _get_signing_key(), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_admin_token(token: str) -> dict | None:
    """
    Verify an admin JWT token. Returns the payload dict or None if invalid/expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            _get_signing_key(), signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes)

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None

        # Check type
        if payload.get("type") != "admin":
            return None

        return payload
    except Exception:
        return None


# ============================================================
# AUTHENTICATE ADMIN
# ============================================================

async def authenticate_admin(db: AsyncSession, email: str, password: str):
    """
    Look up admin by email and verify password.
    Returns the AdminUser object or None.
    """
    from app.models.admin_user import AdminUser

    result = await db.execute(
        select(AdminUser).where(
            AdminUser.email == email,
            AdminUser.is_active == True,
        )
    )
    admin = result.scalar_one_or_none()
    if not admin:
        return None

    if not verify_password(password, admin.password_hash):
        return None

    return admin
