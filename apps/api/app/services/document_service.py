import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_folder import DocumentFolder
from app.models.event_log import EventLog
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentUploadNewVersion,
    FolderCreate,
    FolderUpdate,
)

DEFAULT_FOLDERS = [
    "Contracts",
    "Specifications",
    "Reports",
    "Correspondence",
    "Closeout",
    "General",
]


async def create_default_folders(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> list[DocumentFolder]:
    folders = []
    for name in DEFAULT_FOLDERS:
        folder = DocumentFolder(
            organization_id=organization_id,
            project_id=project_id,
            name=name,
            is_system=True,
            created_by=user_id,
        )
        db.add(folder)
        folders.append(folder)
    await db.flush()
    return folders


async def create_folder(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: FolderCreate,
) -> DocumentFolder:
    folder = DocumentFolder(
        organization_id=organization_id,
        project_id=project_id,
        name=data.name,
        parent_folder_id=data.parent_folder_id,
        is_system=False,
        created_by=user["user_id"],
    )
    db.add(folder)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="folder_created",
        event_data={"name": data.name},
    )
    db.add(event)

    await db.flush()
    return folder


async def list_folders(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[DocumentFolder]:
    result = await db.execute(
        select(DocumentFolder)
        .where(DocumentFolder.project_id == project_id)
        .order_by(DocumentFolder.is_system.desc(), DocumentFolder.name.asc())
    )
    return result.scalars().all()


async def get_folder(
    db: AsyncSession,
    folder_id: uuid.UUID,
    project_id: uuid.UUID,
) -> DocumentFolder:
    result = await db.execute(
        select(DocumentFolder).where(
            DocumentFolder.id == folder_id,
            DocumentFolder.project_id == project_id,
        )
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(404, "Folder not found")
    return folder


async def update_folder(
    db: AsyncSession,
    folder_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: FolderUpdate,
) -> DocumentFolder:
    folder = await get_folder(db, folder_id, project_id)
    if folder.is_system:
        raise HTTPException(400, "Cannot modify system folders")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(folder, key):
            setattr(folder, key, value)

    await db.flush()
    return folder


async def delete_folder(
    db: AsyncSession,
    folder_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> None:
    folder = await get_folder(db, folder_id, project_id)
    if folder.is_system:
        raise HTTPException(400, "Cannot delete system folders")

    # Check if folder has documents
    doc_count = await db.execute(
        select(func.count()).select_from(Document).where(
            Document.folder_id == folder_id,
            Document.deleted_at.is_(None),
        )
    )
    if doc_count.scalar() > 0:
        raise HTTPException(400, "Cannot delete folder that contains documents")

    await db.delete(folder)
    await db.flush()


async def create_document(
    db: AsyncSession,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    user: dict,
    data: DocumentCreate,
) -> Document:
    doc = Document(
        organization_id=organization_id,
        project_id=project_id,
        created_by=user["user_id"],
        title=data.title,
        description=data.description,
        category=data.category,
        folder_id=data.folder_id,
        file_id=data.file_id,
        tags=data.tags or [],
        version=1,
    )
    db.add(doc)

    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="document_created",
        event_data={"title": data.title},
    )
    db.add(event)

    await db.flush()
    return doc


async def list_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    per_page: int = 25,
    folder_id: uuid.UUID | None = None,
    category: str | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[Document], int]:
    query = select(Document).where(
        Document.project_id == project_id,
        Document.deleted_at.is_(None),
    )

    if folder_id:
        query = query.where(Document.folder_id == folder_id)
    if category:
        query = query.where(Document.category == category)
    if search:
        query = query.where(
            or_(
                Document.title.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    sort_col = getattr(Document, sort, Document.created_at)
    if order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.project_id == project_id,
            Document.deleted_at.is_(None),
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


async def update_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: DocumentUpdate,
) -> Document:
    doc = await get_document(db, document_id, project_id)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(doc, key):
            setattr(doc, key, value)

    await db.flush()
    return doc


async def delete_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
) -> Document:
    doc = await get_document(db, document_id, project_id)
    doc.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return doc


async def upload_new_version(
    db: AsyncSession,
    document_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: DocumentUploadNewVersion,
) -> Document:
    doc = await get_document(db, document_id, project_id)
    doc.file_id = data.file_id
    doc.version = (doc.version or 1) + 1

    event = EventLog(
        organization_id=user.get("organization_id"),
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="document_new_version",
        event_data={"document_id": str(document_id), "version": doc.version},
    )
    db.add(event)

    await db.flush()
    return doc


def format_folder_response(folder: DocumentFolder) -> dict:
    return {
        "id": folder.id,
        "project_id": folder.project_id,
        "name": folder.name,
        "parent_folder_id": folder.parent_folder_id,
        "is_system": folder.is_system,
        "created_at": folder.created_at,
    }


def format_document_response(
    doc: Document,
    uploaded_by_name: str | None = None,
    folder_name: str | None = None,
) -> dict:
    return {
        "id": doc.id,
        "project_id": doc.project_id,
        "title": doc.title,
        "description": doc.description,
        "category": doc.category,
        "folder_id": doc.folder_id,
        "folder_name": folder_name,
        "file_id": doc.file_id,
        "tags": doc.tags if doc.tags else [],
        "version": doc.version,
        "uploaded_by": doc.created_by,
        "uploaded_by_name": uploaded_by_name,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }
