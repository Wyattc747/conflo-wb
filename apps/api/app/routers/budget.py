"""Budget management router — GC portal."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.budget import (
    BudgetLineItemCreate,
    BudgetLineItemResponse,
    BudgetLineItemUpdate,
    BudgetSummaryResponse,
)
from app.services.budget_service import (
    bulk_import_line_items,
    create_budget_line_item,
    delete_budget_line_item,
    format_budget_line_item_response,
    get_budget_line_item,
    get_budget_summary,
    update_budget_line_item,
)

router = APIRouter(prefix="/api/gc/projects/{project_id}/budget", tags=["budget"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("", response_model=dict)
async def get_budget(
    request: Request,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full budget summary with all line items and derived values."""
    _get_user(request)
    summary = await get_budget_summary(db, project_id)
    return {"data": summary.model_dump(mode="json"), "meta": {}}


@router.post("/line-items", response_model=dict, status_code=201)
async def add_line_item(
    request: Request,
    project_id: uuid.UUID,
    body: BudgetLineItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a budget line item."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(403, "Only Management and above can edit the budget")

    item = await create_budget_line_item(db, project_id, user["organization_id"], user, body)

    return {
        "data": format_budget_line_item_response(item),
        "meta": {},
    }


@router.patch("/line-items/{item_id}", response_model=dict)
async def update_line_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    body: BudgetLineItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a budget line item."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(403, "Only Management and above can edit the budget")

    item = await update_budget_line_item(db, item_id, project_id, body)

    return {
        "data": format_budget_line_item_response(item),
        "meta": {},
    }


@router.delete("/line-items/{item_id}", status_code=200)
async def remove_line_item(
    request: Request,
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a budget line item."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(403, "Only Management and above can edit the budget")

    await delete_budget_line_item(db, item_id, project_id)

    return {"data": {"id": str(item_id), "deleted": True}, "meta": {}}


@router.post("/import", response_model=dict, status_code=201)
async def import_budget(
    request: Request,
    project_id: uuid.UUID,
    body: list[BudgetLineItemCreate],
    db: AsyncSession = Depends(get_db),
):
    """Bulk import budget line items."""
    user = _get_user(request)

    if user.get("permission_level") not in ("OWNER_ADMIN", "MANAGEMENT"):
        raise HTTPException(403, "Only Management and above can edit the budget")

    items_data = [
        {"cost_code": item.cost_code, "description": item.description, "amount": item.original_amount}
        for item in body
    ]
    created = await bulk_import_line_items(db, project_id, user["organization_id"], user, items_data)

    return {
        "data": {"imported": len(created)},
        "meta": {},
    }
