"""
Tests for GEOMETRY-003: Kerfing Geometry Calculator.
"""

import pytest
from app.calculators.kerfing_calc import (
    KerfingSpec,
    KerfingDimensions,
    compute_kerfing_schedule,
    compute_total_side_depth,
    compute_kerfing_dimensions,
    list_kerfing_types,
    get_kerfing_type_info,
    KERFING_TYPES,
)


class TestComputeKerfingSchedule:
    """Tests for compute_kerfing_schedule function."""

    def test_dreadnought_standard_kerfing(self):
        """Dreadnought with standard lining should use correct dimensions."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="dreadnought",
            kerfing_type="standard_lining",
        )
        assert spec.kerfing_type == "standard_lining"
        assert spec.side_depth_mm == 100.0
        assert spec.top_kerfing.height_mm == 7.94
        assert spec.top_kerfing.width_mm == 6.35
        assert spec.top_kerfing.kerf_spacing_mm == 3.0

    def test_total_depth_equals_side_plus_kerfing(self):
        """Total depth should equal side + top kerfing + back kerfing."""
        side_depth = 95.0
        spec = compute_kerfing_schedule(
            side_depth_mm=side_depth,
            body_style="om_000",
            kerfing_type="standard_lining",
        )
        expected_total = side_depth + spec.top_kerfing.height_mm + spec.back_kerfing.height_mm
        assert spec.total_side_depth_mm == expected_total

    def test_reverse_kerfing_taller_than_standard(self):
        """Reverse kerfing should be taller than standard lining."""
        standard = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="dreadnought",
            kerfing_type="standard_lining",
        )
        reverse = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="dreadnought",
            kerfing_type="reverse_kerfing",
        )
        assert reverse.top_kerfing.height_mm > standard.top_kerfing.height_mm
        assert reverse.top_kerfing.height_mm == 9.53

    def test_carbon_fiber_has_no_kerfs(self):
        """Carbon fiber kerfing should have no kerf slots."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="dreadnought",
            kerfing_type="carbon_fiber",
        )
        assert spec.top_kerfing.kerf_spacing_mm == 0.0
        assert spec.top_kerfing.kerf_depth_mm == 0.0
        assert spec.top_kerfing.material == "carbon_fiber"


class TestComputeTotalSideDepth:
    """Tests for compute_total_side_depth function."""

    def test_total_depth_calculation(self):
        """Total depth should be sum of side + top kerfing + back kerfing."""
        total = compute_total_side_depth(
            side_depth_mm=100.0,
            top_kerfing_height_mm=7.94,
            back_kerfing_height_mm=7.94,
        )
        assert total == 115.88

    def test_total_depth_with_different_kerfing_heights(self):
        """Total depth should handle different top and back kerfing heights."""
        total = compute_total_side_depth(
            side_depth_mm=95.0,
            top_kerfing_height_mm=7.94,
            back_kerfing_height_mm=9.53,
        )
        assert total == 112.47


class TestKerfingTypes:
    """Tests for kerfing type specifications."""

    def test_solid_lining_has_no_kerfs(self):
        """Solid lining should have no kerf slots."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="jumbo",
            kerfing_type="solid_lining",
        )
        assert spec.top_kerfing.kerf_spacing_mm == 0.0
        assert spec.top_kerfing.kerf_depth_mm == 0.0

    def test_laminate_lining_dimensions(self):
        """Laminate lining should have smaller height and tighter spacing."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="parlor",
            kerfing_type="laminate_lining",
        )
        assert spec.top_kerfing.height_mm == 6.35
        assert spec.top_kerfing.kerf_spacing_mm == 2.5
        assert "flexible" in spec.flexibility_note.lower()


class TestBodyStyleDefaults:
    """Tests for body style kerfing defaults."""

    def test_archtop_uses_solid_lining(self):
        """Archtop should default to solid lining for back."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="archtop",
        )
        # Archtop uses solid lining
        assert spec.back_kerfing.kerf_spacing_mm == 0.0

    def test_unknown_kerfing_type_defaults_to_standard(self):
        """Unknown kerfing type should default to standard lining."""
        spec = compute_kerfing_schedule(
            side_depth_mm=100.0,
            body_style="dreadnought",
            kerfing_type="unknown_type",
        )
        # Should fall back to body style default (standard_lining for dreadnought)
        assert spec.top_kerfing.height_mm == 7.94


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_list_kerfing_types(self):
        """list_kerfing_types should return all available types."""
        types = list_kerfing_types()
        assert "standard_lining" in types
        assert "reverse_kerfing" in types
        assert "carbon_fiber" in types
        assert len(types) == 5

    def test_get_kerfing_type_info(self):
        """get_kerfing_type_info should return type specifications."""
        info = get_kerfing_type_info("standard_lining")
        assert info["height_mm"] == 7.94
        assert info["has_kerfs"] is True
        assert info["flexibility"] == "flexible"
