"""
Test: Blueprint AI disabled returns 503

Verifies PHASE1_BUNDLE_02 contract:
- Server boots without ANTHROPIC_API_KEY / EMERGENT_LLM_KEY
- /api/blueprint/analyze returns 503 AI_DISABLED when no key set
- Phase 2 (vectorize) still works (no AI required)
"""
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client_no_ai_keys():
    """Create test client with AI keys cleared."""
    # Clear AI keys from environment
    env_patch = {
        "EMERGENT_LLM_KEY": "",
        "ANTHROPIC_API_KEY": "",
    }
    with patch.dict(os.environ, env_patch, clear=False):
        # Import after patching to get fresh state
        from app.main import app
        yield TestClient(app)


class TestBlueprintAIDisabled:
    """Tests for Blueprint AI disabled behavior (H1 optional AI)."""

    def test_analyze_returns_503_when_no_api_key(self, client_no_ai_keys):
        """POST /blueprint/analyze returns 503 AI_DISABLED without API key."""
        # Create minimal valid PNG (1x1 red pixel)
        import io
        from PIL import Image
        
        img = Image.new("RGB", (1, 1), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        response = client_no_ai_keys.post(
            "/api/blueprint/analyze",
            files={"file": ("test.png", buf, "image/png")},
        )
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["error"] == "AI_DISABLED"
        assert "API key" in data["detail"]["message"]

    def test_server_boots_without_api_key(self, client_no_ai_keys):
        """Server imports and health check works without AI keys."""
        # If we got here, server booted successfully
        response = client_no_ai_keys.get("/health")
        assert response.status_code == 200

    def test_blueprint_health_returns_degraded_without_ai(self, client_no_ai_keys):
        """GET /blueprint/health returns status but AI shows degraded."""
        response = client_no_ai_keys.get("/api/blueprint/health")
        # Health endpoint should still work (200), just report degraded AI
        assert response.status_code == 200


class TestBlueprintPhase2StillWorks:
    """Verify Phase 2 (vectorize) works without AI keys."""

    def test_vectorize_geometry_available_without_ai(self, client_no_ai_keys):
        """Phase 2 vectorization doesn't require AI keys."""
        # Just check the endpoint exists and accepts requests
        # (actual vectorization needs valid image, but 400 != 503)
        import io
        from PIL import Image
        
        img = Image.new("RGB", (100, 100), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        response = client_no_ai_keys.post(
            "/api/blueprint/vectorize-geometry",
            files={"file": ("test.png", buf, "image/png")},
        )
        
        # Should not be 503 AI_DISABLED - vectorize is local compute
        assert response.status_code != 503


class TestImportSafety:
    """Verify import-time safety (no crashes on missing deps)."""

    def test_blueprint_router_imports_without_crash(self):
        """Blueprint router can be imported even if analyzer deps missing."""
        # This test passes if the import doesn't raise
        from app.routers import blueprint_router
        
        # Check the availability flags exist
        assert hasattr(blueprint_router, "ANALYZER_AVAILABLE")
        assert hasattr(blueprint_router, "ANALYZER_IMPORT_ERROR")
