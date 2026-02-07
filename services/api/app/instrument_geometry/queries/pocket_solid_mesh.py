"""
Pocket solid mesh generator.

Builds a watertight mesh for a pocket volume:
- vertical sidewalls
- top cap (z_top)  
- floor cap (z_floor)

Supports:
- Fan triangulation (convex polygons)
- Ear-clipping triangulation (concave-safe)
- Polygon cleanup (duplicates, collinear vertices)
- Self-intersection detection + bow-tie splitting

Target: instrument_geometry/queries/pocket_solid_mesh.py
"""
from __future__ import annotations

from typing import List, Tuple, Dict, Any

from ..models.mesh import TriangleMesh
from ..queries.truss_union_outline_pipeline2d import get_truss_union_outline_final_2d
from ..queries.polygon_cleanup import clean_ring
from ..queries.polygon_self_intersection import first_self_intersection, try_split_single_bowtie

Pt2 = Tuple[float, float]


def build_pocket_solid_mesh(
    geom,
    *,
    z_top_mm: float,
    z_floor_mm: float,
    cap_mode: str = "earclip",  # "fan" or "earclip"
    cleanup_tol_mm: float = 1e-6,
    collinear_eps: float = 1e-12,
    earclip_eps: float = 1e-12,
    earclip_guard: int = 10000,
    fallback_on_fail: bool = True,  # if earclip fails, return sidewalls-only
    reject_self_intersections: bool = True,
    auto_split_self_intersections: bool = False,
    self_intersection_eps: float = 1e-12,
) -> TriangleMesh:
    """
    Build a watertight mesh for a pocket volume.
    """
    outline = get_truss_union_outline_final_2d(geom)
    pts2d = outline.points

    if not pts2d:
        return TriangleMesh(vertices=[], triangles=[], meta={"error": "no_outline_points"})

    # Convert to float ring
    raw: List[Pt2] = [(float(p.x_mm), float(p.y_mm)) for p in pts2d]

    # Cleanup
    ring, clean_meta = clean_ring(raw, tol_mm=cleanup_tol_mm, collinear_eps=collinear_eps)
    n = len(ring)

    if n < 3:
        return TriangleMesh(vertices=[], triangles=[], meta={"error": "ring_too_small_after_cleanup", **clean_meta})

    # Self-intersection detection
    hit = first_self_intersection(ring, eps=self_intersection_eps)
    if hit is not None:
        clean_meta["self_intersection"] = {
            "status": "hit",
            "seg_i": hit.i,
            "seg_j": hit.j,
            "x": hit.p[0],
            "y": hit.p[1],
        }
        if auto_split_self_intersections:
            split = try_split_single_bowtie(ring, hit, eps=self_intersection_eps)
            if split is None:
                clean_meta["self_intersection"]["split"] = "failed"
                if reject_self_intersections:
                    return TriangleMesh(vertices=[], triangles=[], meta={"error": "self_intersection_unsplittable", **clean_meta})
                # If not rejecting, fall through and let earclip attempt (may fail) with fallback_on_fail
            else:
                ringA, ringB = split
                clean_meta["self_intersection"]["split"] = "ok"
                return _build_solid_from_two_rings(
                    ringA=ringA,
                    ringB=ringB,
                    z_top_mm=z_top_mm,
                    z_floor_mm=z_floor_mm,
                    cap_mode=cap_mode,
                    cleanup_tol_mm=cleanup_tol_mm,
                    collinear_eps=collinear_eps,
                    earclip_eps=earclip_eps,
                    earclip_guard=earclip_guard,
                    fallback_on_fail=fallback_on_fail,
                    meta_extra=clean_meta,
                )
        if reject_self_intersections:
            # safest behavior: refuse caps; you can still emit sidewalls-only via fallback later
            return TriangleMesh(vertices=[], triangles=[], meta={"error": "self_intersection_detected", **clean_meta})
    else:
        clean_meta["self_intersection"] = {"status": "none"}

    # Build mesh from cleaned ring
    return _build_solid_from_ring(
        ring,
        z_top_mm=z_top_mm,
        z_floor_mm=z_floor_mm,
        cap_mode=cap_mode,
        cleanup_tol_mm=cleanup_tol_mm,
        collinear_eps=collinear_eps,
        earclip_eps=earclip_eps,
        earclip_guard=earclip_guard,
        fallback_on_fail=fallback_on_fail,
        meta_extra=clean_meta,
    )


# =============================================================================
# Internal builders
# =============================================================================

def _build_solid_from_ring(
    ring: List[Pt2],
    *,
    z_top_mm: float,
    z_floor_mm: float,
    cap_mode: str,
    cleanup_tol_mm: float,
    collinear_eps: float,
    earclip_eps: float,
    earclip_guard: int,
    fallback_on_fail: bool,
    meta_extra: dict,
) -> TriangleMesh:
    """Build solid mesh from a single cleaned ring."""
    n = len(ring)
    ccw = _signed_area_2d(ring) > 0

    vertices: List[Tuple[float, float, float]] = []
    triangles: List[Tuple[int, int, int]] = []
    top_idx: List[int] = []
    bot_idx: List[int] = []

    for (x, y) in ring:
        top_idx.append(len(vertices))
        vertices.append((x, y, float(z_top_mm)))

    for (x, y) in ring:
        bot_idx.append(len(vertices))
        vertices.append((x, y, float(z_floor_mm)))

    # Sidewalls
    for i in range(n):
        i2 = (i + 1) % n
        t0, t1 = top_idx[i], top_idx[i2]
        b0, b1 = bot_idx[i], bot_idx[i2]
        # outward normals (consistent with your earlier convention)
        if ccw:
            triangles.append((t0, b0, b1))
            triangles.append((t0, b1, t1))
        else:
            triangles.append((t0, b1, b0))
            triangles.append((t0, t1, b1))

    meta: Dict[str, Any] = {
        "cap_mode": cap_mode,
        "ccw": ccw,
        **meta_extra,
    }

    # Caps
    if cap_mode == "fan":
        triangles += _fan_cap(top_idx, ccw=ccw, face="top")
        triangles += _fan_cap(bot_idx, ccw=ccw, face="bottom")
        meta["cap_status"] = "ok_fan"
        return TriangleMesh(vertices=vertices, triangles=triangles, meta=meta)

    if cap_mode == "earclip":
        try:
            cap_tris = _earclip_triangulate(ring, eps=earclip_eps, guard=earclip_guard)
            triangles += _apply_cap_tris(cap_tris, top_idx, ccw=ccw, face="top")
            triangles += _apply_cap_tris(cap_tris, bot_idx, ccw=ccw, face="bottom")
            meta["cap_status"] = "ok_earclip"
            meta["cap_triangle_count"] = len(cap_tris) * 2
            return TriangleMesh(vertices=vertices, triangles=triangles, meta=meta)
        except Exception as e:  # WP-1: keep broad — earclip triangulation can fail in many ways; fallback is safe
            meta["cap_status"] = "earclip_failed"
            meta["cap_error"] = str(e)
            if fallback_on_fail:
                meta["fallback"] = "sidewalls_only"
                return TriangleMesh(vertices=vertices, triangles=triangles, meta=meta)
            raise

    raise ValueError("cap_mode must be 'fan' or 'earclip'")


def _build_solid_from_two_rings(
    *,
    ringA: List[Pt2],
    ringB: List[Pt2],
    z_top_mm: float,
    z_floor_mm: float,
    cap_mode: str,
    cleanup_tol_mm: float,
    collinear_eps: float,
    earclip_eps: float,
    earclip_guard: int,
    fallback_on_fail: bool,
    meta_extra: dict,
) -> TriangleMesh:
    """Build solid from two split rings and merge them."""
    # Clean each ring again (splitting introduces an intersection vertex p)
    rA, metaA = clean_ring(ringA, tol_mm=cleanup_tol_mm, collinear_eps=collinear_eps)
    rB, metaB = clean_ring(ringB, tol_mm=cleanup_tol_mm, collinear_eps=collinear_eps)

    mA = _build_solid_from_ring(
        rA,
        z_top_mm=z_top_mm,
        z_floor_mm=z_floor_mm,
        cap_mode=cap_mode,
        cleanup_tol_mm=cleanup_tol_mm,
        collinear_eps=collinear_eps,
        earclip_eps=earclip_eps,
        earclip_guard=earclip_guard,
        fallback_on_fail=fallback_on_fail,
        meta_extra={**meta_extra, "split_ring": "A", **metaA},
    )

    mB = _build_solid_from_ring(
        rB,
        z_top_mm=z_top_mm,
        z_floor_mm=z_floor_mm,
        cap_mode=cap_mode,
        cleanup_tol_mm=cleanup_tol_mm,
        collinear_eps=collinear_eps,
        earclip_eps=earclip_eps,
        earclip_guard=earclip_guard,
        fallback_on_fail=fallback_on_fail,
        meta_extra={**meta_extra, "split_ring": "B", **metaB},
    )

    return _merge_meshes(mA, mB, meta=meta_extra)


def _merge_meshes(a: TriangleMesh, b: TriangleMesh, meta: dict) -> TriangleMesh:
    """Merge two meshes into one."""
    v = a.vertices + b.vertices
    t = a.triangles + [(x + len(a.vertices), y + len(a.vertices), z + len(a.vertices)) for (x, y, z) in b.triangles]
    meta_out = dict(meta)
    meta_out["merged"] = True
    meta_out["meshA"] = {"v": len(a.vertices), "t": len(a.triangles)}
    meta_out["meshB"] = {"v": len(b.vertices), "t": len(b.triangles)}
    return TriangleMesh(vertices=v, triangles=t, meta=meta_out)


# =============================================================================
# Cap utilities
# =============================================================================

def _apply_cap_tris(
    cap_tris: List[Tuple[int, int, int]],
    ring_idx: List[int],
    *,
    ccw: bool,
    face: str,
) -> List[Tuple[int, int, int]]:
    """Map 2D ring triangle indices to vertex indices, adjusting winding."""
    out: List[Tuple[int, int, int]] = []
    for (i, j, k) in cap_tris:
        a = ring_idx[i]
        b = ring_idx[j]
        c = ring_idx[k]
        if face == "top":
            out.append((a, b, c) if ccw else (a, c, b))
        else:
            out.append((a, c, b) if ccw else (a, b, c))
    return out


def _fan_cap(ring_idx: List[int], *, ccw: bool, face: str) -> List[Tuple[int, int, int]]:
    """
    Fan triangulation using vertex 0 as the center anchor.
    Works reliably for convex polygons.
    """
    tris: List[Tuple[int, int, int]] = []
    n = len(ring_idx)
    if n < 3:
        return tris
    c = ring_idx[0]
    for i in range(1, n - 1):
        a = ring_idx[i]
        b = ring_idx[i + 1]
        if face == "top":
            tris.append((c, a, b) if ccw else (c, b, a))
        else:
            tris.append((c, b, a) if ccw else (c, a, b))
    return tris


# =============================================================================
# Ear clipping (concave-safe)
# =============================================================================

def _earclip_triangulate(pts: List[Pt2], *, eps: float, guard: int) -> List[Tuple[int, int, int]]:
    """
    Ear clipping triangulation for a simple polygon (non-self-intersecting).
    Deterministic: walks vertices in ring order and clips first ear found.
    Returns triangles as indices into pts (0..n-1).
    """
    n = len(pts)
    if n < 3:
        return []

    base_idx = list(reversed(range(n))) if _signed_area_2d(pts) < 0 else list(range(n))
    idx = base_idx[:]
    tris: List[Tuple[int, int, int]] = []

    iters = 0
    while len(idx) > 3:
        iters += 1
        if iters > guard:
            raise ValueError("earclip_guard_tripped (possible self-intersection or degeneracy)")

        ear_found = False
        m = len(idx)
        for t in range(m):
            i_prev = idx[(t - 1) % m]
            i_curr = idx[t]
            i_next = idx[(t + 1) % m]

            ax, ay = pts[i_prev]
            bx, by = pts[i_curr]
            cx, cy = pts[i_next]

            # convex corner test (CCW local)
            if _cross2(ax, ay, bx, by, cx, cy) <= eps:
                continue

            if _any_point_in_tri(idx, pts, i_prev, i_curr, i_next, eps=eps):
                continue

            tris.append((i_prev, i_curr, i_next))
            del idx[t]
            ear_found = True
            break

        if not ear_found:
            raise ValueError("earclip_failed_no_ear (degenerate or self-intersecting polygon)")

    tris.append((idx[0], idx[1], idx[2]))
    return tris


def _any_point_in_tri(
    idx: List[int],
    pts: List[Pt2],
    i_prev: int,
    i_curr: int,
    i_next: int,
    *,
    eps: float,
) -> bool:
    ax, ay = pts[i_prev]
    bx, by = pts[i_curr]
    cx, cy = pts[i_next]
    for p_i in idx:
        if p_i in (i_prev, i_curr, i_next):
            continue
        px, py = pts[p_i]
        if _point_in_triangle(px, py, ax, ay, bx, by, cx, cy, eps=eps):
            return True
    return False


def _point_in_triangle(px, py, ax, ay, bx, by, cx, cy, *, eps: float) -> bool:
    c1 = _cross2(ax, ay, bx, by, px, py)
    c2 = _cross2(bx, by, cx, cy, px, py)
    c3 = _cross2(cx, cy, ax, ay, px, py)
    return (c1 >= -eps) and (c2 >= -eps) and (c3 >= -eps)


def _cross2(ax, ay, bx, by, cx, cy) -> float:
    """Cross of AB x AC (2D scalar z-component)."""
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


# =============================================================================
# Geometry helpers
# =============================================================================

def _signed_area_2d(pts: List[Pt2]) -> float:
    """Shoelace formula; positive => CCW."""
    area = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += (x1 * y2 - x2 * y1)
    return 0.5 * area
