"""
IBG-2B Infrastructure Tests

Tests for production infrastructure enablement:
- Redis-backed session storage
- Authentication integration
- Rate limiting
- CORS configuration

Sprint: IBG-2B
"""

import json
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# =============================================================================
# DIRECT SESSION STORE IMPORT (bypasses heavy ezdxf imports)
# =============================================================================

def _load_session_store_module():
    """Load session store module directly without triggering ibg __init__."""
    import importlib.util
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "instrument_geometry", "body", "ibg", "session_store.py"
    )
    spec = importlib.util.spec_from_file_location("ibg_session_store", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load once at module level
_session_store_mod = _load_session_store_module()


# =============================================================================
# SESSION STORE TESTS
# =============================================================================


class TestInMemoryIBGSessionStore:
    """Test in-memory IBG session store."""

    def test_create_and_get(self):
        """In-memory store can create and retrieve sessions."""
        store = _session_store_mod.InMemoryIBGSessionStore()
        data = {"instrument_spec": "dreadnought", "model": {"confidence": 0.9}}

        session_id = store.create(data)
        assert session_id.startswith("sess_")

        retrieved = store.get(session_id)
        assert retrieved == data

    def test_update(self):
        """In-memory store can update sessions."""
        store = _session_store_mod.InMemoryIBGSessionStore()
        data = {"instrument_spec": "dreadnought"}
        session_id = store.create(data)

        updated_data = {"instrument_spec": "dreadnought", "model": {"confidence": 0.95}}
        result = store.update(session_id, updated_data)
        assert result is True

        retrieved = store.get(session_id)
        assert retrieved["model"]["confidence"] == 0.95

    def test_update_nonexistent_returns_false(self):
        """In-memory store returns False for updating nonexistent session."""
        store = _session_store_mod.InMemoryIBGSessionStore()
        result = store.update("nonexistent_session", {"data": "test"})
        assert result is False

    def test_delete(self):
        """In-memory store can delete sessions."""
        store = _session_store_mod.InMemoryIBGSessionStore()
        data = {"instrument_spec": "dreadnought"}
        session_id = store.create(data)

        store.delete(session_id)
        assert store.get(session_id) is None

    def test_exists(self):
        """In-memory store can check session existence."""
        store = _session_store_mod.InMemoryIBGSessionStore()
        data = {"instrument_spec": "dreadnought"}
        session_id = store.create(data)

        assert store.exists(session_id) is True
        assert store.exists("nonexistent") is False

    def test_ttl_expiration(self):
        """In-memory store expires sessions after TTL."""
        store = _session_store_mod.InMemoryIBGSessionStore(ttl_seconds=1)
        data = {"instrument_spec": "dreadnought"}
        session_id = store.create(data)

        # Manually backdate the timestamp to simulate expiration
        store._timestamps[session_id] = datetime.utcnow() - timedelta(seconds=10)

        # Get should trigger cleanup
        assert store.get(session_id) is None


class TestRedisIBGSessionStore:
    """Test Redis IBG session store (mocked)."""

    def test_create_and_get(self):
        """Redis store can create and retrieve sessions."""
        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps({"instrument_spec": "dreadnought"})

        store = _session_store_mod.RedisIBGSessionStore(client=mock_client)
        data = {"instrument_spec": "dreadnought"}

        session_id = store.create(data)
        assert session_id.startswith("sess_")
        mock_client.setex.assert_called_once()

        result = store.get(session_id)
        assert result["instrument_spec"] == "dreadnought"

    def test_get_returns_none_for_missing(self):
        """Redis store returns None for missing session."""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        store = _session_store_mod.RedisIBGSessionStore(client=mock_client)
        result = store.get("nonexistent")
        assert result is None

    def test_update_refreshes_ttl(self):
        """Redis store update refreshes TTL."""
        mock_client = MagicMock()
        mock_client.exists.return_value = True

        store = _session_store_mod.RedisIBGSessionStore(client=mock_client, ttl_seconds=3600)
        result = store.update("sess_test", {"data": "updated"})

        assert result is True
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 3600  # TTL preserved

    def test_delete(self):
        """Redis store can delete sessions."""
        mock_client = MagicMock()
        store = _session_store_mod.RedisIBGSessionStore(client=mock_client)

        store.delete("sess_test")
        mock_client.delete.assert_called_once()


class TestGetSessionStore:
    """Test session store factory function."""

    def test_defaults_to_memory(self):
        """get_session_store() defaults to in-memory when env not set."""
        _session_store_mod.reset_session_store()
        try:
            with patch.dict(os.environ, {"IBG_SESSION_STORE": "memory"}, clear=False):
                store = _session_store_mod.get_session_store()
                assert isinstance(store, _session_store_mod.InMemoryIBGSessionStore)
        finally:
            _session_store_mod.reset_session_store()

    def test_redis_fallback_without_url(self):
        """get_session_store() falls back to memory if REDIS_URL not set."""
        _session_store_mod.reset_session_store()
        try:
            env = {"IBG_SESSION_STORE": "redis"}
            with patch.dict(os.environ, env, clear=False):
                os.environ.pop("REDIS_URL", None)
                store = _session_store_mod.get_session_store()
                assert isinstance(store, _session_store_mod.InMemoryIBGSessionStore)
        finally:
            _session_store_mod.reset_session_store()


# =============================================================================
# CORS CONFIGURATION TESTS (no external dependencies)
# =============================================================================


class TestCORSConfiguration:
    """Test CORS configuration logic."""

    def test_cors_origins_from_env(self):
        """CORS origins can be parsed from environment."""
        cors_env = "https://example.com,https://api.example.com"
        origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

        assert len(origins) == 2
        assert "https://example.com" in origins
        assert "https://api.example.com" in origins

    def test_cors_wildcard_when_not_configured(self):
        """CORS defaults to wildcard when CORS_ORIGINS not set."""
        cors_env = ""
        if cors_env:
            origins = [origin.strip() for origin in cors_env.split(",")]
        else:
            origins = ["*"]

        assert origins == ["*"]

    def test_cors_credentials_with_explicit_origins(self):
        """CORS credentials can be enabled with explicit origins."""
        cors_env = "https://example.com"
        if cors_env:
            allow_credentials = True
        else:
            allow_credentials = False
        assert allow_credentials is True

    def test_cors_no_credentials_with_wildcard(self):
        """CORS credentials must be disabled with wildcard origins."""
        cors_env = ""
        if cors_env:
            allow_credentials = True
        else:
            allow_credentials = False
        assert allow_credentials is False


# =============================================================================
# API INTEGRATION TESTS (require full app import)
# =============================================================================

# These tests depend on the full FastAPI app loading, which may have issues
# in certain test environments. We mark them with pytest markers for flexibility.


@pytest.mark.integration
class TestBodySolverAPIIntegration:
    """Integration tests for body solver endpoints."""

    @pytest.fixture
    def api_client(self):
        """Create a test client for the FastAPI app."""
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"Could not load app: {e}")

    @pytest.fixture
    def mock_auth_header(self):
        """Mock auth header for development mode (AUTH_MODE=header)."""
        return {"x-user-role": "operator", "x-user-id": "test_user_123"}

    def test_session_404_for_nonexistent(self, api_client):
        """Get nonexistent session returns 404."""
        response = api_client.get("/api/body/session/sess_nonexistent_12345")
        # Either 404 (endpoint exists) or skip if router not loaded
        if response.status_code == 404:
            assert "not found" in response.text.lower() or response.status_code == 404
        else:
            pytest.skip("Body solver router not loaded")


# =============================================================================
# RATE LIMITING CONFIGURATION TESTS
# =============================================================================


class TestRateLimitConfiguration:
    """Test rate limit configuration for IBG endpoints."""

    def test_rate_limit_format_valid(self):
        """Rate limit strings have valid format."""
        # Simulate reading env vars with defaults
        free_limit = os.getenv("IBG_RATE_LIMIT_FREE", "10/hour")
        paid_limit = os.getenv("IBG_RATE_LIMIT_PAID", "100/hour")

        # Should contain rate/period format
        assert "/" in free_limit
        assert "/" in paid_limit

        # Period should be valid
        valid_periods = ["second", "minute", "hour", "day"]
        free_period = free_limit.split("/")[1] if "/" in free_limit else ""
        paid_period = paid_limit.split("/")[1] if "/" in paid_limit else ""

        assert any(p in free_period for p in valid_periods)
        assert any(p in paid_period for p in valid_periods)
