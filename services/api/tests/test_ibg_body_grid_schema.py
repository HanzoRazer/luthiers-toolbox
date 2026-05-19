"""
Tests for Body Grid Schema — Core Data Structures

Note: Import directly from body_grid submodules to avoid ezdxf dependency chain.
The body_grid module is designed to be independent of DXF/CAD dependencies.
"""

import pytest

# Direct imports to avoid ezdxf dependency through ibg.__init__
from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    BodyEvidence,
    CenterlineDescriptor,
    AsymmetryDescriptor,
    ContourSegment,
    CoordinateSpace,
    EvidenceSource,
    Landmark,
    NormalizedPoint,
    RawCoordinate,
    ZoneAssignment,
)


class TestNormalizedPoint:
    """Tests for NormalizedPoint data structure."""

    def test_create_basic(self):
        """Test basic point creation."""
        pt = NormalizedPoint(x_norm=0.5, y_norm=0.3)
        assert pt.x_norm == 0.5
        assert pt.y_norm == 0.3
        assert pt.confidence == 1.0
        assert pt.raw is None

    def test_create_with_raw(self):
        """Test point creation with raw coordinates."""
        raw = RawCoordinate(x=100.0, y=200.0, space=CoordinateSpace.RAW_MM)
        pt = NormalizedPoint(x_norm=0.5, y_norm=0.3, raw=raw)
        assert pt.raw.x == 100.0
        assert pt.raw.y == 200.0
        assert pt.raw.space == CoordinateSpace.RAW_MM


class TestZoneAssignment:
    """Tests for ZoneAssignment data structure."""

    def test_primary_only(self):
        """Test zone assignment with primary zone only."""
        za = ZoneAssignment(primary_zone="lower_bout")
        assert za.primary_zone == "lower_bout"
        assert za.zone_weights["lower_bout"] == 1.0

    def test_fuzzy_assignment(self):
        """Test fuzzy zone assignment with multiple zones."""
        za = ZoneAssignment(
            primary_zone="waist",
            secondary_zones=["lower_bout"],
            zone_weights={"waist": 0.68, "lower_bout": 0.32}
        )
        assert za.primary_zone == "waist"
        assert "lower_bout" in za.secondary_zones
        assert za.zone_weights["waist"] == 0.68
        assert za.zone_weights["lower_bout"] == 0.32


class TestContourSegment:
    """Tests for ContourSegment data structure."""

    def test_create_segment(self):
        """Test contour segment creation."""
        points = [
            NormalizedPoint(0.0, 0.0),
            NormalizedPoint(0.1, 0.1),
            NormalizedPoint(0.2, 0.2),
        ]
        seg = ContourSegment(points=points, side="left")
        assert len(seg.points) == 3
        assert seg.side == "left"
        assert seg.is_closed is False


class TestBodyEvidence:
    """Tests for BodyEvidence container."""

    def test_empty_evidence(self):
        """Test empty evidence container."""
        evidence = BodyEvidence()
        assert not evidence.has_landmarks()
        assert not evidence.has_contours()
        assert evidence.get_landmark("test") is None

    def test_with_landmarks(self):
        """Test evidence with landmarks."""
        lm = Landmark(
            label="lower_bout_max",
            point=NormalizedPoint(0.5, 0.25),
            source=EvidenceSource.CONSTRAINT_EXTRACTOR
        )
        evidence = BodyEvidence(landmarks=[lm])
        assert evidence.has_landmarks()
        assert evidence.get_landmark("lower_bout_max") is not None
        assert evidence.get_landmark("nonexistent") is None

    def test_with_outline_points(self):
        """Test evidence with outline points."""
        evidence = BodyEvidence(
            outline_points=[(0, 0), (100, 50), (200, 100)]
        )
        assert len(evidence.outline_points) == 3


class TestCenterlineDescriptor:
    """Tests for CenterlineDescriptor."""

    def test_create_detected(self):
        """Test centerline from detection."""
        cl = CenterlineDescriptor(
            x_mm=190.5,
            source="detected",
            confidence=0.85,
            symmetry_score=0.92
        )
        assert cl.x_mm == 190.5
        assert cl.source == "detected"
        assert cl.symmetry_score == 0.92


class TestAsymmetryDescriptor:
    """Tests for AsymmetryDescriptor."""

    def test_symmetric_body(self):
        """Test symmetric body descriptor."""
        asym = AsymmetryDescriptor(is_symmetric=True)
        assert asym.is_symmetric is True
        assert asym.asymmetry_score == 0.0
        assert asym.dominant_side == "balanced"

    def test_asymmetric_body(self):
        """Test asymmetric body descriptor."""
        asym = AsymmetryDescriptor(
            is_symmetric=False,
            asymmetry_type="single_cut",
            asymmetry_score=0.35,
            dominant_side="left"
        )
        assert asym.is_symmetric is False
        assert asym.asymmetry_type == "single_cut"
        assert asym.asymmetry_score == 0.35
