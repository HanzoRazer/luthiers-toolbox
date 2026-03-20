"""Smoke tests for Art Studio Relief and VCarve preview endpoints (WIRE-002).

Tests verify that preview_consolidated_router is wired at /api/art-studio.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# =============================================================================
# WIRE-002: Endpoint Routing Smoke Tests
# =============================================================================

class TestReliefVCarveEndpointSmoke:
    """Verify Relief and VCarve preview endpoints are routed (not 404)."""

    def test_relief_preview_endpoint_exists(self, client: TestClient):
        """POST /api/art-studio/relief/preview should be routed (200 or 422, not 404)."""
        response = client.post("/api/art-studio/relief/preview", json={})
        assert response.status_code != 404, (
            f"Relief preview endpoint returned 404 - router not wired. "
            f"Got: {response.status_code}"
        )
        # 200 = success, 422 = validation error (expected with empty body)
        assert response.status_code in (200, 422), (
            f"Unexpected status code: {response.status_code}"
        )

    def test_vcarve_preview_endpoint_exists(self, client: TestClient):
        """POST /api/art-studio/vcarve/preview should be routed (200 or 422, not 404)."""
        response = client.post("/api/art-studio/vcarve/preview", json={})
        assert response.status_code != 404, (
            f"VCarve preview endpoint returned 404 - router not wired. "
            f"Got: {response.status_code}"
        )
        # 200 = success, 422 = validation error (expected with empty body)
        assert response.status_code in (200, 422), (
            f"Unexpected status code: {response.status_code}"
        )
