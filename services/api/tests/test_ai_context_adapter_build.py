"""
AI Context Adapter Build Endpoint Tests

Tests for POST /api/ai/context/build with hard boundary rules.

Key test requirements:
1. Endpoint returns bounded context bundle
2. Hard boundary gate blocks manufacturing secrets
3. Unknown includes are ignored with warning
4. Feature flag can disable endpoint
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create minimal app with AI context adapter."""
    from fastapi import FastAPI
    from app.ai_context_adapter.routes import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


# =============================================================================
# Unit Tests - Boundary Gate
# =============================================================================

class TestBoundaryGate:
    """Tests for the manufacturing secrets boundary gate."""

    def test_forbidden_key_detection(self):
        """Forbidden keys are detected in context."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        # Direct forbidden key
        violations = _contains_forbidden_content({"toolpaths": [1, 2, 3]})
        assert len(violations) == 1
        assert "toolpaths" in violations[0]

    def test_nested_forbidden_key(self):
        """Forbidden keys detected in nested structures."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        violations = _contains_forbidden_content({
            "safe_key": {
                "gcode_text": "G21\nG90\n..."
            }
        })
        assert len(violations) >= 1

    def test_gcode_pattern_detection(self):
        """G-code patterns detected in string values."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        # G-code command pattern
        violations = _contains_forbidden_content({
            "note": "Use G01 X10 Y20 for cutting"
        })
        assert len(violations) >= 1

    def test_safe_content_passes(self):
        """Safe content has no violations."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        safe_context = {
            "run_summary": {"status": "ok", "run_id": "run_123"},
            "design_intent": {"domain": "rosette", "summary": "8-ring design"},
            "user_notes": "Please analyze this pattern",
        }
        violations = _contains_forbidden_content(safe_context)
        assert len(violations) == 0

    def test_enforce_boundary_gate_raises(self):
        """Boundary gate raises HTTPException on violations."""
        from app.ai_context_adapter.routes import enforce_boundary_gate
        from fastapi import HTTPException

        bad_context = {"toolpaths": []}
        with pytest.raises(HTTPException) as exc_info:
            enforce_boundary_gate(bad_context)
        assert exc_info.value.status_code == 500
        assert "boundary_violation" in str(exc_info.value.detail)


# =============================================================================
# Integration Tests - Build Endpoint
# =============================================================================

@pytest.mark.integration
@pytest.mark.allow_missing_request_id
class TestBuildEndpoint:
    """Integration tests for POST /api/ai/context/build."""

    def test_build_returns_schema(self, client):
        """Build endpoint returns valid schema."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "include": ["governance_notes"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify schema structure
        assert data["schema_id"] == "toolbox_ai_context"
        assert data["schema_version"] == "v1"
        assert "context_id" in data
        assert "summary" in data
        assert "context" in data
        assert "warnings" in data

    def test_build_with_user_notes(self, client):
        """User notes are included in context."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "user_notes": "Please help me understand this pattern",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["context"].get("user_notes") == "Please help me understand this pattern"

    def test_build_unknown_includes_warned(self, client):
        """Unknown includes generate warnings."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "include": ["governance_notes", "unknown_thing", "secret_data"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should have warning about unknown includes
        assert any("unknown" in w.lower() for w in data["warnings"])

    def test_build_governance_notes(self, client):
        """Governance notes include works."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "include": ["governance_notes"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "governance_notes" in data["context"]
        assert data["context"]["governance_notes"]["status"] == "ok"

    def test_build_includes_meta(self, client):
        """Context includes _meta section."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test123",
                "pattern_id": "pat_abc",
                "include": [],
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "_meta" in data["context"]
        assert data["context"]["_meta"]["run_id"] == "run_test123"
        assert data["context"]["_meta"]["pattern_id"] == "pat_abc"

    def test_build_secrets_warning(self, client):
        """Response includes manufacturing secrets warning."""
        response = client.post(
            "/api/ai/context/build",
            json={},
        )
        assert response.status_code == 200
        data = response.json()

        # Should have warning about secrets being excluded
        assert any("secrets" in w.lower() or "toolpath" in w.lower() for w in data["warnings"])


# =============================================================================
# Health Check Tests
# =============================================================================

@pytest.mark.allow_missing_request_id
class TestHealthEndpoint:
    """Tests for GET /api/ai/context/health."""

    def test_health_returns_ok(self, client):
        """Health endpoint returns ok status."""
        response = client.get("/api/ai/context/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["schema_version"] == "v1"
