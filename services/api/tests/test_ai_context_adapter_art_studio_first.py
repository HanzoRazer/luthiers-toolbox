"""
AI Context Adapter - Art Studio First Mode Tests

Tests for the art_studio_first context mode which provides:
- rosette_param_spec (design intent snapshot)
- diff_summary (safe, text-only)
- artifact_manifest (file list + hashes + kinds, NO bytes, NO toolpaths/gcode)

These tests are CI gates for the art-studio-first AI context pathway.
"""

import json
from typing import Any, Dict

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


# =============================================================================
# Art-Studio-First Mode Tests
# =============================================================================

class TestArtStudioFirstMode:
    """Tests for art_studio_first context mode."""

    def test_build_art_studio_first_mode(self, client):
        """POST /build with art_studio_first mode returns expected fields."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test_art_studio",
                "mode": "art_studio_first",
                "include": ["rosette_param_spec", "diff_summary", "artifact_manifest"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify mode is recorded
        assert data["context"]["_meta"]["mode"] == "art_studio_first"

        # Verify art-studio-first sections are present
        ctx = data["context"]
        assert "rosette_param_spec" in ctx
        assert "diff_summary" in ctx
        assert "artifact_manifest" in ctx

    def test_artifact_manifest_has_metadata_only(self, client):
        """Artifact manifest contains only metadata, never raw bytes."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test_manifest",
                "include": ["artifact_manifest"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        manifest = data["context"].get("artifact_manifest", {})
        artifacts = manifest.get("artifacts", [])

        # Even if empty, the structure should be correct
        assert "artifact_count" in manifest

        # If there are artifacts, verify no raw bytes
        for art in artifacts:
            # These are allowed metadata fields
            assert set(art.keys()) <= {"kind", "sha256", "size_bytes", "mime", "filename", "created_at_utc"}
            # These should NEVER appear
            assert "data" not in art
            assert "content" not in art
            assert "bytes" not in art  # "bytes" as content, size_bytes is OK
            assert "base64" not in str(art)

    def test_artifact_manifest_no_inline_gcode(self, client):
        """Artifact manifest never includes inline G-code content."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test_no_gcode",
                "include": ["artifact_manifest"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Serialize to check for G-code patterns
        data_str = json.dumps(data["context"].get("artifact_manifest", {}))

        # G-code patterns should never appear in manifest
        assert "G0 " not in data_str
        assert "G1 " not in data_str
        assert "M3 " not in data_str
        assert "M5 " not in data_str
        # Note: "gcode" as a kind label is OK, "G01 X10..." content is NOT

    def test_diff_summary_is_safe_text(self, client):
        """diff_summary contains only safe text, never forbidden patterns."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test_diff",
                "include": ["diff_summary"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        diff_summary = data["context"].get("diff_summary", {})

        # Should have summary text
        assert "summary" in diff_summary

        # Summary should be a string
        summary_text = diff_summary.get("summary", "")
        assert isinstance(summary_text, str)

        # Summary should never contain G-code
        assert "G0 " not in summary_text
        assert "G1 " not in summary_text
        assert "M3 " not in summary_text

    def test_diff_summary_no_comparison_returns_status(self, client):
        """diff_summary without compare_run_id returns no_comparison status."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_test_diff_no_compare",
                "include": ["diff_summary"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        diff_summary = data["context"].get("diff_summary", {})
        assert diff_summary.get("status") == "no_comparison"

    def test_rosette_param_spec_design_only(self, client):
        """rosette_param_spec contains design params, never manufacturing params."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "pattern_id": "pattern_test_rosette",
                "include": ["rosette_param_spec"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        rosette_spec = data["context"].get("rosette_param_spec", {})
        spec_str = json.dumps(rosette_spec)

        # Design params are OK
        # Manufacturing params should never appear
        assert "toolpath" not in spec_str.lower()
        assert "gcode" not in spec_str.lower()
        assert "feeds" not in spec_str.lower()
        assert "speeds" not in spec_str.lower()


# =============================================================================
# Boundary Tripwire Tests
# =============================================================================

class TestArtStudioBoundaryTripwire:
    """Tests that verify boundary violations are caught."""

    def test_boundary_catches_gcode_in_any_field(self):
        """Boundary gate catches G-code patterns regardless of location."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        # G-code in random nested location
        payload = {
            "safe_field": "normal text",
            "nested": {
                "deep": {
                    "data": "G01 X10 Y20 Z-5 F1000",
                }
            }
        }

        violations = _contains_forbidden_content(payload)
        assert len(violations) > 0
        assert any("G0" in v or "pattern" in v.lower() for v in violations)

    def test_boundary_catches_toolpath_keys(self):
        """Boundary gate catches toolpath-related keys."""
        from app.ai_context_adapter.routes import _contains_forbidden_content

        payload = {
            "safe": "ok",
            "toolpaths": [],  # Forbidden key
        }

        violations = _contains_forbidden_content(payload)
        assert len(violations) > 0
        assert any("toolpath" in v.lower() for v in violations)


# =============================================================================
# Response Schema Tests
# =============================================================================

class TestArtStudioResponseSchema:
    """Tests for response schema compliance."""

    def test_response_has_required_fields(self, client):
        """Response contains all required envelope fields."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_schema_test",
                "mode": "art_studio_first",
                "include": ["artifact_manifest"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Required top-level fields
        assert "schema_id" in data
        assert "schema_version" in data
        assert "context_id" in data
        assert "context" in data
        assert "warnings" in data

    def test_meta_includes_mode(self, client):
        """_meta section includes mode field."""
        response = client.post(
            "/api/ai/context/build",
            json={
                "run_id": "run_meta_test",
                "mode": "art_studio_first",
                "include": [],
            },
        )
        assert response.status_code == 200
        data = response.json()

        meta = data["context"].get("_meta", {})
        assert meta.get("mode") == "art_studio_first"
