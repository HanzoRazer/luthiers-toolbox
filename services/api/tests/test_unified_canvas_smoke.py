# tests/test_unified_canvas_smoke.py

"""
Smoke tests for unified fretboard↔headstock canvas.

VINE-05: Verifies UnifiedInlayCanvas provides correct coordinate transforms
between fretboard and headstock regions.
"""

import pytest
import math

from app.calculators.unified_canvas import (
    UnifiedInlayCanvas,
    FretboardParams,
    HeadstockParams,
    CanvasRegion,
    UnifiedCanvasRequest,
    create_unified_canvas,
)
from app.generators.neck_headstock_config import HeadstockStyle


class TestUnifiedCanvasBasics:
    """Basic canvas functionality tests."""

    def test_canvas_creates_with_defaults(self):
        """Canvas creates successfully with default parameters."""
        canvas = UnifiedInlayCanvas()
        assert canvas is not None
        assert canvas.fretboard.scale_length_mm == 648.0
        assert canvas.headstock.style == HeadstockStyle.GIBSON_SOLID

    def test_canvas_creates_with_custom_params(self):
        """Canvas creates with custom Gibson J-45 parameters."""
        fretboard = FretboardParams(
            scale_length_mm=628.65,  # Gibson 24.75"
            nut_width_mm=43.0,
            heel_width_mm=55.0,
            fret_count=20,  # Acoustic
        )
        headstock = HeadstockParams(
            style=HeadstockStyle.GIBSON_SOLID,
            angle_deg=17.0,
            length_mm=178.0,
        )
        canvas = UnifiedInlayCanvas(fretboard=fretboard, headstock=headstock)

        assert canvas.fretboard.scale_length_mm == 628.65
        assert canvas.fretboard.fret_count == 20
        assert canvas.headstock.angle_deg == 17.0


class TestRegionDetection:
    """Region detection tests (VINE-05 requirement)."""

    def test_region_at_nut_is_transition(self):
        """X=0 (nut) is in transition zone."""
        canvas = UnifiedInlayCanvas()
        region = canvas.get_region(0.0)
        assert region == CanvasRegion.NUT_TRANSITION

    def test_region_positive_x_is_fretboard(self):
        """Positive X is fretboard region."""
        canvas = UnifiedInlayCanvas()
        region = canvas.get_region(100.0)
        assert region == CanvasRegion.FRETBOARD

    def test_region_negative_x_is_headstock(self):
        """Negative X is headstock region."""
        canvas = UnifiedInlayCanvas()
        region = canvas.get_region(-50.0)
        assert region == CanvasRegion.HEADSTOCK

    def test_region_beyond_fretboard(self):
        """Position beyond last fret is BEYOND_HEEL."""
        canvas = UnifiedInlayCanvas()
        # 22nd fret is around 481mm from nut for 648mm scale
        region = canvas.get_region(500.0)
        assert region == CanvasRegion.BEYOND_HEEL


class TestBoundingContour:
    """get_bounding_contour_at_x tests (VINE-05 test expectations)."""

    def test_contour_at_nut_returns_nut_width(self):
        """canvas.get_bounding_contour_at_x(0) returns nut width."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(nut_width_mm=43.0)
        )
        y_min, y_max = canvas.get_bounding_contour_at_x(0.0)

        # Symmetric around centerline
        assert y_max == pytest.approx(21.5, abs=0.1)  # Half of 43mm
        assert y_min == pytest.approx(-21.5, abs=0.1)
        assert y_max - y_min == pytest.approx(43.0, abs=0.1)

    def test_contour_at_fretboard_is_wider(self):
        """canvas.get_bounding_contour_at_x(100) returns wider width."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(
                nut_width_mm=43.0,
                heel_width_mm=57.0,
            )
        )
        y_min, y_max = canvas.get_bounding_contour_at_x(100.0)
        width = y_max - y_min

        # Should be wider than nut but narrower than heel
        assert width > 43.0
        assert width < 57.0

    def test_contour_at_headstock_returns_headstock_bounds(self):
        """canvas.get_bounding_contour_at_x(-50) returns headstock width."""
        canvas = UnifiedInlayCanvas(
            headstock=HeadstockParams(style=HeadstockStyle.GIBSON_SOLID)
        )
        y_min, y_max = canvas.get_bounding_contour_at_x(-50.0)

        # Should have non-zero width in headstock region
        width = y_max - y_min
        assert width > 0, "Headstock should have positive width at x=-50mm"

    def test_bounding_width_convenience_method(self):
        """get_bounding_width_at_x returns correct width."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(nut_width_mm=43.0)
        )
        width = canvas.get_bounding_width_at_x(0.0)
        assert width == pytest.approx(43.0, abs=0.1)


class TestFretPositions:
    """Fret position calculation tests."""

    def test_fret_position_at_12th(self):
        """12th fret is at half scale length."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(scale_length_mm=648.0)
        )
        pos = canvas.fret_position_mm(12)

        # 12th fret should be at scale_length / 2
        assert pos == pytest.approx(324.0, abs=0.5)

    def test_fret_midpoint(self):
        """Fret midpoint is between two frets."""
        canvas = UnifiedInlayCanvas()
        mid = canvas.fret_midpoint_mm(5)
        pos_4 = canvas.fret_position_mm(4)
        pos_5 = canvas.fret_position_mm(5)

        expected = (pos_4 + pos_5) / 2.0
        assert mid == pytest.approx(expected, abs=0.1)


class TestHeadstockOutline:
    """Headstock outline tests."""

    def test_headstock_outline_has_points(self):
        """Headstock outline returns points in mm."""
        canvas = UnifiedInlayCanvas(
            headstock=HeadstockParams(style=HeadstockStyle.GIBSON_SOLID)
        )
        outline = canvas.get_headstock_outline_mm()

        assert len(outline) > 10, "Gibson solid should have >10 outline points"

    def test_headstock_points_are_negative_x(self):
        """Headstock points have negative X (toward tuners)."""
        canvas = UnifiedInlayCanvas()
        outline = canvas.get_headstock_outline_mm()

        # Most points should have negative X
        negative_x_count = sum(1 for x, y in outline if x <= 0)
        assert negative_x_count >= len(outline) - 2  # Allow for nut endpoints

    def test_headstock_styles_produce_different_outlines(self):
        """Different headstock styles produce different outlines."""
        canvas_gibson = UnifiedInlayCanvas(
            headstock=HeadstockParams(style=HeadstockStyle.GIBSON_SOLID)
        )
        canvas_fender = UnifiedInlayCanvas(
            headstock=HeadstockParams(style=HeadstockStyle.FENDER_STRAT)
        )

        outline_gibson = canvas_gibson.get_headstock_outline_mm()
        outline_fender = canvas_fender.get_headstock_outline_mm()

        # Should have different point counts or positions
        assert outline_gibson != outline_fender


class TestCoordinateTransforms:
    """Headstock angle coordinate transform tests."""

    def test_fretboard_coords_unchanged(self):
        """Fretboard coordinates are not affected by headstock angle."""
        canvas = UnifiedInlayCanvas(
            headstock=HeadstockParams(angle_deg=17.0)
        )
        x, y = canvas.apply_headstock_angle_2d(100.0, 20.0)

        assert x == 100.0
        assert y == 20.0

    def test_headstock_coords_foreshortened(self):
        """Headstock X coords are foreshortened by cos(angle)."""
        canvas = UnifiedInlayCanvas(
            headstock=HeadstockParams(angle_deg=17.0)
        )
        original_x = -100.0
        x, y = canvas.apply_headstock_angle_2d(original_x, 0.0)

        expected_x = original_x * math.cos(math.radians(17.0))
        assert x == pytest.approx(expected_x, abs=0.1)
        assert y == 0.0

    def test_headstock_z_height(self):
        """headstock_3d_z_at_x returns correct Z drop."""
        canvas = UnifiedInlayCanvas(
            headstock=HeadstockParams(angle_deg=17.0)
        )

        # At nut (x=0), Z should be 0
        assert canvas.headstock_3d_z_at_x(0.0) == 0.0

        # On headstock (negative X), Z should be negative
        z = canvas.headstock_3d_z_at_x(-100.0)
        assert z < 0, "Headstock Z should be below fretboard plane"


class TestPointInBounds:
    """Point-in-bounds tests."""

    def test_point_on_centerline_in_fretboard(self):
        """Point on centerline in fretboard is in bounds."""
        canvas = UnifiedInlayCanvas()
        assert canvas.is_point_in_bounds(100.0, 0.0) is True

    def test_point_outside_fretboard_width(self):
        """Point outside fretboard width is out of bounds."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(nut_width_mm=43.0)
        )
        # 50mm from centerline is outside 43mm wide fretboard
        assert canvas.is_point_in_bounds(0.0, 50.0) is False


class TestCanvasBounds:
    """Overall canvas bounds tests."""

    def test_canvas_bounds_includes_headstock(self):
        """Canvas bounds include headstock (negative X)."""
        canvas = UnifiedInlayCanvas()
        bounds = canvas.get_canvas_bounds()

        assert bounds["x_min"] < 0, "Headstock should extend into negative X"

    def test_canvas_bounds_includes_fretboard(self):
        """Canvas bounds include fretboard to last fret."""
        canvas = UnifiedInlayCanvas(
            fretboard=FretboardParams(fret_count=22, scale_length_mm=648.0)
        )
        bounds = canvas.get_canvas_bounds()

        # 22nd fret is around 481mm
        assert bounds["x_max"] > 400


class TestAPIFactory:
    """Factory function tests."""

    def test_create_from_request(self):
        """create_unified_canvas creates canvas from request."""
        request = UnifiedCanvasRequest(
            scale_length_mm=628.65,
            nut_width_mm=43.0,
            fret_count=20,
            headstock_style="gibson_solid",
            headstock_angle_deg=17.0,
        )
        canvas = create_unified_canvas(request)

        assert canvas.fretboard.scale_length_mm == 628.65
        assert canvas.fretboard.fret_count == 20
        assert canvas.headstock.angle_deg == 17.0

    def test_invalid_headstock_style_defaults(self):
        """Invalid headstock style falls back to gibson_solid."""
        request = UnifiedCanvasRequest(
            headstock_style="nonexistent_style"
        )
        canvas = create_unified_canvas(request)

        assert canvas.headstock.style == HeadstockStyle.GIBSON_SOLID
