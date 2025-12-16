"""
Ear clipping triangulation tests.

Target: instrument_geometry/tests/test_earclip_triangulation.py
"""
from app.instrument_geometry.queries.pocket_solid_mesh import _earclip_triangulate


def test_earclip_concave_polygon_triangulates():
    # Simple concave "arrow" polygon (non-self-intersecting)
    pts = [
        (0.0, 0.0),
        (3.0, 0.0),
        (3.0, 1.0),
        (1.5, 0.5),  # inward dent (concave)
        (3.0, 2.0),
        (3.0, 3.0),
        (0.0, 3.0),
    ]
    tris = _earclip_triangulate(pts, eps=1e-12, guard=10000)
    
    # A simple polygon with n vertices yields n-2 triangles
    assert len(tris) == len(pts) - 2


def test_earclip_simple_square():
    pts = [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ]
    tris = _earclip_triangulate(pts, eps=1e-12, guard=10000)
    
    assert len(tris) == 2  # 4 vertices -> 2 triangles


def test_earclip_simple_triangle():
    pts = [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.5, 1.0),
    ]
    tris = _earclip_triangulate(pts, eps=1e-12, guard=10000)
    
    assert len(tris) == 1  # 3 vertices -> 1 triangle
