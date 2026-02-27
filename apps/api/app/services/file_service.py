"""File storage service — S3 pre-signed URL upload/download flow."""

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

import boto3
from botocore.config import Config
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.file import File

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    region_name=settings.AWS_REGION or "us-east-1",
    config=Config(signature_version="s3v4"),
)

BUCKET = settings.S3_BUCKET_NAME

# Categories that map to tool attachment types
VALID_CATEGORIES = {
    "rfi_attachment", "daily_log_photo", "submittal_doc", "transmittal_doc",
    "punch_list_photo", "inspection_photo", "drawing_sheet", "document",
    "bid_scope_doc", "bid_submission_doc", "meeting_attachment", "photo",
    "avatar", "change_order_attachment", "pay_app_doc", "other",
}

ALLOWED_MIME_TYPES = {
    "image": {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic"},
    "document": {
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv", "text/plain",
    },
    "drawing": {"application/pdf", "image/jpeg", "image/png", "image/tiff"},
}

# Categories that restrict to images only
IMAGE_CATEGORIES = {"daily_log_photo", "punch_list_photo", "inspection_photo", "photo", "avatar"}
DRAWING_CATEGORIES = {"drawing_sheet"}

MAX_FILE_SIZE_MB = 100


def is_allowed_type(content_type: str, category: str) -> bool:
    if category in IMAGE_CATEGORIES:
        return content_type in ALLOWED_MIME_TYPES["image"]
    if category in DRAWING_CATEGORIES:
        return content_type in ALLOWED_MIME_TYPES["drawing"]
    # General categories allow images + documents
    all_allowed = ALLOWED_MIME_TYPES["image"] | ALLOWED_MIME_TYPES["document"]
    return content_type in all_allowed


async def request_upload_url(
    db: AsyncSession,
    user: dict,
    project_id: UUID,
    filename: str,
    content_type: str,
    category: str,
    file_size_bytes: int | None = None,
) -> dict:
    """Generate a pre-signed PUT URL for direct client -> S3 upload."""
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Invalid category: {category}")

    if not is_allowed_type(content_type, category):
        raise HTTPException(400, f"File type {content_type} not allowed for {category}")

    if file_size_bytes and file_size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    file_id = _uuid.uuid4()
    org_id = user.get("organization_id") or user.get("sub_company_id") or user.get("owner_account_id")
    key = f"{org_id}/{project_id}/{category}/{file_id}.{ext}"

    upload_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=900,  # 15 minutes
    )

    file_record = File(
        id=file_id,
        project_id=project_id,
        organization_id=org_id,
        filename=filename,
        mime_type=content_type,
        size_bytes=file_size_bytes,
        s3_key=key,
        category=category,
        status="PENDING",
        uploaded_by=user["user_id"],
    )
    db.add(file_record)
    await db.flush()

    return {
        "file_id": str(file_id),
        "upload_url": upload_url,
        "key": key,
    }


async def confirm_upload(
    db: AsyncSession,
    file_id: UUID,
    user: dict,
) -> dict:
    """Client calls this after successful S3 upload to confirm the file."""
    file_record = await db.get(File, file_id)
    if not file_record:
        raise HTTPException(404, "File not found")
    if file_record.status != "PENDING":
        raise HTTPException(400, "File already confirmed")

    # Verify file exists in S3
    try:
        head = s3_client.head_object(Bucket=BUCKET, Key=file_record.s3_key)
        file_record.size_bytes = head["ContentLength"]
    except Exception:
        raise HTTPException(400, "File not found in storage — upload may have failed")

    file_record.status = "CONFIRMED"
    file_record.confirmed_at = datetime.now(timezone.utc)

    # Image processing happens asynchronously if needed
    if file_record.mime_type and file_record.mime_type.startswith("image/"):
        try:
            from app.services.image_service import process_image
            await process_image(db, file_record)
        except Exception:
            pass  # Image processing is non-critical

    await db.flush()
    return format_file_response(file_record)


async def get_download_url(
    db: AsyncSession,
    file_id: UUID,
    user: dict,
) -> str:
    """Generate a pre-signed GET URL for downloading (1 hour expiry)."""
    file_record = await db.get(File, file_id)
    if not file_record:
        raise HTTPException(404, "File not found")
    if file_record.deleted_at:
        raise HTTPException(404, "File not found")

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET,
            "Key": file_record.s3_key,
            "ResponseContentDisposition": f'attachment; filename="{file_record.filename}"',
        },
        ExpiresIn=3600,
    )
    return url


async def get_view_url(
    db: AsyncSession,
    file_id: UUID,
) -> str:
    """Generate a pre-signed GET URL for in-browser viewing (1 hour, inline disposition)."""
    file_record = await db.get(File, file_id)
    if not file_record:
        raise HTTPException(404, "File not found")
    if file_record.deleted_at:
        raise HTTPException(404, "File not found")

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET,
            "Key": file_record.s3_key,
            "ResponseContentDisposition": "inline",
            "ResponseContentType": file_record.mime_type or "application/octet-stream",
        },
        ExpiresIn=3600,
    )
    return url


async def get_thumbnail_url(
    db: AsyncSession,
    file_id: UUID,
) -> str | None:
    """Generate a pre-signed URL for the thumbnail if it exists."""
    file_record = await db.get(File, file_id)
    if not file_record or not file_record.thumbnail_key:
        return None

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET,
            "Key": file_record.thumbnail_key,
            "ResponseContentDisposition": "inline",
            "ResponseContentType": "image/jpeg",
        },
        ExpiresIn=3600,
    )
    return url


async def delete_file(db: AsyncSession, file_id: UUID, user: dict) -> dict:
    """Soft delete file record. Actual S3 cleanup via background job."""
    file_record = await db.get(File, file_id)
    if not file_record:
        raise HTTPException(404, "File not found")
    if file_record.deleted_at:
        raise HTTPException(404, "File not found")

    file_record.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": str(file_id), "deleted": True}


async def list_project_files(
    db: AsyncSession,
    project_id: UUID,
    category: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[File], int]:
    """List confirmed files for a project."""
    from sqlalchemy import func

    query = select(File).where(
        File.project_id == project_id,
        File.status == "CONFIRMED",
        File.deleted_at.is_(None),
    )
    if category:
        query = query.where(File.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(File.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


def format_file_response(file_record: File) -> dict:
    return {
        "id": str(file_record.id),
        "filename": file_record.filename,
        "mime_type": file_record.mime_type,
        "size_bytes": file_record.size_bytes,
        "category": file_record.category,
        "status": file_record.status,
        "thumbnail_key": file_record.thumbnail_key,
        "exif_data": file_record.exif_data,
        "uploaded_by": str(file_record.uploaded_by) if file_record.uploaded_by else None,
        "confirmed_at": file_record.confirmed_at.isoformat() if file_record.confirmed_at else None,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
    }
