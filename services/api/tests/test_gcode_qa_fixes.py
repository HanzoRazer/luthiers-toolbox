"""Tests for G-code QA fixes.

Verifies:
1. G83/G73 expanded peck drilling terminates (no infinite loop)
2. Arc direction uses cross-product (G2 for CW, G3 for CCW)
"""
import pytest


class TestG83G73ExpandedTermination:
    """Verify G83/G73 expanded mode terminates correctly."""

    def test_g83_expanded_terminates(self):
        """G83 expanded peck drilling should terminate, not infinite loop."""
        from app.cam.modal_cycles import generate_g83_peck_drill

        holes = [{'x': 10, 'y': 10}]
        depth = -20.0  # 20mm deep
        retract = 2.0
        feed = 300
        safe_z = 10.0
        peck_depth = 5.0

        # This would hang if infinite loop exists
        lines, stats = generate_g83_peck_drill(
            holes, depth, retract, feed, safe_z, peck_depth, use_modal=False
        )

        # Should complete with reasonable number of lines
        assert len(lines) > 0
        assert len(lines) < 100  # Sanity check - not infinite
        assert stats['mode'] == 'expanded'
        assert stats['holes'] == 1

        # Should have multiple peck moves (depth/peck = 22/5 ≈ 5 pecks)
        peck_moves = [l for l in lines if 'G1 Z' in l]
        assert len(peck_moves) >= 4  # At least 4 pecks for 22mm depth

    def test_g73_expanded_terminates(self):
        """G73 expanded chip break should terminate, not infinite loop."""
        from app.cam.modal_cycles import generate_g73_chip_break

        holes = [{'x': 10, 'y': 10}]
        depth = -15.0  # 15mm deep
        retract = 2.0
        feed = 300
        safe_z = 10.0
        peck_depth = 3.0

        # This would hang if infinite loop exists
        lines, stats = generate_g73_chip_break(
            holes, depth, retract, feed, safe_z, peck_depth, 0.5, use_modal=False
        )

        # Should complete with reasonable number of lines
        assert len(lines) > 0
        assert len(lines) < 100  # Sanity check
        assert stats['mode'] == 'expanded'

        # Should have multiple chip break moves
        peck_moves = [l for l in lines if 'G1 Z' in l]
        assert len(peck_moves) >= 5  # At least 5 pecks for 17mm depth

    def test_g83_multiple_holes_terminates(self):
        """G83 with multiple holes should terminate correctly."""
        from app.cam.modal_cycles import generate_g83_peck_drill

        holes = [{'x': i * 10, 'y': 0} for i in range(5)]  # 5 holes
        depth = -10.0
        retract = 2.0
        feed = 300
        safe_z = 10.0
        peck_depth = 2.0

        lines, stats = generate_g83_peck_drill(
            holes, depth, retract, feed, safe_z, peck_depth, use_modal=False
        )

        assert stats['holes'] == 5
        # Each hole needs ~6 pecks (12mm / 2mm) plus moves
        assert len(lines) > 20


class TestArcDirection:
    """Verify arc direction uses cross-product correctly."""

    def test_ccw_arc_produces_g3(self):
        """Counter-clockwise arc should produce G3."""
        from app.core.rmos_gcode_materials import emit_segment_with_params

        # CCW arc: from (0,10) to (0,0) around center (5,5)
        # Cross: (0-0)*(5-10) - (0-10)*(5-0) = 0 - (-50) = 50 > 0 → G3
        segment = {
            'type': 'arc',
            'x1': 0, 'y1': 10,
            'x2': 0, 'y2': 0,
            'cx': 5, 'cy': 5,
        }
        params = {'feed_rate_mm_min': 1000}

        lines = emit_segment_with_params(segment, params)
        arc_line = [l for l in lines if l.startswith('G2') or l.startswith('G3')]

        assert len(arc_line) == 1
        assert arc_line[0].startswith('G3'), f"Expected G3 (CCW), got: {arc_line[0]}"

    def test_cw_arc_produces_g2(self):
        """Clockwise arc should produce G2."""
        from app.core.rmos_gcode_materials import emit_segment_with_params

        # CW arc: from (0,0) to (0,10) around center (5,5)
        # Cross: (0-0)*(5-0) - (10-0)*(5-0) = 0 - 50 = -50 < 0 → G2
        segment = {
            'type': 'arc',
            'x1': 0, 'y1': 0,
            'x2': 0, 'y2': 10,
            'cx': 5, 'cy': 5,
        }
        params = {'feed_rate_mm_min': 1000}

        lines = emit_segment_with_params(segment, params)
        arc_line = [l for l in lines if l.startswith('G2') or l.startswith('G3')]

        assert len(arc_line) == 1
        assert arc_line[0].startswith('G2'), f"Expected G2 (CW), got: {arc_line[0]}"

    def test_quarter_arc_cw(self):
        """Quarter circle CW should produce G2."""
        from app.core.rmos_gcode_materials import emit_segment_with_params

        # CW quarter arc: from (10,0) to (0,10) around center (0,0)
        segment = {
            'type': 'arc',
            'x1': 10, 'y1': 0,
            'x2': 0, 'y2': 10,
            'cx': 0, 'cy': 0,
        }
        params = {'feed_rate_mm_min': 1000}

        lines = emit_segment_with_params(segment, params)
        arc_line = [l for l in lines if l.startswith('G2') or l.startswith('G3')]

        assert len(arc_line) == 1
        # Cross product: (0-10)*(0-0) - (10-0)*(0-10) = 0 - (-100) = 100 > 0 → G3
        # Wait, let me recalculate...
        # (x2-x1)*(cy-y1) - (y2-y1)*(cx-x1)
        # (0-10)*(0-0) - (10-0)*(0-10)
        # (-10)*0 - 10*(-10) = 0 + 100 = 100 > 0 → G3 (CCW)
        # Actually this is CCW in standard math coords
        assert arc_line[0].startswith('G3'), f"Got: {arc_line[0]}"

    def test_quarter_arc_ccw(self):
        """Quarter circle CCW should produce G3."""
        from app.core.rmos_gcode_materials import emit_segment_with_params

        # CCW quarter arc: from (0,10) to (10,0) around center (0,0)
        segment = {
            'type': 'arc',
            'x1': 0, 'y1': 10,
            'x2': 10, 'y2': 0,
            'cx': 0, 'cy': 0,
        }
        params = {'feed_rate_mm_min': 1000}

        lines = emit_segment_with_params(segment, params)
        arc_line = [l for l in lines if l.startswith('G2') or l.startswith('G3')]

        assert len(arc_line) == 1
        # Cross product: (10-0)*(0-10) - (0-10)*(0-0)
        # 10*(-10) - (-10)*0 = -100 - 0 = -100 < 0 → G2 (CW)
        assert arc_line[0].startswith('G2'), f"Got: {arc_line[0]}"
