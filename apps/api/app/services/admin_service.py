"""Admin service — organization management, platform stats, impersonation."""
import uuid
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.models.sub_user import SubUser
from app.models.sub_company import SubCompany
from app.models.owner_user import OwnerUser
from app.models.project import Project
from app.models.audit_log import AuditLog
from app.services.billing_service import TIER_CONFIG


# ============================================================
# PLATFORM STATS
# ============================================================

async def get_platform_stats(db: AsyncSession) -> dict:
    """
    Platform-wide metrics: total_orgs, total_users, total_projects,
    total_sub_companies, mrr estimate, orgs by tier.
    """
    # Total organizations
    result = await db.execute(select(func.count()).select_from(Organization))
    total_orgs = result.scalar_one()

    # Total GC users (non-deleted)
    result = await db.execute(
        select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    )
    total_gc_users = result.scalar_one()

    # Total sub users
    result = await db.execute(select(func.count()).select_from(SubUser))
    total_sub_users = result.scalar_one()

    # Total owner users
    result = await db.execute(select(func.count()).select_from(OwnerUser))
    total_owner_users = result.scalar_one()

    total_users = total_gc_users + total_sub_users + total_owner_users

    # Total projects (non-deleted)
    result = await db.execute(
        select(func.count()).select_from(Project).where(Project.deleted_at.is_(None))
    )
    total_projects = result.scalar_one()

    # Total sub companies
    result = await db.execute(select(func.count()).select_from(SubCompany))
    total_sub_companies = result.scalar_one()

    # Orgs by tier
    result = await db.execute(
        select(Organization.subscription_tier, func.count())
        .group_by(Organization.subscription_tier)
    )
    orgs_by_tier = {row[0]: row[1] for row in result.all()}

    # MRR estimate (cents) — sum of monthly prices for active subscriptions
    mrr_cents = 0
    for tier_name, count in orgs_by_tier.items():
        tier_info = TIER_CONFIG.get(tier_name)
        if tier_info and tier_info.get("price_monthly"):
            mrr_cents += tier_info["price_monthly"] * 100 * count  # dollars to cents

    return {
        "total_organizations": total_orgs,
        "total_users": total_users,
        "total_projects": total_projects,
        "total_sub_companies": total_sub_companies,
        "monthly_recurring_revenue": mrr_cents,
        "orgs_by_tier": orgs_by_tier,
    }


# ============================================================
# ORGANIZATIONS
# ============================================================

async def list_organizations(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 25,
    search: Optional[str] = None,
) -> dict:
    """
    List all organizations with pagination.
    Includes user_count, project_count, and subscription info.
    """
    # Base query
    base_query = select(Organization)

    if search:
        base_query = base_query.where(
            Organization.name.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()

    # Paginate
    offset = (page - 1) * per_page
    query = base_query.order_by(Organization.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    orgs = result.scalars().all()

    # Build response with counts per org
    items = []
    for org in orgs:
        # User count
        user_count_result = await db.execute(
            select(func.count()).select_from(User).where(
                User.organization_id == org.id,
                User.deleted_at.is_(None),
            )
        )
        user_count = user_count_result.scalar_one()

        # Project count
        project_count_result = await db.execute(
            select(func.count()).select_from(Project).where(
                Project.organization_id == org.id,
                Project.deleted_at.is_(None),
            )
        )
        project_count = project_count_result.scalar_one()

        items.append({
            "id": str(org.id),
            "name": org.name,
            "subscription_tier": org.subscription_tier,
            "subscription_status": org.subscription_status,
            "stripe_customer_id": org.stripe_customer_id,
            "user_count": user_count,
            "project_count": project_count,
            "onboarding_completed": org.onboarding_completed,
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        })

    return {
        "data": items,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        },
    }


async def get_organization_detail(db: AsyncSession, org_id: uuid.UUID) -> dict | None:
    """
    Full org detail with users, projects, subscription info.
    """
    org = await db.get(Organization, org_id)
    if not org:
        return None

    # Users
    result = await db.execute(
        select(User).where(
            User.organization_id == org_id,
            User.deleted_at.is_(None),
        ).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    # Projects
    result = await db.execute(
        select(Project).where(
            Project.organization_id == org_id,
            Project.deleted_at.is_(None),
        ).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    return {
        "id": str(org.id),
        "name": org.name,
        "logo_url": org.logo_url,
        "address_line1": org.address_line1,
        "address_line2": org.address_line2,
        "city": org.city,
        "state": org.state,
        "zip_code": org.zip_code,
        "phone": org.phone,
        "timezone": org.timezone,
        "subscription_tier": org.subscription_tier,
        "subscription_status": org.subscription_status,
        "stripe_customer_id": org.stripe_customer_id,
        "stripe_subscription_id": org.stripe_subscription_id,
        "grace_period_end": org.grace_period_end.isoformat() if org.grace_period_end else None,
        "onboarding_completed": org.onboarding_completed,
        "contract_start_date": org.contract_start_date.isoformat() if org.contract_start_date else None,
        "contract_end_date": org.contract_end_date.isoformat() if org.contract_end_date else None,
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "permission_level": u.permission_level,
                "status": u.status,
                "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "projects": [
            {
                "id": str(p.id),
                "name": p.name,
                "project_number": p.project_number,
                "phase": p.phase,
                "project_type": p.project_type,
                "contract_value": str(p.contract_value) if p.contract_value else None,
                "is_major": p.is_major,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ],
    }


async def list_org_users(db: AsyncSession, org_id: uuid.UUID) -> list:
    """All users for an organization."""
    result = await db.execute(
        select(User).where(
            User.organization_id == org_id,
            User.deleted_at.is_(None),
        ).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "phone": u.phone,
            "title": u.title,
            "permission_level": u.permission_level,
            "status": u.status,
            "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


# ============================================================
# USER SEARCH
# ============================================================

async def search_users(db: AsyncSession, query: str) -> list:
    """
    Search users across all three tables (User, SubUser, OwnerUser)
    by email or name.
    """
    search_pattern = f"%{query}%"
    results = []

    # GC users
    gc_result = await db.execute(
        select(User).where(
            User.deleted_at.is_(None),
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
            ),
        ).limit(25)
    )
    for u in gc_result.scalars().all():
        results.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "user_type": "gc",
            "organization_id": str(u.organization_id),
            "permission_level": u.permission_level,
            "status": u.status,
        })

    # Sub users
    sub_result = await db.execute(
        select(SubUser).where(
            or_(
                SubUser.email.ilike(search_pattern),
                SubUser.name.ilike(search_pattern),
            ),
        ).limit(25)
    )
    for u in sub_result.scalars().all():
        results.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "user_type": "sub",
            "sub_company_id": str(u.sub_company_id),
            "status": u.status,
        })

    # Owner users
    owner_result = await db.execute(
        select(OwnerUser).where(
            or_(
                OwnerUser.email.ilike(search_pattern),
                OwnerUser.name.ilike(search_pattern),
            ),
        ).limit(25)
    )
    for u in owner_result.scalars().all():
        results.append({
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "user_type": "owner",
            "owner_account_id": str(u.owner_account_id),
            "status": u.status,
        })

    return results


# ============================================================
# IMPERSONATION
# ============================================================

async def impersonate_user(
    db: AsyncSession,
    admin_id: uuid.UUID,
    target_user_id: uuid.UUID,
    target_user_type: str,
) -> dict:
    """
    Create an impersonation session. Logs to audit_logs.
    Returns a user context dict matching the format used by auth middleware.
    """
    user_ctx = None

    if target_user_type == "gc":
        result = await db.execute(
            select(User).where(User.id == target_user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user:
            user_ctx = {
                "user_id": str(user.id),
                "clerk_user_id": user.clerk_user_id,
                "email": user.email,
                "user_type": "gc",
                "organization_id": str(user.organization_id),
                "permission_level": user.permission_level,
            }
    elif target_user_type == "sub":
        result = await db.execute(
            select(SubUser).where(SubUser.id == target_user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user_ctx = {
                "user_id": str(user.id),
                "clerk_user_id": user.clerk_user_id,
                "email": user.email,
                "user_type": "sub",
                "sub_company_id": str(user.sub_company_id),
                "permission_level": None,
            }
    elif target_user_type == "owner":
        result = await db.execute(
            select(OwnerUser).where(OwnerUser.id == target_user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user_ctx = {
                "user_id": str(user.id),
                "clerk_user_id": user.clerk_user_id,
                "email": user.email,
                "user_type": "owner",
                "owner_account_id": str(user.owner_account_id),
                "permission_level": None,
            }

    if not user_ctx:
        return None

    # Log impersonation to audit_logs
    audit = AuditLog(
        organization_id=None,
        actor_id=admin_id,
        action="admin_impersonate",
        resource_type=f"{target_user_type}_user",
        resource_id=target_user_id,
        before_data={},
        after_data={
            "admin_id": str(admin_id),
            "target_user_id": str(target_user_id),
            "target_user_type": target_user_type,
            "target_email": user_ctx["email"],
        },
    )
    db.add(audit)
    await db.flush()

    return user_ctx
