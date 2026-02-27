"""Tests for integration services — encryption, Google Calendar, Microsoft Graph, QuickBooks."""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from tests.conftest import ADMIN_USER_ID, ORG_ID, PROJECT_ID

# ============================================================
# MODULE-LEVEL MOCKS for missing third-party libraries
# These must be inserted into sys.modules BEFORE the integration
# modules are imported so that the top-level imports succeed.
# ============================================================

# -- httpx --
mock_httpx = MagicMock()
sys.modules.setdefault("httpx", mock_httpx)

# -- msal --
mock_msal_module = MagicMock()
sys.modules.setdefault("msal", mock_msal_module)

# -- google_auth_oauthlib --
mock_gao = MagicMock()
mock_gao_flow = MagicMock()
sys.modules.setdefault("google_auth_oauthlib", mock_gao)
sys.modules.setdefault("google_auth_oauthlib.flow", mock_gao_flow)

# -- google.oauth2.credentials --
mock_google = MagicMock()
sys.modules.setdefault("google", mock_google)
sys.modules.setdefault("google.oauth2", mock_google.oauth2)
sys.modules.setdefault("google.oauth2.credentials", mock_google.oauth2.credentials)

# -- googleapiclient --
mock_gapi = MagicMock()
sys.modules.setdefault("googleapiclient", mock_gapi)
sys.modules.setdefault("googleapiclient.discovery", mock_gapi.discovery)

# -- intuitlib --
mock_intuitlib = MagicMock()
mock_intuitlib_client = MagicMock()
mock_intuitlib_enums = MagicMock()
sys.modules.setdefault("intuitlib", mock_intuitlib)
sys.modules.setdefault("intuitlib.client", mock_intuitlib_client)
sys.modules.setdefault("intuitlib.enums", mock_intuitlib_enums)

# Generate a stable test Fernet key for the entire module
TEST_FERNET_KEY = Fernet.generate_key().decode()


def _make_user(
    user_type="gc",
    user_id=None,
    organization_id=None,
    permission_level="OWNER_ADMIN",
):
    return {
        "user_type": user_type,
        "user_id": user_id or ADMIN_USER_ID,
        "organization_id": organization_id or ORG_ID,
        "permission_level": permission_level,
    }


# ============================================================
# ENCRYPTION SERVICE
# ============================================================


class TestEncryptionService:
    """Tests for app.services.encryption_service."""

    @patch("app.services.encryption_service.settings")
    def test_encrypt_decrypt_roundtrip(self, mock_settings):
        """encrypt then decrypt returns the original plaintext."""
        mock_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        from app.services.encryption_service import decrypt, encrypt

        plaintext = "super-secret-oauth-token-12345"
        ciphertext = encrypt(plaintext)
        assert ciphertext != plaintext
        assert decrypt(ciphertext) == plaintext

    @patch("app.services.encryption_service.settings")
    def test_encrypt_decrypt_unicode(self, mock_settings):
        """Roundtrip preserves unicode data."""
        mock_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        from app.services.encryption_service import decrypt, encrypt

        plaintext = "tok\u00e9n-with-\u00fcnicode-\u2603"
        assert decrypt(encrypt(plaintext)) == plaintext

    @patch("app.services.encryption_service.settings")
    def test_encrypt_produces_different_ciphertexts(self, mock_settings):
        """Fernet includes random IV so each encryption differs."""
        mock_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        from app.services.encryption_service import encrypt

        c1 = encrypt("same-value")
        c2 = encrypt("same-value")
        assert c1 != c2  # Different IVs

    @patch("app.services.encryption_service.settings")
    def test_decrypt_with_wrong_key_raises_value_error(self, mock_settings):
        """Decrypting with a different key raises ValueError."""
        mock_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        from app.services.encryption_service import encrypt

        ciphertext = encrypt("my-token")

        # Switch to a different key
        mock_settings.ENCRYPTION_KEY = Fernet.generate_key().decode()
        from app.services.encryption_service import decrypt

        with pytest.raises(ValueError, match="Failed to decrypt"):
            decrypt(ciphertext)

    @patch("app.services.encryption_service.settings")
    def test_decrypt_corrupted_data_raises_value_error(self, mock_settings):
        """Corrupted ciphertext raises ValueError."""
        mock_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        from app.services.encryption_service import decrypt

        with pytest.raises(ValueError, match="Failed to decrypt"):
            decrypt("this-is-not-valid-fernet-data")

    @patch("app.services.encryption_service.settings")
    def test_encrypt_with_empty_key_raises_runtime_error(self, mock_settings):
        """Empty ENCRYPTION_KEY raises RuntimeError."""
        mock_settings.ENCRYPTION_KEY = ""
        from app.services.encryption_service import encrypt

        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY not configured"):
            encrypt("data")

    @patch("app.services.encryption_service.settings")
    def test_encrypt_with_none_key_raises_runtime_error(self, mock_settings):
        """None ENCRYPTION_KEY raises RuntimeError."""
        mock_settings.ENCRYPTION_KEY = None
        from app.services.encryption_service import encrypt

        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY not configured"):
            encrypt("data")

    @patch("app.services.encryption_service.settings")
    def test_decrypt_with_empty_key_raises_runtime_error(self, mock_settings):
        """Empty ENCRYPTION_KEY on decrypt also raises RuntimeError."""
        mock_settings.ENCRYPTION_KEY = ""
        from app.services.encryption_service import decrypt

        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY not configured"):
            decrypt("some-ciphertext")


# ============================================================
# GOOGLE CALENDAR INTEGRATION
# ============================================================


class TestGoogleCalendarInitiate:
    """Tests for initiate_google_oauth."""

    @pytest.mark.asyncio
    @patch("app.integrations.google_calendar.settings")
    async def test_initiate_returns_auth_url_and_state(self, mock_settings):
        """initiate_google_oauth returns (url, state) tuple."""
        mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
        mock_settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        mock_flow_instance = MagicMock()
        mock_flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test",
            "random-state-string",
        )

        # The function does a lazy import: from google_auth_oauthlib.flow import Flow
        # We need to set Flow.from_client_config on the sys.modules mock
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow_instance

        from app.integrations.google_calendar import initiate_google_oauth

        user = _make_user()
        auth_url, state = await initiate_google_oauth(
            user, "http://localhost:3000/callback"
        )

        assert "accounts.google.com" in auth_url
        assert state == "random-state-string"

    @pytest.mark.asyncio
    @patch("app.integrations.google_calendar.settings")
    async def test_initiate_passes_offline_access(self, mock_settings):
        """OAuth flow requests offline access for refresh tokens."""
        mock_settings.GOOGLE_CLIENT_ID = "cid"
        mock_settings.GOOGLE_CLIENT_SECRET = "csecret"

        mock_flow_instance = MagicMock()
        mock_flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth",
            "state-123",
        )
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow_instance

        from app.integrations.google_calendar import initiate_google_oauth

        await initiate_google_oauth(_make_user(), "http://localhost/cb")

        mock_flow_instance.authorization_url.assert_called_once_with(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )


class TestGoogleCalendarComplete:
    """Tests for complete_google_oauth."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.google_calendar.settings")
    async def test_complete_stores_encrypted_tokens(
        self, mock_gc_settings, mock_enc_settings
    ):
        """complete_google_oauth stores encrypted access and refresh tokens."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_gc_settings.GOOGLE_CLIENT_ID = "cid"
        mock_gc_settings.GOOGLE_CLIENT_SECRET = "csecret"

        mock_credentials = MagicMock()
        mock_credentials.token = "access-token-abc"
        mock_credentials.refresh_token = "refresh-token-xyz"
        mock_credentials.expiry = datetime(2026, 6, 1, tzinfo=timezone.utc)

        mock_flow_instance = MagicMock()
        mock_flow_instance.credentials = mock_credentials
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow_instance

        # Mock db: no existing connection
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import complete_google_oauth

        user = _make_user()
        connection = await complete_google_oauth(
            mock_db, user, "auth-code-123", "state-abc", "http://localhost/cb"
        )

        # Token exchange was called
        mock_flow_instance.fetch_token.assert_called_once_with(code="auth-code-123")
        # Connection was added to session
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

        # Tokens are encrypted (not plaintext)
        added_conn = mock_db.add.call_args[0][0]
        assert added_conn.access_token_enc != "access-token-abc"
        assert added_conn.refresh_token_enc != "refresh-token-xyz"
        assert added_conn.provider == "google_calendar"
        assert added_conn.status == "CONNECTED"

        # Verify they decrypt correctly
        from app.services.encryption_service import decrypt

        assert decrypt(added_conn.access_token_enc) == "access-token-abc"
        assert decrypt(added_conn.refresh_token_enc) == "refresh-token-xyz"

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.google_calendar.settings")
    async def test_complete_upserts_existing_connection(
        self, mock_gc_settings, mock_enc_settings
    ):
        """If connection already exists, update instead of insert."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_gc_settings.GOOGLE_CLIENT_ID = "cid"
        mock_gc_settings.GOOGLE_CLIENT_SECRET = "csecret"

        mock_credentials = MagicMock()
        mock_credentials.token = "new-access-token"
        mock_credentials.refresh_token = "new-refresh-token"
        mock_credentials.expiry = datetime(2026, 7, 1, tzinfo=timezone.utc)

        mock_flow_instance = MagicMock()
        mock_flow_instance.credentials = mock_credentials
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow_instance

        existing_conn = MagicMock()
        existing_conn.refresh_token_enc = "old-enc-refresh"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import complete_google_oauth

        await complete_google_oauth(
            mock_db, _make_user(), "code", "state", "http://localhost/cb"
        )

        # Should NOT add a new record
        mock_db.add.assert_not_called()
        # Should update existing
        assert existing_conn.status == "CONNECTED"
        assert existing_conn.token_expiry == mock_credentials.expiry

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.google_calendar.settings")
    async def test_complete_sets_token_expiry(
        self, mock_gc_settings, mock_enc_settings
    ):
        """Token expiry from credentials is stored on the connection."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_gc_settings.GOOGLE_CLIENT_ID = "cid"
        mock_gc_settings.GOOGLE_CLIENT_SECRET = "csecret"

        expected_expiry = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        mock_credentials = MagicMock()
        mock_credentials.token = "token"
        mock_credentials.refresh_token = "refresh"
        mock_credentials.expiry = expected_expiry

        mock_flow_instance = MagicMock()
        mock_flow_instance.credentials = mock_credentials
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow_instance

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import complete_google_oauth

        await complete_google_oauth(
            mock_db, _make_user(), "code", "state", "http://localhost/cb"
        )

        added = mock_db.add.call_args[0][0]
        assert added.token_expiry == expected_expiry


class TestGoogleCalendarDisconnect:
    """Tests for disconnect_google."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    async def test_disconnect_deletes_connection(self, mock_enc_settings):
        """disconnect_google deletes the connection record."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY

        existing_conn = MagicMock()
        existing_conn.access_token_enc = Fernet(TEST_FERNET_KEY.encode()).encrypt(
            b"token"
        ).decode()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        # Configure the sys.modules httpx mock with an async context manager
        # disconnect_google does a lazy `import httpx` which hits sys.modules
        mock_client_instance = AsyncMock()
        mock_async_cm = AsyncMock()
        mock_async_cm.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_cm.__aexit__ = AsyncMock(return_value=False)
        mock_httpx.AsyncClient.return_value = mock_async_cm

        from app.integrations.google_calendar import disconnect_google

        await disconnect_google(mock_db, _make_user())

        mock_db.delete.assert_called_once_with(existing_conn)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_raises_404_when_not_connected(self):
        """disconnect_google raises 404 if no connection found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import disconnect_google

        with pytest.raises(HTTPException) as exc_info:
            await disconnect_google(mock_db, _make_user())
        assert exc_info.value.status_code == 404
        assert "not connected" in str(exc_info.value.detail).lower()


class TestGoogleCalendarGetConnection:
    """Tests for get_google_connection."""

    @pytest.mark.asyncio
    async def test_get_connection_returns_connection(self):
        """Returns IntegrationConnection when found."""
        mock_conn = MagicMock()
        mock_conn.provider = "google_calendar"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import get_google_connection

        result = await get_google_connection(mock_db, ADMIN_USER_ID)
        assert result is mock_conn

    @pytest.mark.asyncio
    async def test_get_connection_returns_none_when_absent(self):
        """Returns None when no connection exists."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.google_calendar import get_google_connection

        result = await get_google_connection(mock_db, ADMIN_USER_ID)
        assert result is None


# ============================================================
# MICROSOFT GRAPH INTEGRATION
# ============================================================


class TestMicrosoftOAuthInitiate:
    """Tests for initiate_microsoft_oauth."""

    @pytest.mark.asyncio
    @patch("app.integrations.microsoft_graph.settings")
    async def test_initiate_returns_auth_url(self, mock_settings):
        """initiate_microsoft_oauth returns an authorization URL string."""
        mock_settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        mock_settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"

        mock_msal_app = MagicMock()
        mock_msal_app.get_authorization_request_url.return_value = (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=ms-client-id"
        )
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        from app.integrations.microsoft_graph import initiate_microsoft_oauth

        user = _make_user()
        url = await initiate_microsoft_oauth(user, "http://localhost/cb")

        assert "login.microsoftonline.com" in url
        mock_msal_app.get_authorization_request_url.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.integrations.microsoft_graph.settings")
    async def test_initiate_passes_user_id_as_state(self, mock_settings):
        """State parameter contains the user_id for validation on callback."""
        mock_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        mock_msal_app = MagicMock()
        mock_msal_app.get_authorization_request_url.return_value = "https://example.com"
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        from app.integrations.microsoft_graph import initiate_microsoft_oauth

        user = _make_user()
        await initiate_microsoft_oauth(user, "http://localhost/cb")

        call_kwargs = mock_msal_app.get_authorization_request_url.call_args
        assert call_kwargs[1]["state"] == str(user["user_id"])


class TestMicrosoftOAuthComplete:
    """Tests for complete_microsoft_oauth."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_complete_stores_encrypted_tokens(
        self, mock_ms_settings, mock_enc_settings
    ):
        """Stores encrypted access and refresh tokens on new connection."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        msal_result = {
            "access_token": "ms-access-token-123",
            "refresh_token": "ms-refresh-token-456",
            "expires_in": 3600,
        }

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_authorization_code.return_value = msal_result
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import complete_microsoft_oauth

        conn = await complete_microsoft_oauth(
            mock_db, _make_user(), "auth-code", "http://localhost/cb"
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

        added = mock_db.add.call_args[0][0]
        assert added.provider == "microsoft"
        assert added.status == "CONNECTED"

        # Tokens are encrypted
        from app.services.encryption_service import decrypt

        assert decrypt(added.access_token_enc) == "ms-access-token-123"
        assert decrypt(added.refresh_token_enc) == "ms-refresh-token-456"

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_complete_sets_token_expiry(
        self, mock_ms_settings, mock_enc_settings
    ):
        """Token expiry is computed from expires_in."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        msal_result = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_in": 7200,
        }

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_authorization_code.return_value = msal_result
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        before = datetime.now(timezone.utc)

        from app.integrations.microsoft_graph import complete_microsoft_oauth

        await complete_microsoft_oauth(
            mock_db, _make_user(), "code", "http://localhost/cb"
        )

        after = datetime.now(timezone.utc)

        added = mock_db.add.call_args[0][0]
        # Expiry should be roughly now + 7200 seconds
        assert added.token_expiry >= before + timedelta(seconds=7200)
        assert added.token_expiry <= after + timedelta(seconds=7200)

    @pytest.mark.asyncio
    @patch("app.integrations.microsoft_graph.settings")
    async def test_complete_raises_on_oauth_failure(self, mock_settings):
        """Raises HTTPException when MSAL returns error."""
        mock_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        msal_result = {
            "error": "invalid_grant",
            "error_description": "Code expired",
        }

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_authorization_code.return_value = msal_result
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        mock_db = AsyncMock()

        from app.integrations.microsoft_graph import complete_microsoft_oauth

        with pytest.raises(HTTPException) as exc_info:
            await complete_microsoft_oauth(
                mock_db, _make_user(), "bad-code", "http://localhost/cb"
            )
        assert exc_info.value.status_code == 400
        assert "Code expired" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_complete_upserts_existing_connection(
        self, mock_ms_settings, mock_enc_settings
    ):
        """Updates existing connection instead of creating new."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        msal_result = {
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        }

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_authorization_code.return_value = msal_result
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        existing_conn = MagicMock()
        existing_conn.refresh_token_enc = "old"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import complete_microsoft_oauth

        await complete_microsoft_oauth(
            mock_db, _make_user(), "code", "http://localhost/cb"
        )

        mock_db.add.assert_not_called()
        assert existing_conn.status == "CONNECTED"


class TestMicrosoftDisconnect:
    """Tests for disconnect_microsoft."""

    @pytest.mark.asyncio
    async def test_disconnect_deletes_connection(self):
        """disconnect_microsoft removes the connection from db."""
        existing_conn = MagicMock()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import disconnect_microsoft

        await disconnect_microsoft(mock_db, _make_user())

        mock_db.delete.assert_called_once_with(existing_conn)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_raises_404_when_not_connected(self):
        """disconnect_microsoft raises 404 if no connection found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import disconnect_microsoft

        with pytest.raises(HTTPException) as exc_info:
            await disconnect_microsoft(mock_db, _make_user())
        assert exc_info.value.status_code == 404
        assert "not connected" in str(exc_info.value.detail).lower()


class TestMicrosoftGetToken:
    """Tests for get_microsoft_token."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    async def test_returns_token_when_valid(self, mock_enc_settings):
        """Returns decrypted access token when not expired."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY

        from app.services.encryption_service import encrypt

        mock_conn = MagicMock()
        mock_conn.access_token_enc = encrypt("valid-access-token")
        mock_conn.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_conn.refresh_token_enc = None

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import get_microsoft_token

        token = await get_microsoft_token(mock_db, ADMIN_USER_ID)
        assert token == "valid-access-token"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_connected(self):
        """Returns None when no connection exists."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import get_microsoft_token

        token = await get_microsoft_token(mock_db, ADMIN_USER_ID)
        assert token is None

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_refreshes_expired_token(self, mock_ms_settings, mock_enc_settings):
        """When token is expired, uses refresh_token to get new access token."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        from app.services.encryption_service import encrypt

        mock_conn = MagicMock()
        mock_conn.access_token_enc = encrypt("expired-token")
        mock_conn.refresh_token_enc = encrypt("valid-refresh-token")
        mock_conn.token_expiry = datetime.now(timezone.utc) - timedelta(minutes=5)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        refresh_result = {
            "access_token": "brand-new-access-token",
            "expires_in": 3600,
        }

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_refresh_token.return_value = refresh_result
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        from app.integrations.microsoft_graph import get_microsoft_token

        token = await get_microsoft_token(mock_db, ADMIN_USER_ID)

        assert token == "brand-new-access-token"
        mock_msal_app.acquire_token_by_refresh_token.assert_called_once()
        mock_db.flush.assert_awaited()

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_refresh_failure_marks_expired(
        self, mock_ms_settings, mock_enc_settings
    ):
        """When refresh fails, connection is marked EXPIRED and returns None."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        from app.services.encryption_service import encrypt

        mock_conn = MagicMock()
        mock_conn.access_token_enc = encrypt("expired-token")
        mock_conn.refresh_token_enc = encrypt("bad-refresh")
        mock_conn.token_expiry = datetime.now(timezone.utc) - timedelta(minutes=5)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        # MSAL returns error (no access_token key)
        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_refresh_token.return_value = {
            "error": "invalid_grant"
        }
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        from app.integrations.microsoft_graph import get_microsoft_token

        token = await get_microsoft_token(mock_db, ADMIN_USER_ID)

        assert token is None
        assert mock_conn.status == "EXPIRED"

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    async def test_expired_no_refresh_token_returns_none(self, mock_enc_settings):
        """When token expired and no refresh_token, returns None."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY

        from app.services.encryption_service import encrypt

        mock_conn = MagicMock()
        mock_conn.access_token_enc = encrypt("expired")
        mock_conn.refresh_token_enc = None
        mock_conn.token_expiry = datetime.now(timezone.utc) - timedelta(hours=1)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.microsoft_graph import get_microsoft_token

        token = await get_microsoft_token(mock_db, ADMIN_USER_ID)
        assert token is None


# ============================================================
# QUICKBOOKS INTEGRATION
# ============================================================


class TestQuickBooksOAuthInitiate:
    """Tests for initiate_quickbooks_oauth."""

    @pytest.mark.asyncio
    @patch("app.integrations.quickbooks.settings")
    async def test_initiate_returns_auth_url(self, mock_settings):
        """initiate_quickbooks_oauth returns an authorization URL."""
        mock_settings.QUICKBOOKS_CLIENT_ID = "qb-client-id"
        mock_settings.QUICKBOOKS_CLIENT_SECRET = "qb-secret"
        mock_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.get_authorization_url.return_value = (
            "https://appcenter.intuit.com/connect/oauth2?client_id=qb-client-id"
        )
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        from app.integrations.quickbooks import initiate_quickbooks_oauth

        url = await initiate_quickbooks_oauth(
            _make_user(), "http://localhost/qb-callback"
        )

        assert "intuit.com" in url
        mock_auth_client.get_authorization_url.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.integrations.quickbooks.settings")
    async def test_initiate_uses_accounting_scope(self, mock_settings):
        """OAuth request includes ACCOUNTING scope."""
        mock_settings.QUICKBOOKS_CLIENT_ID = "cid"
        mock_settings.QUICKBOOKS_CLIENT_SECRET = "csecret"
        mock_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.get_authorization_url.return_value = "https://example.com"
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        from app.integrations.quickbooks import initiate_quickbooks_oauth

        await initiate_quickbooks_oauth(_make_user(), "http://localhost/cb")

        call_args = mock_auth_client.get_authorization_url.call_args
        # First positional arg is the scopes list
        scopes = call_args[0][0]
        assert len(scopes) == 1


class TestQuickBooksOAuthComplete:
    """Tests for complete_quickbooks_oauth."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.quickbooks.settings")
    async def test_complete_stores_encrypted_tokens_with_realm_id(
        self, mock_qb_settings, mock_enc_settings
    ):
        """Stores encrypted tokens and realm_id in provider_metadata."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_qb_settings.QUICKBOOKS_CLIENT_ID = "cid"
        mock_qb_settings.QUICKBOOKS_CLIENT_SECRET = "csecret"
        mock_qb_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.access_token = "qb-access-token"
        mock_auth_client.refresh_token = "qb-refresh-token"
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.quickbooks import complete_quickbooks_oauth

        conn = await complete_quickbooks_oauth(
            mock_db,
            _make_user(),
            "auth-code-qb",
            "realm-123456",
            "http://localhost/cb",
        )

        mock_auth_client.get_bearer_token.assert_called_once_with(
            "auth-code-qb", realm_id="realm-123456"
        )
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

        added = mock_db.add.call_args[0][0]
        assert added.provider == "quickbooks"
        assert added.status == "CONNECTED"
        assert added.provider_metadata == {"realm_id": "realm-123456"}

        # Tokens are encrypted
        from app.services.encryption_service import decrypt

        assert decrypt(added.access_token_enc) == "qb-access-token"
        assert decrypt(added.refresh_token_enc) == "qb-refresh-token"

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.quickbooks.settings")
    async def test_complete_sets_token_expiry(
        self, mock_qb_settings, mock_enc_settings
    ):
        """Token expiry is set to ~1 hour from now."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_qb_settings.QUICKBOOKS_CLIENT_ID = "cid"
        mock_qb_settings.QUICKBOOKS_CLIENT_SECRET = "csecret"
        mock_qb_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.access_token = "token"
        mock_auth_client.refresh_token = "refresh"
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        before = datetime.now(timezone.utc)

        from app.integrations.quickbooks import complete_quickbooks_oauth

        await complete_quickbooks_oauth(
            mock_db, _make_user(), "code", "realm", "http://localhost/cb"
        )

        after = datetime.now(timezone.utc)

        added = mock_db.add.call_args[0][0]
        assert added.token_expiry >= before + timedelta(hours=1) - timedelta(seconds=5)
        assert added.token_expiry <= after + timedelta(hours=1) + timedelta(seconds=5)

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.quickbooks.settings")
    async def test_complete_upserts_existing_connection(
        self, mock_qb_settings, mock_enc_settings
    ):
        """Updates existing QuickBooks connection instead of creating new."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_qb_settings.QUICKBOOKS_CLIENT_ID = "cid"
        mock_qb_settings.QUICKBOOKS_CLIENT_SECRET = "csecret"
        mock_qb_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.access_token = "new-token"
        mock_auth_client.refresh_token = "new-refresh"
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        existing_conn = MagicMock()
        existing_conn.refresh_token_enc = "old-enc"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.quickbooks import complete_quickbooks_oauth

        await complete_quickbooks_oauth(
            mock_db, _make_user(), "code", "realm-789", "http://localhost/cb"
        )

        mock_db.add.assert_not_called()
        assert existing_conn.status == "CONNECTED"
        assert existing_conn.provider_metadata == {"realm_id": "realm-789"}


class TestQuickBooksDisconnect:
    """Tests for disconnect_quickbooks."""

    @pytest.mark.asyncio
    async def test_disconnect_deletes_connection(self):
        """disconnect_quickbooks removes the connection record."""
        existing_conn = MagicMock()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conn
        mock_db.execute.return_value = mock_result

        from app.integrations.quickbooks import disconnect_quickbooks

        await disconnect_quickbooks(mock_db, _make_user())

        mock_db.delete.assert_called_once_with(existing_conn)
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_raises_404_when_not_connected(self):
        """disconnect_quickbooks raises 404 if no connection found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.integrations.quickbooks import disconnect_quickbooks

        with pytest.raises(HTTPException) as exc_info:
            await disconnect_quickbooks(mock_db, _make_user())
        assert exc_info.value.status_code == 404
        assert "not connected" in str(exc_info.value.detail).lower()


# ============================================================
# CROSS-CUTTING: ALL OAUTH FLOWS USE ENCRYPTION
# ============================================================


class TestOAuthFlowsUseEncryption:
    """Verify that all OAuth complete functions use encrypt() for token storage."""

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.google_calendar.settings")
    async def test_google_complete_calls_encrypt(
        self, mock_gc_settings, mock_enc_settings
    ):
        """Google OAuth complete calls encrypt for access and refresh tokens."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_gc_settings.GOOGLE_CLIENT_ID = "cid"
        mock_gc_settings.GOOGLE_CLIENT_SECRET = "csecret"

        mock_credentials = MagicMock()
        mock_credentials.token = "g-access"
        mock_credentials.refresh_token = "g-refresh"
        mock_credentials.expiry = datetime(2026, 6, 1, tzinfo=timezone.utc)

        mock_flow = MagicMock()
        mock_flow.credentials = mock_credentials
        mock_gao_flow.Flow.from_client_config.return_value = mock_flow

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.services.encryption_service import encrypt as real_encrypt

        with patch(
            "app.integrations.google_calendar.encrypt",
            wraps=real_encrypt,
        ) as mock_encrypt:
            from app.integrations.google_calendar import complete_google_oauth

            await complete_google_oauth(
                mock_db, _make_user(), "code", "state", "http://localhost/cb"
            )

            # encrypt was called for both tokens
            encrypt_calls = [c[0][0] for c in mock_encrypt.call_args_list]
            assert "g-access" in encrypt_calls
            assert "g-refresh" in encrypt_calls

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.microsoft_graph.settings")
    async def test_microsoft_complete_calls_encrypt(
        self, mock_ms_settings, mock_enc_settings
    ):
        """Microsoft OAuth complete calls encrypt for tokens."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_ms_settings.MICROSOFT_CLIENT_ID = "cid"
        mock_ms_settings.MICROSOFT_CLIENT_SECRET = "csecret"

        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_by_authorization_code.return_value = {
            "access_token": "ms-access",
            "refresh_token": "ms-refresh",
            "expires_in": 3600,
        }
        mock_msal_module.ConfidentialClientApplication.return_value = mock_msal_app

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.services.encryption_service import encrypt as real_encrypt

        with patch(
            "app.integrations.microsoft_graph.encrypt",
            wraps=real_encrypt,
        ) as mock_encrypt:
            from app.integrations.microsoft_graph import complete_microsoft_oauth

            await complete_microsoft_oauth(
                mock_db, _make_user(), "code", "http://localhost/cb"
            )

            encrypt_calls = [c[0][0] for c in mock_encrypt.call_args_list]
            assert "ms-access" in encrypt_calls
            assert "ms-refresh" in encrypt_calls

    @pytest.mark.asyncio
    @patch("app.services.encryption_service.settings")
    @patch("app.integrations.quickbooks.settings")
    async def test_quickbooks_complete_calls_encrypt(
        self, mock_qb_settings, mock_enc_settings
    ):
        """QuickBooks OAuth complete calls encrypt for tokens."""
        mock_enc_settings.ENCRYPTION_KEY = TEST_FERNET_KEY
        mock_qb_settings.QUICKBOOKS_CLIENT_ID = "cid"
        mock_qb_settings.QUICKBOOKS_CLIENT_SECRET = "csecret"
        mock_qb_settings.QUICKBOOKS_ENVIRONMENT = "sandbox"

        mock_auth_client = MagicMock()
        mock_auth_client.access_token = "qb-access"
        mock_auth_client.refresh_token = "qb-refresh"
        mock_intuitlib_client.AuthClient.return_value = mock_auth_client

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.services.encryption_service import encrypt as real_encrypt

        with patch(
            "app.integrations.quickbooks.encrypt",
            wraps=real_encrypt,
        ) as mock_encrypt:
            from app.integrations.quickbooks import complete_quickbooks_oauth

            await complete_quickbooks_oauth(
                mock_db, _make_user(), "code", "realm", "http://localhost/cb"
            )

            encrypt_calls = [c[0][0] for c in mock_encrypt.call_args_list]
            assert "qb-access" in encrypt_calls
            assert "qb-refresh" in encrypt_calls
