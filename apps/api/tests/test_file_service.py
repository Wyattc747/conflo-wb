"""Tests for File storage service and Image processing service."""
import io
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.file import File
from app.services.file_service import (
    confirm_upload,
    delete_file,
    format_file_response,
    get_download_url,
    get_thumbnail_url,
    get_view_url,
    is_allowed_type,
    list_project_files,
    request_upload_url,
    VALID_CATEGORIES,
    IMAGE_CATEGORIES,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_MB,
)
from app.services.image_service import (
    extract_exif,
    generate_thumbnail,
    parse_gps_info,
    _gps_to_decimal,
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


def _make_sub_user(user_id=SUB_USER_ID):
    return {
        "user_type": "sub",
        "user_id": user_id,
        "sub_company_id": SUB_COMPANY_ID,
        "permission_level": None,
    }


def _make_file(
    file_id=None,
    status="CONFIRMED",
    mime_type="application/pdf",
    category="document",
    deleted_at=None,
    thumbnail_key=None,
    exif_data=None,
    size_bytes=1024,
):
    f = MagicMock(spec=File)
    f.id = file_id or uuid.uuid4()
    f.organization_id = ORG_ID
    f.project_id = PROJECT_ID
    f.s3_key = f"{ORG_ID}/{PROJECT_ID}/{category}/{f.id}.pdf"
    f.filename = "test-file.pdf"
    f.mime_type = mime_type
    f.size_bytes = size_bytes
    f.category = category
    f.status = status
    f.thumbnail_key = thumbnail_key
    f.exif_data = exif_data
    f.uploaded_by = ADMIN_USER_ID
    f.confirmed_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc) if status == "CONFIRMED" else None
    f.created_at = datetime(2026, 2, 20, 9, 0, tzinfo=timezone.utc)
    f.deleted_at = deleted_at
    return f


# ============================================================
# TestRequestUploadUrl
# ============================================================

class TestRequestUploadUrl:
    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_file_id_upload_url_and_key(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned-put"

        result = await request_upload_url(
            db, user, PROJECT_ID, "blueprint.pdf", "application/pdf", "document", 5000
        )

        assert "file_id" in result
        assert result["upload_url"] == "https://s3.example.com/presigned-put"
        assert "key" in result
        assert str(ORG_ID) in result["key"]
        assert str(PROJECT_ID) in result["key"]
        assert "document" in result["key"]
        assert result["key"].endswith(".pdf")
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_presigned_url_called_with_correct_params(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        await request_upload_url(
            db, user, PROJECT_ID, "photo.jpg", "image/jpeg", "photo", 2048
        )

        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "put_object"
        params = call_args[1]["Params"]
        assert params["ContentType"] == "image/jpeg"
        assert call_args[1]["ExpiresIn"] == 900

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_rejects_invalid_category(self, mock_s3):
        db = AsyncMock()
        user = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await request_upload_url(
                db, user, PROJECT_ID, "file.pdf", "application/pdf", "invalid_category", 1024
            )
        assert exc_info.value.status_code == 400
        assert "Invalid category" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_rejects_oversized_file(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        oversized = (MAX_FILE_SIZE_MB * 1024 * 1024) + 1

        with pytest.raises(HTTPException) as exc_info:
            await request_upload_url(
                db, user, PROJECT_ID, "huge.pdf", "application/pdf", "document", oversized
            )
        assert exc_info.value.status_code == 400
        assert "limit" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_rejects_disallowed_mime_for_image_category(self, mock_s3):
        db = AsyncMock()
        user = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await request_upload_url(
                db, user, PROJECT_ID, "scan.pdf", "application/pdf", "photo", 1024
            )
        assert exc_info.value.status_code == 400
        assert "not allowed" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_accepts_image_for_image_category(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        result = await request_upload_url(
            db, user, PROJECT_ID, "site-photo.jpg", "image/jpeg", "daily_log_photo", 2048
        )

        assert "file_id" in result
        db.add.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_file_record_status_is_pending(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        await request_upload_url(
            db, user, PROJECT_ID, "doc.pdf", "application/pdf", "document", 1024
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.status == "PENDING"
        assert added_obj.uploaded_by == ADMIN_USER_ID

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_sub_user_uses_sub_company_id_in_key(self, mock_s3):
        db = AsyncMock()
        user = _make_sub_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        result = await request_upload_url(
            db, user, PROJECT_ID, "coi.pdf", "application/pdf", "document", 1024
        )

        assert str(SUB_COMPANY_ID) in result["key"]

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_file_without_extension_gets_bin(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        result = await request_upload_url(
            db, user, PROJECT_ID, "README", "text/plain", "document", 512
        )

        assert result["key"].endswith(".bin")

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_no_file_size_skips_size_check(self, mock_s3):
        db = AsyncMock()
        user = _make_user()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        result = await request_upload_url(
            db, user, PROJECT_ID, "doc.pdf", "application/pdf", "document", None
        )

        assert "file_id" in result


# ============================================================
# TestConfirmUpload
# ============================================================

class TestConfirmUpload:
    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_confirm_sets_status_to_confirmed(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(status="PENDING")
        db.get.return_value = file_record
        mock_s3.head_object.return_value = {"ContentLength": 4096}

        user = _make_user()
        result = await confirm_upload(db, file_record.id, user)

        assert file_record.status == "CONFIRMED"
        assert file_record.confirmed_at is not None
        assert file_record.size_bytes == 4096
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_confirm_rejects_already_confirmed(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(status="CONFIRMED")
        db.get.return_value = file_record

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await confirm_upload(db, file_record.id, user)
        assert exc_info.value.status_code == 400
        assert "already confirmed" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_confirm_returns_404_if_not_found(self, mock_s3):
        db = AsyncMock()
        db.get.return_value = None

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await confirm_upload(db, uuid.uuid4(), user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.image_service.process_image", new_callable=AsyncMock)
    @patch("app.services.file_service.s3_client")
    async def test_confirm_calls_image_processing_for_images(self, mock_s3, mock_process):
        db = AsyncMock()
        file_record = _make_file(status="PENDING", mime_type="image/jpeg")
        file_record.s3_key = f"{ORG_ID}/{PROJECT_ID}/photo/{file_record.id}.jpg"
        db.get.return_value = file_record
        mock_s3.head_object.return_value = {"ContentLength": 8192}

        user = _make_user()
        await confirm_upload(db, file_record.id, user)

        mock_process.assert_awaited_once_with(db, file_record)

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_confirm_skips_image_processing_for_pdf(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(status="PENDING", mime_type="application/pdf")
        db.get.return_value = file_record
        mock_s3.head_object.return_value = {"ContentLength": 2048}

        user = _make_user()
        with patch("app.services.image_service.process_image", new_callable=AsyncMock) as mock_process:
            await confirm_upload(db, file_record.id, user)
            mock_process.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_confirm_raises_when_s3_file_missing(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(status="PENDING")
        db.get.return_value = file_record
        mock_s3.head_object.side_effect = Exception("NoSuchKey")

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await confirm_upload(db, file_record.id, user)
        assert exc_info.value.status_code == 400
        assert "not found in storage" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @patch("app.services.image_service.process_image", new_callable=AsyncMock)
    @patch("app.services.file_service.s3_client")
    async def test_confirm_returns_formatted_response(self, mock_s3, mock_process):
        db = AsyncMock()
        file_record = _make_file(status="PENDING", mime_type="image/png")
        db.get.return_value = file_record
        mock_s3.head_object.return_value = {"ContentLength": 3000}

        user = _make_user()
        result = await confirm_upload(db, file_record.id, user)

        assert result["id"] == str(file_record.id)
        assert result["status"] == "CONFIRMED"
        assert result["filename"] == file_record.filename

    @pytest.mark.asyncio
    @patch("app.services.image_service.process_image", new_callable=AsyncMock)
    @patch("app.services.file_service.s3_client")
    async def test_confirm_continues_if_image_processing_fails(self, mock_s3, mock_process):
        """Image processing failure is non-critical -- confirm should still succeed."""
        db = AsyncMock()
        file_record = _make_file(status="PENDING", mime_type="image/jpeg")
        db.get.return_value = file_record
        mock_s3.head_object.return_value = {"ContentLength": 5000}
        mock_process.side_effect = Exception("Pillow error")

        user = _make_user()
        result = await confirm_upload(db, file_record.id, user)

        assert file_record.status == "CONFIRMED"


# ============================================================
# TestGetDownloadUrl
# ============================================================

class TestGetDownloadUrl:
    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_url_with_attachment_disposition(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file()
        db.get.return_value = file_record
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/download"

        user = _make_user()
        url = await get_download_url(db, file_record.id, user)

        assert url == "https://s3.example.com/download"
        call_args = mock_s3.generate_presigned_url.call_args
        params = call_args[1]["Params"]
        assert "attachment" in params["ResponseContentDisposition"]
        assert file_record.filename in params["ResponseContentDisposition"]
        assert call_args[1]["ExpiresIn"] == 3600

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_404_for_nonexistent_file(self, mock_s3):
        db = AsyncMock()
        db.get.return_value = None

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await get_download_url(db, uuid.uuid4(), user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_404_for_deleted_file(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(deleted_at=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc))
        db.get.return_value = file_record

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await get_download_url(db, file_record.id, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_uses_get_object_method(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file()
        db.get.return_value = file_record
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/dl"

        user = _make_user()
        await get_download_url(db, file_record.id, user)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"


# ============================================================
# TestGetViewUrl
# ============================================================

class TestGetViewUrl:
    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_url_with_inline_disposition(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(mime_type="application/pdf")
        db.get.return_value = file_record
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/view"

        url = await get_view_url(db, file_record.id)

        assert url == "https://s3.example.com/view"
        call_args = mock_s3.generate_presigned_url.call_args
        params = call_args[1]["Params"]
        assert params["ResponseContentDisposition"] == "inline"
        assert params["ResponseContentType"] == "application/pdf"

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_404_for_nonexistent_file(self, mock_s3):
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_view_url(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_404_for_deleted_file(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(deleted_at=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc))
        db.get.return_value = file_record

        with pytest.raises(HTTPException) as exc_info:
            await get_view_url(db, file_record.id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_fallback_to_octet_stream_for_none_mime(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(mime_type=None)
        db.get.return_value = file_record
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/view"

        await get_view_url(db, file_record.id)

        call_args = mock_s3.generate_presigned_url.call_args
        params = call_args[1]["Params"]
        assert params["ResponseContentType"] == "application/octet-stream"


# ============================================================
# TestGetThumbnailUrl
# ============================================================

class TestGetThumbnailUrl:
    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_url_when_thumbnail_exists(self, mock_s3):
        db = AsyncMock()
        thumb_key = f"{ORG_ID}/{PROJECT_ID}/photo/thumb_abc.jpg"
        file_record = _make_file(thumbnail_key=thumb_key, mime_type="image/jpeg")
        db.get.return_value = file_record
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/thumb"

        url = await get_thumbnail_url(db, file_record.id)

        assert url == "https://s3.example.com/thumb"
        call_args = mock_s3.generate_presigned_url.call_args
        params = call_args[1]["Params"]
        assert params["Key"] == thumb_key
        assert params["ResponseContentType"] == "image/jpeg"

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_none_when_no_thumbnail(self, mock_s3):
        db = AsyncMock()
        file_record = _make_file(thumbnail_key=None)
        db.get.return_value = file_record

        url = await get_thumbnail_url(db, file_record.id)

        assert url is None
        mock_s3.generate_presigned_url.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.file_service.s3_client")
    async def test_returns_none_when_file_not_found(self, mock_s3):
        db = AsyncMock()
        db.get.return_value = None

        url = await get_thumbnail_url(db, uuid.uuid4())

        assert url is None


# ============================================================
# TestDeleteFile
# ============================================================

class TestDeleteFile:
    @pytest.mark.asyncio
    async def test_sets_deleted_at(self):
        db = AsyncMock()
        file_record = _make_file()
        db.get.return_value = file_record

        user = _make_user()
        result = await delete_file(db, file_record.id, user)

        assert file_record.deleted_at is not None
        assert result["id"] == str(file_record.id)
        assert result["deleted"] is True
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_404_if_not_found(self):
        db = AsyncMock()
        db.get.return_value = None

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_file(db, uuid.uuid4(), user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_404_if_already_deleted(self):
        db = AsyncMock()
        file_record = _make_file(deleted_at=datetime(2026, 2, 21, 12, 0, tzinfo=timezone.utc))
        db.get.return_value = file_record

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_file(db, file_record.id, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_management_user_can_delete(self):
        db = AsyncMock()
        file_record = _make_file()
        db.get.return_value = file_record

        user = _make_user(user_id=MGMT_USER_ID, permission_level="MANAGEMENT")
        result = await delete_file(db, file_record.id, user)

        assert result["deleted"] is True


# ============================================================
# TestListProjectFiles
# ============================================================

class TestListProjectFiles:
    @pytest.mark.asyncio
    async def test_returns_files_and_total(self):
        db = AsyncMock()
        file1 = _make_file()
        file2 = _make_file()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [file1, file2]

        db.execute.side_effect = [mock_count_result, mock_list_result]

        files, total = await list_project_files(db, PROJECT_ID)

        assert total == 2
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_filters_by_category(self):
        db = AsyncMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [_make_file(category="photo")]

        db.execute.side_effect = [mock_count_result, mock_list_result]

        files, total = await list_project_files(db, PROJECT_ID, category="photo")

        assert total == 1

    @pytest.mark.asyncio
    async def test_pagination(self):
        db = AsyncMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [_make_file() for _ in range(10)]

        db.execute.side_effect = [mock_count_result, mock_list_result]

        files, total = await list_project_files(db, PROJECT_ID, page=2, per_page=10)

        assert total == 50
        assert len(files) == 10

    @pytest.mark.asyncio
    async def test_empty_project_returns_empty(self):
        db = AsyncMock()

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [mock_count_result, mock_list_result]

        files, total = await list_project_files(db, PROJECT_ID)

        assert total == 0
        assert len(files) == 0


# ============================================================
# TestFileTypeValidation
# ============================================================

class TestFileTypeValidation:
    def test_accepts_jpeg_for_image_category(self):
        assert is_allowed_type("image/jpeg", "photo") is True

    def test_accepts_png_for_image_category(self):
        assert is_allowed_type("image/png", "daily_log_photo") is True

    def test_accepts_webp_for_image_category(self):
        assert is_allowed_type("image/webp", "punch_list_photo") is True

    def test_accepts_gif_for_image_category(self):
        assert is_allowed_type("image/gif", "inspection_photo") is True

    def test_accepts_heic_for_image_category(self):
        assert is_allowed_type("image/heic", "avatar") is True

    def test_rejects_pdf_for_image_category(self):
        assert is_allowed_type("application/pdf", "photo") is False

    def test_rejects_word_for_image_category(self):
        assert is_allowed_type("application/msword", "daily_log_photo") is False

    def test_rejects_csv_for_image_category(self):
        assert is_allowed_type("text/csv", "punch_list_photo") is False

    def test_accepts_pdf_for_document_category(self):
        assert is_allowed_type("application/pdf", "document") is True

    def test_accepts_word_for_document_category(self):
        assert is_allowed_type("application/msword", "rfi_attachment") is True

    def test_accepts_docx_for_document_category(self):
        assert is_allowed_type(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "submittal_doc"
        ) is True

    def test_accepts_excel_for_document_category(self):
        assert is_allowed_type("application/vnd.ms-excel", "document") is True

    def test_accepts_xlsx_for_document_category(self):
        assert is_allowed_type(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "bid_scope_doc"
        ) is True

    def test_accepts_csv_for_document_category(self):
        assert is_allowed_type("text/csv", "document") is True

    def test_accepts_plain_text_for_document_category(self):
        assert is_allowed_type("text/plain", "other") is True

    def test_accepts_image_for_general_category(self):
        assert is_allowed_type("image/jpeg", "document") is True

    def test_rejects_unknown_mime_for_any_category(self):
        assert is_allowed_type("application/zip", "document") is False

    def test_rejects_html_for_any_category(self):
        assert is_allowed_type("text/html", "other") is False

    def test_accepts_pdf_for_drawing_category(self):
        assert is_allowed_type("application/pdf", "drawing_sheet") is True

    def test_accepts_jpeg_for_drawing_category(self):
        assert is_allowed_type("image/jpeg", "drawing_sheet") is True

    def test_accepts_tiff_for_drawing_category(self):
        assert is_allowed_type("image/tiff", "drawing_sheet") is True

    def test_rejects_word_for_drawing_category(self):
        assert is_allowed_type("application/msword", "drawing_sheet") is False

    def test_all_image_categories_are_subset_of_valid(self):
        for cat in IMAGE_CATEGORIES:
            assert cat in VALID_CATEGORIES


# ============================================================
# TestFormatFileResponse
# ============================================================

class TestFormatFileResponse:
    def test_basic_format(self):
        file_record = _make_file()
        result = format_file_response(file_record)

        assert result["id"] == str(file_record.id)
        assert result["filename"] == "test-file.pdf"
        assert result["mime_type"] == "application/pdf"
        assert result["size_bytes"] == 1024
        assert result["category"] == "document"
        assert result["status"] == "CONFIRMED"
        assert result["uploaded_by"] == str(ADMIN_USER_ID)
        assert result["confirmed_at"] is not None
        assert result["created_at"] is not None

    def test_format_pending_file(self):
        file_record = _make_file(status="PENDING")
        result = format_file_response(file_record)

        assert result["status"] == "PENDING"
        assert result["confirmed_at"] is None

    def test_format_with_thumbnail(self):
        thumb_key = "org/proj/photo/abc_thumb.jpg"
        file_record = _make_file(thumbnail_key=thumb_key)
        result = format_file_response(file_record)

        assert result["thumbnail_key"] == thumb_key

    def test_format_with_exif_data(self):
        exif = {"camera_make": "Canon", "gps_lat": 39.7392}
        file_record = _make_file(exif_data=exif)
        result = format_file_response(file_record)

        assert result["exif_data"] == exif

    def test_format_without_uploaded_by(self):
        file_record = _make_file()
        file_record.uploaded_by = None
        result = format_file_response(file_record)

        assert result["uploaded_by"] is None

    def test_format_without_created_at(self):
        file_record = _make_file()
        file_record.created_at = None
        result = format_file_response(file_record)

        assert result["created_at"] is None


# ============================================================
# TestImageProcessing
# ============================================================

class TestImageProcessing:
    def test_extract_exif_returns_none_for_no_exif(self):
        img = MagicMock()
        img._getexif.return_value = None

        result = extract_exif(img)
        assert result is None

    def test_extract_exif_returns_none_when_getexif_raises(self):
        img = MagicMock()
        img._getexif.side_effect = AttributeError("no EXIF")

        result = extract_exif(img)
        assert result is None

    def test_extract_exif_extracts_date_taken(self):
        from PIL.ExifTags import TAGS

        # Find the tag ID for DateTimeOriginal
        date_tag_id = None
        for tag_id, name in TAGS.items():
            if name == "DateTimeOriginal":
                date_tag_id = tag_id
                break

        img = MagicMock()
        img._getexif.return_value = {date_tag_id: "2026:02:20 10:30:00"}

        result = extract_exif(img)
        assert result is not None
        assert result["date_taken"] == "2026:02:20 10:30:00"

    def test_extract_exif_extracts_camera_info(self):
        from PIL.ExifTags import TAGS

        make_tag = None
        model_tag = None
        for tag_id, name in TAGS.items():
            if name == "Make":
                make_tag = tag_id
            elif name == "Model":
                model_tag = tag_id

        img = MagicMock()
        img._getexif.return_value = {
            make_tag: "Canon",
            model_tag: "EOS R5",
        }

        result = extract_exif(img)
        assert result is not None
        assert result["camera_make"] == "Canon"
        assert result["camera_model"] == "EOS R5"

    def test_extract_exif_returns_none_for_empty_exif(self):
        img = MagicMock()
        img._getexif.return_value = {}

        result = extract_exif(img)
        assert result is None

    def test_generate_thumbnail_respects_max_width(self):
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (1200, 800))

        thumbnail = generate_thumbnail(img, max_width=400)

        assert thumbnail.width <= 400

    def test_generate_thumbnail_maintains_aspect_ratio(self):
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (1200, 800))

        thumbnail = generate_thumbnail(img, max_width=600)

        original_ratio = 1200 / 800
        thumb_ratio = thumbnail.width / thumbnail.height
        assert abs(original_ratio - thumb_ratio) < 0.05

    def test_generate_thumbnail_converts_rgba_to_rgb(self):
        from PIL import Image as PILImage

        img = PILImage.new("RGBA", (800, 600))

        thumbnail = generate_thumbnail(img, max_width=400)

        assert thumbnail.mode == "RGB"

    def test_generate_thumbnail_default_width(self):
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (2000, 1500))

        thumbnail = generate_thumbnail(img)

        assert thumbnail.width <= 400

    def test_generate_thumbnail_smaller_than_max(self):
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (200, 150))

        thumbnail = generate_thumbnail(img, max_width=400)

        # thumbnail() method does not upscale
        assert thumbnail.width <= 200


# ============================================================
# TestGPSParsing
# ============================================================

class TestGPSParsing:
    def test_gps_to_decimal_north_east(self):
        # 39 degrees, 44 minutes, 21.12 seconds N
        result = _gps_to_decimal((39.0, 44.0, 21.12), "N")
        assert result is not None
        assert abs(result - 39.7392) < 0.001

    def test_gps_to_decimal_south(self):
        result = _gps_to_decimal((33.0, 51.0, 54.0), "S")
        assert result is not None
        assert result < 0
        assert abs(result - (-33.865)) < 0.001

    def test_gps_to_decimal_west(self):
        result = _gps_to_decimal((104.0, 59.0, 24.0), "W")
        assert result is not None
        assert result < 0

    def test_gps_to_decimal_east(self):
        result = _gps_to_decimal((151.0, 12.0, 33.6), "E")
        assert result is not None
        assert result > 0

    def test_gps_to_decimal_returns_none_for_missing_coords(self):
        result = _gps_to_decimal(None, "N")
        assert result is None

    def test_gps_to_decimal_returns_none_for_missing_ref(self):
        result = _gps_to_decimal((39.0, 44.0, 21.12), None)
        assert result is None

    def test_gps_to_decimal_returns_none_for_both_missing(self):
        result = _gps_to_decimal(None, None)
        assert result is None

    def test_gps_to_decimal_returns_none_for_invalid_coords(self):
        result = _gps_to_decimal("not_a_tuple", "N")
        assert result is None

    def test_parse_gps_info_returns_lat_lon(self):
        from PIL.ExifTags import GPSTAGS

        # Build GPS info dict using actual GPSTAG keys
        gps_tag_map = {v: k for k, v in GPSTAGS.items()}

        gps_info = {
            gps_tag_map["GPSLatitude"]: (39.0, 44.0, 21.12),
            gps_tag_map["GPSLatitudeRef"]: "N",
            gps_tag_map["GPSLongitude"]: (104.0, 59.0, 24.0),
            gps_tag_map["GPSLongitudeRef"]: "W",
        }

        result = parse_gps_info(gps_info)
        assert result is not None
        assert "lat" in result
        assert "lon" in result
        assert result["lat"] > 0
        assert result["lon"] < 0

    def test_parse_gps_info_returns_none_for_empty(self):
        result = parse_gps_info({})
        assert result is None

    def test_parse_gps_info_returns_none_for_partial_data(self):
        from PIL.ExifTags import GPSTAGS

        gps_tag_map = {v: k for k, v in GPSTAGS.items()}

        # Only latitude, no longitude
        gps_info = {
            gps_tag_map["GPSLatitude"]: (39.0, 44.0, 21.12),
            gps_tag_map["GPSLatitudeRef"]: "N",
        }

        result = parse_gps_info(gps_info)
        assert result is None
