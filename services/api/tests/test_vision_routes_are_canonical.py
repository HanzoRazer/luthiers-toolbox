"""
Guard test: Verify vision routes use canonical implementation.

This test ensures:
1. Canonical /api/vision/* endpoints are live and respond correctly
2. Legacy /vision/* routes are NOT mounted (return 404)
3. No _experimental.ai_graphics dependencies in the canonical path

Created as part of legacy vision cleanup (PR: stop-the-bleeding).
See: FENCE_REGISTRY.json profile "ai_sandbox_boundary"
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestCanonicalVisionRoutes:
    """Verify canonical /api/vision/* surface is live."""

    def test_api_vision_providers_returns_200(self, client):
        """GET /api/vision/providers should return 200 with providers list."""
        response = client.get("/api/vision/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_api_vision_vocabulary_returns_200(self, client):
        """GET /api/vision/vocabulary should return 200 with vocabulary dict."""
        response = client.get("/api/vision/vocabulary")
        assert response.status_code == 200
        data = response.json()
        assert "vocabulary" in data

    def test_api_vision_prompt_accepts_post(self, client):
        """POST /api/vision/prompt should accept prompt preview requests."""
        response = client.post(
            "/api/vision/prompt",
            json={"prompt": "test guitar", "style": "studio"}
        )
        # Should return 200 with engineered prompt (no AI call needed)
        assert response.status_code == 200
        data = response.json()
        assert "raw_prompt" in data
        assert "engineered_prompt" in data


class TestLegacyVisionRoutesRemoved:
    """Verify legacy /vision/* surface is NOT mounted (404)."""

    def test_legacy_vision_providers_returns_404(self, client):
        """GET /vision/providers should return 404 (legacy route removed)."""
        response = client.get("/vision/providers")
        assert response.status_code == 404

    def test_legacy_vision_generate_returns_404(self, client):
        """POST /vision/generate should return 404 (legacy route removed)."""
        response = client.post("/vision/generate", json={"prompt": "test"})
        assert response.status_code == 404

    def test_legacy_vision_health_returns_404(self, client):
        """GET /vision/health should return 404 (legacy route removed)."""
        response = client.get("/vision/health")
        assert response.status_code == 404


class TestNoExperimentalAiGraphicsImports:
    """Verify canonical vision does not import _experimental.ai_graphics."""

    def test_canonical_vision_router_imports_cleanly(self):
        """app.vision.router should import without _experimental dependencies."""
        # This will fail if _experimental.ai_graphics is still required
        from app.vision import router
        assert router.router is not None

    def test_canonical_prompt_engine_imports_cleanly(self):
        """app.vision.prompt_engine should import without _experimental dependencies."""
        from app.vision import prompt_engine
        assert hasattr(prompt_engine, "engineer_guitar_prompt")

    def test_canonical_schemas_imports_cleanly(self):
        """app.vision.schemas should import without _experimental dependencies."""
        from app.vision import schemas
        assert hasattr(schemas, "VisionGenerateRequest")
        assert hasattr(schemas, "VisionGenerateResponse")
