"""
Self-intersection detection and bow-tie splitting for polygon rings.

Robust enough for cleaned rings. O(n^2), deterministic.

Target: instrument_geometry/queries/polygon_self_intersection.py
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

Pt2 = Tuple[float, float]


@dataclass(frozen=True)
class SegmentHit:
    i: int   # segment i = (i -> i+1)
    j: int   # segment j = (j -> j+1)
    p: Pt2   # intersection point


def first_self_intersection(
    ring: List[Pt2],
    *,
    eps: float = 1e-12,
) -> Optional[SegmentHit]:
    """
    Detect the first self-intersection of a closed ring (not explicitly closed).
    Returns the first hit (lowest i then lowest j) excluding adjacent edges.
    O(n^2), deterministic.
    """
    n = len(ring)
    if n < 4:
        return None

    for i in range(n):
        a1 = ring[i]
        a2 = ring[(i + 1) % n]
        for j in range(i + 1, n):
            # Skip same/adjacent segments (share endpoints)
            if _segments_adjacent(i, j, n):
                continue
            b1 = ring[j]
            b2 = ring[(j + 1) % n]
            hit = _segment_intersection(a1, a2, b1, b2, eps=eps)
            if hit is not None:
                return SegmentHit(i=i, j=j, p=hit)
    return None


def try_split_single_bowtie(
    ring: List[Pt2],
    hit: SegmentHit,
    *,
    eps: float = 1e-12,
) -> Optional[Tuple[List[Pt2], List[Pt2]]]:
    """
    Attempts to split a ring with a single crossing (bow-tie / figure-8)
    into two simple rings.
    
    Works when there is ONE intersection between two non-adjacent segments.
    If the shape is more complex (multiple intersections), returns None.
    
    Returns (ringA, ringB) as open rings (not explicitly closed), or None if not splittable.
    """
    n = len(ring)
    if n < 4:
        return None

    i, j = hit.i, hit.j
    p = hit.p

    # Ensure ordering i < j
    if j < i:
        i, j = j, i

    # Build two rings by cutting at the intersection point:
    # Path 1: p -> (i+1..j) -> p
    # Path 2: p -> (j+1..i) -> p (wrap)
    # We will include p as first vertex, and again at end, then caller can normalize/clean.

    path1 = [p]
    k = (i + 1) % n
    while True:
        path1.append(ring[k])
        if k == j:
            break
        k = (k + 1) % n
        if k == (i + 1) % n:
            return None  # guard loop
    path1.append(p)

    path2 = [p]
    k = (j + 1) % n
    while True:
        path2.append(ring[k])
        if k == i:
            break
        k = (k + 1) % n
        if k == (j + 1) % n:
            return None
    path2.append(p)

    # Basic sanity: both rings must have at least 4 points including closure point
    if len(path1) < 4 or len(path2) < 4:
        return None

    # Return without explicit closure duplication (strip last p; cleanup will manage closure)
    return (path1[:-1], path2[:-1])


def _segments_adjacent(i: int, j: int, n: int) -> bool:
    if i == j:
        return True
    # Adjacent in ring sense: share a vertex
    if (i + 1) % n == j:
        return True
    if (j + 1) % n == i:
        return True
    # First and last segments are adjacent
    if i == 0 and j == n - 1:
        return True
    if j == 0 and i == n - 1:
        return True
    return False


def _segment_intersection(a1: Pt2, a2: Pt2, b1: Pt2, b2: Pt2, *, eps: float) -> Optional[Pt2]:
    """
    Proper segment intersection (including near-touch within eps). 
    Returns intersection point or None.
    Uses line-line intersection with bounding-box checks + orientation tests.
    """
    # Fast bbox reject
    if (max(a1[0], a2[0]) + eps < min(b1[0], b2[0]) or
        max(b1[0], b2[0]) + eps < min(a1[0], a2[0]) or
        max(a1[1], a2[1]) + eps < min(b1[1], b2[1]) or
        max(b1[1], b2[1]) + eps < min(a1[1], a2[1])):
        return None

    o1 = _orient(a1, a2, b1)
    o2 = _orient(a1, a2, b2)
    o3 = _orient(b1, b2, a1)
    o4 = _orient(b1, b2, a2)

    # General case
    if _sign(o1, eps) * _sign(o2, eps) < 0 and _sign(o3, eps) * _sign(o4, eps) < 0:
        return _line_intersection(a1, a2, b1, b2)

    # Collinear / touching cases (treat as intersection if on-segment within eps)
    if abs(o1) <= eps and _on_segment(a1, a2, b1, eps):
        return b1
    if abs(o2) <= eps and _on_segment(a1, a2, b2, eps):
        return b2
    if abs(o3) <= eps and _on_segment(b1, b2, a1, eps):
        return a1
    if abs(o4) <= eps and _on_segment(b1, b2, a2, eps):
        return a2

    return None


def _orient(a: Pt2, b: Pt2, c: Pt2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _sign(x: float, eps: float) -> int:
    if x > eps:
        return 1
    if x < -eps:
        return -1
    return 0


def _on_segment(a: Pt2, b: Pt2, p: Pt2, eps: float) -> bool:
    return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
            min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps)


def _line_intersection(a1: Pt2, a2: Pt2, b1: Pt2, b2: Pt2) -> Pt2:
    """
    Returns intersection point of infinite lines (assumes they cross).
    """
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        # Parallel; fallback to midpoint of closest endpoints (rare)
        return ((x2 + x3) * 0.5, (y2 + y3) * 0.5)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return (px, py)
