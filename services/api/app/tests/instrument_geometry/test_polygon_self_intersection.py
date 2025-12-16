"""
Polygon self-intersection detection tests.

Target: instrument_geometry/tests/test_polygon_self_intersection.py
"""
from app.instrument_geometry.queries.polygon_self_intersection import first_self_intersection, try_split_single_bowtie


def test_detects_bowtie_self_intersection():
    # A classic bow-tie polygon (self-intersecting)
    ring = [
        (0.0, 0.0),
        (2.0, 2.0),
        (0.0, 2.0),
        (2.0, 0.0),
    ]
    hit = first_self_intersection(ring)
    
    assert hit is not None
    assert hit.p[0] == hit.p[0]  # not NaN


def test_splits_bowtie_into_two_rings():
    ring = [
        (0.0, 0.0),
        (2.0, 2.0),
        (0.0, 2.0),
        (2.0, 0.0),
    ]
    hit = first_self_intersection(ring)
    
    assert hit is not None
    split = try_split_single_bowtie(ring, hit)
    
    assert split is not None
    rA, rB = split
    assert len(rA) >= 3
    assert len(rB) >= 3


def test_simple_square_has_no_self_intersection():
    ring = [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ]
    hit = first_self_intersection(ring)
    
    assert hit is None


def test_concave_polygon_has_no_self_intersection():
    # Concave but not self-intersecting
    ring = [
        (0.0, 0.0),
        (3.0, 0.0),
        (3.0, 1.0),
        (1.5, 0.5),  # inward dent
        (3.0, 2.0),
        (3.0, 3.0),
        (0.0, 3.0),
    ]
    hit = first_self_intersection(ring)
    
    assert hit is None
