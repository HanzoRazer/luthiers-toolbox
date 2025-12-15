"""
Test suite for N18 Spiral PolyCut System

Validates the production-grade polygon spiral pocketing engine with:
- Robust pyclipper offsetting (Phase 1)
- Ring-to-spiral stitching (Phase 2)  
- Arc smoothing for G2/G3 geometry (Phase 3)

Tests cover 3 canonical guitar geometry cases:
1. Small rect pocket (100×60mm)
2. Bridge slot (140×18mm)
3. Thin strip (200×12mm)
"""

import json
from pathlib import Path
import pytest

# Test baseline geometries
BASE = Path(__file__).parent / "baseline_n18"


def load_json(name: str):
    """Load JSON test geometry"""
    return json.loads((BASE / name).read_text())


def test_n18_baseline_files_exist():
    """Verify all baseline test files are present"""
    assert (BASE / "geom_small_rect.json").exists()
    assert (BASE / "geom_bridge_slot.json").exists()
    assert (BASE / "geom_thin_strip.json").exists()


def test_n18_small_rect_geometry():
    """Validate small rectangle test geometry"""
    geom = load_json("geom_small_rect.json")
    
    assert "outer" in geom
    assert len(geom["outer"]) == 5  # Closed rectangle
    assert geom["tool_d"] == 6.0
    assert geom["stepover"] == 0.45
    assert geom["margin"] == 0.5


def test_n18_bridge_slot_geometry():
    """Validate bridge slot test geometry"""
    geom = load_json("geom_bridge_slot.json")
    
    assert "outer" in geom
    assert len(geom["outer"]) == 5  # Closed rectangle
    assert geom["tool_d"] == 3.175  # 1/8" tool
    assert geom["stepover"] == 0.40
    assert geom["margin"] == 0.3


def test_n18_thin_strip_geometry():
    """Validate thin strip test geometry"""
    geom = load_json("geom_thin_strip.json")
    
    assert "outer" in geom
    assert len(geom["outer"]) == 5  # Closed rectangle
    assert geom["tool_d"] == 6.0
    assert geom["stepover"] == 0.35
    assert geom["margin"] == 0.0  # No margin for tight strip


def test_n18_poly_offset_spiral_import():
    """Verify N18 core module imports correctly"""
    from app.util.poly_offset_spiral import (
        offset_polygon_mm,
        generate_offset_rings,
        link_rings_to_spiral,
        build_spiral_poly,
        smooth_with_arcs,
    )
    
    # All Phase 1-3 functions should be importable
    assert callable(offset_polygon_mm)
    assert callable(generate_offset_rings)
    assert callable(link_rings_to_spiral)
    assert callable(build_spiral_poly)
    assert callable(smooth_with_arcs)


def test_n18_offset_polygon_simple():
    """Test Phase 1 - Basic polygon offsetting"""
    from app.util.poly_offset_spiral import offset_polygon_mm
    
    # Simple square
    outer = [(0, 0), (100, 0), (100, 100), (0, 100)]
    
    rings = offset_polygon_mm(outer, offset_step=10.0, max_rings=5)
    
    assert len(rings) > 0
    assert len(rings) <= 5  # Respects max_rings
    
    # Each ring should be smaller than previous
    for i in range(1, len(rings)):
        # Just verify structure (detailed area checks in integration tests)
        assert len(rings[i]) >= 3  # Valid polygon


def test_n18_generate_offset_rings():
    """Test Phase 2 - Ring generation with margin"""
    from app.util.poly_offset_spiral import generate_offset_rings
    
    outer = [(0, 0), (100, 0), (100, 60), (0, 60)]
    
    rings = generate_offset_rings(
        outer=outer,
        tool_d=6.0,
        stepover=0.45,
        margin=0.5,
    )
    
    assert len(rings) > 0
    
    # First ring should honor margin (roughly 3.5mm from edge: 3mm tool_radius + 0.5mm margin)
    # Detailed geometry checks in integration tests


def test_n18_link_rings_to_spiral():
    """Test Phase 2 - Spiral stitching"""
    from app.util.poly_offset_spiral import generate_offset_rings, link_rings_to_spiral
    
    outer = [(0, 0), (80, 0), (80, 50), (0, 50)]
    
    rings = generate_offset_rings(
        outer=outer,
        tool_d=6.0,
        stepover=0.45,
        margin=0.5,
    )
    
    spiral = link_rings_to_spiral(rings, climb=True)
    
    assert len(spiral) > 0
    assert isinstance(spiral[0], tuple)
    assert len(spiral[0]) == 2  # (x, y) tuples
    
    # Spiral should be continuous (no closure at end)
    # Spiral length should be roughly sum of ring perimeters


def test_n18_build_spiral_poly():
    """Test Phase 3 - Complete spiral builder"""
    from app.util.poly_offset_spiral import build_spiral_poly
    
    outer = [(0, 0), (100, 0), (100, 60), (0, 60)]
    
    spiral = build_spiral_poly(
        outer=outer,
        tool_d=6.0,
        stepover=0.45,
        margin=0.5,
        climb=True,
        corner_radius_min=1.0,
        corner_tol_mm=0.3,
    )
    
    assert len(spiral) > 0
    assert isinstance(spiral[0], tuple)
    
    # Verify spiral starts inside boundary (margin + tool_radius clearance)
    x0, y0 = spiral[0]
    assert x0 > 3  # Roughly 3mm from left edge
    assert y0 > 3  # Roughly 3mm from bottom


def test_n18_smooth_with_arcs():
    """Test Phase 3 - Arc smoothing"""
    from app.util.poly_offset_spiral import smooth_with_arcs
    
    # Path with sharp corners
    path = [(0, 0), (10, 0), (10, 10), (20, 10), (20, 20)]
    
    smoothed = smooth_with_arcs(
        path,
        corner_radius_min=1.0,
        corner_tol_mm=0.3,
    )
    
    assert len(smoothed) > len(path)  # Arc insertion adds points
    
    # First and last points should be preserved
    assert smoothed[0] == path[0]
    assert smoothed[-1] == path[-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
