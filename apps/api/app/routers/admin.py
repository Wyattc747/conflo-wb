"""Admin portal endpoints — authentication, org management, impersonation."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    ImpersonateRequest,
    PlatformStats,
)
from app.services.admin_auth_service import (
    authenticate_admin,
    create_admin_token,
    verify_admin_token,
)
from app.services import admin_service


router = APIRouter(prefix="/api/admin", tags=["admin"])


# ============================================================
# DEPENDENCY — Admin Auth
# ============================================================

async def get_admin_user(request: Request) -> dict:
    """
    Validate the admin JWT from the Authorization header
    and return the admin context dict.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header[len("Bearer "):]
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")

    return {
        "admin_id": payload["sub"],
        "email": payload["email"],
        "type": "admin",
    }


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@router.post("/login")
async def admin_login(
    body: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate admin user and return a JWT."""
    admin_user = await authenticate_admin(db, body.email, body.password)
    if not admin_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last_login_at
    admin_user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    token = create_admin_token(admin_user.id, admin_user.email)

    return {
        "data": {
            "token": token,
            "admin": {
                "id": str(admin_user.id),
                "email": admin_user.email,
                "name": admin_user.name,
                "role": admin_user.role,
            },
        },
        "meta": {},
    }


@router.get("/me")
async def admin_me(
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current admin user's profile."""
    from app.models.admin_user import AdminUser

    admin_user = await db.get(AdminUser, uuid.UUID(admin["admin_id"]))
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    return {
        "data": {
            "id": str(admin_user.id),
            "email": admin_user.email,
            "name": admin_user.name,
            "role": admin_user.role,
            "is_active": admin_user.is_active,
            "last_login_at": admin_user.last_login_at.isoformat() if admin_user.last_login_at else None,
            "created_at": admin_user.created_at.isoformat() if admin_user.created_at else None,
        },
        "meta": {},
    }


# ============================================================
# PLATFORM STATS
# ============================================================

@router.get("/stats")
async def platform_stats(
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Platform-wide statistics."""
    stats = await admin_service.get_platform_stats(db)
    return {"data": stats, "meta": {}}


# ============================================================
# ORGANIZATIONS
# ============================================================

@router.get("/organizations")
async def list_organizations(
    page: int = 1,
    per_page: int = 25,
    search: str | None = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations with pagination and optional search."""
    result = await admin_service.list_organizations(db, page=page, per_page=per_page, search=search)
    return result


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: uuid.UUID,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a single organization."""
    detail = await admin_service.get_organization_detail(db, org_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"data": detail, "meta": {}}


@router.get("/organizations/{org_id}/users")
async def get_org_users(
    org_id: uuid.UUID,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users for a specific organization."""
    users = await admin_service.list_org_users(db, org_id)
    return {"data": users, "meta": {}}


# ============================================================
# USER SEARCH
# ============================================================

@router.get("/users/search")
async def search_users(
    q: str = "",
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Search users across all three user tables by email or name."""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    results = await admin_service.search_users(db, q)
    return {"data": results, "meta": {"query": q, "total": len(results)}}


# ============================================================
# IMPERSONATION
# ============================================================

@router.post("/impersonate")
async def impersonate(
    body: ImpersonateRequest,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create an impersonation session for a target user.
    Logs the action to audit_logs.
    """
    valid_types = {"gc", "sub", "owner"}
    if body.user_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user_type: {body.user_type}. Must be one of {', '.join(sorted(valid_types))}",
        )

    try:
        target_user_id = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    admin_id = uuid.UUID(admin["admin_id"])

    user_ctx = await admin_service.impersonate_user(
        db, admin_id=admin_id, target_user_id=target_user_id, target_user_type=body.user_type
    )

    if not user_ctx:
        raise HTTPException(status_code=404, detail="Target user not found")

    return {"data": user_ctx, "meta": {"impersonated_by": admin["email"]}}
