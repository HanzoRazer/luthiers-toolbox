"""
Tests for logarithmic spiral soundhole geometry.

Tests the corrected arc length formula:
  L = sqrt(1 + k²) / k × (r_end - r0)

For k → 0 fallback:
  L = r0 × θ (circular arc)
"""

import math
import tempfile
from pathlib import Path

import pytest

from app.instrument_geometry.soundhole.spiral_geometry import (
    SpiralSpec,
    DualSpiralSpec,
    SpiralGeometry,
    compute_spiral_geometry,
    compute_dual_geometry,
    default_carlos_jumbo_spec,
    _spiral_arc_length,
    _closed_form_stats,
)


class TestSpiralArcLengthFormula:
    """Regression tests for the corrected spiral arc length formula."""

    def test_arc_length_formula_known_values(self):
        """
        Verify arc length matches hand-calculated values.

        For r(θ) = r0 × e^(kθ):
        L = sqrt(1 + k²) / k × (r_end - r0)

        Test case: r0=10, k=0.18, turns=1.1
        theta_end = 1.1 × 2π = 6.9115
        r_end = 10 × e^(0.18 × 6.9115) = 10 × e^1.2441 = 34.69 mm
        L = sqrt(1.0324) / 0.18 × (34.69 - 10) = 5.645 × 24.69 = 139.4 mm
        """
        r0 = 10.0
        k = 0.18
        turns = 1.1
        theta_end = turns * 2 * math.pi
        r_end = r0 * math.exp(k * theta_end)

        arc_length = _spiral_arc_length(r0, r_end, k, theta_end)

        # Hand-calculated: sqrt(1 + 0.18²) / 0.18 × (34.69 - 10) ≈ 139.4 mm
        assert abs(arc_length - 139.4) < 1.0, f"Arc length {arc_length:.1f} != expected 139.4 mm"

    def test_arc_length_factor_is_sqrt_1_plus_k2_over_k(self):
        """Verify the scaling factor matches sqrt(1 + k²) / k."""
        r0 = 10.0
        k = 0.18
        turns = 1.1
        theta_end = turns * 2 * math.pi
        r_end = r0 * math.exp(k * theta_end)

        arc_length = _spiral_arc_length(r0, r_end, k, theta_end)
        expected_factor = math.sqrt(1 + k * k) / k
        expected_length = expected_factor * (r_end - r0)

        assert abs(arc_length - expected_length) < 0.01

    def test_near_circular_fallback(self):
        """For k ≈ 0, arc length should fall back to r0 × θ."""
        r0 = 50.0
        k = 1e-8  # Near zero
        turns = 1.0
        theta_end = turns * 2 * math.pi
        r_end = r0 * math.exp(k * theta_end)  # ≈ r0

        arc_length = _spiral_arc_length(r0, r_end, k, theta_end)

        # For a circle, arc length = r × θ
        expected = r0 * theta_end
        assert abs(arc_length - expected) < 0.01

    def test_closed_form_stats_consistency(self):
        """Verify _closed_form_stats uses the corrected formula."""
        r0 = 10.0
        k = 0.18
        turns = 1.1
        slot_w = 14.0

        stats = _closed_form_stats(r0, k, turns, slot_w)

        # one_wall_length should match _spiral_arc_length
        theta_end = turns * 2 * math.pi
        r_end = r0 * math.exp(k * theta_end)
        expected_length = _spiral_arc_length(r0, r_end, k, theta_end)

        assert abs(stats["one_wall_length"] - expected_length) < 0.01

        # Area = slot_width × arc_length
        assert abs(stats["area_mm2"] - slot_w * expected_length) < 0.1

        # Perimeter = 2 × arc_length
        assert abs(stats["perimeter_mm"] - 2 * expected_length) < 0.1

        # P:A = 2 / slot_width (invariant)
        expected_pa = 2.0 / slot_w
        assert abs(stats["pa_ratio_mm_inv"] - expected_pa) < 0.001


class TestCarlosJumboPresets:
    """Tests for the Carlos Jumbo preset values after formula correction."""

    def test_carlos_defaults_produce_reasonable_area(self):
        """
        With corrected formula, Carlos spirals should have larger area
        than the old (incorrect) calculation.

        Old formula gave ~25mm arc length per spiral.
        Correct formula gives ~139mm arc length per spiral.
        Area = slot_width (14mm) × arc_length, so ~1950 mm² per spiral.
        """
        dual = default_carlos_jumbo_spec()
        geo = compute_dual_geometry(dual)

        # Each spiral should have area ≈ 14 × 139 ≈ 1950 mm²
        # Total area ≈ 3900 mm²
        assert geo.upper.area_mm2 > 1500, f"Upper area {geo.upper.area_mm2} too small"
        assert geo.lower.area_mm2 > 1500, f"Lower area {geo.lower.area_mm2} too small"
        assert geo.total_area_mm2 > 3000, f"Total area {geo.total_area_mm2} too small"

    def test_carlos_pa_ratio_is_invariant(self):
        """
        P:A ratio should be 2/slot_width regardless of formula used.
        For slot_width=14mm: P:A = 2/14 ≈ 0.143 mm⁻¹
        """
        dual = default_carlos_jumbo_spec()
        geo = compute_dual_geometry(dual)

        expected_pa = 2.0 / 14.0  # ≈ 0.143
        assert abs(geo.upper.pa_ratio_mm_inv - expected_pa) < 0.001
        assert abs(geo.lower.pa_ratio_mm_inv - expected_pa) < 0.001

    def test_carlos_passes_williams_threshold(self):
        """
        Carlos spirals with 14mm slot should pass Williams P:A > 0.10 threshold.
        P:A = 2/14 = 0.143 > 0.10 ✓
        """
        dual = default_carlos_jumbo_spec()
        geo = compute_dual_geometry(dual)

        assert geo.upper.pa_ratio_mm_inv > 0.10
        assert geo.lower.pa_ratio_mm_inv > 0.10


class TestSpiralGeometryBasic:
    """Basic geometry computation tests using current SpiralSpec schema."""

    def test_spiral_geometry_basic(self):
        """Test basic spiral geometry computation."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=20.0,
            growth_rate_k=0.15,
            turns=1.0,
            slot_width_mm=10.0,
            rotation_deg=0.0,
            label="test",
        )

        geom = compute_spiral_geometry(spec)

        # Should have points (default n_steps=300)
        assert len(geom.centerline) == 301
        assert len(geom.outer_wall) == 301
        assert len(geom.inner_wall) == 301

        # Area should be positive and reasonable
        assert geom.area_mm2 > 0
        assert geom.area_mm2 < 50000  # Sanity upper bound

        # Perimeter should be positive
        assert geom.perimeter_mm > 0

        # Total length should be positive
        assert geom.total_length_mm > 0

        # P:A ratio should be 2/slot_width
        assert abs(geom.pa_ratio_mm_inv - 0.20) < 0.001

    def test_spiral_grows_outward(self):
        """Test that spiral radius increases along the path."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=20.0,
            growth_rate_k=0.2,
            turns=1.0,
            slot_width_mm=10.0,
            rotation_deg=0.0,
        )

        geom = compute_spiral_geometry(spec)

        # First point should be closer to center than last point
        first_x, first_y = geom.centerline[0]
        last_x, last_y = geom.centerline[-1]

        first_r = (first_x**2 + first_y**2) ** 0.5
        last_r = (last_x**2 + last_y**2) ** 0.5

        assert last_r > first_r, "Spiral should grow outward"

    def test_slot_width_affects_area(self):
        """Test that wider slots produce larger area."""
        narrow_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=15.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=8.0,
            rotation_deg=0.0,
        )

        wide_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=15.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=16.0,  # Double width
            rotation_deg=0.0,
        )

        narrow_geom = compute_spiral_geometry(narrow_spec)
        wide_geom = compute_spiral_geometry(wide_spec)

        # Double width = double area (same arc length)
        assert abs(wide_geom.area_mm2 / narrow_geom.area_mm2 - 2.0) < 0.01


class TestPARatio:
    """Perimeter to area ratio tests for acoustic properties."""

    def test_pa_ratio_invariant_of_k(self):
        """
        P:A ratio should be 2/slot_width regardless of k value.
        This is because both perimeter and area scale with arc length.
        """
        for k in [0.10, 0.15, 0.18, 0.25, 0.30]:
            spec = SpiralSpec(
                center_x_mm=0.0,
                center_y_mm=0.0,
                start_radius_mm=10.0,
                growth_rate_k=k,
                turns=1.0,
                slot_width_mm=14.0,
                rotation_deg=0.0,
            )
            geom = compute_spiral_geometry(spec)
            expected_pa = 2.0 / 14.0
            assert abs(geom.pa_ratio_mm_inv - expected_pa) < 0.001, f"k={k} failed"

    def test_narrow_slot_higher_pa_ratio(self):
        """Narrower slots should have higher P:A ratio."""
        narrow_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=15.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=8.0,
            rotation_deg=0.0,
        )

        wide_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=15.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=16.0,
            rotation_deg=0.0,
        )

        narrow_geom = compute_spiral_geometry(narrow_spec)
        wide_geom = compute_spiral_geometry(wide_spec)

        # P:A = 2/w, so narrow (w=8) has higher ratio than wide (w=16)
        assert narrow_geom.pa_ratio_mm_inv > wide_geom.pa_ratio_mm_inv


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_zero_turns_produces_zero_area(self):
        """Zero turns should produce zero or near-zero area."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=20.0,
            growth_rate_k=0.18,
            turns=0.0,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )

        geom = compute_spiral_geometry(spec)
        assert geom.area_mm2 < 1.0  # Near zero

    def test_small_k_near_circular(self):
        """Very small k should produce near-circular arc length."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=50.0,
            growth_rate_k=0.001,  # Very small
            turns=1.0,
            slot_width_mm=10.0,
            rotation_deg=0.0,
        )

        geom = compute_spiral_geometry(spec)

        # For nearly circular: arc length ≈ r × θ = 50 × 2π ≈ 314 mm
        assert abs(geom.total_length_mm - 314.2) < 5.0

    def test_offset_center(self):
        """Test spiral with offset center."""
        spec = SpiralSpec(
            center_x_mm=50.0,
            center_y_mm=-30.0,
            start_radius_mm=20.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )

        geom = compute_spiral_geometry(spec)

        # First point should be approximately start_radius from center
        first_x, first_y = geom.centerline[0]
        dist_from_center = ((first_x - 50.0) ** 2 + (first_y + 30.0) ** 2) ** 0.5
        assert abs(dist_from_center - 20.0) < 0.1
