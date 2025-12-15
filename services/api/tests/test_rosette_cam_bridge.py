"""
Art Studio Bundle 5: Rosette CAM Bridge Tests

Smoke tests for rosette_cam_bridge.py:
- plan_rosette_toolpath() - Toolpath generation
- postprocess_toolpath_grbl() - G-code post-processing

Run with:
    pytest tests/test_rosette_cam_bridge.py -v
"""

import pytest
from app.services.rosette_cam_bridge import (
    plan_rosette_toolpath,
    postprocess_toolpath_grbl,
    RosetteGeometry,
    CamParams,
)


def test_rosette_plan_toolpath_smoke():
    """Test basic toolpath planning."""
    # Simple 50mm rosette
    geom = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=25.0,
        outer_radius_mm=50.0,
        units="mm",
    )
    
    params = CamParams(
        tool_diameter_mm=6.0,
        stepover_pct=0.45,  # 45% stepover
        stepdown_mm=1.5,
        feed_xy_mm_min=1200,
        safe_z_mm=5.0,
        cut_depth_mm=3.0,
    )
    
    moves, stats = plan_rosette_toolpath(geom, params, circle_segments=32)
    
    # Validate moves
    assert len(moves) > 0, "Should generate moves"
    assert isinstance(moves, list), "Moves should be a list"
    
    # Check first move is a retract
    assert moves[0]["code"] == "G0", "First move should be rapid"
    assert "z" in moves[0], "First move should have Z"
    assert moves[0]["z"] == params.safe_z_mm, "First move should be safe retract"
    
    # Validate stats
    assert "rings" in stats, "Stats should include ring count"
    assert "z_passes" in stats, "Stats should include Z pass count"
    assert "length_mm" in stats, "Stats should include toolpath length"
    assert "move_count" in stats, "Stats should include move count"
    
    assert stats["rings"] > 0, "Should have at least one ring"
    assert stats["z_passes"] == 2, "Should have 2 Z passes (3mm / 1.5mm)"
    assert stats["length_mm"] > 100, "Toolpath should be reasonably long"
    assert stats["move_count"] == len(moves), "Move count should match actual moves"
    
    print(f"✓ Toolpath generated: {stats['rings']} rings, {stats['z_passes']} Z passes, {stats['length_mm']:.1f}mm")


def test_rosette_post_gcode_smoke():
    """Test G-code post-processing."""
    # Generate a simple toolpath first
    geom = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=20.0,
        outer_radius_mm=40.0,
        units="mm",
    )
    
    params = CamParams(
        tool_diameter_mm=6.0,
        stepover_pct=0.5,
        stepdown_mm=2.0,
        feed_xy_mm_min=1000,
        safe_z_mm=5.0,
        cut_depth_mm=2.0,
    )
    
    moves, _ = plan_rosette_toolpath(geom, params, circle_segments=16)
    
    # Post-process to G-code
    gcode, stats = postprocess_toolpath_grbl(moves, units="mm", spindle_rpm=18000)
    
    # Validate G-code
    assert len(gcode) > 0, "Should generate G-code"
    assert isinstance(gcode, str), "G-code should be a string"
    
    lines = gcode.strip().split("\n")
    assert len(lines) > 10, "Should have multiple G-code lines"
    
    # Check header
    assert "G21" in gcode, "Should have G21 (mm units)"
    assert "G90" in gcode, "Should have G90 (absolute positioning)"
    assert "G17" in gcode, "Should have G17 (XY plane)"
    assert "M3" in gcode, "Should have M3 (spindle on)"
    assert "S18000" in gcode, "Should have spindle RPM"
    
    # Check footer
    assert "M5" in gcode, "Should have M5 (spindle off)"
    assert "M30" in gcode, "Should have M30 (program end)"
    
    # Validate stats
    assert "lines" in stats, "Stats should include line count"
    assert "bytes" in stats, "Stats should include byte count"
    
    assert stats["lines"] == len(lines), "Line count should match actual lines"
    assert stats["bytes"] == len(gcode), "Byte count should match actual bytes"
    
    print(f"✓ G-code generated: {stats['lines']} lines, {stats['bytes']} bytes")
    print(f"✓ First 10 lines:\n" + "\n".join(lines[:10]))


def test_rosette_toolpath_units_inch():
    """Test toolpath generation with inch units."""
    geom = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=1.0,  # 1 inch (treated as mm by dataclass)
        outer_radius_mm=2.0,  # 2 inches
        units="inch",
    )
    
    params = CamParams(
        tool_diameter_mm=0.25,  # 1/4" end mill
        stepover_pct=0.5,
        stepdown_mm=0.1,
        feed_xy_mm_min=40,  # 40 ipm
        safe_z_mm=0.2,
        cut_depth_mm=0.125,  # 1/8" deep
    )
    
    moves, stats = plan_rosette_toolpath(geom, params, circle_segments=24)
    
    assert len(moves) > 0, "Should generate moves in inch units"
    assert stats["rings"] > 0, "Should have rings in inch calculation"
    
    # Post-process with inch units
    gcode, gcode_stats = postprocess_toolpath_grbl(moves, units="inch", spindle_rpm=12000)
    
    assert "G20" in gcode, "Should have G20 (inch units)"
    assert "G21" not in gcode, "Should not have G21 (mm units)"
    
    print(f"✓ Inch units: {stats['rings']} rings, {stats['length_mm']:.3f} (units in inch)")


def test_rosette_multiple_z_passes():
    """Test toolpath with multiple Z passes."""
    geom = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=15.0,
        outer_radius_mm=30.0,
        units="mm",
    )
    
    params = CamParams(
        tool_diameter_mm=3.0,
        stepover_pct=0.4,
        stepdown_mm=1.0,  # 1mm per pass
        feed_xy_mm_min=800,
        safe_z_mm=5.0,
        cut_depth_mm=5.0,  # 5mm total depth = 5 passes
    )
    
    moves, stats = plan_rosette_toolpath(geom, params, circle_segments=32)
    
    assert stats["z_passes"] == 5, "Should have 5 Z passes (5mm / 1mm)"
    
    # Count Z plunge moves in toolpath
    z_plunges = [m for m in moves if m["code"] == "G1" and "z" in m and m["z"] < 0]
    assert len(z_plunges) >= 5, "Should have at least 5 plunge moves"
    
    print(f"✓ Multiple Z passes: {stats['z_passes']} passes, {len(z_plunges)} plunge moves")


def test_rosette_toolpath_edge_cases():
    """Test edge cases for toolpath generation."""
    # Very small rosette
    geom_small = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=3.0,
        outer_radius_mm=6.0,
        units="mm",
    )
    
    params_small = CamParams(
        tool_diameter_mm=2.0,
        stepover_pct=0.5,
        stepdown_mm=1.0,
        feed_xy_mm_min=600,
        safe_z_mm=3.0,
        cut_depth_mm=1.0,
    )
    
    moves_small, stats_small = plan_rosette_toolpath(geom_small, params_small)
    assert len(moves_small) > 0, "Should handle small rosettes"
    assert stats_small["rings"] >= 1, "Should have at least 1 ring for small rosette"
    
    # Large stepover (aggressive)
    params_aggressive = CamParams(
        tool_diameter_mm=12.0,  # Large tool
        stepover_pct=0.8,  # 80% stepover
        stepdown_mm=3.0,
        feed_xy_mm_min=2000,
        safe_z_mm=10.0,
        cut_depth_mm=6.0,
    )
    
    geom_large = RosetteGeometry(
        center_x_mm=0.0,
        center_y_mm=0.0,
        inner_radius_mm=30.0,
        outer_radius_mm=80.0,
        units="mm",
    )
    
    moves_aggressive, stats_aggressive = plan_rosette_toolpath(geom_large, params_aggressive)
    assert len(moves_aggressive) > 0, "Should handle aggressive stepover"
    assert stats_aggressive["rings"] < 10, "Aggressive stepover should reduce ring count"
    
    print(f"✓ Edge cases: small rosette {stats_small['rings']} rings, aggressive {stats_aggressive['rings']} rings")


if __name__ == "__main__":
    # Run tests directly (for quick debugging)
    print("=== Rosette CAM Bridge Tests ===\n")
    
    test_rosette_plan_toolpath_smoke()
    test_rosette_post_gcode_smoke()
    test_rosette_toolpath_units_inch()
    test_rosette_multiple_z_passes()
    test_rosette_toolpath_edge_cases()
    
    print("\n=== All Tests Passed ===")
