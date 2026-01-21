from __future__ import annotations
"""
Unit tests for topology helpers in services.api.app.mesh.o3d_heal:
 - _edge_map_from_triangles
 - _boundary_loops

We use tiny synthetic triangle sets so behavior is deterministic and does not
depend on Open3D. These match/extend the scaffold example OBJ (single triangle).
"""
import numpy as np
from services.api.app.mesh.o3d_heal import _edge_map_from_triangles, _boundary_loops


def test_edge_map_counts_single_triangle():
    # One triangle (like examples/retopo/intake.obj)
    F = np.array([[0, 1, 2]], dtype=np.int64)
    ecounts = _edge_map_from_triangles(F)
    # 3 undirected edges, each seen once
    assert len(ecounts) == 3
    assert sorted(ecounts.values()) == [1, 1, 1]
    # boundary edges == all three; they form one boundary loop
    assert _boundary_loops(ecounts) == 1


def test_boundary_loops_two_triangles_forming_quad():
    # Two triangles sharing an interior diagonal: quad split into two tris
    # Vertices: 0--1
    #           | /|
    #           |/ |
    #           2--3
    #
    # Faces (share edge 1-2 as diagonal):
    F = np.array([[0, 1, 2], [1, 3, 2]], dtype=np.int64)
    ecounts = _edge_map_from_triangles(F)
    # Edges:
    #  (0,1):1, (1,2):2, (0,2):1, (1,3):1, (2,3):1  => 5 unique edges
    assert len(ecounts) == 5
    # Exactly one interior edge with count 2 (the shared diagonal), others are boundary
    counts = sorted(ecounts.values())
    assert counts.count(2) == 1
    assert counts.count(1) == 4
    # Boundary edges (count==1) should form a single outer loop
    assert _boundary_loops(ecounts) == 1


def test_boundary_loops_disconnected_two_triangles():
    # Two disconnected triangles -> two separate boundary loops
    F = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.int64)
    ecounts = _edge_map_from_triangles(F)
    # 6 edges total, each seen once
    assert len(ecounts) == 6
    assert all(c == 1 for c in ecounts.values())
    # Two disjoint boundary components
    assert _boundary_loops(ecounts) == 2


def test_boundary_loops_ring_square_no_hole_after_triangulation():
    # A square as two triangles should have ONE boundary loop (the perimeter),
    # not two; covered implicitly by the two-triangle test above.
    F = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)
    ecounts = _edge_map_from_triangles(F)
    assert _boundary_loops(ecounts) == 1


def test_boundary_loops_annulus_ring_has_two_loops():
    """
    Synthetic "ring" (annulus) triangulation:
    - Outer square: 0-1-2-3 (counterclockwise)
    - Inner square (hole boundary): 4-5-6-7 (counterclockwise)
    We fill only the *ring* between outer and inner boundaries with triangles.
    Expected: two boundary loops (outer perimeter and inner hole perimeter).
    """
    # Faces connect each outer edge to the corresponding inner edge via two triangles.
    # Side 0-1 ↔ 4-5:
    #   (0,1,5), (0,5,4)
    # Side 1-2 ↔ 5-6:
    #   (1,2,6), (1,6,5)
    # Side 2-3 ↔ 6-7:
    #   (2,3,7), (2,7,6)
    # Side 3-0 ↔ 7-4:
    #   (3,0,4), (3,4,7)
    F = np.array([
        [0, 1, 5], [0, 5, 4],
        [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6],
        [3, 0, 4], [3, 4, 7],
    ], dtype=np.int64)

    ecounts = _edge_map_from_triangles(F)
    # Expect exactly two disjoint boundary cycles: outer (0-1-2-3) and inner (4-5-6-7)
    loops = _boundary_loops(ecounts)
    assert loops == 2, f"expected 2 boundary loops (outer + inner hole), got {loops}"
