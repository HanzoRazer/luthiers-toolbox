"""
AI Availability Tests
Verifies that AI endpoints return 503 when API keys are not configured.

Tests the behavior defined in PHASE1_BUNDLE_02__OPTIONAL_AI_DEP:
- Server boots normally without ANTHROPIC_API_KEY
- AI endpoints return HTTP 503 with AI_DISABLED error
- Non-AI endpoints remain fully functional
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


class TestAiAvailabilityGate:
    """Tests for app.ai.availability module."""

    def test_is_ai_available_returns_false_when_key_missing(self, monkeypatch):
        """is_ai_available() returns False when ANTHROPIC_API_KEY not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        from app.ai.availability import is_ai_available
        
        assert is_ai_available(provider="anthropic") is False

    def test_is_ai_available_returns_true_when_key_set(self, monkeypatch):
        """is_ai_available() returns True when ANTHROPIC_API_KEY is set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-12345")
        
        from app.ai.availability import is_ai_available
        
        assert is_ai_available(provider="anthropic") is True

    def test_require_anthropic_available_raises_503_when_key_missing(self, monkeypatch):
        """require_anthropic_available() raises HTTP 503 when key missing."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        from fastapi import HTTPException
        from app.ai.availability import require_anthropic_available
        
        with pytest.raises(HTTPException) as exc_info:
            require_anthropic_available(feature="Test Feature")
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["error"] == "AI_DISABLED"
        assert "ANTHROPIC_API_KEY" in exc_info.value.detail["message"]

    def test_require_anthropic_available_passes_when_key_set(self, monkeypatch):
        """require_anthropic_available() does not raise when key is set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-12345")
        
        from app.ai.availability import require_anthropic_available
        
        # Should not raise
        require_anthropic_available(feature="Test Feature")

    def test_get_ai_status_shows_anthropic_disabled_when_key_missing(self, monkeypatch):
        """get_ai_status() shows anthropic disabled when no API key configured."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        from app.ai.availability import get_ai_status
        
        status = get_ai_status()
        
        # Anthropic and OpenAI should be disabled
        assert status["providers"]["anthropic"] is False
        assert status["providers"]["openai"] is False
        # Note: "local" may still be available (Ollama fallback to localhost)

    def test_get_ai_status_shows_available_when_key_set(self, monkeypatch):
        """get_ai_status() reports available when API key configured."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-12345")
        
        from app.ai.availability import get_ai_status
        
        status = get_ai_status()
        
        assert status["status"] == "available"
        assert status["providers"]["anthropic"] is True


class TestAiEndpoint503Behavior:
    """Tests that AI endpoints return 503 when keys missing."""

    @pytest.fixture
    def client_without_key(self, monkeypatch):
        """Create test client with ANTHROPIC_API_KEY unset."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        from fastapi.testclient import TestClient
        from app.main import app
        
        return TestClient(app, raise_server_exceptions=False)

    def test_ai_health_returns_200_with_disabled_status(self, client_without_key):
        """
        GET /api/rmos/ai/health returns 200 even when AI disabled.
        
        Health endpoints should always return 200 so monitoring can scrape them.
        The status field indicates operational state.
        """
        resp = client_without_key.get("/api/rmos/ai/health")
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "disabled"
        assert data["ai"]["providers"]["anthropic"] is False

    def test_constraint_search_returns_503_when_key_missing(self, client_without_key):
        """
        POST /api/rmos/ai/constraint-search returns 503 when ANTHROPIC_API_KEY missing.
        """
        resp = client_without_key.post(
            "/api/rmos/ai/constraint-search",
            json={
                "workflow_mode": "constraint_first",
                "context": {"tool_id": "T1", "material_id": "M1"},
            },
        )
        
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["error"] == "AI_DISABLED"
        assert "ANTHROPIC_API_KEY" in data["detail"]["message"]

    def test_quick_check_returns_503_when_key_missing(self, client_without_key):
        """
        POST /api/rmos/ai/quick-check returns 503 when ANTHROPIC_API_KEY missing.
        """
        resp = client_without_key.post(
            "/api/rmos/ai/quick-check",
            json={
                "workflow_mode": "constraint_first",
                "context": {"tool_id": "T1", "material_id": "M1"},
            },
        )
        
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["error"] == "AI_DISABLED"

    def test_non_ai_endpoint_still_works_without_key(self, client_without_key):
        """
        Non-AI endpoints work normally even when ANTHROPIC_API_KEY missing.
        
        This verifies the app boots and serves requests without AI keys.
        """
        resp = client_without_key.get("/health")
        
        assert resp.status_code == 200


class TestServerBootsWithoutKey:
    """Tests that the server boots successfully without API keys."""

    def test_app_imports_without_anthropic_key(self, monkeypatch):
        """
        app.main imports successfully without ANTHROPIC_API_KEY.
        
        This is the key test - verifies no import-time crashes.
        """
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        # This should not raise
        from app.main import app
        
        assert app is not None

    def test_ai_availability_module_imports_cleanly(self):
        """
        app.ai.availability imports without any env vars.
        
        Verifies no import-time env var access that could crash.
        """
        # This should not raise
        from app.ai.availability import (
            is_ai_available,
            require_anthropic_available,
            get_ai_status,
        )
        
        assert callable(is_ai_available)
        assert callable(require_anthropic_available)
        assert callable(get_ai_status)
