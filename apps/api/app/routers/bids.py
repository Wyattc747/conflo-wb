"""Bid Management CRUD router — GC and Sub portal endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginationMeta
from app.schemas.bid_package import (
    AwardBidRequest,
    BidComparisonResponse,
    BidPackageCreate,
    BidPackageListResponse,
    BidPackageResponse,
    BidPackageUpdate,
    BidSubmissionCreate,
    BidSubmissionResponse,
    BidSubmissionUpdate,
    DistributeBidPackageRequest,
)
from app.services.bid_service import (
    award_bid,
    close_bidding,
    compare_bids,
    create_package,
    create_submission,
    delete_package,
    distribute_package,
    format_package_response,
    format_submission_response,
    get_my_submission,
    get_package,
    list_packages,
    list_submissions_for_package,
    submit_bid,
    update_package,
    update_submission,
)

gc_router = APIRouter(prefix="/api/gc/projects/{project_id}/bid-packages", tags=["bid-packages"])


def _get_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@gc_router.get("", response_model=BidPackageListResponse)
async def list_packages_endpoint(
    request: Request, project_id: uuid.UUID,
    page: int = Query(1, ge=1), per_page: int = Query(25, ge=1, le=100),
    status: str | None = Query(None), search: str | None = Query(None),
    sort: str = Query("number"), order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    packages, total = await list_packages(
        db, project_id=project_id, page=page, per_page=per_page,
        status=status, search=search, sort=sort, order=order,
    )
    data = []
    for p in packages:
        resp = await format_package_response(db, p)
        data.append(BidPackageResponse.model_validate(resp))
    return BidPackageListResponse(
        data=data,
        meta=PaginationMeta(page=page, per_page=per_page, total=total,
                            total_pages=math.ceil(total / per_page) if per_page > 0 else 0),
    )


@gc_router.post("", response_model=dict, status_code=201)
async def create_package_endpoint(
    request: Request, project_id: uuid.UUID, body: BidPackageCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pkg = await create_package(db, project_id=project_id, organization_id=user["organization_id"], user=user, data=body)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{package_id}", response_model=dict)
async def get_package_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    pkg = await get_package(db, package_id, project_id)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.patch("/{package_id}", response_model=dict)
async def update_package_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID, body: BidPackageUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pkg = await update_package(db, package_id, project_id, user, body)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.delete("/{package_id}", status_code=200)
async def delete_package_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    await delete_package(db, package_id, project_id, user)
    return {"data": {"id": str(package_id), "deleted": True}, "meta": {}}


@gc_router.post("/{package_id}/distribute", response_model=dict)
async def distribute_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    body: DistributeBidPackageRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pkg = await distribute_package(db, package_id, project_id, user, body)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.post("/{package_id}/close", response_model=dict)
async def close_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pkg = await close_bidding(db, package_id, project_id, user)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{package_id}/compare", response_model=BidComparisonResponse)
async def compare_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    comparison = await compare_bids(db, package_id, project_id)
    formatted_submissions = [BidSubmissionResponse.model_validate(s) for s in comparison["submissions"]]
    return BidComparisonResponse(
        submissions=formatted_submissions,
        lowest_amount_cents=comparison["lowest_amount_cents"],
        highest_amount_cents=comparison["highest_amount_cents"],
        average_amount_cents=comparison["average_amount_cents"],
        recommended_submission_id=comparison["recommended_submission_id"],
    )


@gc_router.post("/{package_id}/award", response_model=dict)
async def award_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    body: AwardBidRequest,
    db: AsyncSession = Depends(get_db),
):
    user = _get_user(request)
    pkg = await award_bid(db, package_id, project_id, user["organization_id"], user, body)
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@gc_router.get("/{package_id}/submissions", response_model=dict)
async def list_submissions_endpoint(
    request: Request, project_id: uuid.UUID, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_user(request)
    submissions = await list_submissions_for_package(db, package_id)
    data = [BidSubmissionResponse.model_validate(format_submission_response(s)).model_dump(mode="json") for s in submissions]
    return {"data": data, "meta": {}}


# ============================================================
# SUB PORTAL — Bid Submissions
# ============================================================

sub_router = APIRouter(prefix="/api/sub/bid-packages", tags=["sub-bids"])


def _get_sub_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@sub_router.get("/{package_id}", response_model=dict)
async def sub_get_package(
    request: Request, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    _get_sub_user(request)
    # Sub can view any published package they're invited to
    from sqlalchemy import select as sa_select
    from app.models.bid_package import BidPackage as BP
    result = await db.execute(sa_select(BP).where(BP.id == package_id, BP.deleted_at.is_(None)))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(404, "Bid package not found")
    resp = await format_package_response(db, pkg)
    return {"data": BidPackageResponse.model_validate(resp).model_dump(mode="json"), "meta": {}}


@sub_router.get("/{package_id}/my-submission", response_model=dict)
async def sub_get_my_submission(
    request: Request, package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    submission = await get_my_submission(db, package_id, user.get("sub_company_id"))
    if not submission:
        raise HTTPException(404, "No submission found")
    return {
        "data": BidSubmissionResponse.model_validate(format_submission_response(submission)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{package_id}/submissions", response_model=dict, status_code=201)
async def sub_create_submission(
    request: Request, package_id: uuid.UUID, body: BidSubmissionCreate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    submission = await create_submission(db, package_id, user.get("sub_company_id"), user, body)
    return {
        "data": BidSubmissionResponse.model_validate(format_submission_response(submission)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.patch("/{package_id}/submissions/{submission_id}", response_model=dict)
async def sub_update_submission(
    request: Request, package_id: uuid.UUID, submission_id: uuid.UUID,
    body: BidSubmissionUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    submission = await update_submission(db, submission_id, user, body)
    return {
        "data": BidSubmissionResponse.model_validate(format_submission_response(submission)).model_dump(mode="json"),
        "meta": {},
    }


@sub_router.post("/{package_id}/submissions/{submission_id}/submit", response_model=dict)
async def sub_submit_bid(
    request: Request, package_id: uuid.UUID, submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    user = _get_sub_user(request)
    submission = await submit_bid(db, submission_id, user)
    return {
        "data": BidSubmissionResponse.model_validate(format_submission_response(submission)).model_dump(mode="json"),
        "meta": {},
    }
