"""Project assignment management router."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.user import User
from app.models.sub_company import SubCompany
from app.models.owner_account import OwnerAccount
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.services.phase_machine import create_audit_log, create_event_log, create_notification

router = APIRouter(
    prefix="/api/gc/projects/{project_id}/assignments",
    tags=["assignments"],
)


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ============================================================
# LIST ASSIGNMENTS
# ============================================================

@router.get("", response_model=AssignmentListResponse)
async def list_assignments(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all assignments for a project."""
    user = _get_user(request)

    # Verify project exists and belongs to org
    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
        )
    )
    assignments = list(result.scalars().all())

    return AssignmentListResponse(
        data=[AssignmentResponse.model_validate(a) for a in assignments],
    )


# ============================================================
# CREATE ASSIGNMENT
# ============================================================

@router.post("", response_model=dict, status_code=201)
async def create_assignment(
    request: Request,
    project_id: uuid.UUID,
    body: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add an assignment to a project. Owner/Admin and Management only."""
    user = _get_user(request)

    # Permission check
    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(status_code=403, detail="Only Owner/Admin and Management can manage assignments")

    # Verify project
    project = await db.get(Project, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    # Validate assignee_type
    valid_types = {"GC_USER", "SUB_COMPANY", "OWNER_ACCOUNT"}
    if body.assignee_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"assignee_type must be one of {valid_types}")

    # Validate assignee exists
    if body.assignee_type == "GC_USER":
        assignee = await db.get(User, body.assignee_id)
        if not assignee or assignee.deleted_at is not None:
            raise HTTPException(status_code=404, detail="User not found")
        if assignee.organization_id != user["organization_id"]:
            raise HTTPException(status_code=400, detail="User not in your organization")
    elif body.assignee_type == "SUB_COMPANY":
        assignee = await db.get(SubCompany, body.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="Sub company not found")
    elif body.assignee_type == "OWNER_ACCOUNT":
        assignee = await db.get(OwnerAccount, body.assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="Owner account not found")

    # Check for existing assignment (UNIQUE constraint)
    existing = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.assignee_type == body.assignee_type,
            ProjectAssignment.assignee_id == body.assignee_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Assignment already exists")

    # Create assignment
    assignment = ProjectAssignment(
        project_id=project_id,
        assignee_type=body.assignee_type,
        assignee_id=body.assignee_id,
        financial_access=body.financial_access,
        bidding_access=body.bidding_access,
        trade=body.trade,
        contract_value=body.contract_value,
        assigned_by_user_id=user["user_id"],
    )
    db.add(assignment)
    await db.flush()

    # Notify the assignee
    notify_type_map = {
        "GC_USER": "gc",
        "SUB_COMPANY": "sub",
        "OWNER_ACCOUNT": "owner",
    }
    await create_notification(
        db,
        user_type=notify_type_map[body.assignee_type],
        user_id=body.assignee_id,
        notification_type="assigned_to_project",
        title=f"You've been assigned to {project.name}",
        source_type="project",
        source_id=project.id,
    )

    # Event log
    await create_event_log(
        db, user, "assignment_created", project.id,
        event_data={
            "assignee_type": body.assignee_type,
            "assignee_id": str(body.assignee_id),
        },
    )

    return {
        "data": AssignmentResponse.model_validate(assignment).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# UPDATE ASSIGNMENT
# ============================================================

@router.patch("/{assignment_id}", response_model=dict)
async def update_assignment(
    request: Request,
    project_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an assignment (financial_access, bidding_access, trade, contract_value)."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(status_code=403, detail="Only Owner/Admin and Management can manage assignments")

    assignment = await db.get(ProjectAssignment, assignment_id)
    if not assignment or assignment.project_id != project_id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify project ownership
    project = await db.get(Project, project_id)
    if not project or project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    before_data = {}
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        before_data[field] = getattr(assignment, field, None)
        setattr(assignment, field, value)

    await create_audit_log(
        db, user, "assignment_updated", "project_assignment", assignment_id,
        before_data=before_data,
        after_data=update_data,
    )

    await db.flush()

    return {
        "data": AssignmentResponse.model_validate(assignment).model_dump(mode="json"),
        "meta": {},
    }


# ============================================================
# DELETE ASSIGNMENT
# ============================================================

@router.delete("/{assignment_id}", status_code=200)
async def delete_assignment(
    request: Request,
    project_id: uuid.UUID,
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove an assignment from a project."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(status_code=403, detail="Only Owner/Admin and Management can manage assignments")

    assignment = await db.get(ProjectAssignment, assignment_id)
    if not assignment or assignment.project_id != project_id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    project = await db.get(Project, project_id)
    if not project or project.organization_id != user["organization_id"]:
        raise HTTPException(status_code=403, detail="Not your organization's project")

    await create_audit_log(
        db, user, "assignment_deleted", "project_assignment", assignment_id,
        before_data={
            "assignee_type": assignment.assignee_type,
            "assignee_id": str(assignment.assignee_id),
        },
        after_data={},
    )

    await create_event_log(
        db, user, "assignment_deleted", project.id,
        event_data={
            "assignee_type": assignment.assignee_type,
            "assignee_id": str(assignment.assignee_id),
        },
    )

    await db.delete(assignment)
    await db.flush()

    return {"data": {"id": str(assignment_id), "deleted": True}, "meta": {}}
