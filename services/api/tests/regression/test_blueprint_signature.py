"""
Tests for Blueprint Reader output signature.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

import pytest

from app.regression.blueprint_signature import (
    BlueprintOutputSignature,
    extract_blueprint_signature,
)


class TestBlueprintOutputSignature:
    """Tests for BlueprintOutputSignature."""

    def test_create_signature(self):
        """Test basic signature creation."""
        sig = BlueprintOutputSignature(
            artifact_id="dreadnought_001",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=1247,
            dxf_closed_contours=3,
        )
        assert sig.system_id == "BLUEPRINT_READER_MVP"
        assert sig.body_width_mm == 381.0
        assert sig.body_height_mm == 520.0

    def test_auto_populates_dimensions(self):
        """Test that dimensions dict is auto-populated."""
        sig = BlueprintOutputSignature(
            artifact_id="test_001",
            body_width_mm=100.0,
            body_height_mm=200.0,
            selection_score=0.85,
        )
        assert sig.dimensions["body_width_mm"] == 100.0
        assert sig.dimensions["body_height_mm"] == 200.0
        assert sig.dimensions["selection_score"] == 0.85

    def test_auto_populates_counts(self):
        """Test that counts dict is auto-populated."""
        sig = BlueprintOutputSignature(
            artifact_id="test_001",
            dxf_entity_count=500,
            dxf_closed_contours=5,
            svg_path_count=3,
            candidate_count=12,
        )
        assert sig.counts["dxf_entity_count"] == 500
        assert sig.counts["dxf_closed_contours"] == 5
        assert sig.counts["svg_path_count"] == 3
        assert sig.counts["candidate_count"] == 12

    def test_auto_populates_flags(self):
        """Test that flags dict is auto-populated."""
        sig = BlueprintOutputSignature(
            artifact_id="test_001",
            svg_present=True,
            dxf_closed_contours=3,
            selected_index=2,
            recommendation_action="accept",
        )
        assert sig.flags["svg_present"] is True
        assert sig.flags["has_closed_contours"] is True
        assert sig.flags["has_selection"] is True
        assert sig.flags["is_accepted"] is True

    def test_to_dict_includes_all_fields(self):
        """Test serialization includes all fields."""
        sig = BlueprintOutputSignature(
            artifact_id="test_001",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=1247,
            mode="refined",
            spec_name="dreadnought",
        )
        data = sig.to_dict()

        assert data["artifact_id"] == "test_001"
        assert data["body_width_mm"] == 381.0
        assert data["mode"] == "refined"
        assert data["spec_name"] == "dreadnought"

    def test_from_dict_roundtrip(self):
        """Test deserialization preserves all fields."""
        original = BlueprintOutputSignature(
            artifact_id="test_001",
            body_width_mm=381.0,
            body_height_mm=520.0,
            dxf_entity_count=1247,
            dxf_closed_contours=3,
            dxf_layers=["BODY", "CENTERLINE"],
            recommendation_action="accept",
            recommendation_confidence=0.72,
        )
        data = original.to_dict()
        restored = BlueprintOutputSignature.from_dict(data)

        assert restored.artifact_id == original.artifact_id
        assert restored.body_width_mm == original.body_width_mm
        assert restored.dxf_entity_count == original.dxf_entity_count
        assert restored.dxf_layers == original.dxf_layers
        assert restored.recommendation_action == original.recommendation_action


class TestExtractBlueprintSignature:
    """Tests for extract_blueprint_signature function."""

    def test_extract_from_result_dict(self):
        """Test extracting signature from Blueprint Reader result."""
        result_dict = {
            "ok": True,
            "dimensions": {"width_mm": 381.0, "height_mm": 520.0},
            "artifacts": {
                "dxf": {"entity_count": 1247, "closed_contours": 3, "present": True},
                "svg": {"path_count": 3, "present": True},
            },
            "selection": {
                "candidate_count": 12,
                "selected_index": 3,
                "selection_score": 0.72,
                "winner_margin": 0.15,
            },
            "recommendation": {
                "action": "accept",
                "confidence": 0.72,
            },
        }
        sig = extract_blueprint_signature(
            result_dict,
            artifact_id="dreadnought_test_001",
            input_description="Test dreadnought blueprint",
        )

        assert sig.artifact_id == "dreadnought_test_001"
        assert sig.body_width_mm == 381.0
        assert sig.body_height_mm == 520.0
        assert sig.dxf_entity_count == 1247
        assert sig.selection_score == 0.72
        assert sig.recommendation_action == "accept"

    def test_extract_with_input_bytes(self):
        """Test that input bytes are hashed."""
        result_dict = {
            "dimensions": {"width_mm": 100.0, "height_mm": 200.0},
            "artifacts": {"dxf": {}, "svg": {}},
            "selection": {},
            "recommendation": {},
        }
        sig = extract_blueprint_signature(
            result_dict,
            artifact_id="test_001",
            input_bytes=b"test input data",
        )

        assert sig.input_hash is not None
        assert len(sig.input_hash) == 16  # Truncated SHA256

    def test_extract_handles_missing_fields(self):
        """Test graceful handling of missing fields."""
        result_dict = {}
        sig = extract_blueprint_signature(
            result_dict,
            artifact_id="empty_test",
        )

        assert sig.artifact_id == "empty_test"
        assert sig.body_width_mm == 0.0
        assert sig.dxf_entity_count == 0
