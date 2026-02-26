import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.event_log import EventLog


# ============================================================
# VALID TRANSITIONS
# ============================================================

VALID_TRANSITIONS = {
    "BIDDING": ["BUYOUT"],
    "BUYOUT": ["ACTIVE"],
    "ACTIVE": ["CLOSEOUT"],
    "CLOSEOUT": ["CLOSED"],
    "CLOSED": [],  # Terminal
}

PHASE_ORDER = ["BIDDING", "BUYOUT", "ACTIVE", "CLOSEOUT", "CLOSED"]


# ============================================================
# ACTOR VALIDATION
# ============================================================

def validate_transition_actor(user: dict, current_phase: str, target_phase: str) -> None:
    """Validates whether the user can trigger the given phase transition."""
    if user["user_type"] == "owner":
        if current_phase == "BIDDING" and target_phase == "BUYOUT":
            return
        raise HTTPException(
            status_code=403,
            detail="Owners can only award projects (BIDDING → BUYOUT)"
        )

    if user["user_type"] == "sub":
        raise HTTPException(
            status_code=403,
            detail="Subcontractors cannot change project phases"
        )

    # GC users
    if user.get("permission_level") in ("OWNER_ADMIN", "MANAGEMENT"):
        return  # Can trigger any valid transition

    if user.get("permission_level") == "PRE_CONSTRUCTION":
        if current_phase == "BIDDING" and target_phase == "BUYOUT":
            return
        raise HTTPException(
            status_code=403,
            detail="Pre-Construction can only trigger award (BIDDING → BUYOUT)"
        )

    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions to change project phase"
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def get_sub_assignments(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectAssignment]:
    """Get all SUB_COMPANY assignments for a project."""
    result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.assignee_type == "SUB_COMPANY",
        )
    )
    return list(result.scalars().all())


async def get_all_assignments(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectAssignment]:
    """Get all assignments for a project."""
    result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
        )
    )
    return list(result.scalars().all())


def _user_type_from_assignee(assignee_type: str) -> str:
    """Map assignee_type to notification user_type."""
    mapping = {
        "GC_USER": "gc",
        "SUB_COMPANY": "sub",
        "OWNER_ACCOUNT": "owner",
    }
    return mapping.get(assignee_type, "gc")


async def create_notification(
    db: AsyncSession,
    user_type: str,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    source_type: str | None = None,
    source_id: uuid.UUID | None = None,
    body: str | None = None,
) -> Notification:
    """Create a notification record."""
    notification = Notification(
        user_type=user_type,
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        source_type=source_type,
        source_id=source_id,
    )
    db.add(notification)
    return notification


async def create_audit_log(
    db: AsyncSession,
    user: dict,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    log = AuditLog(
        organization_id=user.get("organization_id"),
        actor_id=user.get("user_id"),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_data=before_data or {},
        after_data=after_data or {},
    )
    db.add(log)
    return log


async def create_event_log(
    db: AsyncSession,
    user: dict,
    event_type: str,
    project_id: uuid.UUID | None = None,
    event_data: dict | None = None,
) -> EventLog:
    """Create an event log entry."""
    log = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type"),
        user_id=user.get("user_id"),
        event_type=event_type,
        event_data=event_data or {},
    )
    db.add(log)
    return log


# ============================================================
# SIDE EFFECTS
# ============================================================

async def execute_side_effects(
    project: Project,
    target_phase: str,
    user: dict,
    db: AsyncSession,
) -> None:
    """Execute side effects for a phase transition."""
    if project.phase == "BIDDING" and target_phase == "BUYOUT":
        await on_bidding_to_buyout(project, user, db)
    elif project.phase == "BUYOUT" and target_phase == "ACTIVE":
        await on_buyout_to_active(project, user, db)
    elif project.phase == "ACTIVE" and target_phase == "CLOSEOUT":
        await on_active_to_closeout(project, user, db)
    elif project.phase == "CLOSEOUT" and target_phase == "CLOSED":
        await on_closeout_to_closed(project, user, db)


async def on_bidding_to_buyout(project: Project, user: dict, db: AsyncSession) -> None:
    """BIDDING → BUYOUT: Bid data preserved, notify awarded subs."""
    sub_assignments = await get_sub_assignments(db, project.id)
    for assignment in sub_assignments:
        await create_notification(
            db,
            user_type="sub",
            user_id=assignment.assignee_id,
            notification_type="project_awarded",
            title=f"You've been awarded work on {project.name}",
            source_type="project",
            source_id=project.id,
        )


async def on_buyout_to_active(project: Project, user: dict, db: AsyncSession) -> None:
    """BUYOUT → ACTIVE: All 16 tools activate, notify all assigned."""
    assignments = await get_all_assignments(db, project.id)
    for a in assignments:
        await create_notification(
            db,
            user_type=_user_type_from_assignee(a.assignee_type),
            user_id=a.assignee_id,
            notification_type="project_active",
            title=f"{project.name} is now in active construction",
            source_type="project",
            source_id=project.id,
        )


async def on_active_to_closeout(project: Project, user: dict, db: AsyncSession) -> None:
    """ACTIVE → CLOSEOUT: Notify subs to submit closeout docs."""
    sub_assignments = await get_sub_assignments(db, project.id)
    for a in sub_assignments:
        await create_notification(
            db,
            user_type="sub",
            user_id=a.assignee_id,
            notification_type="closeout_docs_requested",
            title=f"Please submit closeout documents for {project.name}",
            source_type="project",
            source_id=project.id,
        )


async def on_closeout_to_closed(project: Project, user: dict, db: AsyncSession) -> None:
    """CLOSEOUT → CLOSED: Archive, all read-only, removed from tier count, notify all."""
    assignments = await get_all_assignments(db, project.id)
    for a in assignments:
        await create_notification(
            db,
            user_type=_user_type_from_assignee(a.assignee_type),
            user_id=a.assignee_id,
            notification_type="project_closed",
            title=f"{project.name} has been closed and archived",
            source_type="project",
            source_id=project.id,
        )


# ============================================================
# MAIN TRANSITION FUNCTION
# ============================================================

async def transition_project(
    project_id: uuid.UUID,
    target_phase: str,
    user: dict,
    db: AsyncSession,
) -> Project:
    """
    Transition a project to a new phase.

    Validates the transition, checks actor permissions,
    executes side effects, logs audit + events.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate target phase is valid
    if target_phase not in PHASE_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase: {target_phase}"
        )

    # Validate transition is allowed
    valid_targets = VALID_TRANSITIONS.get(project.phase, [])
    if target_phase not in valid_targets:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {project.phase} to {target_phase}"
        )

    # Validate user can trigger this transition
    validate_transition_actor(user, project.phase, target_phase)

    # Execute side effects BEFORE updating phase
    await execute_side_effects(project, target_phase, user, db)

    # Update phase
    old_phase = project.phase
    project.phase = target_phase

    # Audit log
    await create_audit_log(
        db, user, "phase_transition", "project", project.id,
        before_data={"phase": old_phase},
        after_data={"phase": target_phase},
    )

    # Event log
    await create_event_log(
        db, user, "project_phase_transitioned", project.id,
        event_data={"from_phase": old_phase, "to_phase": target_phase},
    )

    return project
