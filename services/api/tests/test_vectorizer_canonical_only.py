"""
Regression guard: Vectorizer response must be canonical-only.

This test ensures legacy fields are never reintroduced to the
photo vectorizer response schema after the Phase 2 migration.

Run: pytest tests/test_vectorizer_canonical_only.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Legacy fields that must NOT appear in the response
FORBIDDEN_LEGACY_FIELDS = [
    "svg_path_d",
    "svg_path",
    "dxf_path",
    "body_width_mm",
    "body_height_mm",
    "body_width_in",
    "body_height_in",
    "contour_count",
    "line_count",
    "export_blocked",
    "export_block_reason",
    "deprecation",
    "scale_source",  # moved to metrics.*
    "bg_method",  # moved to metrics.*
    "perspective_corrected",  # moved to metrics.*
    "processing_ms",  # moved to metrics.*
]

# Required canonical fields
REQUIRED_CANONICAL_FIELDS = [
    "ok",
    "processed",
    "stage",
    "error",
    "warnings",
    "artifacts",
    "dimensions",
    "selection",
    "recommendation",
    "metrics",
]


class TestVectorizerCanonicalResponse:
    """Ensure vectorizer response adheres to canonical-only schema."""

    def test_status_endpoint_available(self):
        """Status endpoint should work."""
        resp = client.get("/api/vectorizer/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data

    def test_legacy_fields_absent_from_response_model(self):
        """
        VectorizeResponse model must not contain legacy fields.

        This is a schema-level check that runs without needing
        the full vectorizer pipeline.
        """
        from app.routers.photo_vectorizer_router import VectorizeResponse

        model_fields = set(VectorizeResponse.model_fields.keys())

        for legacy_field in FORBIDDEN_LEGACY_FIELDS:
            assert legacy_field not in model_fields, (
                f"Legacy field '{legacy_field}' found in VectorizeResponse. "
                "This field was removed in the Phase 2 canonical migration."
            )

    def test_canonical_fields_present_in_response_model(self):
        """VectorizeResponse model must contain all canonical fields."""
        from app.routers.photo_vectorizer_router import VectorizeResponse

        model_fields = set(VectorizeResponse.model_fields.keys())

        for canonical_field in REQUIRED_CANONICAL_FIELDS:
            assert canonical_field in model_fields, (
                f"Canonical field '{canonical_field}' missing from VectorizeResponse."
            )

    def test_artifacts_structure(self):
        """Artifacts must have svg and dxf sub-structures."""
        from app.routers.photo_vectorizer_router import Artifacts

        model_fields = set(Artifacts.model_fields.keys())
        assert "svg" in model_fields
        assert "dxf" in model_fields

    def test_recommendation_structure(self):
        """Recommendation must have action, confidence, reasons."""
        from app.routers.photo_vectorizer_router import Recommendation

        model_fields = set(Recommendation.model_fields.keys())
        assert "action" in model_fields
        assert "confidence" in model_fields
        assert "reasons" in model_fields

    def test_selection_structure(self):
        """Selection must have contour selection diagnostics."""
        from app.routers.photo_vectorizer_router import Selection

        model_fields = set(Selection.model_fields.keys())
        assert "candidate_count" in model_fields
        assert "selection_score" in model_fields
        assert "winner_margin" in model_fields


class TestPhotoResultCanonical:
    """Ensure PhotoResult dataclass is canonical-only."""

    def test_photo_result_no_legacy_passthrough(self):
        """PhotoResult must not have legacy pass-through fields."""
        from app.services.photo_orchestrator import PhotoResult
        import dataclasses

        field_names = {f.name for f in dataclasses.fields(PhotoResult)}

        legacy_passthrough = [
            "export_blocked",
            "export_block_reason",
            "scale_source",
            "bg_method",
            "perspective_corrected",
        ]

        for field in legacy_passthrough:
            assert field not in field_names, (
                f"Legacy pass-through field '{field}' found in PhotoResult. "
                "These fields were removed in the Phase 2 canonical migration."
            )
