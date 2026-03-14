"""
Inlay Geometry Transforms

Miter-join polygon offset, polyline offset, and collection-level transforms.

All coordinates in mm. Positive offset = outward / male, negative = inward / pocket.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from .inlay_geometry_core import (
    GeometryCollection,
    GeometryElement,
    Polyline,
    Pt,
)


def _normalize(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector to unit length."""
    length = math.hypot(x, y) or 1.0
    return x / length, y / length


def line_line_intersect(
    p1: Pt, p2: Pt, p3: Pt, p4: Pt,
) -> Optional[Pt]:
    """Determinant-based line–line intersection.

    Returns *None* if lines are (near-)parallel (det < 1e-10).
    """
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    det = d1x * d2y - d1y * d2x
    if abs(det) < 1e-10:
        return None
    t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / det
    return (p1[0] + t * d1x, p1[1] + t * d1y)


def offset_polyline(pts: Polyline, dist: float) -> Polyline:
    """Offset an *open* polyline by ``dist`` mm using per-vertex normals.

    Positive ``dist`` offsets to the left of the travel direction.
    """
    n = len(pts)
    if n < 2:
        return list(pts)
    result: Polyline = []
    for i in range(n):
        prev = pts[max(0, i - 1)]
        nxt = pts[min(n - 1, i + 1)]
        tx, ty = _normalize(nxt[0] - prev[0], nxt[1] - prev[1])
        nx, ny = -ty, tx
        result.append((pts[i][0] + nx * dist, pts[i][1] + ny * dist))
    return result


def offset_polygon(pts: Polyline, dist: float) -> Polyline:
    """Offset a *closed* polygon by ``dist`` mm using miter-join geometry.

    For each edge, shift by the outward normal × dist, then intersect
    adjacent offset edges at miter corners. Falls back to averaged
    normals when the intersection is degenerate.

    Positive = outward (for CCW winding).
    """
    n = len(pts)
    if n < 3:
        return list(pts)

    # Build per-edge offset segments
    edges: List[Tuple[Pt, Pt]] = []
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy) or 1.0
        # Outward normal for CCW winding: (dy, -dx) / len
        nx, ny = dy / length, -dx / length
        edges.append((
            (p1[0] + nx * dist, p1[1] + ny * dist),
            (p2[0] + nx * dist, p2[1] + ny * dist),
        ))

    result: Polyline = []
    for i in range(n):
        prev_edge = edges[(i - 1) % n]
        curr_edge = edges[i]
        hit = line_line_intersect(
            prev_edge[0], prev_edge[1],
            curr_edge[0], curr_edge[1],
        )
        if hit is not None:
            result.append(hit)
        else:
            # Fallback: midpoint of the two offset endpoints
            result.append((
                (prev_edge[1][0] + curr_edge[0][0]) * 0.5,
                (prev_edge[1][1] + curr_edge[0][1]) * 0.5,
            ))
    return result


def offset_polyline_strip(pts: Polyline, dist: float) -> Polyline:
    """Dual-rail closed strip around an open polyline.

    Returns a closed polygon: outer rail forward → inner rail reversed.
    Used for CNC pocket boundaries around vine stems, binding paths, etc.
    """
    if len(pts) < 2:
        return list(pts)
    outer = offset_polyline(pts, dist)
    inner = offset_polyline(pts, -dist)
    return outer + list(reversed(inner))


def offset_collection(
    geo: GeometryCollection,
    amount_mm: float,
) -> GeometryCollection:
    """Return a new collection with every element offset by *amount_mm*.

    * Polygons  → ``offset_polygon``
    * Polylines → ``offset_polyline``
    * Circles   → radius adjusted (clamped ≥ 0)
    * Rects     → expanded/contracted symmetrically
    """
    out_elements: List[GeometryElement] = []
    for el in geo.elements:
        if el.kind == "polygon" and len(el.points) >= 3:
            new_pts = offset_polygon(el.points, amount_mm)
            out_elements.append(GeometryElement(
                kind="polygon",
                points=new_pts,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "polyline" and len(el.points) >= 2:
            new_pts = offset_polyline(el.points, amount_mm)
            out_elements.append(GeometryElement(
                kind="polyline",
                points=new_pts,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "circle" and el.points:
            new_r = max(0.0, el.radius + amount_mm)
            out_elements.append(GeometryElement(
                kind="circle",
                points=list(el.points),
                radius=new_r,
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        elif el.kind == "rect" and len(el.points) >= 2:
            (x0, y0), (x1, y1) = el.points[0], el.points[1]
            out_elements.append(GeometryElement(
                kind="rect",
                points=[
                    (x0 - amount_mm, y0 - amount_mm),
                    (x1 + amount_mm, y1 + amount_mm),
                ],
                material_index=el.material_index,
                stroke_width=el.stroke_width,
            ))
        else:
            out_elements.append(el)

    return GeometryCollection(
        elements=out_elements,
        width_mm=geo.width_mm,
        height_mm=geo.height_mm,
        origin_x=geo.origin_x,
        origin_y=geo.origin_y,
        radial=geo.radial,
        tile_w=geo.tile_w,
        tile_h=geo.tile_h,
    )
