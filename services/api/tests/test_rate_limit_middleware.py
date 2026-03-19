# tests/test_rate_limit_middleware.py
"""
Rate Limiting Middleware Tests

Tests for API rate limiting using slowapi.
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


class TestRateLimitModule:
    """Test rate limit module configuration and helpers."""

    def test_rate_limit_tiers_defined(self):
        """Verify all expected rate limit tiers are defined."""
        from app.middleware.rate_limit import RATE_LIMITS

        expected_tiers = [
            "default",
            "public",
            "authenticated",
            "pro",
            "ai",
            "cam",
            "upload",
            "export",
            "health",
        ]

        for tier in expected_tiers:
            assert tier in RATE_LIMITS, f"Missing rate limit tier: {tier}"

    def test_rate_limit_tier_helper(self):
        """Test rate_limit_tier helper returns correct values."""
        from app.middleware.rate_limit import rate_limit_tier, RATE_LIMITS

        # Valid tier
        assert rate_limit_tier("ai") == RATE_LIMITS["ai"]
        assert rate_limit_tier("cam") == RATE_LIMITS["cam"]

        # Unknown tier falls back to default
        assert rate_limit_tier("unknown_tier") == RATE_LIMITS["default"]

    def test_get_client_key_unauthenticated(self):
        """Test client key generation for unauthenticated requests."""
        from app.middleware.rate_limit import get_client_key

        # Mock request without auth
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"

        key = get_client_key(mock_request)
        assert key.startswith("ip:")

    def test_get_client_key_authenticated(self):
        """Test client key generation for authenticated requests."""
        from app.middleware.rate_limit import get_client_key

        # Mock request with auth
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = "user_12345"
        mock_request.headers = {}

        key = get_client_key(mock_request)
        assert key == "user:user_12345"

    def test_get_client_key_api_key(self):
        """Test client key generation for API key requests."""
        from app.middleware.rate_limit import get_client_key

        # Mock request with API key
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        mock_request.headers = {"X-API-Key": "sk_test_abcd1234efgh5678"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"

        key = get_client_key(mock_request)
        assert key == "apikey:sk_test_"

    def test_exempt_paths(self):
        """Test rate limit exemption for health/docs endpoints."""
        from app.middleware.rate_limit import should_exempt, EXEMPT_PATHS

        # Mock requests for exempt paths
        for path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            mock_request = MagicMock(spec=Request)
            mock_request.url = MagicMock()
            mock_request.url.path = path
            assert should_exempt(mock_request), f"{path} should be exempt"

        # Non-exempt path
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/cam/gcode"
        assert not should_exempt(mock_request), "/api/cam/gcode should not be exempt"


class TestRateLimitIntegration:
    """Integration tests for rate limiting."""

    def test_limiter_is_enabled_by_default(self):
        """Verify rate limiter is enabled by default."""
        from app.middleware.rate_limit import limiter, RATE_LIMIT_ENABLED

        # Should be enabled unless RATE_LIMIT_ENABLED=0
        assert limiter is not None
        # Default is enabled
        assert RATE_LIMIT_ENABLED is True

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_response_format(self):
        """Test rate limit exceeded handler returns proper format."""
        from app.middleware.rate_limit import rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = MagicMock()
        mock_request.state.user_id = None
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # slowapi RateLimitExceeded(limit) expects a Limit with .error_message
        mock_limit = MagicMock()
        mock_limit.error_message = "10 per minute"
        exc = RateLimitExceeded(mock_limit)

        response = await rate_limit_exceeded_handler(mock_request, exc)

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers

    def test_dynamic_rate_limit_unauthenticated(self):
        """Test dynamic rate limit returns public tier for unauthenticated."""
        from app.middleware.rate_limit import dynamic_rate_limit, RATE_LIMITS

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = None

        limit = dynamic_rate_limit(mock_request)
        assert limit == RATE_LIMITS["public"]

    def test_dynamic_rate_limit_authenticated_free(self):
        """Test dynamic rate limit returns authenticated tier for free users."""
        from app.middleware.rate_limit import dynamic_rate_limit, RATE_LIMITS

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = "user_123"
        mock_request.state.tier = "free"

        limit = dynamic_rate_limit(mock_request)
        assert limit == RATE_LIMITS["authenticated"]

    def test_dynamic_rate_limit_authenticated_pro(self):
        """Test dynamic rate limit returns pro tier for pro users."""
        from app.middleware.rate_limit import dynamic_rate_limit, RATE_LIMITS

        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user_id = "user_456"
        mock_request.state.tier = "pro"

        limit = dynamic_rate_limit(mock_request)
        assert limit == RATE_LIMITS["pro"]
