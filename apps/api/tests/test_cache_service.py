"""Tests for cache service."""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache_service import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    invalidate_org_cache,
    invalidate_project_cache,
    org_key,
    project_key,
    user_key,
)
from tests.conftest import ORG_ID, PROJECT_ID, ADMIN_USER_ID


# ============================================================
# HELPERS
# ============================================================

def _make_mock_redis():
    """Create a mock async Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    return redis


# ============================================================
# cache_get
# ============================================================

class TestCacheGet:
    @pytest.mark.asyncio
    async def test_returns_none_when_redis_unavailable(self):
        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await cache_get("some:key")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_cache_miss(self):
        mock_redis = _make_mock_redis()
        mock_redis.get.return_value = None

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("nonexistent:key")
            assert result is None
            mock_redis.get.assert_awaited_once_with("nonexistent:key")

    @pytest.mark.asyncio
    async def test_returns_cached_dict(self):
        mock_redis = _make_mock_redis()
        cached_data = {"name": "Test Project", "phase": "ACTIVE"}
        mock_redis.get.return_value = json.dumps(cached_data)

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("project:123:detail")
            assert result == cached_data
            assert result["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_returns_cached_list(self):
        mock_redis = _make_mock_redis()
        cached_data = [1, 2, 3, "four"]
        mock_redis.get.return_value = json.dumps(cached_data)

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("project:123:list")
            assert result == cached_data

    @pytest.mark.asyncio
    async def test_returns_cached_string(self):
        mock_redis = _make_mock_redis()
        mock_redis.get.return_value = json.dumps("hello")

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("some:key")
            assert result == "hello"

    @pytest.mark.asyncio
    async def test_handles_json_decode_error_gracefully(self):
        mock_redis = _make_mock_redis()
        mock_redis.get.return_value = "not-valid-json{{{"

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("corrupt:key")
            # Should return None rather than raising
            assert result is None

    @pytest.mark.asyncio
    async def test_handles_redis_exception(self):
        mock_redis = _make_mock_redis()
        mock_redis.get.side_effect = Exception("Connection refused")

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_get("some:key")
            assert result is None


# ============================================================
# cache_set
# ============================================================

class TestCacheSet:
    @pytest.mark.asyncio
    async def test_returns_false_when_redis_unavailable(self):
        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await cache_set("some:key", {"data": "value"})
            assert result is False

    @pytest.mark.asyncio
    async def test_stores_value_with_default_ttl(self):
        mock_redis = _make_mock_redis()

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_set("project:123:detail", {"name": "Test"})
            assert result is True
            mock_redis.set.assert_awaited_once()
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "project:123:detail"
            # Verify data is JSON-serialized
            stored_data = json.loads(call_args[0][1])
            assert stored_data["name"] == "Test"
            # Default TTL is 300 seconds
            assert call_args[1]["ex"] == 300

    @pytest.mark.asyncio
    async def test_stores_value_with_custom_ttl(self):
        mock_redis = _make_mock_redis()

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_set("key", "value", ttl=60)
            assert result is True
            call_args = mock_redis.set.call_args
            assert call_args[1]["ex"] == 60

    @pytest.mark.asyncio
    async def test_serializes_datetime_via_default_str(self):
        mock_redis = _make_mock_redis()
        dt = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_set("key", {"created_at": dt})
            assert result is True
            call_args = mock_redis.set.call_args
            stored = json.loads(call_args[0][1])
            # datetime should be serialized to string
            assert "2026" in stored["created_at"]

    @pytest.mark.asyncio
    async def test_serializes_uuid_via_default_str(self):
        mock_redis = _make_mock_redis()
        test_uuid = uuid.uuid4()

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_set("key", {"id": test_uuid})
            assert result is True
            call_args = mock_redis.set.call_args
            stored = json.loads(call_args[0][1])
            assert stored["id"] == str(test_uuid)

    @pytest.mark.asyncio
    async def test_handles_redis_exception(self):
        mock_redis = _make_mock_redis()
        mock_redis.set.side_effect = Exception("Connection lost")

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_set("key", "value")
            assert result is False


# ============================================================
# cache_delete
# ============================================================

class TestCacheDelete:
    @pytest.mark.asyncio
    async def test_returns_false_when_redis_unavailable(self):
        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await cache_delete("some:key")
            assert result is False

    @pytest.mark.asyncio
    async def test_deletes_key(self):
        mock_redis = _make_mock_redis()

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_delete("project:123:detail")
            assert result is True
            mock_redis.delete.assert_awaited_once_with("project:123:detail")

    @pytest.mark.asyncio
    async def test_handles_redis_exception(self):
        mock_redis = _make_mock_redis()
        mock_redis.delete.side_effect = Exception("Redis down")

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_delete("some:key")
            assert result is False


# ============================================================
# cache_delete_pattern
# ============================================================

class TestCacheDeletePattern:
    @pytest.mark.asyncio
    async def test_returns_zero_when_redis_unavailable(self):
        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=None):
            result = await cache_delete_pattern("project:*")
            assert result == 0

    @pytest.mark.asyncio
    async def test_deletes_matching_keys(self):
        mock_redis = _make_mock_redis()

        # Mock scan_iter to return matching keys
        async def mock_scan_iter(match=None):
            for key in ["project:123:rfis", "project:123:submittals", "project:123:detail"]:
                yield key

        mock_redis.scan_iter = mock_scan_iter

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_delete_pattern("project:123:*")
            assert result == 3
            mock_redis.delete.assert_awaited_once_with(
                "project:123:rfis",
                "project:123:submittals",
                "project:123:detail",
            )

    @pytest.mark.asyncio
    async def test_no_matching_keys(self):
        mock_redis = _make_mock_redis()

        async def mock_scan_iter(match=None):
            return
            yield  # make it an async generator

        mock_redis.scan_iter = mock_scan_iter

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_delete_pattern("nonexistent:*")
            assert result == 0
            mock_redis.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handles_redis_exception(self):
        mock_redis = _make_mock_redis()

        async def mock_scan_iter(match=None):
            raise Exception("Scan error")
            yield  # make it an async generator

        mock_redis.scan_iter = mock_scan_iter

        with patch("app.services.cache_service._get_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await cache_delete_pattern("bad:*")
            assert result == 0


# ============================================================
# Key builders
# ============================================================

class TestKeyBuilders:
    def test_project_key_with_tool(self):
        key = project_key("abc-123", "rfis")
        assert key == "project:abc-123:rfis"

    def test_project_key_with_suffix(self):
        key = project_key("abc-123", "rfis", suffix="page-1")
        assert key == "project:abc-123:rfis:page-1"

    def test_project_key_without_suffix(self):
        key = project_key("abc-123", "budget")
        assert key == "project:abc-123:budget"

    def test_org_key(self):
        key = org_key("org-456", "overview")
        assert key == "org:org-456:overview"

    def test_user_key(self):
        key = user_key("user-789", "notifications")
        assert key == "user:user-789:notifications"

    def test_project_key_with_uuid(self):
        pid = uuid.uuid4()
        key = project_key(pid, "submittals")
        assert key == f"project:{pid}:submittals"

    def test_org_key_with_uuid(self):
        oid = uuid.uuid4()
        key = org_key(oid, "stats")
        assert key == f"org:{oid}:stats"


# ============================================================
# invalidate_project_cache / invalidate_org_cache
# ============================================================

class TestInvalidateCache:
    @pytest.mark.asyncio
    async def test_invalidate_project_cache(self):
        with patch("app.services.cache_service.cache_delete_pattern", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = 5
            await invalidate_project_cache("project-123")
            mock_delete.assert_awaited_once_with("project:project-123:*")

    @pytest.mark.asyncio
    async def test_invalidate_org_cache(self):
        with patch("app.services.cache_service.cache_delete_pattern", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = 3
            await invalidate_org_cache("org-456")
            mock_delete.assert_awaited_once_with("org:org-456:*")

    @pytest.mark.asyncio
    async def test_invalidate_project_with_uuid(self):
        pid = str(uuid.uuid4())
        with patch("app.services.cache_service.cache_delete_pattern", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = 2
            await invalidate_project_cache(pid)
            mock_delete.assert_awaited_once_with(f"project:{pid}:*")

    @pytest.mark.asyncio
    async def test_invalidate_org_with_uuid(self):
        oid = str(uuid.uuid4())
        with patch("app.services.cache_service.cache_delete_pattern", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = 0
            await invalidate_org_cache(oid)
            mock_delete.assert_awaited_once_with(f"org:{oid}:*")


# ============================================================
# _get_redis initialization
# ============================================================

class TestGetRedis:
    @pytest.mark.asyncio
    async def test_handles_import_error_gracefully(self):
        """If redis.asyncio is not installed, caching should be disabled."""
        import app.services.cache_service as cs
        original_client = cs._redis_client

        try:
            cs._redis_client = None

            with patch("builtins.__import__", side_effect=ImportError("No module redis")):
                # Reset to force re-init
                result = await cs._get_redis()
                # Should not raise, returns None
                assert result is None
        finally:
            cs._redis_client = original_client

    @pytest.mark.asyncio
    async def test_returns_existing_client_on_subsequent_calls(self):
        """Once initialized, _get_redis should return the same client."""
        import app.services.cache_service as cs
        original_client = cs._redis_client

        try:
            mock_redis = _make_mock_redis()
            cs._redis_client = mock_redis

            result = await cs._get_redis()
            assert result is mock_redis
        finally:
            cs._redis_client = original_client
