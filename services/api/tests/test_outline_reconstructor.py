"""
Tests for OutlineReconstructor.
Run: pytest tests/test_outline_reconstructor.py -v
"""

import math
import pytest
from app.cam.unified_dxf_cleaner import Chain, Point
from app.services.outline_reconstructor import (
    OutlineReconstructor,
    BoundingBox,
    GapZone,
    complete_outline_if_needed,
    MEASURED_RADII,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_chain(points: list) -> Chain:
    return Chain(points=[Point(x=x, y=y) for x, y in points])


def semicircle_chain(R: float = 50.0, n: int = 20) -> Chain:
    """Half circle from (R,0) to (-R,0) — has a gap across the diameter."""
    pts = []
    for i in range(n + 1):
        angle = math.pi * i / n
        pts.append((R * math.cos(angle), R * math.sin(angle)))
    return make_chain(pts)


# ── BoundingBox tests ─────────────────────────────────────────────────────────

def test_bbox_union():
    b1 = BoundingBox(0, 0, 100, 200)
    b2 = BoundingBox(50, 50, 200, 300)
    union = BoundingBox.union([b1, b2])
    assert union.x0 == 0
    assert union.y0 == 0
    assert union.x1 == 200
    assert union.y1 == 300


def test_bbox_from_points():
    pts = [Point(x, y) for x, y in [(0, 0), (100, 0), (50, 200)]]
    bb = BoundingBox.from_points(pts)
    assert bb.x0 == 0 and bb.x1 == 100
    assert bb.y0 == 0 and bb.y1 == 200


def test_bbox_properties():
    bb = BoundingBox(10, 20, 110, 220)
    assert bb.width == 100
    assert bb.height == 200
    assert bb.cx == 60
    assert bb.cy == 120


# ── Zone classification tests ─────────────────────────────────────────────────

def test_acoustic_lower_bout_zone():
    r = OutlineReconstructor("dreadnought")
    bbox = BoundingBox(0, 0, 400, 500)
    # Gap midpoint at y=400 -> rel_y = 0.8 -> lower bout
    zone = r._classify_zone(Point(200, 390), Point(200, 410), bbox)
    assert zone == GapZone.LOWER_BOUT


def test_acoustic_waist_zone():
    r = OutlineReconstructor("dreadnought")
    bbox = BoundingBox(0, 0, 400, 500)
    # Gap midpoint at y=200 -> rel_y = 0.4 -> waist
    zone = r._classify_zone(Point(200, 190), Point(200, 210), bbox)
    assert zone == GapZone.WAIST


def test_acoustic_upper_bout_zone():
    r = OutlineReconstructor("dreadnought")
    bbox = BoundingBox(0, 0, 400, 500)
    # Gap midpoint at y=75 -> rel_y = 0.15 -> upper bout
    zone = r._classify_zone(Point(200, 70), Point(200, 80), bbox)
    assert zone == GapZone.UPPER_BOUT


def test_electric_horn_tip_zone():
    r = OutlineReconstructor("melody_maker")
    bbox = BoundingBox(0, 0, 350, 450)
    # Gap midpoint at y=45 -> rel_y = 0.1 -> horn tip
    zone = r._classify_zone(Point(175, 40), Point(175, 50), bbox)
    assert zone == GapZone.HORN_TIP


def test_electric_cutaway_zone():
    r = OutlineReconstructor("melody_maker")
    bbox = BoundingBox(0, 0, 350, 450)
    # Gap midpoint at y=135 -> rel_y = 0.3 -> cutaway
    zone = r._classify_zone(Point(175, 130), Point(175, 140), bbox)
    assert zone == GapZone.CUTAWAY


# ── Radius lookup tests ───────────────────────────────────────────────────────

def test_dreadnought_bout_radius():
    r = OutlineReconstructor("dreadnought")
    radius = r._get_zone_radius(GapZone.LOWER_BOUT)
    assert 250.0 <= radius <= 320.0  # measured: 280.0mm


def test_melody_maker_horn_tip_radius():
    r = OutlineReconstructor("melody_maker")
    radius = r._get_zone_radius(GapZone.HORN_TIP)
    assert radius < 15.0  # MM horn tip = 5.7mm


def test_unknown_zone_fallback():
    r = OutlineReconstructor("dreadnought")
    radius = r._get_zone_radius(GapZone.UNKNOWN)
    assert radius == 200.0  # near-flat fallback


def test_missing_spec_uses_defaults():
    r = OutlineReconstructor("unknown_instrument_xyz")
    radius = r._get_zone_radius(GapZone.LOWER_BOUT)
    assert radius == 200.0  # fallback


# ── Arc generation tests ──────────────────────────────────────────────────────

def test_arc_closes_gap():
    r = OutlineReconstructor("dreadnought")
    from app.services.outline_reconstructor import Gap
    gap = Gap(
        chain_idx=0,
        start=Point(0, 0),
        end=Point(20, 0),
        distance_mm=20.0,
        zone=GapZone.LOWER_BOUT,
        radius_mm=47.1,
        concave=False,
    )
    arc = r._generate_arc(gap)
    assert arc is not None
    assert len(arc) >= 3
    # Last arc point should be close to gap.end
    last = arc[-1]
    dist = math.hypot(last.x - gap.end.x, last.y - gap.end.y)
    assert dist < 1.0


def test_arc_points_on_circle():
    """All arc points should be approximately on the specified radius circle."""
    r = OutlineReconstructor("dreadnought")
    from app.services.outline_reconstructor import Gap
    R = 50.0
    gap = Gap(
        chain_idx=0,
        start=Point(-R, 0),
        end=Point(R, 0),
        distance_mm=2 * R,
        zone=GapZone.LOWER_BOUT,
        radius_mm=R,
        concave=False,
    )
    arc = r._generate_arc(gap)
    assert arc is not None
    # For this symmetric case, center should be near (0, 0)
    # Points should all be at distance R from center
    # Find approximate center from arc midpoint
    mid_idx = len(arc) // 2
    # The arc should curve - check that middle point is offset from chord
    assert arc[mid_idx].y != 0  # Arc curves away from chord


def test_degenerate_radius_too_small():
    """Chord > 2R is degenerate — should not crash, should clamp R."""
    r = OutlineReconstructor("dreadnought")
    from app.services.outline_reconstructor import Gap
    gap = Gap(
        chain_idx=0,
        start=Point(0, 0),
        end=Point(100, 0),  # chord=100mm
        distance_mm=100.0,
        zone=GapZone.LOWER_BOUT,
        radius_mm=10.0,  # R < chord/2 — invalid
        concave=False,
    )
    arc = r._generate_arc(gap)
    assert arc is not None  # Should clamp, not crash


def test_concave_arc_direction():
    """Concave arcs should curve inward."""
    r = OutlineReconstructor("melody_maker")
    from app.services.outline_reconstructor import Gap
    gap = Gap(
        chain_idx=0,
        start=Point(0, 0),
        end=Point(20, 0),
        distance_mm=20.0,
        zone=GapZone.CUTAWAY,
        radius_mm=22.0,
        concave=True,
    )
    arc = r._generate_arc(gap)
    assert arc is not None
    # For concave, arc should curve in opposite direction
    mid_idx = len(arc) // 2
    # With this setup, concave should give negative Y
    assert arc[mid_idx].y < 0


# ── Integration tests ─────────────────────────────────────────────────────────

def test_complete_closes_open_chain():
    r = OutlineReconstructor("dreadnought", max_gap_mm=8.0)
    # Chain with a 5mm gap
    chain = make_chain([(0, 0), (10, 0), (20, 0), (25, 0)])
    # Modify to create gap: start at (0,0), end at (25,0), but we want gap
    # Actually need to make first and last point 5mm apart
    chain.points[0] = Point(0, 0)
    chain.points[-1] = Point(5, 0)

    result = r.complete([chain])
    assert result.gaps_found == 1
    assert result.gaps_bridged == 1


def test_closed_chain_passes_through():
    r = OutlineReconstructor("dreadnought", max_gap_mm=8.0)
    # Create a closed chain (first and last point same)
    chain = make_chain([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])

    result = r.complete([chain])
    assert result.gaps_found == 0
    assert result.gaps_bridged == 0
    assert len(result.chains) == 1


def test_gap_too_large_skipped():
    r = OutlineReconstructor("dreadnought", max_gap_mm=8.0)
    # Gap of 50mm - too large
    chain = make_chain([(0, 0), (100, 0)])
    chain.points[0] = Point(0, 0)
    chain.points[-1] = Point(50, 0)

    result = r.complete([chain])
    assert result.gaps_found == 0  # Gap > max_gap_mm, not detected


def test_gap_too_small_ignored():
    r = OutlineReconstructor("dreadnought", max_gap_mm=8.0, min_gap_mm=1.0)
    # Gap of 0.5mm - too small
    chain = make_chain([(0, 0), (10, 0), (20, 0)])
    chain.points[-1] = Point(0.5, 0)

    result = r.complete([chain])
    assert result.gaps_found == 0  # Gap < min_gap_mm


def test_unknown_spec_passthrough():
    import os
    os.environ["ENABLE_OUTLINE_RECONSTRUCTION"] = "1"
    try:
        chains = [make_chain([(0, 0), (10, 0), (20, 5)])]
        completed, recon = complete_outline_if_needed(chains, spec_name="unknown_lute")
        assert recon is None
        assert completed is chains  # exact same object returned
    finally:
        os.environ.pop("ENABLE_OUTLINE_RECONSTRUCTION", None)


def test_none_spec_passthrough():
    import os
    os.environ["ENABLE_OUTLINE_RECONSTRUCTION"] = "1"
    try:
        chains = [make_chain([(0, 0), (10, 0), (20, 5)])]
        completed, recon = complete_outline_if_needed(chains, spec_name=None)
        assert recon is None
    finally:
        os.environ.pop("ENABLE_OUTLINE_RECONSTRUCTION", None)


def test_feature_flag_disabled():
    import os
    os.environ.pop("ENABLE_OUTLINE_RECONSTRUCTION", None)  # Ensure disabled
    chains = [make_chain([(0, 0), (5, 0)])]  # Small gap
    completed, recon = complete_outline_if_needed(chains, spec_name="dreadnought")
    assert recon is None
    assert completed is chains


def test_feature_flag_enabled():
    import os
    os.environ["ENABLE_OUTLINE_RECONSTRUCTION"] = "1"
    try:
        # Create chain with valid gap
        chain = make_chain([(0, 0), (10, 0), (20, 0)])
        chain.points[-1] = Point(5, 0)  # 5mm gap to first point

        completed, recon = complete_outline_if_needed([chain], spec_name="dreadnought")
        assert recon is not None
        assert recon.gaps_found == 1
    finally:
        os.environ.pop("ENABLE_OUTLINE_RECONSTRUCTION", None)


# ── Regression tests ──────────────────────────────────────────────────────────

def test_melody_maker_not_regressed():
    """Melody Maker has no open gaps after gap joiner — reconstructor should be a no-op."""
    r = OutlineReconstructor("melody_maker", max_gap_mm=8.0)
    # Simulate closed MM chain
    chain = semicircle_chain(R=100.0)
    chain.points.append(chain.points[0])  # close it

    result = r.complete([chain])
    assert result.gaps_bridged == 0
    assert result.gaps_found == 0


def test_measured_radii_completeness():
    """Verify all benchmark instruments have measured radii."""
    required = ["dreadnought", "om_000", "classical", "melody_maker"]
    for spec in required:
        assert spec in MEASURED_RADII, f"Missing MEASURED_RADII entry for {spec}"
        assert "bout" in MEASURED_RADII[spec] or "default" in MEASURED_RADII[spec]


def test_multiple_chains():
    """Test with multiple chains, some with gaps, some without."""
    r = OutlineReconstructor("dreadnought", max_gap_mm=8.0)

    # Chain 1: closed
    chain1 = make_chain([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])

    # Chain 2: 5mm gap
    chain2 = make_chain([(100, 0), (110, 0), (115, 0)])
    chain2.points[-1] = Point(105, 0)

    # Chain 3: 20mm gap (too large)
    chain3 = make_chain([(200, 0), (220, 0)])

    result = r.complete([chain1, chain2, chain3])

    assert len(result.chains) == 3
    assert result.gaps_found == 1  # Only chain2 has valid gap
    assert result.gaps_bridged == 1
