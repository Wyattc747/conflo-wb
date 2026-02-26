import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Path, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.owner_portal_config import OwnerPortalConfig


# ============================================================
# TOOL AND ACTION DEFINITIONS
# ============================================================

TOOLS = [
    "daily_logs", "rfis", "submittals", "transmittals", "change_orders",
    "schedule", "drawings", "punch_list", "inspections", "budget",
    "pay_apps", "meetings", "todo", "procurement", "look_ahead",
    "closeout", "bid_packages", "directory", "documents", "photos",
]

ACTIONS = ["create", "read", "update", "delete", "verify", "approve", "assign"]

FINANCIAL_TOOLS = {"budget", "pay_apps", "change_orders"}
BIDDING_TOOLS = {"bid_packages"}


# ============================================================
# GC PERMISSION MATRIX
# ============================================================
# Structure: GC_MATRIX[permission_level][tool] = set of allowed actions
# Based on CLAUDE.md "GC Permission Matrix"

GC_MATRIX = {
    "OWNER_ADMIN": {
        # Full CRUD + all special actions on everything
        "daily_logs": {"create", "read", "update", "delete"},
        "rfis": {"create", "read", "update", "delete"},
        "submittals": {"create", "read", "update", "delete"},
        "transmittals": {"create", "read", "update", "delete"},
        "change_orders": {"create", "read", "update", "delete", "approve"},
        "schedule": {"create", "read", "update", "delete"},
        "drawings": {"create", "read", "update", "delete"},
        "punch_list": {"create", "read", "update", "delete", "verify"},
        "inspections": {"create", "read", "update", "delete"},
        "budget": {"create", "read", "update", "delete"},
        "pay_apps": {"create", "read", "update", "delete", "approve"},
        "meetings": {"create", "read", "update", "delete"},
        "todo": {"create", "read", "update", "delete"},
        "procurement": {"create", "read", "update", "delete"},
        "look_ahead": {"create", "read", "update", "delete"},
        "closeout": {"create", "read", "update", "delete"},
        "bid_packages": {"create", "read", "update", "delete"},
        "directory": {"create", "read", "update", "delete"},
        "documents": {"create", "read", "update", "delete"},
        "photos": {"create", "read", "update", "delete"},
    },
    "PRE_CONSTRUCTION": {
        # CRUD on bid tools only, N/A on everything else
        "daily_logs": set(),
        "rfis": set(),
        "submittals": set(),
        "transmittals": set(),
        "change_orders": set(),
        "schedule": set(),
        "drawings": set(),
        "punch_list": set(),
        "inspections": set(),
        "budget": set(),
        "pay_apps": set(),
        "meetings": set(),
        "todo": set(),
        "procurement": set(),
        "look_ahead": set(),
        "closeout": set(),
        "bid_packages": {"create", "read", "update", "delete"},
        "directory": {"read", "create"},  # R, add
        "documents": set(),
        "photos": set(),
    },
    "MANAGEMENT": {
        "daily_logs": {"create", "read", "update"},  # CRU own, R all
        "rfis": {"create", "read", "update", "delete"},  # CRUD assigned
        "submittals": {"create", "read", "update", "delete"},  # CRUD, review
        "transmittals": {"create", "read"},  # CR, send
        "change_orders": {"create", "read", "update", "delete"},  # CRUD, negotiate
        "schedule": {"create", "read", "update", "delete"},  # CRUD
        "drawings": {"create", "read", "update"},  # Upload, version
        "punch_list": {"create", "read", "update", "verify"},  # CRU, verify
        "inspections": {"create", "read"},  # CR, conduct
        "budget": {"create", "read", "update", "delete"},  # CRUD
        "pay_apps": {"create", "read", "update", "delete"},  # CRUD
        "meetings": {"create", "read", "update", "delete"},  # CRUD
        "todo": {"create", "read", "update", "delete"},  # CRUD
        "procurement": {"create", "read", "update", "delete"},  # CRUD
        "look_ahead": {"create", "read", "update", "delete"},  # CRUD
        "closeout": {"create", "read", "update", "delete"},  # CRUD, assemble
        "bid_packages": {"read"},  # View only
        "directory": {"create", "read", "update", "delete"},  # CRUD
        "documents": {"create", "read", "update", "delete"},
        "photos": {"create", "read", "update", "delete"},
    },
    "USER": {
        "daily_logs": {"create", "read", "update"},  # CRU own, R all
        "rfis": {"create", "read"},  # CR, respond
        "submittals": {"create", "read"},  # CR, submit
        "transmittals": {"create", "read"},  # CR, send
        "change_orders": {"read"},  # View only (CRUD if financial_access)
        "schedule": {"read", "update"},  # R, update %
        "drawings": {"read"},  # R, download
        "punch_list": {"create", "read"},  # CR, photo (no verify)
        "inspections": {"create", "read"},  # CR, conduct
        "budget": set(),  # R if financial_access (handled by conditional)
        "pay_apps": set(),  # R if financial_access (handled by conditional)
        "meetings": {"create", "read", "update", "delete"},  # CRUD
        "todo": {"create", "read", "update", "delete"},  # CRUD
        "procurement": {"create", "read", "update", "delete"},  # CRUD
        "look_ahead": {"create", "read", "update", "delete"},  # CRUD
        "closeout": {"read", "create"},  # Contribute
        "bid_packages": set(),  # View if bidding_access (handled by conditional)
        "directory": {"read", "create"},  # R, add
        "documents": {"create", "read", "update"},
        "photos": {"create", "read"},
    },
}


# ============================================================
# SUB PORTAL PERMISSION MATRIX
# ============================================================
# Sub users have a flat permission set (no permission_level dimension)

SUB_MATRIX = {
    "rfis": {"read", "create"},  # view assigned, create new, respond
    "submittals": {"create", "read"},  # submit, track status
    "transmittals": {"read"},  # receive, acknowledge (cannot create)
    "change_orders": {"read", "update"},  # receive pricing requests, submit pricing, negotiate
    "punch_list": {"read", "update"},  # view assigned, mark complete with photos (cannot create/verify)
    "pay_apps": {"create", "read", "update"},  # create G702/G703, submit to GC, track
    "schedule": {"read"},  # view own scope only, read-only
    "drawings": {"read"},  # view/download relevant sheets
    "todo": {"create", "read", "update", "delete"},  # CRUD
    "closeout": {"create", "read"},  # submit docs against checklist
    "bid_packages": {"read"},  # view packages, submit pricing (via bid_submissions)
    "daily_logs": set(),
    "budget": set(),
    "inspections": set(),
    "meetings": set(),
    "procurement": set(),
    "look_ahead": set(),
    "directory": {"read"},
    "documents": {"read"},
    "photos": {"read"},
}


# ============================================================
# OWNER PORTAL PERMISSION MATRIX
# ============================================================

OWNER_MATRIX = {
    "pay_apps": {"read", "approve"},  # review, approve, reject, revision -- ALWAYS visible
    "change_orders": {"read", "approve"},  # review, approve, reject, revision -- ALWAYS visible
    "schedule": {"read"},  # view only -- GC toggle
    "punch_list": {"read", "create"},  # view; create IF GC enables -- GC toggle
    "submittals": {"read"},  # view, respond if routed -- GC toggle
    "rfis": {"read"},  # view, respond if assigned -- GC toggle
    "drawings": {"read"},  # view, download -- GC toggle
    "closeout": {"read"},  # receive package -- always visible
    "directory": {"read"},  # view GC team -- always visible
    "daily_logs": {"read"},  # GC toggle (show_daily_logs)
    "budget": {"read"},  # GC toggle (show_budget_summary)
    # These are never available to owners:
    "transmittals": set(),
    "inspections": set(),
    "meetings": set(),
    "todo": set(),
    "procurement": set(),
    "look_ahead": set(),
    "bid_packages": set(),
    "documents": set(),
    "photos": set(),
}

# Owner tools that are ALWAYS visible (not controlled by GC toggle)
OWNER_ALWAYS_VISIBLE = {"pay_apps", "change_orders", "closeout", "directory"}

# Map owner_portal_config fields to tool names
OWNER_CONFIG_TOOL_MAP = {
    "schedule": "show_schedule",
    "submittals": "show_submittals",
    "rfis": "show_rfis",
    "transmittals": "show_transmittals",
    "drawings": "show_drawings",
    "punch_list": "show_punch_list",
    "budget": "show_budget_summary",
    "daily_logs": "show_daily_logs",
}


# ============================================================
# PHASE-TOOL AVAILABILITY MAP
# ============================================================
# Values: "active", "read_only", "hidden", "limited"

_ALL_ACTIVE = {tool: "active" for tool in TOOLS}

PHASE_TOOL_MAP = {
    "BIDDING": {
        "bid_packages": "active",
        "daily_logs": "hidden",
        "rfis": "limited",
        "submittals": "limited",
        "transmittals": "limited",
        "change_orders": "hidden",
        "schedule": "hidden",
        "drawings": "active",
        "punch_list": "hidden",
        "inspections": "hidden",
        "budget": "hidden",
        "pay_apps": "hidden",
        "meetings": "limited",
        "todo": "hidden",
        "procurement": "hidden",
        "look_ahead": "hidden",
        "closeout": "hidden",
        "directory": "active",
        "documents": "active",
        "photos": "active",
    },
    "BUYOUT": {
        **_ALL_ACTIVE,
        "bid_packages": "read_only",
        "closeout": "hidden",
    },
    "ACTIVE": {
        **_ALL_ACTIVE,
        "bid_packages": "read_only",
        "closeout": "hidden",
    },
    "CLOSEOUT": {
        **_ALL_ACTIVE,
        "bid_packages": "read_only",
    },
    "CLOSED": {tool: "read_only" for tool in TOOLS},
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def get_assignment(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_type: str,
    user_id: uuid.UUID,
) -> Optional[ProjectAssignment]:
    """Get a user's assignment to a project."""
    # Map user_type to assignee_type
    type_map = {
        "gc": "GC_USER",
        "sub": "SUB_COMPANY",
        "owner": "OWNER_ACCOUNT",
    }
    assignee_type = type_map.get(user_type)
    if not assignee_type:
        return None

    result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.assignee_type == assignee_type,
            ProjectAssignment.assignee_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_owner_portal_config(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> Optional[OwnerPortalConfig]:
    """Get the owner portal visibility config for a project."""
    result = await db.execute(
        select(OwnerPortalConfig).where(
            OwnerPortalConfig.project_id == project_id
        )
    )
    return result.scalar_one_or_none()


def is_tool_visible_to_owner(config: OwnerPortalConfig, tool: str) -> bool:
    """Check if a tool is visible to owner based on portal config."""
    if tool in OWNER_ALWAYS_VISIBLE:
        return True
    config_field = OWNER_CONFIG_TOOL_MAP.get(tool)
    if config_field is None:
        return False  # Tool not configurable for owner = not visible
    return getattr(config, config_field, False)


def get_matrix_permission(user_type: str, permission_level: Optional[str], tool: str, action: str) -> bool:
    """Check if action is allowed by the permission matrix."""
    if user_type == "gc":
        level_matrix = GC_MATRIX.get(permission_level, {})
        tool_actions = level_matrix.get(tool, set())
        return action in tool_actions
    elif user_type == "sub":
        tool_actions = SUB_MATRIX.get(tool, set())
        return action in tool_actions
    elif user_type == "owner":
        tool_actions = OWNER_MATRIX.get(tool, set())
        return action in tool_actions
    return False


# ============================================================
# CORE PERMISSION CHECK
# ============================================================

async def check_permission(
    user: dict,
    project_id: uuid.UUID,
    tool: str,
    action: str,
    db: AsyncSession,
) -> None:
    """
    Raises HTTPException(403) if not allowed. Returns None if allowed.

    user dict keys: user_type, user_id, organization_id (or sub_company_id/owner_account_id), permission_level
    """
    # Step 1: Get project
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Step 2: Organization check (GC users only access own org's projects)
    if user["user_type"] == "gc" and project.organization_id != user.get("organization_id"):
        raise HTTPException(status_code=403, detail="Not your organization's project")

    # Step 3: Assignment check
    # For sub users, the assignee_id is sub_company_id, for owner it's owner_account_id
    assignee_id = user["user_id"]
    if user["user_type"] == "sub":
        assignee_id = user.get("sub_company_id", user["user_id"])
    elif user["user_type"] == "owner":
        assignee_id = user.get("owner_account_id", user["user_id"])

    assignment = await get_assignment(db, project_id, user["user_type"], assignee_id)

    if not assignment:
        # Owner/Admin exempt -- sees all projects in their org
        if user["user_type"] == "gc" and user.get("permission_level") == "OWNER_ADMIN":
            pass
        else:
            raise HTTPException(status_code=403, detail="Not assigned to this project")

    # Step 4: Phase check
    phase_availability = PHASE_TOOL_MAP.get(project.phase, {}).get(tool, "hidden")
    if phase_availability == "hidden":
        raise HTTPException(
            status_code=403,
            detail=f"{tool} is not available in {project.phase} phase"
        )
    if phase_availability == "read_only" and action != "read":
        raise HTTPException(
            status_code=403,
            detail=f"{tool} is read-only in {project.phase} phase"
        )

    # Step 5: Permission matrix check
    allowed = get_matrix_permission(
        user["user_type"], user.get("permission_level"), tool, action
    )

    # Step 6: Conditional access for USER level
    if not allowed and user.get("permission_level") == "USER" and assignment:
        if tool in FINANCIAL_TOOLS and assignment.financial_access:
            allowed = True
        elif tool in BIDDING_TOOLS and assignment.bidding_access:
            allowed = True

    # Step 7: Owner portal visibility check
    if user["user_type"] == "owner":
        config = await get_owner_portal_config(db, project_id)
        if config and not is_tool_visible_to_owner(config, tool):
            raise HTTPException(
                status_code=403,
                detail=f"{tool} is not shared with owner on this project"
            )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions for {action} on {tool}"
        )


# ============================================================
# FASTAPI DEPENDENCY
# ============================================================

def require_permission(tool: str, action: str):
    """
    FastAPI dependency for permission checks.

    Usage:
        @router.get("/api/gc/projects/{project_id}/rfis",
                     dependencies=[require_permission("rfis", "read")])
    """
    async def dependency(
        request: Request,
        project_id: uuid.UUID = Path(...),
        db: AsyncSession = Depends(get_db),
    ):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        await check_permission(user, project_id, tool, action, db)

    return Depends(dependency)


# ============================================================
# SIDEBAR HELPER: GET VISIBLE TOOLS
# ============================================================

async def get_visible_tools(
    user: dict,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    """
    Returns list of {"tool": str, "access": str} for frontend sidebar rendering.
    access is one of: "active", "read_only", "limited"
    """
    project = await db.get(Project, project_id)
    if not project:
        return []

    visible = []

    # For sub users, use sub_company_id as assignee
    assignee_id = user["user_id"]
    if user["user_type"] == "sub":
        assignee_id = user.get("sub_company_id", user["user_id"])
    elif user["user_type"] == "owner":
        assignee_id = user.get("owner_account_id", user["user_id"])

    assignment = await get_assignment(db, project_id, user["user_type"], assignee_id)

    # Owner portal config (if owner)
    owner_config = None
    if user["user_type"] == "owner":
        owner_config = await get_owner_portal_config(db, project_id)

    for tool in TOOLS:
        # Phase check
        phase_avail = PHASE_TOOL_MAP.get(project.phase, {}).get(tool, "hidden")
        if phase_avail == "hidden":
            continue

        # Matrix check
        has_perm = get_matrix_permission(
            user["user_type"], user.get("permission_level"), tool, "read"
        )

        # Conditional access for USER level
        if not has_perm and user.get("permission_level") == "USER" and assignment:
            if tool in FINANCIAL_TOOLS and assignment.financial_access:
                has_perm = True
            elif tool in BIDDING_TOOLS and assignment.bidding_access:
                has_perm = True

        # Owner visibility check
        if user["user_type"] == "owner" and owner_config:
            if not is_tool_visible_to_owner(owner_config, tool):
                continue

        if has_perm:
            visible.append({"tool": tool, "access": phase_avail})

    return visible
