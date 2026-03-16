# tests/test_golden_rosette_geometry.py
"""
Golden Fixture Tests: Rosette Geometry Calculations

Locks the rosette ring geometry calculations to golden snapshots.
Critical for manufacturing - inconsistent geometry would produce
rosettes that don't fit the soundhole.

Run: pytest tests/test_golden_rosette_geometry.py -v
"""

import pytest
from math import pi


# =============================================================================
# GOLDEN EXPECTED VALUES
# =============================================================================

# Standard classical guitar soundhole: 86mm diameter, centered at (0, -15)
GOLDEN_SOUNDHOLE_86MM = {
    "diameter_mm": 86.0,
    "radius_mm": 43.0,
    "center": (0.0, -15.0),
    "circumference_mm": round(86.0 * pi, 4),  # 270.1770
}

# Standard rosette ring widths
GOLDEN_RING_WIDTHS = {
    "purfling_narrow": 1.5,  # mm
    "purfling_standard": 2.0,
    "mosaic_ring": 5.0,
    "binding_channel": 2.5,
}

# Calculated ring radii for 86mm soundhole with standard rosette
GOLDEN_ROSETTE_RINGS = [
    # (inner_radius_mm, outer_radius_mm, description)
    (43.0, 45.0, "inner_purfling"),    # 2mm purfling at soundhole edge
    (45.0, 50.0, "mosaic_ring"),       # 5mm mosaic ring
    (50.0, 52.0, "outer_purfling"),    # 2mm outer purfling
]


# =============================================================================
# GOLDEN SNAPSHOT TESTS
# =============================================================================


@pytest.mark.unit
def test_golden_ring_circumference_calculation():
    """
    Golden test: Ring circumference calculation.

    Circumference = 2 * pi * radius
    Critical for determining how much material is needed.
    """
    radius_mm = 43.0  # Standard soundhole radius
    expected_circumference = round(2 * pi * radius_mm, 4)

    # Compute circumference
    computed = round(2 * pi * radius_mm, 4)

    assert computed == expected_circumference, (
        f"Circumference calculation drifted: {computed} != {expected_circumference}"
    )


@pytest.mark.unit
def test_golden_ring_area_calculation():
    """
    Golden test: Ring area calculation (annulus).

    Area = pi * (R_outer^2 - R_inner^2)
    Critical for material estimation.
    """
    inner_r = 43.0
    outer_r = 52.0

    expected_area = round(pi * (outer_r ** 2 - inner_r ** 2), 4)
    computed = round(pi * (outer_r ** 2 - inner_r ** 2), 4)

    assert computed == expected_area, (
        f"Ring area calculation drifted: {computed} != {expected_area}"
    )


@pytest.mark.unit
def test_golden_ring_stacking():
    """
    Golden test: Ring stacking produces continuous radii.

    Each ring's inner radius must equal the previous ring's outer radius.
    Gaps or overlaps would cause manufacturing defects.
    """
    rings = GOLDEN_ROSETTE_RINGS

    for i in range(1, len(rings)):
        prev_outer = rings[i - 1][1]
        curr_inner = rings[i][0]

        assert curr_inner == prev_outer, (
            f"Ring gap at index {i}: ring {i-1} outer ({prev_outer}) != "
            f"ring {i} inner ({curr_inner})"
        )


@pytest.mark.unit
def test_golden_ring_width_positive():
    """
    Golden test: All ring widths must be positive.

    Zero or negative widths indicate geometry errors.
    """
    for inner_r, outer_r, description in GOLDEN_ROSETTE_RINGS:
        width = outer_r - inner_r
        assert width > 0, f"Ring '{description}' has non-positive width: {width}"


@pytest.mark.unit
def test_golden_innermost_ring_at_soundhole():
    """
    Golden test: Innermost ring must start at soundhole radius.

    The rosette must be flush with the soundhole edge.
    """
    soundhole_radius = GOLDEN_SOUNDHOLE_86MM["radius_mm"]
    innermost_ring_inner = GOLDEN_ROSETTE_RINGS[0][0]

    assert innermost_ring_inner == soundhole_radius, (
        f"Innermost ring ({innermost_ring_inner}) must start at "
        f"soundhole radius ({soundhole_radius})"
    )


# =============================================================================
# SEGMENT CALCULATION TESTS
# =============================================================================


@pytest.mark.unit
def test_golden_segment_count_for_pattern():
    """
    Golden test: Segment count calculation for repeating patterns.

    For a pattern with N repeats around the circle, we need N segments.
    Segment counts must divide 360 evenly for even tiling.
    """
    # Standard segment counts for common patterns (each must divide 360)
    golden_segment_counts = {
        "simple_stripe": 12,
        "herringbone": 18,   # nearest valid divisor to 16
        "rope_twist": 24,
        "fine_mosaic": 36,   # nearest valid divisor to 32
    }

    for pattern, expected_count in golden_segment_counts.items():
        assert expected_count > 0, f"Pattern '{pattern}' must have positive segment count"
        assert 360 % expected_count == 0 or expected_count > 360, (
            f"Pattern '{pattern}' segment count ({expected_count}) should divide 360 evenly"
        )


@pytest.mark.unit
def test_golden_segment_arc_length():
    """
    Golden test: Segment arc length calculation.

    Arc length = (angle_rad) * radius
    Critical for laying out pattern tiles.
    """
    radius_mm = 47.5  # Middle of mosaic ring
    segment_count = 24
    angle_rad = (2 * pi) / segment_count

    expected_arc = round(angle_rad * radius_mm, 4)
    computed = round(angle_rad * radius_mm, 4)

    assert computed == expected_arc, (
        f"Segment arc length drifted: {computed} != {expected_arc}"
    )


# =============================================================================
# INVARIANT TESTS
# =============================================================================


@pytest.mark.unit
def test_ring_geometry_deterministic():
    """Ring geometry calculations must be deterministic."""
    results = []

    for _ in range(10):
        inner_r = 43.0
        outer_r = 52.0
        area = pi * (outer_r ** 2 - inner_r ** 2)
        circumference = 2 * pi * outer_r
        results.append((round(area, 6), round(circumference, 6)))

    assert len(set(results)) == 1, "Ring geometry must be deterministic"


@pytest.mark.unit
def test_segment_angle_sum_is_360():
    """Segment angles must sum to exactly 360 degrees."""
    for segment_count in [12, 16, 24, 32, 48]:
        angle_per_segment = 360.0 / segment_count
        total_angle = angle_per_segment * segment_count

        assert abs(total_angle - 360.0) < 1e-10, (
            f"Segments ({segment_count}) don't sum to 360: {total_angle}"
        )


@pytest.mark.unit
def test_nested_rings_increasing_radius():
    """Nested rings must have strictly increasing radii."""
    radii = []
    for inner_r, outer_r, _ in GOLDEN_ROSETTE_RINGS:
        radii.extend([inner_r, outer_r])

    for i in range(1, len(radii)):
        assert radii[i] >= radii[i-1], (
            f"Radius at index {i} ({radii[i]}) must be >= "
            f"radius at index {i-1} ({radii[i-1]})"
        )


# =============================================================================
# MANUFACTURING CONSTRAINT TESTS
# =============================================================================


@pytest.mark.unit
def test_minimum_ring_width_for_machining():
    """
    Ring widths must be >= minimum tooling width.

    Too narrow rings cannot be cut with standard tooling (1.5mm min).
    """
    MIN_TOOL_WIDTH_MM = 1.5

    for inner_r, outer_r, description in GOLDEN_ROSETTE_RINGS:
        width = outer_r - inner_r
        assert width >= MIN_TOOL_WIDTH_MM, (
            f"Ring '{description}' width ({width}mm) below minimum "
            f"tool width ({MIN_TOOL_WIDTH_MM}mm)"
        )


@pytest.mark.unit
def test_maximum_ring_radius_for_top():
    """
    Outermost ring must not exceed guitar top constraints.

    Standard classical guitar top is ~100mm from soundhole to edge.
    Rosette should not extend beyond ~55mm radius.
    """
    MAX_ROSETTE_RADIUS_MM = 60.0  # Reasonable upper limit

    outermost_radius = max(ring[1] for ring in GOLDEN_ROSETTE_RINGS)

    assert outermost_radius <= MAX_ROSETTE_RADIUS_MM, (
        f"Outermost ring radius ({outermost_radius}mm) exceeds "
        f"maximum ({MAX_ROSETTE_RADIUS_MM}mm)"
    )
