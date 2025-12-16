"""
Polygon ring cleanup utilities.

Removes duplicates, near-duplicates, and collinear vertices.
Deterministic and safe for golden tests.

Target: instrument_geometry/queries/polygon_cleanup.py
"""
from __future__ import annotations

from typing import List, Tuple, Dict, Any

Pt2 = Tuple[float, float]


def clean_ring(
    pts: List[Pt2],
    *,
    tol_mm: float = 1e-6,
    collinear_eps: float = 1e-12,
    max_passes: int = 3,
) -> tuple[List[Pt2], Dict[str, Any]]:
    """
    Clean a polygon ring (not necessarily closed):
    1) remove consecutive duplicates / near-duplicates
    2) remove closing duplicate (if present)
    3) remove collinear vertices (within eps)
    
    Deterministic and safe for golden tests.
    """
    meta: Dict[str, Any] = {
        "input_count": len(pts),
        "removed_duplicates": 0,
        "removed_collinear": 0,
        "passes": 0,
    }

    if len(pts) < 3:
        meta["output_count"] = len(pts)
        return pts[:], meta

    # Drop closing point if duplicates first
    ring = pts[:]
    if _same_xy(ring[0], ring[-1], tol_mm):
        ring = ring[:-1]
        meta["removed_duplicates"] += 1

    # Iterative cleanup passes (handles patterns like A A B B C C)
    for _ in range(max_passes):
        meta["passes"] += 1
        before = len(ring)
        ring, dups_removed = _remove_consecutive_duplicates(ring, tol_mm)
        meta["removed_duplicates"] += dups_removed
        ring, col_removed = _remove_collinear(ring, collinear_eps)
        meta["removed_collinear"] += col_removed
        after = len(ring)
        if after == before:
            break
        if len(ring) < 3:
            break

    meta["output_count"] = len(ring)
    return ring, meta


def _remove_consecutive_duplicates(pts: List[Pt2], tol: float) -> tuple[List[Pt2], int]:
    if not pts:
        return [], 0
    out: List[Pt2] = [pts[0]]
    removed = 0
    for p in pts[1:]:
        if _same_xy(out[-1], p, tol):
            removed += 1
            continue
        out.append(p)
    # Also check first/last adjacency after removal
    if len(out) >= 2 and _same_xy(out[0], out[-1], tol):
        out.pop()
        removed += 1
    return out, removed


def _remove_collinear(pts: List[Pt2], eps: float) -> tuple[List[Pt2], int]:
    """
    Remove vertices where prev-curr-next are collinear.
    Uses a ring interpretation (wrap-around).
    """
    n = len(pts)
    if n < 3:
        return pts[:], 0
    keep = [True] * n
    removed = 0
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[i]
        c = pts[(i + 1) % n]
        if _is_collinear(a, b, c, eps):
            keep[i] = False
    out: List[Pt2] = []
    for i in range(n):
        if keep[i]:
            out.append(pts[i])
        else:
            removed += 1
    # If we removed too much, return original (safer than collapsing)
    if len(out) < 3:
        return pts[:], 0
    return out, removed


def _is_collinear(a: Pt2, b: Pt2, c: Pt2, eps: float) -> bool:
    ax, ay = a
    bx, by = b
    cx, cy = c
    # area of triangle *2 = cross(AB, AC)
    cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return abs(cross) <= eps


def _same_xy(a: Pt2, b: Pt2, tol: float) -> bool:
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol
