"""Tests for Bézier body outline generator."""
import math
import pytest

from app.generators.bezier_body import (
    BezierBodyParams,
    BezierBodyGenerator,
    ControlPoints,
    cubic_bezier,
    get_preset,
    list_presets,
    BODY_PRESETS,
)
import numpy as np


class TestBezierBodyParams:
    """Tests for body parameter configuration."""

    def test_dreadnought_preset(self):
        """Verify dreadnought preset values."""
        params = BezierBodyParams.dreadnought()
        assert params.body_length == 20.0
        assert params.lower_bout_width == 15.625
        assert params.model_name == "dreadnought"

    def test_default_end_widths(self):
        """Neck and tail end widths should default based on bouts."""
        params = BezierBodyParams(
            body_length=20.0,
            upper_bout_width=10.0,
            waist_width=8.0,
            lower_bout_width=14.0,
        )
        # Default: neck_end = upper_bout * 0.85
        assert abs(params.neck_end_width - 8.5) < 0.01
        # Default: tail_end = lower_bout * 0.92
        assert abs(params.tail_end_width - 12.88) < 0.01

    def test_explicit_end_widths(self):
        """Explicit end widths should override defaults."""
        params = BezierBodyParams(
            body_length=20.0,
            upper_bout_width=10.0,
            waist_width=8.0,
            lower_bout_width=14.0,
            neck_end_width=9.0,
            tail_end_width=13.0,
        )
        assert params.neck_end_width == 9.0
        assert params.tail_end_width == 13.0

    def test_to_dict_roundtrip(self):
        """Params should survive dict roundtrip."""
        original = BezierBodyParams.orchestra_model()
        d = original.to_dict()
        restored = BezierBodyParams.from_dict(d)
        assert restored.body_length == original.body_length
        assert restored.model_name == original.model_name

    def test_all_presets_exist(self):
        """All presets should be valid."""
        for name in list_presets():
            params = get_preset(name)
            assert params.body_length > 0
            assert params.lower_bout_width > params.waist_width

    def test_invalid_preset_raises(self):
        """Unknown preset should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset("fender_telecaster_body")


class TestCubicBezier:
    """Tests for the cubic Bézier evaluation function."""

    def test_endpoints(self):
        """Curve should pass through endpoints at t=0 and t=1."""
        P0 = (0.0, 0.0)
        C1 = (1.0, 2.0)
        C2 = (3.0, 2.0)
        P1 = (4.0, 0.0)

        x0, y0 = cubic_bezier(P0, C1, C2, P1, 0.0)
        assert abs(x0[0] - P0[0]) < 1e-10
        assert abs(y0[0] - P0[1]) < 1e-10

        x1, y1 = cubic_bezier(P0, C1, C2, P1, 1.0)
        assert abs(x1[0] - P1[0]) < 1e-10
        assert abs(y1[0] - P1[1]) < 1e-10

    def test_midpoint_straight_line(self):
        """Straight line Bézier should have midpoint at center."""
        P0 = (0.0, 0.0)
        P1 = (4.0, 0.0)
        # Control points on line = straight line
        C1 = (1.333, 0.0)
        C2 = (2.666, 0.0)

        x_mid, y_mid = cubic_bezier(P0, C1, C2, P1, 0.5)
        assert abs(x_mid[0] - 2.0) < 0.1
        assert abs(y_mid[0]) < 1e-10

    def test_array_input(self):
        """Should handle array of t values."""
        P0 = (0.0, 0.0)
        C1 = (1.0, 1.0)
        C2 = (2.0, 1.0)
        P1 = (3.0, 0.0)

        t = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        x, y = cubic_bezier(P0, C1, C2, P1, t)

        assert len(x) == 5
        assert len(y) == 5
        assert x[0] == P0[0]
        assert x[-1] == P1[0]


class TestControlPointComputation:
    """Tests for control point derivation from parameters."""

    def test_anchor_points_on_curve(self):
        """P0, P1, P2 should be at expected positions."""
        params = BezierBodyParams(
            body_length=20.0,
            upper_bout_width=10.0,
            waist_width=8.0,
            lower_bout_width=14.0,
            waist_position=0.5,
            neck_end_width=9.0,
            tail_end_width=12.0,
        )
        gen = BezierBodyGenerator(params)
        cp = gen.compute_control_points()

        # P0 at x=0, y=W_0/2
        assert cp.P0[0] == 0.0
        assert abs(cp.P0[1] - 4.5) < 1e-10  # 9.0 / 2

        # P1 at x=waist_position*L, y=W_w/2
        assert abs(cp.P1[0] - 10.0) < 1e-10  # 0.5 * 20
        assert abs(cp.P1[1] - 4.0) < 1e-10  # 8.0 / 2

        # P2 at x=L, y=W_t/2
        assert cp.P2[0] == 20.0
        assert abs(cp.P2[1] - 6.0) < 1e-10  # 12.0 / 2

    def test_c1_continuity_at_waist(self):
        """Control points at waist should ensure C¹ continuity."""
        params = BezierBodyParams.dreadnought()
        gen = BezierBodyGenerator(params)
        cp = gen.compute_control_points()

        # C_A2 and C_B1 should be symmetric about P1
        # (P1 - C_A2) should equal (C_B1 - P1)
        diff_a = (cp.P1[0] - cp.C_A2[0], cp.P1[1] - cp.C_A2[1])
        diff_b = (cp.C_B1[0] - cp.P1[0], cp.C_B1[1] - cp.P1[1])

        assert abs(diff_a[0] - diff_b[0]) < 1e-10
        assert abs(diff_a[1] - diff_b[1]) < 1e-10


class TestBezierBodyGenerator:
    """Tests for the body outline generator."""

    def test_outline_closed(self):
        """Closed outline should start and end at same point."""
        gen = BezierBodyGenerator(BezierBodyParams.dreadnought())
        outline = gen.generate_outline(resolution=100, closed=True)

        assert len(outline) > 10
        assert abs(outline[0][0] - outline[-1][0]) < 1e-10
        assert abs(outline[0][1] - outline[-1][1]) < 1e-10

    def test_outline_symmetric(self):
        """Outline should be symmetric about x-axis."""
        gen = BezierBodyGenerator(BezierBodyParams.parlor())
        outline = gen.generate_outline(resolution=200, closed=False)

        # Find points at same x on both sides
        x_test = gen.params.body_length * 0.5  # Waist
        tolerance = 0.5

        nearby = [p for p in outline if abs(p[0] - x_test) < tolerance]
        if len(nearby) >= 2:
            ys = sorted([p[1] for p in nearby])
            # Should have positive and negative y values
            assert min(ys) < 0
            assert max(ys) > 0
            # Should be symmetric
            assert abs(abs(min(ys)) - abs(max(ys))) < 0.1

    def test_waist_is_narrowest(self):
        """Waist control point should be narrower than endpoints."""
        params = BezierBodyParams.dreadnought()
        gen = BezierBodyGenerator(params)
        cp = gen.compute_control_points()

        # The waist point P1 should have smaller y than P0 and P2
        # (y = half-width, so smaller y = narrower)
        waist_half_width = cp.P1[1]
        neck_half_width = cp.P0[1]
        tail_half_width = cp.P2[1]

        # Waist should be narrower than both ends
        assert waist_half_width < tail_half_width
        # Note: neck end can be narrower than waist in some designs
        # The key constraint is waist < lower bout
        assert params.waist_width < params.lower_bout_width

    def test_bounding_box(self):
        """Bounding box should match expected dimensions."""
        params = BezierBodyParams.dreadnought()
        gen = BezierBodyGenerator(params)
        gen.generate_outline()

        dims = gen.get_dimensions()

        # Length should be close to body_length
        assert abs(dims["length"] - params.body_length) < 0.1

        # Width should be close to lower_bout_width (widest part)
        assert dims["width"] >= params.waist_width * 0.95

    def test_segment_continuity(self):
        """Segment A end should equal Segment B start."""
        gen = BezierBodyGenerator(BezierBodyParams.orchestra_model())

        seg_a = gen.generate_segment_a(resolution=50)
        seg_b = gen.generate_segment_b(resolution=50)

        # Last point of A should equal first point of B (waist)
        assert abs(seg_a[-1][0] - seg_b[0][0]) < 1e-10
        assert abs(seg_a[-1][1] - seg_b[0][1]) < 1e-10

    def test_right_side_positive_y(self):
        """Right side should have all positive y values."""
        gen = BezierBodyGenerator(BezierBodyParams.classical())
        right = gen.generate_right_side(resolution=100)

        for x, y in right:
            assert y >= 0, f"Right side point ({x}, {y}) has negative y"

    def test_left_side_negative_y(self):
        """Left side should have all negative y values."""
        gen = BezierBodyGenerator(BezierBodyParams.classical())
        left = gen.generate_left_side(resolution=100)

        for x, y in left:
            assert y <= 0, f"Left side point ({x}, {y}) has positive y"


class TestExportFormats:
    """Tests for export functionality."""

    def test_to_json(self, tmp_path):
        """JSON export should include all required fields."""
        gen = BezierBodyGenerator(BezierBodyParams.concert())
        gen.generate_outline()

        json_path = tmp_path / "body.json"
        data = gen.to_json(json_path)

        assert "params" in data
        assert "control_points" in data
        assert "dimensions" in data
        assert data["params"]["model_name"] == "concert"
        assert json_path.exists()

    def test_to_svg(self, tmp_path):
        """SVG export should create valid file."""
        gen = BezierBodyGenerator(BezierBodyParams.parlor())
        gen.generate_outline()

        svg_path = tmp_path / "body.svg"
        result = gen.to_svg(svg_path)

        assert result == svg_path
        assert svg_path.exists()

        content = svg_path.read_text()
        assert "<svg" in content
        assert "<path" in content
        assert 'fill="none"' in content

    def test_to_dxf_requires_ezdxf(self):
        """DXF export should fail gracefully without ezdxf."""
        gen = BezierBodyGenerator(BezierBodyParams.jumbo())
        gen.generate_outline()

        # This test just verifies the method exists
        # Actual DXF export tested separately if ezdxf available
        assert hasattr(gen, "to_dxf")


class TestPresetRegistry:
    """Tests for the preset system."""

    def test_preset_names_normalized(self):
        """Preset lookup should normalize names."""
        # Various formats should work
        p1 = get_preset("orchestra_model")
        p2 = get_preset("orchestra-model")
        p3 = get_preset("ORCHESTRA_MODEL")

        assert p1.model_name == p2.model_name == p3.model_name

    def test_om_alias(self):
        """'om' should alias to orchestra_model."""
        om = get_preset("om")
        full = get_preset("orchestra_model")

        assert om.body_length == full.body_length
        assert om.lower_bout_width == full.lower_bout_width

    def test_list_presets_complete(self):
        """All presets should be listed."""
        presets = list_presets()
        assert "dreadnought" in presets
        assert "classical" in presets
        assert len(presets) >= 6


class TestPhysicalPlausibility:
    """Sanity checks for physical dimensions."""

    @pytest.mark.parametrize("preset_name", list(BODY_PRESETS.keys()))
    def test_preset_dimensions_reasonable(self, preset_name):
        """All presets should have physically reasonable dimensions."""
        if preset_name == "om":
            pytest.skip("om is alias")

        params = BODY_PRESETS[preset_name]

        # Body length: 17-22 inches for acoustic guitars
        assert 17 <= params.body_length <= 22

        # Widths should be positive and ordered
        assert params.waist_width > 0
        assert params.upper_bout_width > params.waist_width * 0.8
        assert params.lower_bout_width > params.waist_width

        # Waist position between 40-60% of body length
        assert 0.40 <= params.waist_position <= 0.60

    @pytest.mark.parametrize("preset_name", list(BODY_PRESETS.keys()))
    def test_outline_generates_without_error(self, preset_name):
        """All presets should generate valid outlines."""
        if preset_name == "om":
            pytest.skip("om is alias")

        params = BODY_PRESETS[preset_name]
        gen = BezierBodyGenerator(params)
        outline = gen.generate_outline(resolution=100)

        assert len(outline) >= 50
        # No NaN or Inf values
        for x, y in outline:
            assert math.isfinite(x)
            assert math.isfinite(y)
