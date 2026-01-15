"""
AI Context Adapter Gate Tests

Tests that verify the AI context adapter enforces hard boundaries:
- No G-code / toolpaths in any response
- Schema-valid envelopes
- Redaction works correctly
- Feature flag disables the endpoint

These tests are CI gates - if they fail, shipping is blocked.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mark all tests in this module to allow missing request ID
pytestmark = pytest.mark.allow_missing_request_id


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def app():
    """Create app with AI context adapter router."""
    from app.ai_context_adapter.routes import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Test client for AI context adapter."""
    return TestClient(app)


@pytest.fixture
def schema():
    """Load the envelope schema for validation."""
    schema_path = Path(__file__).parents[2] / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"
    if not schema_path.exists():
        # Fallback to repo root
        schema_path = Path(__file__).parents[3] / "contracts" / "toolbox_ai_context_envelope_v1.schema.json"

    if not schema_path.exists():
        pytest.skip("Schema file not found")

    return json.loads(schema_path.read_text())


# =============================================================================
# Hard Boundary Tests - Manufacturing Secrets
# =============================================================================

class TestBoundaryGcode:
    """Tests that G-code is NEVER included in context."""

    def test_build_rejects_gcode_in_context(self, client):
        """POST /build must reject any attempt to include G-code."""
        # The /build endpoint should never return gcode even if we try to inject it
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test123",
                "include": ["run_summary"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify no forbidden keys in response
        context_str = json.dumps(data)
        assert "gcode" not in context_str.lower()
        assert "G0 " not in context_str  # G-code rapid
        assert "G1 " not in context_str  # G-code linear
        assert "M3 " not in context_str  # Spindle start
        assert "M5 " not in context_str  # Spindle stop

    def test_build_does_not_leak_toolpaths(self, client):
        """POST /build must never leak toolpath data in the context payload."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test456",
                "include": ["run_summary", "manufacturing_candidates"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Check the context payload specifically, not warnings/metadata
        context = data.get("context", {})
        context_str = json.dumps(context)

        # These should not appear as data keys/values (metadata mentions are OK)
        assert '"toolpath":' not in context_str.lower()
        assert '"toolpaths":' not in context_str.lower()
        assert '"trajectory":' not in context_str.lower()
        assert '"path_data":' not in context_str.lower()


class TestBoundaryToolpaths:
    """Tests that toolpaths are NEVER included in context."""

    def test_envelope_excludes_toolpaths(self, client):
        """GET /api/ai/context should never include toolpaths."""
        # This will 404 for missing run, but we're testing the mechanism
        response = client.get("/api/ai/context?run_id=run_nonexistent")

        # Even a 404 response body should not leak toolpaths
        body = response.text
        assert "toolpath" not in body.lower()

    def test_redactor_removes_toolpath_keys(self):
        """Redactor must remove toolpath-related keys."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        dirty = {
            "schema_id": "test",
            "toolpaths": [{"x": 0, "y": 0}],
            "toolpath_data": {"segments": []},
            "safe_data": {"value": 42},
        }

        result = redact_strict(dirty)

        assert "toolpaths" not in result.redacted
        assert "toolpath_data" not in result.redacted
        assert result.redacted.get("safe_data") == {"value": 42}
        assert len(result.warnings) >= 2  # At least 2 fields removed


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSchemaValidity:
    """Tests that responses conform to the contract schema."""

    def test_build_schema_valid(self, client):
        """POST /build response should match expected structure."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_schema_test",
                "include": ["run_summary", "governance_notes"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify required fields in build response
        assert "schema_id" in data
        assert "schema_version" in data
        assert "context_id" in data
        assert "summary" in data
        assert "context" in data
        assert "warnings" in data

        # Verify version
        assert data["schema_version"] == "v1"

    def test_health_endpoint_returns_ok(self, client):
        """GET /health should return status ok."""
        response = client.get("/api/ai/context/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["schema_version"] == "v1"


# =============================================================================
# Redaction Tests
# =============================================================================

class TestRedaction:
    """Tests that redaction removes all forbidden content."""

    def test_redactor_removes_pii_keys(self):
        """Redactor must remove PII-related keys."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        dirty = {
            "schema_id": "test",
            "email": "test@example.com",
            "phone": "555-1234",
            "password": "secret123",
            "api_key": "key_123",
            "safe_field": "keep this",
        }

        result = redact_strict(dirty)

        assert "email" not in result.redacted
        assert "phone" not in result.redacted
        assert "password" not in result.redacted
        assert "api_key" not in result.redacted
        assert result.redacted.get("safe_field") == "keep this"

    def test_redactor_removes_nested_forbidden_keys(self):
        """Redactor must remove forbidden keys in nested structures."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        dirty = {
            "level1": {
                "level2": {
                    "gcode": "G0 X0 Y0",
                    "safe": "keep",
                },
                "toolpath": [1, 2, 3],
            },
        }

        result = redact_strict(dirty)

        # Check actual data structure (redaction warnings may mention the removed keys)
        level1 = result.redacted.get("level1", {})
        level2 = level1.get("level2", {})

        # Forbidden keys should be removed from actual data
        assert "gcode" not in level2
        assert "toolpath" not in level1

        # But safe content preserved
        assert level2.get("safe") == "keep"

        # Warnings should indicate what was removed
        assert len(result.warnings) >= 2

    def test_redactor_caps_warnings(self):
        """Redactor should cap warnings at 200."""
        from app.ai_context_adapter.redactor.strict import redact_strict

        # Create many forbidden keys
        dirty = {f"gcode_{i}": f"value_{i}" for i in range(300)}
        dirty["schema_id"] = "test"

        result = redact_strict(dirty)

        # Warnings should be capped
        assert len(result.redacted["redaction"]["warnings"]) <= 200


# =============================================================================
# Feature Flag Tests
# =============================================================================

class TestFeatureFlag:
    """Tests that feature flag properly disables the adapter."""

    def test_feature_flag_disables_build(self):
        """POST /build should return 503 when disabled."""
        # Patch at module level before import
        with patch.dict(os.environ, {"AI_CONTEXT_ENABLED": "false"}, clear=False):
            # Force reimport with new env
            import importlib
            import app.ai_context_adapter.routes as routes_module
            importlib.reload(routes_module)

            try:
                app_disabled = FastAPI()
                app_disabled.include_router(routes_module.router)
                client = TestClient(app_disabled)

                response = client.post(
                    "/api/ai/context/build",
                    json={"include": ["run_summary"]},
                )
                assert response.status_code == 503
                assert "disabled" in response.json().get("detail", "").lower()
            finally:
                # Restore for other tests
                with patch.dict(os.environ, {"AI_CONTEXT_ENABLED": "true"}, clear=False):
                    importlib.reload(routes_module)

    def test_health_still_works_when_enabled(self, client):
        """Health endpoint should work when adapter enabled."""
        response = client.get("/api/ai/context/health")
        # Health should always work
        assert response.status_code == 200


# =============================================================================
# Boundary Gate Tests
# =============================================================================

class TestBoundaryGate:
    """Tests for the boundary gate enforcement."""

    def test_boundary_gate_catches_gcode_patterns(self):
        """Boundary gate should detect G-code patterns in values."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        # G-code command pattern
        violations = _contains_forbidden_content({"data": "G01 X10 Y20 F500"})
        assert len(violations) > 0

        # M-code pattern
        violations = _contains_forbidden_content({"data": "M3 S18000"})
        assert len(violations) > 0

        # Coordinate pattern
        violations = _contains_forbidden_content({"data": "X10.5 Y-20.3"})
        assert len(violations) > 0

    def test_boundary_gate_allows_safe_content(self):
        """Boundary gate should allow normal text content."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        safe_content = {
            "summary": "This is a rosette design with 8 rings",
            "status": "OK",
            "notes": "Ready for review",
        }

        violations = _contains_forbidden_content(safe_content)
        assert len(violations) == 0

    def test_boundary_gate_detects_forbidden_keys(self):
        """Boundary gate should detect forbidden keys."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        violations = _contains_forbidden_content({"toolpaths": []})
        assert any("toolpaths" in v.lower() for v in violations)

        violations = _contains_forbidden_content({"gcode_text": "..."})
        assert any("gcode" in v.lower() for v in violations)


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests for the full context flow."""

    def test_build_with_all_includes(self, client):
        """Build with all allowed includes should work."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_integration_test",
                "pattern_id": "pattern_test",
                "include": [
                    "run_summary",
                    "design_intent",
                    "rosette_param_spec",
                    "manufacturing_candidates",
                    "governance_notes",
                ],
                "user_notes": "Testing the full integration",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify context has requested sections
        ctx = data["context"]
        assert "run_summary" in ctx or "rosette_param_spec" in ctx
        assert "governance_notes" in ctx
        assert ctx.get("user_notes") == "Testing the full integration"

        # Verify no manufacturing secrets leaked
        ctx_str = json.dumps(ctx)
        assert "gcode" not in ctx_str.lower()
        assert "toolpath" not in ctx_str.lower()

    def test_unknown_includes_warned(self, client):
        """Unknown includes should generate warnings."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "include": ["run_summary", "not_a_real_include", "also_fake"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should have warning about unknown includes
        warnings = data.get("warnings", [])
        assert any("unknown" in w.lower() or "ignored" in w.lower() for w in warnings)
