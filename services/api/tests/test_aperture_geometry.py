"""
Tests for ApertureGeometry common output model.

Verifies:
- Equivalent diameter round-trip for known areas
- Spiral conversion preserves corrected area/perimeter/path length
- P:A ratio remains 2/slot_width for constant-width spirals
- Graceful handling of missing spec metadata
"""

import math
import pytest

from app.instrument_geometry.soundhole.aperture_geometry import (
    ApertureGeometry,
    equivalent_diameter_from_area,
    aperture_from_spiral_geometry,
)
from app.instrument_geometry.soundhole.spiral_geometry import (
    SpiralSpec,
    SpiralGeometry,
    compute_spiral_geometry,
)


class TestEquivalentDiameter:
    """Tests for equivalent_diameter_from_area helper."""

    def test_round_trip_100mm_diameter(self):
        """Area of 100mm circle → equivalent diameter → should return 100mm."""
        diameter = 100.0
        area = math.pi * (diameter / 2) ** 2
        computed_diameter = equivalent_diameter_from_area(area)
        assert abs(computed_diameter - diameter) < 0.001

    def test_round_trip_standard_soundhole_diameters(self):
        """Verify round-trip for standard soundhole sizes."""
        standard_diameters = [88.9, 95.25, 101.6, 102.0]  # 3.5", 3.75", 4", carlos_jumbo

        for d in standard_diameters:
            area = math.pi * (d / 2) ** 2
            computed = equivalent_diameter_from_area(area)
            assert abs(computed - d) < 0.001, f"Round-trip failed for {d}mm"

    def test_zero_area_returns_zero(self):
        """Zero area should return zero diameter."""
        assert equivalent_diameter_from_area(0.0) == 0.0

    def test_negative_area_returns_zero(self):
        """Negative area should return zero diameter (graceful fallback)."""
        assert equivalent_diameter_from_area(-100.0) == 0.0

    def test_known_area_value(self):
        """Test with known area: 1000 mm² → d ≈ 35.68 mm."""
        area = 1000.0
        expected = 2.0 * math.sqrt(1000.0 / math.pi)  # ≈ 35.68
        computed = equivalent_diameter_from_area(area)
        assert abs(computed - expected) < 0.01


class TestSpiralConversion:
    """Tests for aperture_from_spiral_geometry conversion."""

    def test_preserves_corrected_area(self):
        """Converted aperture should preserve spiral's corrected area."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.area_mm2 == geo.area_mm2
        assert aperture.area_mm2 > 1500  # Corrected formula gives ~1950 mm²

    def test_preserves_corrected_perimeter(self):
        """Converted aperture should preserve spiral's corrected perimeter."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.perimeter_mm == geo.perimeter_mm
        assert aperture.perimeter_mm > 250  # 2 × arc_length ≈ 278 mm

    def test_preserves_path_length(self):
        """Converted aperture should preserve spiral's total arc length."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.path_length_mm == geo.total_length_mm
        assert aperture.path_length_mm > 100  # Corrected arc length ≈ 139 mm

    def test_computes_equivalent_diameter(self):
        """Converted aperture should compute valid equivalent diameter."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        expected_eq_d = equivalent_diameter_from_area(geo.area_mm2)
        assert abs(aperture.equivalent_diameter_mm - expected_eq_d) < 0.001

    def test_sets_aperture_type_spiral(self):
        """Converted aperture should have type 'spiral'."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.aperture_type == "spiral"

    def test_extracts_characteristic_width_from_spec(self):
        """Converted aperture should extract slot_width as characteristic_width."""
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=14.0,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.characteristic_width_mm == 14.0


class TestPARatioInvariant:
    """Tests for P:A ratio = 2/slot_width invariant."""

    def test_pa_ratio_equals_2_over_slot_width(self):
        """P:A ratio should be 2/slot_width for constant-width spiral."""
        slot_width = 14.0
        spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.1,
            slot_width_mm=slot_width,
            rotation_deg=0.0,
        )
        geo = compute_spiral_geometry(spec)
        aperture = aperture_from_spiral_geometry(geo)

        expected_pa = 2.0 / slot_width
        assert abs(aperture.pa_ratio_mm_inv - expected_pa) < 0.001

    def test_pa_ratio_invariant_across_k_values(self):
        """P:A ratio should be constant regardless of growth rate k."""
        slot_width = 14.0
        expected_pa = 2.0 / slot_width

        for k in [0.10, 0.15, 0.18, 0.25, 0.30]:
            spec = SpiralSpec(
                center_x_mm=0.0,
                center_y_mm=0.0,
                start_radius_mm=10.0,
                growth_rate_k=k,
                turns=1.0,
                slot_width_mm=slot_width,
                rotation_deg=0.0,
            )
            geo = compute_spiral_geometry(spec)
            aperture = aperture_from_spiral_geometry(geo)

            assert abs(aperture.pa_ratio_mm_inv - expected_pa) < 0.001, f"Failed for k={k}"

    def test_narrower_slot_higher_pa_ratio(self):
        """Narrower slots should have higher P:A ratio."""
        narrow_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=8.0,
            rotation_deg=0.0,
        )
        wide_spec = SpiralSpec(
            center_x_mm=0.0,
            center_y_mm=0.0,
            start_radius_mm=10.0,
            growth_rate_k=0.18,
            turns=1.0,
            slot_width_mm=16.0,
            rotation_deg=0.0,
        )

        narrow_aperture = aperture_from_spiral_geometry(compute_spiral_geometry(narrow_spec))
        wide_aperture = aperture_from_spiral_geometry(compute_spiral_geometry(wide_spec))

        assert narrow_aperture.pa_ratio_mm_inv > wide_aperture.pa_ratio_mm_inv


class TestMissingSpecHandling:
    """Tests for graceful handling of missing spec metadata."""

    def test_none_spec_sets_characteristic_width_none(self):
        """When geo.spec is None, characteristic_width_mm should be None."""
        geo = SpiralGeometry(
            centerline=[],
            outer_wall=[],
            inner_wall=[],
            area_mm2=1000.0,
            perimeter_mm=200.0,
            pa_ratio_mm_inv=0.2,
            end_radius_mm=30.0,
            total_length_mm=100.0,
            spec=None,  # No spec attached
        )
        aperture = aperture_from_spiral_geometry(geo)

        assert aperture.characteristic_width_mm is None
        assert aperture.area_mm2 == 1000.0
        assert aperture.perimeter_mm == 200.0
        assert aperture.path_length_mm == 100.0
        assert aperture.aperture_type == "spiral"

    def test_none_spec_does_not_raise(self):
        """Conversion should not raise when spec is None."""
        geo = SpiralGeometry(
            centerline=[],
            outer_wall=[],
            inner_wall=[],
            area_mm2=500.0,
            perimeter_mm=100.0,
            pa_ratio_mm_inv=0.2,
            end_radius_mm=20.0,
            total_length_mm=50.0,
            spec=None,
        )
        # Should not raise
        aperture = aperture_from_spiral_geometry(geo)
        assert aperture is not None
