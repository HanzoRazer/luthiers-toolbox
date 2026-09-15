"""
Geometry model for the DXF catalog gates (DXF-CATALOG-GATE-001).

closed_outline (both gates) and the Files gate's chain-crossing check read the
outline layer through this module. Its rules, and the reason for each number:

1. One sampling per entity. The layer's extent, a contour's bbox, containment
   and the crossing check all read the same points, so they cannot disagree
   about where an entity is. ARC, CIRCLE, ELLIPSE and polyline bulges are
   sampled finely enough that no chord departs from the curve by more than
   SAGITTA_MM. A SPLINE with control points is evaluated from them and its
   knots (de Boor, weights honoured), so an unclamped spline starts where the
   curve starts, not at its first control point. A fit-point-only spline is the
   polyline through its fit points, which the curve passes through.
2. Coordinates. LINE, SPLINE and ELLIPSE are stored in world coordinates. ARC,
   CIRCLE, LWPOLYLINE and 2D POLYLINE are stored in their object coordinate
   system: extrusion +Z is world XY, and -Z is world XY mirrored in x. Any
   other extrusion is not in the XY plane, so the entity yields no points and
   cannot close an outline.
3. Vertices. A chain endpoint within VERTEX_TOLERANCE_MM of a vertex joins it,
   wherever it falls; a vertex sits at the first endpoint that created it.
   0.05 mm is the endpoint tolerance of the repo's R12 LINE dedupe
   (services/blueprint_clean.py) and 50x the 0.001 mm catalog coordinate
   precision (CLAUDE.md: <= 3 dp). It is 20x tighter than the 1.0 mm gap the
   DXF cleaner closes (cam/unified_dxf_cleaner.py): the gate asks whether a
   file is closed, not whether a cleaner could close it.
4. Edges. Two edges are one edge only if they join the same vertices and share
   a midpoint. A LINE drawn twice is one edge; a chord and an arc between the
   same vertices are two, so the chord makes the outline branch.
5. Contours. A closed contour is a closed LWPOLYLINE or POLYLINE, or a
   connected cycle of LINE/ARC/open-SPLINE edges in which every vertex joins
   exactly two edges. CIRCLE, ELLIPSE and closed SPLINE never count.
6. Bounds. A contour bounds its layer when its bbox spans `coverage_min` of the
   layer's bbox in both axes, AND at least `coverage_min` of the layer's drawn
   length lies inside it or within ON_CONTOUR_MM of it. The bbox test alone let
   a thin contour running corner to corner stand in for the body. The registry
   sets `coverage_min` to 0.9, a margin rather than a measured value: on the
   2026-09-15 catalog every body that passes scores 1.000 on both measures, and
   the best contour of every body that fails scores at most 0.085 (bbox) and
   0.454 (enclosed; the Flying V's strip). 0.9 lets a stray mark up to a tenth
   of the layer sit outside the body.

Not proven here: that the contour is the body (a closed frame drawn around an
open body passes), any dimension against a spec, or a contour that touches
itself at a tangent.

Dependencies: stdlib only, plus ezdxf entity attributes. The asset gate job
installs only ezdxf, and ezdxf's numpy-backed helpers (bbox, flattening) are the
double-binding hazard documented in services/api/tests/conftest.py.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]

VERTEX_TOLERANCE_MM = 0.05
SAGITTA_MM = 0.01
ON_CONTOUR_MM = VERTEX_TOLERANCE_MM + SAGITTA_MM  # a vertex snap plus one chord's error
PIECE_MM = 1.0  # containment tests drawn length in pieces no longer than this
MAX_CURVE_SEGMENTS = 720
SPLINE_SAMPLES_PER_SPAN = 16
CHAIN_TYPES = frozenset({"LINE", "ARC", "SPLINE"})


# -----------------------------------------------------------------------------
# Sampling: one ordered point path per entity
# -----------------------------------------------------------------------------

def _curve_segments(radius: float, sweep: float) -> int:
    if radius <= SAGITTA_MM:
        return 1
    step = 2 * math.acos(1 - SAGITTA_MM / radius)
    return max(1, min(MAX_CURVE_SEGMENTS, math.ceil(abs(sweep) / step)))


def arc_points(center: Sequence[float], radius: float, start: float, sweep: float) -> List[Point]:
    """Points from `start` through `sweep` radians, both ends included."""
    n = _curve_segments(radius, sweep)
    return [(center[0] + radius * math.cos(start + sweep * i / n),
             center[1] + radius * math.sin(start + sweep * i / n)) for i in range(n + 1)]


def _bulge_points(p1: Point, p2: Point, bulge: float) -> List[Point]:
    """Points after p1 up to p2 along a polyline bulge (included angle 4*atan(bulge))."""
    chord = math.dist(p1, p2)
    if abs(bulge) < 1e-12 or chord == 0:
        return [p2]
    sign, theta = math.copysign(1.0, bulge), 4 * math.atan(abs(bulge))
    radius = chord / (2 * math.sin(theta / 2))
    offset = sign * radius * math.cos(theta / 2) / chord  # centre, left of p1->p2 for a CCW bulge
    center = ((p1[0] + p2[0]) / 2 - offset * (p2[1] - p1[1]), (p1[1] + p2[1]) / 2 + offset * (p2[0] - p1[0]))
    start = math.atan2(p1[1] - center[1], p1[0] - center[0])
    return arc_points(center, radius, start, sign * theta)[1:-1] + [p2]


def _polyline_points(vertices: List[Tuple[float, float, float]], closed: bool) -> List[Point]:
    """The polyline's path; a closed polyline ends back at its first vertex."""
    if not vertices:
        return []
    points = [(vertices[0][0], vertices[0][1])]
    for (x1, y1, bulge), (x2, y2, _) in zip(vertices, vertices[1:] + (vertices[:1] if closed else [])):
        points.extend(_bulge_points((x1, y1), (x2, y2), bulge))
    return points


def _ocs_sign(entity: Any) -> Optional[float]:
    """+1 for extrusion +Z, -1 for -Z (x mirrored), None when not in the XY plane."""
    ex = entity.dxf.get("extrusion", (0.0, 0.0, 1.0))
    if abs(ex[0]) > 1e-9 or abs(ex[1]) > 1e-9 or ex[2] == 0:
        return None
    return math.copysign(1.0, ex[2])


def _in_wcs(entity: Any, points: List[Point]) -> List[Point]:
    sign = _ocs_sign(entity)
    if sign is None:
        return []
    return points if sign > 0 else [(-x, y) for x, y in points]


def _arc_path(entity: Any) -> List[Point]:
    start, end = entity.dxf.start_angle, entity.dxf.end_angle
    sweep = (end - start) % 360 or 360
    return _in_wcs(entity, arc_points(entity.dxf.center, entity.dxf.radius,
                                      math.radians(start), math.radians(sweep)))


def _circle_path(entity: Any) -> List[Point]:
    return _in_wcs(entity, arc_points(entity.dxf.center, entity.dxf.radius, 0.0, 2 * math.pi))


def _polyline_path(entity: Any) -> List[Point]:
    if entity.dxftype() == "LWPOLYLINE":
        return _in_wcs(entity, _polyline_points([tuple(p) for p in entity.get_points("xyb")], entity.closed))
    if entity.is_2d_polyline:
        vertices = [(v.dxf.location.x, v.dxf.location.y, v.dxf.get("bulge", 0.0)) for v in entity.vertices]
        return _in_wcs(entity, _polyline_points(vertices, entity.is_closed))
    if entity.is_3d_polyline:
        return _polyline_points([(v.dxf.location.x, v.dxf.location.y, 0.0) for v in entity.vertices],
                                entity.is_closed)
    return []  # polyface / mesh: not an outline


def _ellipse_path(entity: Any) -> List[Point]:
    c, major, ratio = entity.dxf.center, entity.dxf.major_axis, entity.dxf.ratio
    ez = entity.dxf.get("extrusion", (0.0, 0.0, 1.0))
    if abs(ez[0]) > 1e-9 or abs(ez[1]) > 1e-9 or ez[2] == 0:
        return []
    minor = (-math.copysign(1.0, ez[2]) * major[1] * ratio, math.copysign(1.0, ez[2]) * major[0] * ratio)
    start = entity.dxf.get("start_param", 0.0)
    sweep = (entity.dxf.get("end_param", 2 * math.pi) - start) % (2 * math.pi) or 2 * math.pi
    n = _curve_segments(math.hypot(major[0], major[1]), sweep)
    return [(c[0] + major[0] * math.cos(t) + minor[0] * math.sin(t),
             c[1] + major[1] * math.cos(t) + minor[1] * math.sin(t))
            for t in (start + sweep * i / n for i in range(n + 1))]


def spline_points(entity: Any) -> List[Point]:
    """Points along the curve; [] when neither valid knots nor fit points define it."""
    ctrl = [(p[0], p[1]) for p in entity.control_points]
    if ctrl:
        degree, knots = entity.dxf.degree, list(entity.knots)
        weights = list(entity.weights) or [1.0] * len(ctrl)
        if degree >= 1 and len(knots) == len(ctrl) + degree + 1 and len(weights) == len(ctrl) \
                and min(weights) > 0 and knots[len(ctrl)] > knots[degree]:
            return _bspline(degree, knots, ctrl, weights)
    return [(p[0], p[1]) for p in entity.fit_points]


def _bspline(degree: int, knots: List[float], ctrl: List[Point], weights: List[float]) -> List[Point]:
    lo, hi = knots[degree], knots[len(ctrl)]
    spans = sum(1 for a, b in zip(knots[degree:len(ctrl)], knots[degree + 1:len(ctrl) + 1]) if b > a)
    n = min(MAX_CURVE_SEGMENTS, spans * SPLINE_SAMPLES_PER_SPAN)
    homogeneous = [(x * w, y * w, w) for (x, y), w in zip(ctrl, weights)]
    return [_de_boor(lo + (hi - lo) * i / n, degree, knots, homogeneous) for i in range(n + 1)]


def _de_boor(u: float, p: int, knots: List[float], ctrl: List[Tuple[float, float, float]]) -> Point:
    k = p
    while k < len(ctrl) - 1 and knots[k + 1] <= u:
        k += 1
    d = [ctrl[j + k - p] for j in range(p + 1)]
    for r in range(1, p + 1):
        for j in range(p, r - 1, -1):
            left, right = knots[j + k - p], knots[j + 1 + k - r]
            a = 0.0 if right == left else (u - left) / (right - left)
            d[j] = tuple((1 - a) * s + a * t for s, t in zip(d[j - 1], d[j]))
    x, y, w = d[p]
    return (x / w, y / w)


def _spline_path(entity: Any) -> List[Point]:
    # An unevaluable spline still has an extent: its control points bound it.
    return spline_points(entity) or [(p[0], p[1]) for p in entity.control_points]


_PATHS = {
    "LINE": lambda e: [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])],
    "ARC": _arc_path,
    "CIRCLE": _circle_path,
    "LWPOLYLINE": _polyline_path,
    "POLYLINE": _polyline_path,
    "ELLIPSE": _ellipse_path,
    "SPLINE": _spline_path,
}


def entity_path(entity: Any) -> List[Point]:
    """The entity as one ordered point path in world XY ([] if it has none)."""
    path = _PATHS.get(entity.dxftype())
    return path(entity) if path else []


def edge_path(entity: Any) -> Optional[List[Point]]:
    """Path of an open chainable entity (LINE, ARC, open SPLINE); None otherwise."""
    kind = entity.dxftype()
    if kind not in CHAIN_TYPES or (kind == "SPLINE" and entity.closed):
        return None
    path = spline_points(entity) if kind == "SPLINE" else entity_path(entity)
    return path if len(path) >= 2 else None


def closed_ring(entity: Any) -> Optional[List[Point]]:
    """A closed LWPOLYLINE/POLYLINE as a ring (last point != first); None otherwise."""
    kind = entity.dxftype()
    closed = (kind == "LWPOLYLINE" and entity.closed) or (kind == "POLYLINE" and entity.is_closed)
    path = entity_path(entity) if closed else []
    return path[:-1] if len(path) > 1 else None


def path_length(path: Sequence[Point]) -> float:
    return sum(math.dist(p, q) for p, q in zip(path, path[1:]))


def bbox(points: Iterable[Point]) -> Optional[BBox]:
    pts = list(points)
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


# -----------------------------------------------------------------------------
# Edge graph: vertices by tolerance, edges by geometry, simple cycles
# -----------------------------------------------------------------------------

class VertexIndex:
    """Points within `tolerance` of a vertex join it; the first point seen places it."""

    def __init__(self, tolerance: float = VERTEX_TOLERANCE_MM):
        self.tolerance = tolerance
        self.points: List[Point] = []
        self._cells: Dict[Tuple[int, int], List[int]] = defaultdict(list)

    def vertex(self, point: Point) -> int:
        cx, cy = math.floor(point[0] / self.tolerance), math.floor(point[1] / self.tolerance)
        for cell in ((cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            for vid in self._cells.get(cell, ()):
                if math.dist(point, self.points[vid]) <= self.tolerance:
                    return vid
        self.points.append(point)
        self._cells[(cx, cy)].append(len(self.points) - 1)
        return len(self.points) - 1


@dataclass
class Edge:
    """A chainable entity between two vertices; `points` start and end on them."""
    start: int
    end: int
    points: List[Point]
    source: int  # index of the path it came from


def _midpoint(path: Sequence[Point]) -> Point:
    """The point halfway along the path (the same point whichever way it is drawn)."""
    remaining = path_length(path) / 2
    for p, q in zip(path, path[1:]):
        seg = math.dist(p, q)
        if seg > 0 and seg >= remaining:
            t = remaining / seg
            return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
        remaining -= seg
    return path[-1]


def build_edges(paths: Sequence[Optional[List[Point]]]) -> List[Edge]:
    """One edge per distinct chainable path; loops on a single vertex never chain."""
    vertices, midpoints = VertexIndex(), VertexIndex()
    seen: Set[Tuple[int, int, int]] = set()
    edges: List[Edge] = []
    for source, path in enumerate(paths):
        if not path:
            continue
        a, b = vertices.vertex(path[0]), vertices.vertex(path[-1])
        key = (min(a, b), max(a, b), midpoints.vertex(_midpoint(path)))
        if a == b or key in seen:
            continue
        seen.add(key)
        edges.append(Edge(a, b, [vertices.points[a], *path[1:-1], vertices.points[b]], source))
    return edges


def _two_core(edges: List[Edge]) -> List[Edge]:
    """Edges that lie on a cycle (degree-1 branches pruned)."""
    incident: Dict[int, Set[int]] = defaultdict(set)
    for i, edge in enumerate(edges):
        incident[edge.start].add(i)
        incident[edge.end].add(i)
    alive = set(range(len(edges)))
    queue = deque(v for v, ids in incident.items() if len(ids) < 2)
    while queue:
        vertex = queue.popleft()
        for i in list(incident[vertex]):
            other = edges[i].end if edges[i].start == vertex else edges[i].start
            incident[vertex].discard(i)
            incident[other].discard(i)
            alive.discard(i)
            if len(incident[other]) == 1:
                queue.append(other)
    return [edges[i] for i in sorted(alive)]


def closed_components(edges: List[Edge]) -> List[List[Edge]]:
    """Connected components of the cycle-bearing part of the edge graph."""
    core = _two_core(edges)
    by_vertex: Dict[int, List[int]] = defaultdict(list)
    for i, edge in enumerate(core):
        by_vertex[edge.start].append(i)
        by_vertex[edge.end].append(i)
    seen: Set[int] = set()
    components = []
    for start in range(len(core)):
        stack, members = [start], []
        while stack:
            i = stack.pop()
            if i not in seen:
                seen.add(i)
                members.append(core[i])
                stack.extend(j for v in (core[i].start, core[i].end) for j in by_vertex[v] if j not in seen)
        if members:
            components.append(members)
    return components


def is_simple_cycle(component: List[Edge]) -> bool:
    """Every vertex joins exactly two edges: one closed contour, no branch or pinch."""
    degree: Dict[int, int] = defaultdict(int)
    for edge in component:
        degree[edge.start] += 1
        degree[edge.end] += 1
    return bool(degree) and all(d == 2 for d in degree.values())


def cycle_ring(component: List[Edge]) -> List[Point]:
    """The ordered ring of a simple cycle (last point != first)."""
    by_vertex: Dict[int, List[Edge]] = defaultdict(list)
    for edge in component:
        by_vertex[edge.start].append(edge)
        by_vertex[edge.end].append(edge)
    first = component[0]
    ring, vertex, used = list(first.points[:-1]), first.end, {id(first)}
    while vertex != first.start:
        edge = next(e for e in by_vertex[vertex] if id(e) not in used)
        used.add(id(edge))
        forward = edge.start == vertex
        ring.extend((edge.points if forward else edge.points[::-1])[:-1])
        vertex = edge.end if forward else edge.start
    return [p for i, p in enumerate(ring) if i == 0 or p != ring[i - 1]]


# -----------------------------------------------------------------------------
# Containment
# -----------------------------------------------------------------------------

Segment = Tuple[Point, Point]


def ring_segments(ring: Sequence[Point]) -> List[Segment]:
    return list(zip(ring, list(ring[1:]) + [ring[0]]))


def _inside(point: Point, segments: Sequence[Segment]) -> bool:
    """Even-odd ray cast."""
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in segments:
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _segment_distance(p: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def contains(segments: Sequence[Segment], point: Point) -> bool:
    """Inside the ring whose segments these are, or within ON_CONTOUR_MM of it."""
    return _inside(point, segments) or any(_segment_distance(point, a, b) <= ON_CONTOUR_MM for a, b in segments)


def enclosed_length(ring: Sequence[Point], paths: Iterable[Sequence[Point]]) -> float:
    """Drawn length of `paths` inside or on the ring, tested in pieces no longer than PIECE_MM."""
    segments = ring_segments(ring)
    total = 0.0
    for path in paths:
        for p, q in zip(path, path[1:]):
            seg = math.dist(p, q)
            n = max(1, math.ceil(seg / PIECE_MM))
            total += seg / n * sum(contains(segments, (p[0] + (i + 0.5) / n * (q[0] - p[0]),
                                                       p[1] + (i + 0.5) / n * (q[1] - p[1]))) for i in range(n))
    return total
