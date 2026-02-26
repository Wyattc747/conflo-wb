"""Tests for Document service (documents + folders)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.document import Document
from app.models.document_folder import DocumentFolder
from app.models.event_log import EventLog
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentUploadNewVersion,
    FolderCreate,
)
from app.services.document_service import (
    create_document,
    create_folder,
    delete_document,
    delete_folder,
    format_document_response,
    format_folder_response,
    get_document,
    get_folder,
    update_document,
    upload_new_version,
)
from tests.conftest import (
    ADMIN_USER_ID,
    MGMT_USER_ID,
    ORG_ID,
    PROJECT_ID,
    SUB_COMPANY_ID,
    SUB_USER_ID,
)


# ============================================================
# HELPERS
# ============================================================

def _make_user(user_id=ADMIN_USER_ID, permission_level="OWNER_ADMIN"):
    return {
        "user_type": "gc",
        "user_id": user_id,
        "organization_id": ORG_ID,
        "permission_level": permission_level,
    }


def _make_document(
    version=1,
    category="Contracts",
    created_by=ADMIN_USER_ID,
    folder_id=None,
):
    doc = MagicMock(spec=Document)
    doc.id = uuid.uuid4()
    doc.organization_id = ORG_ID
    doc.project_id = PROJECT_ID
    doc.created_by = created_by
    doc.title = "Subcontract Agreement - Concrete"
    doc.description = "Signed subcontract for concrete scope."
    doc.category = category
    doc.folder_id = folder_id or uuid.uuid4()
    doc.file_id = uuid.uuid4()
    doc.file_url = None
    doc.tags = ["contract", "concrete"]
    doc.version = version
    doc.uploaded_by = created_by
    doc.created_at = datetime(2026, 2, 20, 10, 0)
    doc.updated_at = datetime(2026, 2, 20, 10, 0)
    doc.deleted_at = None
    return doc


def _make_folder(
    name="Contracts",
    is_system=True,
    parent_folder_id=None,
):
    folder = MagicMock(spec=DocumentFolder)
    folder.id = uuid.uuid4()
    folder.organization_id = ORG_ID
    folder.project_id = PROJECT_ID
    folder.name = name
    folder.parent_folder_id = parent_folder_id
    folder.is_system = is_system
    folder.created_by = ADMIN_USER_ID
    folder.created_at = datetime(2026, 2, 20, 10, 0)
    folder.updated_at = datetime(2026, 2, 20, 10, 0)
    return folder


# ============================================================
# create_document
# ============================================================

class TestCreateDocument:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()
        data = DocumentCreate(
            title="Subcontract Agreement",
            description="Signed subcontract for concrete scope.",
            category="Contracts",
            folder_id=folder_id,
            file_id=file_id,
            tags=["contract", "concrete"],
        )

        result = await create_document(db, PROJECT_ID, ORG_ID, user, data)

        # Document + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_minimal_fields(self):
        db = AsyncMock()
        user = _make_user()
        data = DocumentCreate(title="Quick Note")

        result = await create_document(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# get_document
# ============================================================

class TestGetDocument:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        doc = _make_document()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        result = await get_document(db, doc.id, PROJECT_ID)
        assert result == doc

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_document(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404


# ============================================================
# update_document
# ============================================================

class TestUpdateDocument:
    @pytest.mark.asyncio
    async def test_update_success(self):
        db = AsyncMock()
        doc = _make_document()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        user = _make_user()
        data = DocumentUpdate(title="Updated Title", description="New description")

        result = await update_document(db, doc.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_category(self):
        db = AsyncMock()
        doc = _make_document(category="Contracts")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        user = _make_user()
        data = DocumentUpdate(category="Reports")

        result = await update_document(db, doc.id, PROJECT_ID, user, data)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = DocumentUpdate(title="Oops")

        with pytest.raises(HTTPException) as exc_info:
            await update_document(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# delete_document
# ============================================================

class TestDeleteDocument:
    @pytest.mark.asyncio
    async def test_delete_success(self):
        db = AsyncMock()
        doc = _make_document()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        user = _make_user()
        result = await delete_document(db, doc.id, PROJECT_ID, user)

        assert doc.deleted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_document(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# upload_new_version
# ============================================================

class TestUploadNewVersion:
    @pytest.mark.asyncio
    async def test_version_increments(self):
        db = AsyncMock()
        doc = _make_document(version=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        user = _make_user()
        new_file_id = uuid.uuid4()
        data = DocumentUploadNewVersion(file_id=new_file_id)

        result = await upload_new_version(db, doc.id, PROJECT_ID, user, data)

        assert doc.version == 2
        assert doc.file_id == new_file_id
        # EventLog added
        assert db.add.call_count >= 1
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_version_increments_from_higher(self):
        db = AsyncMock()
        doc = _make_document(version=5)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = doc
        db.execute.return_value = mock_result

        user = _make_user()
        data = DocumentUploadNewVersion(file_id=uuid.uuid4())

        result = await upload_new_version(db, doc.id, PROJECT_ID, user, data)

        assert doc.version == 6
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upload_version_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        data = DocumentUploadNewVersion(file_id=uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await upload_new_version(db, uuid.uuid4(), PROJECT_ID, user, data)
        assert exc_info.value.status_code == 404


# ============================================================
# create_folder
# ============================================================

class TestCreateFolder:
    @pytest.mark.asyncio
    async def test_create_success(self):
        db = AsyncMock()
        user = _make_user()
        data = FolderCreate(name="Submittals")

        result = await create_folder(db, PROJECT_ID, ORG_ID, user, data)

        # Folder + EventLog = 2
        assert db.add.call_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_nested_folder(self):
        db = AsyncMock()
        user = _make_user()
        parent_id = uuid.uuid4()
        data = FolderCreate(name="Sub-folder", parent_folder_id=parent_id)

        result = await create_folder(db, PROJECT_ID, ORG_ID, user, data)

        assert db.add.call_count == 2
        db.flush.assert_awaited_once()


# ============================================================
# delete_folder
# ============================================================

class TestDeleteFolder:
    @pytest.mark.asyncio
    async def test_delete_user_folder(self):
        db = AsyncMock()
        folder = _make_folder(name="My Folder", is_system=False)

        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = folder

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        db.execute.side_effect = [mock_folder_result, mock_count_result]

        user = _make_user()
        await delete_folder(db, folder.id, PROJECT_ID, user)

        db.delete.assert_awaited_once_with(folder)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_system_folder_raises_400(self):
        db = AsyncMock()
        folder = _make_folder(name="Contracts", is_system=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = folder
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_folder(db, folder.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_folder_with_documents_raises_400(self):
        db = AsyncMock()
        folder = _make_folder(name="My Folder", is_system=False)

        mock_folder_result = MagicMock()
        mock_folder_result.scalar_one_or_none.return_value = folder

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3  # Has documents

        db.execute.side_effect = [mock_folder_result, mock_count_result]

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_folder(db, folder.id, PROJECT_ID, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_folder_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_folder(db, uuid.uuid4(), PROJECT_ID, user)
        assert exc_info.value.status_code == 404


# ============================================================
# format_document_response
# ============================================================

class TestFormatDocumentResponse:
    def test_basic_format(self):
        doc = _make_document(version=2, category="Contracts")
        result = format_document_response(
            doc,
            uploaded_by_name="John Smith",
            folder_name="Contracts",
        )

        assert result["id"] == doc.id
        assert result["project_id"] == PROJECT_ID
        assert result["title"] == "Subcontract Agreement - Concrete"
        assert result["description"] == "Signed subcontract for concrete scope."
        assert result["category"] == "Contracts"
        assert result["version"] == 2
        assert result["uploaded_by_name"] == "John Smith"
        assert result["folder_name"] == "Contracts"
        assert result["tags"] == ["contract", "concrete"]
        assert result["file_id"] == doc.file_id

    def test_format_without_optional_names(self):
        doc = _make_document()
        result = format_document_response(doc)

        assert result["uploaded_by_name"] is None
        assert result["folder_name"] is None

    def test_format_empty_tags(self):
        doc = _make_document()
        doc.tags = None
        result = format_document_response(doc)
        assert result["tags"] == []


# ============================================================
# format_folder_response
# ============================================================

class TestFormatFolderResponse:
    def test_system_folder(self):
        folder = _make_folder(name="Contracts", is_system=True)
        result = format_folder_response(folder)

        assert result["id"] == folder.id
        assert result["project_id"] == PROJECT_ID
        assert result["name"] == "Contracts"
        assert result["is_system"] is True
        assert result["parent_folder_id"] is None

    def test_user_folder_with_parent(self):
        parent_id = uuid.uuid4()
        folder = _make_folder(name="Sub-folder", is_system=False, parent_folder_id=parent_id)
        result = format_folder_response(folder)

        assert result["name"] == "Sub-folder"
        assert result["is_system"] is False
        assert result["parent_folder_id"] == parent_id


# ============================================================
# get_folder
# ============================================================

class TestGetFolder:
    @pytest.mark.asyncio
    async def test_found(self):
        db = AsyncMock()
        folder = _make_folder()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = folder
        db.execute.return_value = mock_result

        result = await get_folder(db, folder.id, PROJECT_ID)
        assert result == folder

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_folder(db, uuid.uuid4(), PROJECT_ID)
        assert exc_info.value.status_code == 404
