"""Onboarding wizard endpoints for new GC organizations."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.owner_portal_config import OwnerPortalConfig
from app.models.cost_code_template import CostCodeTemplate
from app.models.sub_company import SubCompany
from app.services.invite_service import create_invitation
from app.services.billing_service import check_tier_limit
from app.schemas.onboarding import (
    CompanyProfileUpdate,
    UserProfileUpdate,
    CostCodeSelection,
    FirstProjectCreate,
    InviteTeamRequest,
    InviteSubRequest,
)

router = APIRouter(prefix="/api/gc/onboarding", tags=["onboarding"])

# ============================================================
# CSI MasterFormat Preset Codes (25 standard trades)
# ============================================================

CSI_MASTERFORMAT = [
    {"code": "01", "description": "General Conditions"},
    {"code": "02", "description": "Demolition"},
    {"code": "31", "description": "Earthwork"},
    {"code": "32", "description": "Paving"},
    {"code": "32.90", "description": "Landscaping"},
    {"code": "33", "description": "Utilities"},
    {"code": "03", "description": "Concrete"},
    {"code": "04", "description": "Masonry"},
    {"code": "05", "description": "Metals"},
    {"code": "06", "description": "Carpentry"},
    {"code": "07", "description": "Thermal/Moisture Protection"},
    {"code": "08", "description": "Doors/Windows"},
    {"code": "09", "description": "Finishes"},
    {"code": "10", "description": "Specialties"},
    {"code": "11", "description": "Equipment"},
    {"code": "12", "description": "Furnishings"},
    {"code": "13", "description": "Special Construction"},
    {"code": "14", "description": "Conveying Systems"},
    {"code": "21", "description": "Fire Protection"},
    {"code": "22", "description": "Plumbing"},
    {"code": "23", "description": "HVAC"},
    {"code": "26", "description": "Electrical"},
    {"code": "27", "description": "Low Voltage"},
    {"code": "28", "description": "Electronic Safety/Security"},
    {"code": "99", "description": "Other"},
]


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _require_owner_admin(user: dict) -> None:
    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Owner/Admin can access onboarding",
        )


# ============================================================
# POST /company — Update organization profile
# ============================================================

@router.post("/company", response_model=dict)
async def update_company_profile(
    request: Request,
    body: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update organization profile during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    org = await db.get(Organization, user["organization_id"])
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.flush()

    return {"data": {"id": str(org.id), "updated_fields": list(update_data.keys())}, "meta": {}}


# ============================================================
# POST /profile — Update user profile
# ============================================================

@router.post("/profile", response_model=dict)
async def update_user_profile(
    request: Request,
    body: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    db_user = await db.get(User, user["user_id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    await db.flush()

    return {"data": {"id": str(db_user.id), "updated_fields": list(update_data.keys())}, "meta": {}}


# ============================================================
# POST /cost-codes — Select cost code template
# ============================================================

@router.post("/cost-codes", response_model=dict)
async def select_cost_codes(
    request: Request,
    body: CostCodeSelection,
    db: AsyncSession = Depends(get_db),
):
    """Select a cost code template during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    # Normalize to lowercase for case-insensitive matching
    template = body.template.lower()

    if template == "skip":
        return {"data": {"template": "skip", "created": False}, "meta": {}}

    if template == "csi_masterformat":
        codes = CSI_MASTERFORMAT
    elif template == "custom":
        if not body.custom_codes:
            raise HTTPException(
                status_code=400,
                detail="custom_codes required when template is 'custom'",
            )
        codes = body.custom_codes
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template: {body.template}. Must be 'csi_masterformat', 'custom', or 'skip'.",
        )

    cc_template = CostCodeTemplate(
        organization_id=user["organization_id"],
        name="CSI MasterFormat" if template == "csi_masterformat" else "Custom",
        codes=codes,
        is_default=True,
    )
    db.add(cc_template)
    await db.flush()

    return {
        "data": {"id": str(cc_template.id), "template": template, "code_count": len(codes)},
        "meta": {},
    }


# ============================================================
# POST /project — Create first project
# ============================================================

@router.post("/project", response_model=dict, status_code=201)
async def create_first_project(
    request: Request,
    body: FirstProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create the first project during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    # Tier check if this will be a major project
    if body.contract_value is not None and body.contract_value >= 250000:
        await check_tier_limit(db, user["organization_id"])

    project = Project(
        organization_id=user["organization_id"],
        created_by_user_id=user["user_id"],
        name=body.name,
        project_number=body.project_number,
        address=body.address,
        project_type=body.project_type,
        contract_value=body.contract_value,
        phase=body.phase,
    )
    db.add(project)
    await db.flush()

    # Auto-create owner portal config with defaults
    portal_config = OwnerPortalConfig(project_id=project.id)
    db.add(portal_config)

    # Auto-assign creating user to project
    assignment = ProjectAssignment(
        project_id=project.id,
        assignee_type="GC_USER",
        assignee_id=user["user_id"],
        assigned_by_user_id=user["user_id"],
    )
    db.add(assignment)

    await db.flush()

    return {
        "data": {"id": str(project.id), "name": project.name, "phase": project.phase},
        "meta": {},
    }


# ============================================================
# POST /invite-team — Batch create GC user invitations
# ============================================================

@router.post("/invite-team", response_model=dict)
async def invite_team_members(
    request: Request,
    body: InviteTeamRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch invite GC team members during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    results = []
    errors = []

    for member in body.members:
        try:
            invitation = await create_invitation(
                db=db,
                inviter=user["user_id"],
                email=member.email,
                invite_type="gc_user",
                organization_id=user["organization_id"],
                role=member.permission_level,
            )
            results.append({
                "email": member.email,
                "invitation_id": str(invitation.id),
                "status": "created",
            })
        except HTTPException as e:
            errors.append({
                "email": member.email,
                "error": e.detail,
            })

    return {
        "data": {"invited": results, "errors": errors},
        "meta": {"total_invited": len(results), "total_errors": len(errors)},
    }


# ============================================================
# POST /invite-subs — Batch create sub companies + invitations
# ============================================================

@router.post("/invite-subs", response_model=dict)
async def invite_subs(
    request: Request,
    body: InviteSubRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch create sub companies and send invitations during onboarding."""
    user = _get_user(request)
    _require_owner_admin(user)

    results = []
    errors = []

    for entry in body.subs:
        try:
            # Create the sub company
            sub_company = SubCompany(
                name=entry.company_name,
                trades=[entry.trade] if entry.trade else [],
            )
            db.add(sub_company)
            await db.flush()

            # Create invitation for the sub contact
            invitation = await create_invitation(
                db=db,
                inviter=user["user_id"],
                email=entry.contact_email,
                invite_type="sub_user",
                organization_id=user["organization_id"],
                sub_company_id=sub_company.id,
            )
            results.append({
                "company_name": entry.company_name,
                "contact_email": entry.contact_email,
                "sub_company_id": str(sub_company.id),
                "invitation_id": str(invitation.id),
                "status": "created",
            })
        except HTTPException as e:
            errors.append({
                "company_name": entry.company_name,
                "contact_email": entry.contact_email,
                "error": e.detail,
            })

    return {
        "data": {"invited": results, "errors": errors},
        "meta": {"total_invited": len(results), "total_errors": len(errors)},
    }


# ============================================================
# POST /complete — Mark onboarding done
# ============================================================

@router.post("/complete", response_model=dict)
async def complete_onboarding(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Mark onboarding as completed for the organization."""
    user = _get_user(request)
    _require_owner_admin(user)

    org = await db.get(Organization, user["organization_id"])
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.onboarding_completed = True
    await db.flush()

    return {"data": {"onboarding_completed": True}, "meta": {}}
