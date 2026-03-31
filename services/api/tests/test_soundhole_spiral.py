"""
Tests for logarithmic concha spiral soundhole generator.
"""

import tempfile
from pathlib import Path

import pytest

from app.woodworking.soundhole_spiral import (
    SpiralSoundholeSpec,
    compute_spiral_geometry,
    generate_dxf,
)


class TestSpiralGeometryBasic:
    """Basic geometry computation tests."""

    def test_spiral_geometry_basic(self):
        """Test basic spiral geometry computation."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,  # Dreadnought upper bout
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
            center_x_mm=0.0,
            center_y_mm=0.0,
        )

        geom = compute_spiral_geometry(spec)

        # Should have points
        assert len(geom.centerline_points) == 100  # default num_points
        assert len(geom.outer_wall) == 100
        assert len(geom.inner_wall) == 100

        # Area should be positive and reasonable
        # For a spiral with ~0.85 turns, 8mm slot, starting at 20mm radius
        # Area should be roughly: length * width
        assert geom.area_mm2 > 0
        assert geom.area_mm2 < 10000  # Sanity upper bound

        # Perimeter should be positive
        assert geom.perimeter_mm > 0

        # Total length should be positive
        assert geom.total_length_mm > 0

        # P:A ratio should be positive
        assert geom.pa_ratio_mm_inv > 0

    def test_spiral_grows_outward(self):
        """Test that spiral radius increases along the path."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=1.0,
            growth_rate=20.0,
        )

        geom = compute_spiral_geometry(spec)

        # First point should be closer to center than last point
        first_x, first_y = geom.centerline_points[0]
        last_x, last_y = geom.centerline_points[-1]

        first_r = (first_x**2 + first_y**2) ** 0.5
        last_r = (last_x**2 + last_y**2) ** 0.5

        assert last_r > first_r, "Spiral should grow outward"

    def test_slot_width_affects_area(self):
        """Test that wider slots produce larger area."""
        base_spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=6.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        wide_spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=12.0,  # Double width
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        base_geom = compute_spiral_geometry(base_spec)
        wide_geom = compute_spiral_geometry(wide_spec)

        assert wide_geom.area_mm2 > base_geom.area_mm2


class TestPARatio:
    """Perimeter to area ratio tests for acoustic properties."""

    def test_pa_ratio_above_threshold(self):
        """
        Verify P:A ratio is above 0.10 for good acoustic coupling.

        A higher P:A ratio means more perimeter per unit area,
        which can affect how the soundhole couples with the air cavity.
        """
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        geom = compute_spiral_geometry(spec)

        # P:A ratio should be > 0.10 for acoustic coupling
        assert geom.pa_ratio_mm_inv > 0.10, (
            f"P:A ratio {geom.pa_ratio_mm_inv:.4f} is below threshold 0.10. "
            f"Area={geom.area_mm2:.1f}mm², Perimeter={geom.perimeter_mm:.1f}mm"
        )

    def test_narrow_slot_higher_pa_ratio(self):
        """Narrower slots should have higher P:A ratio."""
        narrow_spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=4.0,  # Narrow
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        wide_spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=12.0,  # Wide
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        narrow_geom = compute_spiral_geometry(narrow_spec)
        wide_geom = compute_spiral_geometry(wide_spec)

        # Narrower slot = higher P:A ratio (more edge per area)
        assert narrow_geom.pa_ratio_mm_inv > wide_geom.pa_ratio_mm_inv


class TestDXFExport:
    """DXF export smoke tests."""

    def test_dxf_export(self):
        """Smoke test for DXF export."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "spiral_soundhole.dxf"
            result_path = generate_dxf(spec, output_path)

            # File should exist
            assert result_path.exists()
            assert result_path.suffix == ".dxf"

            # File should have content
            assert result_path.stat().st_size > 0

    def test_dxf_contains_layers(self):
        """Test that DXF contains expected layers."""
        import ezdxf

        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "spiral_soundhole.dxf"
            generate_dxf(spec, output_path)

            # Read back and verify layers
            doc = ezdxf.readfile(str(output_path))
            layer_names = [layer.dxf.name for layer in doc.layers]

            assert "SPIRAL_CENTERLINE" in layer_names
            assert "SPIRAL_OUTER_WALL" in layer_names
            assert "SPIRAL_INNER_WALL" in layer_names
            assert "BOUT_REFERENCE" in layer_names


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_zero_turns(self):
        """Test handling of zero turns (degenerate case)."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.0,  # Zero turns
            growth_rate=15.0,
        )

        geom = compute_spiral_geometry(spec)

        # Should still produce valid output
        assert len(geom.centerline_points) == 100

    def test_small_start_radius(self):
        """Test with small starting radius."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=5.0,  # Very small
            spiral_turns=1.5,
            growth_rate=25.0,
        )

        geom = compute_spiral_geometry(spec)

        assert geom.area_mm2 > 0
        assert geom.total_length_mm > 0

    def test_offset_center(self):
        """Test spiral with offset center."""
        spec = SpiralSoundholeSpec(
            bout_radius_mm=195.0,
            slot_width_mm=8.0,
            spiral_start_r_mm=20.0,
            spiral_turns=0.85,
            growth_rate=15.0,
            center_x_mm=50.0,
            center_y_mm=-30.0,
        )

        geom = compute_spiral_geometry(spec)

        # First point should be near the offset center
        first_x, first_y = geom.centerline_points[0]
        dist_from_center = ((first_x - 50.0) ** 2 + (first_y + 30.0) ** 2) ** 0.5

        # Should be approximately spiral_start_r_mm from center
        assert abs(dist_from_center - 20.0) < 1.0
