"""
Tests for CAM G-code bug fixes:
1. G83/G73 expanded peck drilling terminates (no infinite loop)
2. Arc direction detection (G2 for CW, G3 for CCW)
"""

import pytest
from app.cam.modal_cycles import generate_g83_peck_drill, generate_g73_chip_break
from app.core.rmos_gcode_materials import emit_segment_with_params


class TestG83ExpandedTerminates:
    """G83 expanded peck drill must terminate (not infinite loop)."""

    def test_g83_expanded_terminates(self):
        """G83 expanded mode completes without hanging."""
        holes = [{"x": 10.0, "y": 10.0}]
        depth = -20.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        peck_depth = 5.0

        # This would hang forever if current_depth not updated
        lines, stats = generate_g83_peck_drill(
            holes=holes,
            depth=depth,
            retract=retract,
            feed=feed,
            safe_z=safe_z,
            peck_depth=peck_depth,
            use_modal=False  # Expanded mode
        )

        # Verify it completed and produced output
        assert len(lines) > 0
        assert stats["cycle"] == "G83"
        assert stats["mode"] == "expanded"

        # Verify peck sequence has multiple Z moves
        z_moves = [ln for ln in lines if "Z" in ln]
        assert len(z_moves) >= 4  # At least retract + multiple pecks

    def test_g73_expanded_terminates(self):
        """G73 expanded mode completes without hanging."""
        holes = [{"x": 5.0, "y": 5.0}]
        depth = -15.0
        retract = 2.0
        feed = 250.0
        safe_z = 10.0
        peck_depth = 3.0

        # This would hang forever if current_depth not updated
        lines, stats = generate_g73_chip_break(
            holes=holes,
            depth=depth,
            retract=retract,
            feed=feed,
            safe_z=safe_z,
            peck_depth=peck_depth,
            chip_break_retract=0.5,
            use_modal=False  # Expanded mode
        )

        # Verify it completed
        assert len(lines) > 0
        assert stats["cycle"] == "G73"
        assert stats["mode"] == "expanded"


class TestArcDirectionDetection:
    """Arc direction must use cross-product to determine G2/G3."""

    def test_cw_arc_produces_g2(self):
        """Clockwise arc (cross < 0) must emit G2."""
        # CW arc: from (10, 0) to (0, 10) around center (0, 0)
        # Cross product: (x2-x1)*(cy-y1) - (y2-y1)*(cx-x1)
        # = (0-10)*(0-0) - (10-0)*(0-10)
        # = (-10)*0 - 10*(-10) = 0 + 100 = 100 > 0 -> CCW
        #
        # For CW: from (0, 10) to (10, 0) around center (0, 0)
        # = (10-0)*(0-10) - (0-10)*(0-0)
        # = 10*(-10) - (-10)*0 = -100 < 0 -> CW
        segment = {
            "type": "arc",
            "x1": 0.0,
            "y1": 10.0,
            "x2": 10.0,
            "y2": 0.0,
            "cx": 0.0,
            "cy": 0.0,
        }
        params = {"feed_rate_mm_min": 500}

        lines = emit_segment_with_params(segment, params)
        gcode = "\n".join(lines)

        # Should be G2 (clockwise)
        assert "G2" in gcode, f"Expected G2 for CW arc, got: {gcode}"
        assert "G3" not in gcode

    def test_ccw_arc_produces_g3(self):
        """Counter-clockwise arc (cross > 0) must emit G3."""
        # CCW arc: from (10, 0) to (0, 10) around center (0, 0)
        # Cross = (0-10)*(0-0) - (10-0)*(0-10) = 0 - (-100) = 100 > 0 -> CCW
        segment = {
            "type": "arc",
            "x1": 10.0,
            "y1": 0.0,
            "x2": 0.0,
            "y2": 10.0,
            "cx": 0.0,
            "cy": 0.0,
        }
        params = {"feed_rate_mm_min": 500}

        lines = emit_segment_with_params(segment, params)
        gcode = "\n".join(lines)

        # Should be G3 (counter-clockwise)
        assert "G3" in gcode, f"Expected G3 for CCW arc, got: {gcode}"
        assert "G2" not in gcode
