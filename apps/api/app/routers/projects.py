"""Project CRUD router."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.owner_portal_config import OwnerPortalConfig
from app.schemas.project import (
    PaginationMeta,
    PhaseTransitionRequest,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    VisibleToolsResponse,
)
from app.services.billing_service import check_tier_limit
from app.services.phase_machine import (
    create_audit_log,
    create_event_log,
    transition_project,
)

router = APIRouter(prefix="/api/gc/projects", tags=["projects"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# LIST PROJECTS
# ============================================================

@router.get("", response_model=ProjectListResponse)
async def list_projects(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    phase: str | None = Query(None),
    project_type: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List projects. Owner/Admin sees all, others see assigned only."""
    user = _get_user(request)

    # Base query — org scoped, exclude soft-deleted
    query = select(Project).where(
        Project.organization_id == user["organization_id"],
        Project.deleted_at.is_(None),
    )
    count_query = (
        select(func.count())
        .select_from(Project)
        .where(
            Project.organization_id == user["organization_id"],
            Project.deleted_at.is_(None),
        )
    )

    # Non-admin users: only assigned projects
    if user.get("permission_level") != "OWNER_ADMIN":
        assigned_subq = (
            select(ProjectAssignment.project_id)
            .where(
                ProjectAssignment.assignee_type == "GC_USER",
                ProjectAssignment.assignee_id == user["user_id"],
            )
            .scalar_subquery()
        )
        query = query.where(Project.id.in_(assigned_subq))
        count_query = count_query.where(Project.id.in_(assigned_subq))

    # Pre-Con only sees BIDDING phase projects
    if user.get("permission_level") == "PRE_CONSTRUCTION":
        query = query.where(Project.phase == "BIDDING")
        count_query = count_query.where(Project.phase == "BIDDING")

    # Filters
    if phase:
        query = query.where(Project.phase == phase)
        count_query = count_query.where(Project.phase == phase)
    if project_type:
        query = query.where(Project.project_type == project_type)
        count_query = count_query.where(Project.project_type == project_type)
    if search:
        search_filter = Project.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Sort
    sort_col = getattr(Project, sort, Project.created_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    projects = list(result.scalars().all())

    return ProjectListResponse(
        data=[ProjectResponse.model_validate(p) for p in projects],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if per_page > 0 else 0,
        ),
    )


# ============================================================
# CREATE PROJECT
# ============================================================

@router.post("", response_model=dict, status_code=201)
async def create_project(
    request: Request,
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project. Owner/Admin and Pre-Construction can create."""
    user = _get_user(request)

    # Permission check: only Owner/Admin and Pre-Con can create projects
    if user.get("permission_level") not in ("OWNER_ADMIN", "PRE_CONSTRUCTION"):
        raise HTTPException(status_code=403, detail="Only Owner/Admin and Pre-Construction can create projects")

    # Tier check if this will be a major project
    if body.contract_value is not None and body.contract_value >= 250000:
        await check_tier_limit(db, user["organization_id"])

    # Create project
    project = Project(
        organization_id=user["organization_id"],
        created_by_user_id=user["user_id"],
        **body.model_dump(exclude_none=True),
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

    # Event log
    await create_event_log(
        db, user, "project_created", project.id,
        event_data={"name": project.name, "phase": project.phase},
    )

    await db.flush()

    return {
        "data": ProjectResponse.model_validate(project).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# GET PROJECT DETAIL
# ============================================================

@router.get("/{project_id}", response_model=dict)
async def get_project(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single project."""
    user = _get_user(request)

    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Org check
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    # Assignment check (Owner/Admin exempt)
    if user.get("permission_level") != "OWNER_ADMIN":
        result = await db.execute(
            select(ProjectAssignment).where(
                ProjectAssignment.project_id == project_id,
                ProjectAssignment.assignee_type == "GC_USER",
                ProjectAssignment.assignee_id == user["user_id"],
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not assigned to this project")

    return {
        "data": ProjectResponse.model_validate(project).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# UPDATE PROJECT
# ============================================================

@router.patch("/{project_id}", response_model=dict)
async def update_project(
    request: Request,
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a project. Owner/Admin and Management only."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    # Track before state for audit
    before_data = {}
    update_data = body.model_dump(exclude_none=True)

    # Check tier if contract_value crosses $250K threshold
    if "contract_value" in update_data:
        new_value = update_data["contract_value"]
        old_is_major = project.contract_value is not None and project.contract_value >= 250000
        new_is_major = new_value is not None and new_value >= 250000
        if new_is_major and not old_is_major:
            await check_tier_limit(db, user["organization_id"], exclude_project_id=project_id)

    for field, value in update_data.items():
        before_data[field] = getattr(project, field, None)
        setattr(project, field, value)

    # Audit log
    await create_audit_log(
        db, user, "project_updated", "project", project_id,
        before_data=before_data,
        after_data=update_data,
    )

    await create_event_log(
        db, user, "project_updated", project.id,
        event_data={"fields": list(update_data.keys())},
    )

    await db.flush()

    return {
        "data": ProjectResponse.model_validate(project).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# DELETE PROJECT (SOFT)
# ============================================================

@router.delete("/{project_id}", status_code=200)
async def delete_project(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a project. Owner/Admin only."""
    user = _get_user(request)

    if user.get("permission_level") != "OWNER_ADMIN":
        raise HTTPException(status_code=403, detail="Only Owner/Admin can delete projects")

    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    from datetime import datetime, timezone
    before_data = {"deleted_at": None}
    project.deleted_at = datetime.now(timezone.utc)

    await create_audit_log(
        db, user, "project_deleted", "project", project_id,
        before_data=before_data,
        after_data={"deleted_at": str(project.deleted_at)},
    )

    await create_event_log(
        db, user, "project_deleted", project.id,
        event_data={"name": project.name},
    )

    return {"data": {"id": str(project_id), "deleted": True}, "meta": {}}


# ============================================================
# PHASE TRANSITION
# ============================================================

@router.post("/{project_id}/transition", response_model=dict)
async def transition_project_endpoint(
    request: Request,
    project_id: uuid.UUID,
    body: PhaseTransitionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Transition a project to a new phase."""
    user = _get_user(request)

    # Org check
    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    old_phase = project.phase
    project = await transition_project(project_id, body.target_phase, user, db)

    return {
        "data": {
            **ProjectResponse.model_validate(project).model_dump(mode="json"),
            "previous_phase": old_phase,
        },
        "meta": {},
    }


# ============================================================
# VISIBLE TOOLS
# ============================================================

@router.get("/{project_id}/tools", response_model=VisibleToolsResponse)
async def get_project_tools(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get visible tools for the current user on this project."""
    user = _get_user(request)

    from app.services.permission_engine import get_visible_tools
    tools = await get_visible_tools(user, project_id, db)
    return VisibleToolsResponse(tools=tools)
