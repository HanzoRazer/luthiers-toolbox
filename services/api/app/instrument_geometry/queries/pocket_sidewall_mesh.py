"""
Pocket sidewall mesh generator.

Builds a vertical sidewall mesh by extruding a closed 2D outline
from z_top down to z_floor. CAM-friendly: no caps, deterministic.

Target: instrument_geometry/queries/pocket_sidewall_mesh.py
"""
from __future__ import annotations

from typing import List, Tuple

from ..models.mesh import TriangleMesh
from ..queries.truss_union_outline_pipeline2d import get_truss_union_outline_final_2d


def build_pocket_sidewall_mesh(
    geom,
    *,
    z_top_mm: float,
    z_floor_mm: float,
) -> TriangleMesh:
    """
    Build a vertical sidewall mesh by extruding a closed 2D outline
    from z_top down to z_floor.
    
    Assumes outline is ordered and closed.
    Creates only the vertical walls - no caps (top/bottom) by design.
    Deterministic vertex indexing.
    """
    outline = get_truss_union_outline_final_2d(geom)
    pts2d = outline.points

    if not pts2d:
        return TriangleMesh(vertices=[], triangles=[])

    # Ensure closure without duplicating final segment
    if _same_xy(pts2d[0], pts2d[-1]):
        pts = pts2d[:-1]
    else:
        pts = pts2d[:]

    n = len(pts)
    if n < 2:
        return TriangleMesh(vertices=[], triangles=[])

    vertices: List[Tuple[float, float, float]] = []
    triangles: List[Tuple[int, int, int]] = []

    # Create two rings of vertices: top and bottom
    top_idx = []
    bot_idx = []

    for p in pts:
        top_idx.append(len(vertices))
        vertices.append((float(p.x_mm), float(p.y_mm), float(z_top_mm)))

    for p in pts:
        bot_idx.append(len(vertices))
        vertices.append((float(p.x_mm), float(p.y_mm), float(z_floor_mm)))

    # Build sidewall quads → two triangles per edge
    for i in range(n):
        i2 = (i + 1) % n
        t0 = top_idx[i]
        t1 = top_idx[i2]
        b0 = bot_idx[i]
        b1 = bot_idx[i2]
        # Winding chosen to keep normals outward (right-hand rule)
        triangles.append((t0, b0, b1))
        triangles.append((t0, b1, t1))

    return TriangleMesh(vertices=vertices, triangles=triangles)


def _same_xy(a, b, tol: float = 1e-9) -> bool:
    return abs(float(a.x_mm) - float(b.x_mm)) <= tol and abs(float(a.y_mm) - float(b.y_mm)) <= tol
