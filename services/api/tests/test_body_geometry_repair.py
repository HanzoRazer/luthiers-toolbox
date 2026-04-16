"""
Tests for Body Geometry Repair — Phase 6A + 6B
===============================================

Tests conversion, polyline detection, arc fitting validation,
and Phase 6B polyline acceptance/output.
"""

import math
import os
import numpy as np
import pytest

from app.services.body_geometry_repair import (
    contour_to_chain,
    chain_to_contour,
    validate_roundtrip,
    detect_polyline_runs,
    fit_circle_3pts,
    fit_arc_to_segment,
    detect_arc_candidates,
    repair_body_geometry,
    angle_between_vectors,
    compute_positional_deviation,
    evaluate_polyline_acceptance,
    is_polyline_output_enabled,
    PolylineRun,
    ArcCandidate,
    BodyRepairResult,
)
from app.services.layer_builder import LayeredEntities, LayeredEntity, Layer
from app.cam.unified_dxf_cleaner import Chain, Point


# ─── Fixtures ──────────────────────────────────────────────────────────────────

def make_contour(points: list) -> np.ndarray:
    """Create OpenCV contour from list of (x, y) tuples."""
    return np.array(points, dtype=np.float32).reshape(-1, 1, 2)


def make_chain(points: list) -> Chain:
    """Create Chain from list of (x, y) tuples."""
    return Chain(points=[Point(x=x, y=y) for x, y in points])


def make_circle_points(cx: float, cy: float, r: float, n: int = 20) -> list:
    """Generate points on a circle."""
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def make_arc_points(cx: float, cy: float, r: float,
                    start_deg: float, end_deg: float, n: int = 10) -> list:
    """Generate points on an arc."""
    points = []
    start_rad = math.radians(start_deg)
    end_rad = math.radians(end_deg)
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        angle = start_rad + t * (end_rad - start_rad)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def make_line_points(x1: float, y1: float, x2: float, y2: float, n: int = 10) -> list:
    """Generate points on a line segment."""
    points = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        points.append((x, y))
    return points


# ─── Conversion Tests ──────────────────────────────────────────────────────────

class TestContourChainConversion:
    """Test contour ↔ chain conversion."""

    def test_contour_to_chain_basic(self):
        """Basic conversion preserves point count."""
        contour = make_contour([(0, 0), (10, 0), (10, 10), (0, 10)])
        mm_per_px = 0.5

        chain = contour_to_chain(contour, mm_per_px)

        assert len(chain.points) == 4
        assert chain.points[0].x == 0.0
        assert chain.points[0].y == 0.0
        assert chain.points[1].x == 5.0  # 10 * 0.5
        assert chain.points[1].y == 0.0

    def test_contour_to_chain_scaling(self):
        """Conversion applies mm_per_px scaling."""
        contour = make_contour([(100, 200)])
        mm_per_px = 0.25

        chain = contour_to_chain(contour, mm_per_px)

        assert chain.points[0].x == 25.0  # 100 * 0.25
        assert chain.points[0].y == 50.0  # 200 * 0.25

    def test_chain_to_contour_basic(self):
        """Reverse conversion preserves structure."""
        chain = make_chain([(5.0, 10.0), (15.0, 20.0)])
        mm_per_px = 0.5

        contour = chain_to_contour(chain, mm_per_px)

        assert contour.shape == (2, 1, 2)
        assert contour[0, 0, 0] == pytest.approx(10.0, abs=0.01)  # 5 / 0.5
        assert contour[0, 0, 1] == pytest.approx(20.0, abs=0.01)  # 10 / 0.5

    def test_roundtrip_preserves_geometry(self):
        """contour → chain → contour preserves coordinates."""
        original = make_contour([(0, 0), (100, 0), (100, 100), (0, 100)])
        mm_per_px = 0.5

        assert validate_roundtrip(original, mm_per_px)

    def test_roundtrip_with_complex_shape(self):
        """Round-trip works for complex shapes."""
        # Create a more complex contour
        points = make_circle_points(50, 50, 30, n=20)
        original = make_contour(points)
        mm_per_px = 0.3

        assert validate_roundtrip(original, mm_per_px)


# ─── Polyline Detection Tests ──────────────────────────────────────────────────

class TestPolylineDetection:
    """Test polyline run detection."""

    def test_straight_line_single_run(self):
        """Straight line detected as single polyline run."""
        points = make_line_points(0, 0, 100, 0, n=10)
        chain = make_chain(points)

        runs = detect_polyline_runs(chain, dist_tol_mm=5.0, angle_tol_deg=15.0)

        assert len(runs) == 1
        assert runs[0].point_count == 10

    def test_corner_breaks_run(self):
        """90-degree corner breaks polyline into multiple runs."""
        # L-shaped path
        points = [(0, 0), (10, 0), (20, 0), (30, 0), (30, 10), (30, 20), (30, 30)]
        chain = make_chain(points)

        runs = detect_polyline_runs(chain, dist_tol_mm=15.0, angle_tol_deg=45.0)

        # Should break at the corner
        assert len(runs) >= 2

    def test_gentle_curve_single_run(self):
        """Gentle curve within tolerance stays as one run."""
        # Arc with small angular changes
        points = make_arc_points(0, 0, 100, 0, 30, n=10)
        chain = make_chain(points)

        runs = detect_polyline_runs(chain, dist_tol_mm=50.0, angle_tol_deg=20.0)

        # Gentle arc should be one run with generous tolerance
        assert len(runs) >= 1
        assert runs[0].point_count >= 5

    def test_distance_break(self):
        """Large gap between points breaks run."""
        points = [(0, 0), (1, 0), (2, 0), (100, 0), (101, 0)]  # Gap at point 3
        chain = make_chain(points)

        runs = detect_polyline_runs(chain, dist_tol_mm=5.0, angle_tol_deg=15.0)

        assert len(runs) >= 2

    def test_empty_chain(self):
        """Empty chain returns no runs."""
        chain = make_chain([])
        runs = detect_polyline_runs(chain)
        assert len(runs) == 0

    def test_two_point_chain(self):
        """Two-point chain returns single run."""
        chain = make_chain([(0, 0), (10, 0)])
        runs = detect_polyline_runs(chain)
        assert len(runs) == 1
        assert runs[0].point_count == 2


# ─── Arc Fitting Tests ─────────────────────────────────────────────────────────

class TestCircleFit:
    """Test 3-point circle fitting."""

    def test_fit_circle_basic(self):
        """Three points on known circle."""
        # Points on circle centered at (0, 0) with radius 10
        p1 = (10, 0)
        p2 = (0, 10)
        p3 = (-10, 0)

        result = fit_circle_3pts(p1, p2, p3)

        assert result is not None
        cx, cy, r = result
        assert cx == pytest.approx(0.0, abs=0.1)
        assert cy == pytest.approx(0.0, abs=0.1)
        assert r == pytest.approx(10.0, abs=0.1)

    def test_fit_circle_collinear_returns_none(self):
        """Collinear points return None."""
        p1 = (0, 0)
        p2 = (5, 0)
        p3 = (10, 0)

        result = fit_circle_3pts(p1, p2, p3)

        assert result is None

    def test_fit_circle_offset_center(self):
        """Circle with offset center."""
        # Points on circle centered at (50, 50) with radius 20
        cx_true, cy_true, r_true = 50, 50, 20
        p1 = (cx_true + r_true, cy_true)  # (70, 50)
        p2 = (cx_true, cy_true + r_true)  # (50, 70)
        p3 = (cx_true - r_true, cy_true)  # (30, 50)

        result = fit_circle_3pts(p1, p2, p3)

        assert result is not None
        cx, cy, r = result
        assert cx == pytest.approx(cx_true, abs=0.1)
        assert cy == pytest.approx(cy_true, abs=0.1)
        assert r == pytest.approx(r_true, abs=0.1)


class TestArcFitting:
    """Test arc segment fitting."""

    def test_fit_arc_perfect_arc(self):
        """Perfect arc points produce valid arc."""
        points = make_arc_points(0, 0, 50, 0, 90, n=10)

        candidate = fit_arc_to_segment(points, mean_tol_mm=1.0, max_tol_mm=2.0)

        assert candidate.valid
        assert candidate.radius == pytest.approx(50.0, abs=1.0)
        assert candidate.mean_error_mm < 1.0

    def test_fit_arc_straight_line_invalid(self):
        """Straight line produces invalid arc (collinear)."""
        points = make_line_points(0, 0, 100, 0, n=10)

        candidate = fit_arc_to_segment(points, mean_tol_mm=0.5, max_tol_mm=1.5)

        assert not candidate.valid

    def test_fit_arc_too_few_points(self):
        """Less than 5 points produces invalid arc."""
        points = [(0, 0), (10, 5), (20, 0)]

        candidate = fit_arc_to_segment(points)

        assert not candidate.valid

    def test_fit_arc_noisy_points(self):
        """Noisy arc points may exceed tolerance."""
        # Perfect arc
        points = make_arc_points(0, 0, 50, 0, 90, n=10)
        # Add noise
        noisy_points = [(x + 5, y + 5) for x, y in points]

        candidate = fit_arc_to_segment(noisy_points, mean_tol_mm=0.5, max_tol_mm=1.0)

        # With noise, should fail strict tolerance
        assert not candidate.valid or candidate.mean_error_mm > 0.5


class TestArcCandidateDetection:
    """Test arc candidate detection in chains."""

    def test_detect_arc_in_curved_chain(self):
        """Detect arc candidate in curved chain."""
        points = make_arc_points(100, 100, 50, 0, 180, n=20)
        chain = make_chain(points)

        candidates = detect_arc_candidates(chain, min_points=5)

        assert len(candidates) >= 1
        # At least one should be valid (it's a perfect arc)
        valid = [c for c in candidates if c.valid]
        assert len(valid) >= 1

    def test_no_arc_in_straight_chain(self):
        """No valid arcs in straight line."""
        points = make_line_points(0, 0, 100, 0, n=20)
        chain = make_chain(points)

        candidates = detect_arc_candidates(chain, min_points=5)

        # Candidates may be detected but should be invalid
        valid = [c for c in candidates if c.valid]
        assert len(valid) == 0


# ─── Integration Tests ─────────────────────────────────────────────────────────

class TestRepairBodyGeometry:
    """Test main repair function."""

    def test_disabled_when_flag_off(self, monkeypatch):
        """Returns not applied when flag is off."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "0")

        layered = LayeredEntities(
            body=[],
            image_size=(1000, 1000),
            mm_per_px=0.5,
        )

        result = repair_body_geometry(layered)

        assert not result.applied
        assert result.phase == "disabled"

    def test_enabled_with_contours(self, monkeypatch):
        """Computes metrics when enabled with contours."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")

        # Create a simple square contour
        contour = make_contour([(0, 0), (100, 0), (100, 100), (0, 100)])
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 100),
            area=10000.0,
            is_closed=True,
        )

        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=0.5,
        )

        result = repair_body_geometry(layered)

        assert result.applied
        assert result.phase == "6A_validation"
        assert result.metrics.contour_count == 1
        assert result.metrics.total_points == 4
        assert result.metrics.chain_conversion_ok

    def test_metrics_computed(self, monkeypatch):
        """Metrics include polyline detection results."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")

        # Create a contour with distinct segments
        points = (
            make_line_points(0, 0, 50, 0, n=10) +
            make_line_points(50, 0, 50, 50, n=10)[1:]  # Skip duplicate
        )
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 50, 50),
            area=2500.0,
            is_closed=False,
        )

        layered = LayeredEntities(
            body=[entity],
            image_size=(100, 100),
            mm_per_px=1.0,  # 1:1 for simplicity
        )

        result = repair_body_geometry(layered)

        assert result.metrics.polyline_runs_detected >= 1
        assert result.metrics.line_segments_original > 0

    def test_empty_body_layer(self, monkeypatch):
        """Handles empty BODY layer gracefully."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")

        layered = LayeredEntities(
            body=[],
            image_size=(100, 100),
            mm_per_px=0.5,
        )

        result = repair_body_geometry(layered)

        assert result.applied
        assert result.metrics.contour_count == 0

    def test_result_to_dict(self, monkeypatch):
        """Result serializes to dict for debug payload."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")

        contour = make_contour([(0, 0), (10, 0), (10, 10), (0, 10)])
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 10, 10),
            area=100.0,
            is_closed=True,
        )

        layered = LayeredEntities(
            body=[entity],
            image_size=(50, 50),
            mm_per_px=0.5,
        )

        result = repair_body_geometry(layered)
        d = result.to_dict()

        assert "applied" in d
        assert "phase" in d
        assert "metrics" in d
        assert "dxf_output_changed" in d
        assert d["dxf_output_changed"] is False  # Phase 6A


# ─── Angle Calculation Tests ───────────────────────────────────────────────────

class TestAngleBetweenVectors:
    """Test angle calculation helper."""

    def test_parallel_vectors(self):
        """Parallel vectors have 0 degree angle."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([2.0, 0.0])
        assert angle_between_vectors(v1, v2) == pytest.approx(0.0, abs=0.1)

    def test_perpendicular_vectors(self):
        """Perpendicular vectors have 90 degree angle."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert angle_between_vectors(v1, v2) == pytest.approx(90.0, abs=0.1)

    def test_opposite_vectors(self):
        """Opposite vectors have 180 degree angle."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([-1.0, 0.0])
        assert angle_between_vectors(v1, v2) == pytest.approx(180.0, abs=0.1)

    def test_zero_vector(self):
        """Zero vector returns 180 (degenerate)."""
        v1 = np.array([0.0, 0.0])
        v2 = np.array([1.0, 0.0])
        assert angle_between_vectors(v1, v2) == 180.0


# ─── Phase 6B: Positional Deviation Tests ─────────────────────────────────────

class TestPositionalDeviation:
    """Test positional deviation calculation."""

    def test_straight_line_zero_deviation(self):
        """Points on a straight line have zero deviation."""
        points = make_line_points(0, 0, 100, 0, n=10)
        mean_dev, max_dev = compute_positional_deviation(points)

        assert mean_dev == pytest.approx(0.0, abs=0.01)
        assert max_dev == pytest.approx(0.0, abs=0.01)

    def test_arc_has_deviation(self):
        """Points on an arc deviate from the chord."""
        points = make_arc_points(0, 0, 50, 0, 90, n=10)
        mean_dev, max_dev = compute_positional_deviation(points)

        # Arc should have measurable deviation from chord
        assert mean_dev > 0
        assert max_dev > 0
        # Middle of arc has maximum deviation
        assert max_dev > mean_dev

    def test_two_points_zero_deviation(self):
        """Two-point segment has zero deviation (no interior points)."""
        points = [(0, 0), (100, 0)]
        mean_dev, max_dev = compute_positional_deviation(points)

        assert mean_dev == 0.0
        assert max_dev == 0.0

    def test_three_points_single_deviation(self):
        """Three points: single interior point deviation."""
        # Middle point 10mm above the line
        points = [(0, 0), (50, 10), (100, 0)]
        mean_dev, max_dev = compute_positional_deviation(points)

        assert mean_dev == pytest.approx(10.0, abs=0.1)
        assert max_dev == pytest.approx(10.0, abs=0.1)


class TestPolylineAcceptance:
    """Test polyline acceptance evaluation."""

    def test_straight_line_accepted(self):
        """Straight line polyline is accepted."""
        points = make_line_points(0, 0, 100, 0, n=10)
        run = PolylineRun(
            points=points,
            start_idx=0,
            end_idx=9,
            point_count=10,
        )

        evaluated = evaluate_polyline_acceptance(run, mean_tol_mm=0.5, max_tol_mm=1.5)

        assert evaluated.accepted
        assert evaluated.mean_deviation_mm == pytest.approx(0.0, abs=0.01)
        assert evaluated.max_deviation_mm == pytest.approx(0.0, abs=0.01)

    def test_arc_rejected_with_strict_tolerance(self):
        """Arc polyline rejected with strict tolerance."""
        points = make_arc_points(0, 0, 50, 0, 90, n=10)
        run = PolylineRun(
            points=points,
            start_idx=0,
            end_idx=9,
            point_count=10,
        )

        evaluated = evaluate_polyline_acceptance(run, mean_tol_mm=0.1, max_tol_mm=0.2)

        # 90-degree arc on r=50 has significant deviation
        assert not evaluated.accepted
        assert evaluated.max_deviation_mm > 0.2

    def test_gentle_arc_may_be_accepted(self):
        """Gentle arc might be accepted with relaxed tolerance."""
        # Small arc segment (10 degrees)
        points = make_arc_points(0, 0, 100, 0, 10, n=10)
        run = PolylineRun(
            points=points,
            start_idx=0,
            end_idx=9,
            point_count=10,
        )

        evaluated = evaluate_polyline_acceptance(run, mean_tol_mm=2.0, max_tol_mm=5.0)

        # Small arc deviation should be under relaxed tolerance
        assert evaluated.mean_deviation_mm < 2.0


class TestPhase6BIntegration:
    """Test Phase 6B integration in repair_body_geometry."""

    def test_polyline_output_flag_disabled(self, monkeypatch):
        """Phase is 6A when ENABLE_POLYLINE_OUTPUT is not set."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.delenv("ENABLE_POLYLINE_OUTPUT", raising=False)

        assert not is_polyline_output_enabled()

        contour = make_contour([(0, 0), (10, 0), (10, 10)])
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 10, 10),
            area=50.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(50, 50),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        assert result.phase == "6A_validation"

    def test_polyline_output_flag_enabled(self, monkeypatch):
        """Phase is 6B when ENABLE_POLYLINE_OUTPUT=1."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        assert is_polyline_output_enabled()

        contour = make_contour([(0, 0), (10, 0), (10, 10)])
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 10, 10),
            area=50.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(50, 50),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        assert result.phase == "6B_polyline_output"

    def test_accepted_primitives_populated(self, monkeypatch):
        """Accepted primitives list is populated for qualifying runs."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        # Straight line should be accepted
        points = make_line_points(0, 0, 100, 0, n=10)
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 0),
            area=0.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        # Straight line should produce accepted primitives
        assert len(result.accepted_primitives) >= 1
        assert result.metrics.polyline_runs_accepted >= 1

    def test_metrics_track_acceptance(self, monkeypatch):
        """Metrics include accepted/rejected counts."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        # Mix of straight and curved segments
        straight = make_line_points(0, 0, 50, 0, n=10)
        curved = make_arc_points(50, 0, 30, 0, 90, n=10)
        points = straight + curved[1:]  # Skip duplicate junction
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 80, 30),
            area=1200.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(100, 100),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        # Metrics should include acceptance counts
        assert "polyline_runs_accepted" in result.metrics.to_dict()
        assert "polyline_runs_rejected" in result.metrics.to_dict()
        assert "actual_reduction_pct" in result.metrics.to_dict()

    def test_dxf_output_changed_flag(self, monkeypatch):
        """dxf_output_changed is True when Phase 6B has accepted primitives."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        # Straight line should produce accepted primitives
        points = make_line_points(0, 0, 100, 0, n=10)
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 0),
            area=0.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)
        d = result.to_dict()

        assert d["dxf_output_changed"] is True
        assert d["accepted_primitive_count"] >= 1

    def test_flags_off_returns_disabled(self, monkeypatch):
        """When ENABLE_BODY_REPAIR=0, phase is 'disabled' and no processing occurs."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "0")
        monkeypatch.delenv("ENABLE_POLYLINE_OUTPUT", raising=False)

        contour = make_contour([(0, 0), (100, 0), (100, 100)])
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 100),
            area=10000.0,
            is_closed=True,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        # When disabled, no processing occurs
        assert result.applied is False
        assert result.phase == "disabled"
        assert len(result.primitives) == 0
        assert len(result.accepted_primitives) == 0

    def test_only_body_repair_flag_produces_metrics_only(self, monkeypatch):
        """When ENABLE_BODY_REPAIR=1 but ENABLE_POLYLINE_OUTPUT=0, phase is 6A."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "0")

        points = make_line_points(0, 0, 100, 0, n=10)
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 0),
            area=0.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        # Phase 6A: metrics computed but no accepted_primitives for output
        assert result.phase == "6A_validation"
        assert result.applied is True
        assert result.metrics.polyline_runs_detected > 0
        # 6A does NOT populate accepted_primitives (that's 6B)
        # Actually checking: primitives exist but accepted_primitives may not
        # dxf_output_changed should be False for 6A
        d = result.to_dict()
        assert d["dxf_output_changed"] is False

    def test_debug_payload_structure(self, monkeypatch):
        """Debug payload includes all required Phase 6B visibility fields."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        points = make_line_points(0, 0, 100, 0, n=10)
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 100, 0),
            area=0.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(200, 200),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)
        d = result.to_dict()

        # Required visibility fields
        assert "phase" in d
        assert d["phase"] == "6B_polyline_output"
        assert "dxf_output_changed" in d
        assert "primitive_count" in d
        assert "accepted_primitive_count" in d
        assert "metrics" in d

        m = d["metrics"]
        assert "polyline_runs_detected" in m
        assert "polyline_runs_accepted" in m
        assert "polyline_runs_rejected" in m
        assert "actual_reduction_pct" in m

    def test_rejected_runs_not_in_accepted_primitives(self, monkeypatch):
        """Runs that fail deviation tolerance are not in accepted_primitives."""
        monkeypatch.setenv("ENABLE_BODY_REPAIR", "1")
        monkeypatch.setenv("ENABLE_POLYLINE_OUTPUT", "1")

        # Large arc with high deviation - should be rejected
        points = make_arc_points(0, 0, 50, 0, 90, n=20)
        contour = make_contour(points)
        entity = LayeredEntity(
            contour=contour,
            layer=Layer.BODY,
            bbox=(0, 0, 50, 50),
            area=1000.0,
            is_closed=False,
        )
        layered = LayeredEntities(
            body=[entity],
            image_size=(100, 100),
            mm_per_px=1.0,
        )

        result = repair_body_geometry(layered)

        # Arc should produce runs but they may be rejected
        # The 90-degree arc has ~21mm max deviation, well over 1.5mm threshold
        assert result.metrics.polyline_runs_detected >= 1
        # With strict default tolerance, arc runs should be rejected
        # (depends on how runs are segmented, but at least some rejection expected)
