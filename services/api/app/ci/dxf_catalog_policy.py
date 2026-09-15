"""
DXF catalog policy — shared by the two catalog gates (DXF-CATALOG-GATE-001).

Both `scripts/validate_dxf_assets.py` (DXF Asset Validation) and
`app/ci/check_dxf_files.py` (DXF Validation Gate) read the declarative
registry `dxf_catalog_registry.json` next to this module. The registry, not
validator code, says:

- which asset class a catalog path belongs to, and which contract clauses
  that class must satisfy;
- which layers carry the manufacturing outline and which are reference data;
- which DXF versions a stored catalog file may use (R12 only: R2000 is
  bucket-1 paid-tier output of the canonical vectorizer, not a catalog format);
- every quarantine record: an asset that fails a named clause, with evidence,
  disposition, owner stream and exit condition. A record never passes a file;
  it marks manufacturing authority BLOCKED and keeps the failure visible.

Dependencies: stdlib + ezdxf entity attributes, plus the sibling
dxf_catalog_schema module (stdlib), which validates the registry at load time.
The asset gate job installs only ezdxf, so this module must not import shapely
or anything outside app/ci; and it avoids ezdxf's numpy-backed helpers (bbox, flattening),
whose mid-test numpy import is the double-binding hazard documented in
services/api/tests/conftest.py.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import dxf_catalog_schema as schema

REGISTRY_PATH = Path(__file__).with_name("dxf_catalog_registry.json")

DRAWABLE_TYPES = frozenset({"LWPOLYLINE", "POLYLINE", "LINE", "CIRCLE", "ARC", "SPLINE", "ELLIPSE"})
RECORD_FIELDS = schema.RECORD_FIELDS
KNOWN_CLAUSES = schema.KNOWN_CLAUSES
RegistryError = schema.RegistryError
ENDPOINT_QUANTUM_MM = 0.05  # endpoint snap when chaining LINE/ARC/SPLINE edges

Point = Tuple[float, float]
Segment = Tuple[Point, Point]
BBox = Tuple[float, float, float, float]


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

def load_registry(path: Optional[Path] = None, validate: bool = True) -> Dict[str, Any]:
    """Load the registry; by default reject a malformed one (RegistryError)."""
    with open(path or REGISTRY_PATH, encoding="utf-8") as fh:
        registry = json.load(fh)
    if validate:
        schema.validate_registry(registry, classify)
    return registry


def glob_match(path: str, pattern: str) -> bool:
    """Match per '/' segment: '*' stays inside one segment, '**' spans any number."""
    return _match_segments(path.split("/"), pattern.split("/"))


def _match_segments(parts: List[str], patterns: List[str]) -> bool:
    if not patterns:
        return not parts
    if patterns[0] == "**":
        return any(_match_segments(parts[i:], patterns[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], patterns[0]) and _match_segments(parts[1:], patterns[1:])


def classify(asset: Optional[str], registry: Dict[str, Any]) -> Optional[str]:
    """Asset class for a catalog-relative POSIX path, or None if unclassified.

    Raises RegistryError when rules for different classes match the same path:
    classification must never depend on rule order.
    """
    if asset is None:
        return None
    classes = {rule["class"] for rule in registry["class_rules"] if glob_match(asset, rule["glob"])}
    if len(classes) > 1:
        raise RegistryError(f"Ambiguous classification: {asset!r} matches rules for {sorted(classes)}")
    return classes.pop() if classes else None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_sha256(path: Path, asset: Optional[str], registry: Dict[str, Any]) -> Optional[str]:
    """The file's sha256 when a quarantine record needs it, else None.

    Hashing only record-bearing files keeps a gate from adding a failure
    surface to files it already judged. An unreadable file yields a marker
    string, which can never equal a recorded digest, so the record fails
    verification instead of the gate crashing.
    """
    if quarantine_record(asset, registry) is None:
        return None
    try:
        return file_sha256(path)
    except OSError as exc:
        return f"unreadable ({type(exc).__name__})"


def contract_for(asset_class: str, registry: Dict[str, Any]) -> List[str]:
    return list(registry["asset_classes"][asset_class]["contract"])


def quarantine_record(asset: Optional[str], registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for record in registry.get("quarantine", []):
        if record["asset"] == asset:
            return record
    return None


def relative_asset(path: Path, catalog_root: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(catalog_root.resolve()).as_posix()
    except ValueError:
        return None


# -----------------------------------------------------------------------------
# Clauses that need only ezdxf
# -----------------------------------------------------------------------------

def check_version(version: str, registry: Dict[str, Any]) -> Optional[str]:
    approved = registry["version_policy"]["approved"]
    if version in approved:
        return None
    return (f"DXF version {version} is not approved for stored catalog files "
            f"(approved: {', '.join(approved)}; R2000 is paid-tier vectorizer output only)")


def check_geometry_present(entities: Sequence[Any]) -> Optional[str]:
    if any(e.dxftype() in DRAWABLE_TYPES for e in entities):
        return None
    return "No drawable geometry (expected one of: " + ", ".join(sorted(DRAWABLE_TYPES)) + ")"


def _key(point: Point) -> Tuple[int, int]:
    return (round(point[0] / ENDPOINT_QUANTUM_MM), round(point[1] / ENDPOINT_QUANTUM_MM))


def _arc_point(entity: Any, degrees: float) -> Point:
    c, r = entity.dxf.center, entity.dxf.radius
    return (c[0] + r * math.cos(math.radians(degrees)), c[1] + r * math.sin(math.radians(degrees)))


def _spline_defining_points(entity: Any) -> List[Point]:
    pts = list(entity.fit_points) or list(entity.control_points)
    return [(p[0], p[1]) for p in pts]


def _edge(entity: Any) -> Optional[Segment]:
    """Start/end of an open chainable entity; None for anything else.

    Plain math only: ezdxf's curve/bbox helpers pull in numpy mid-import,
    which the test suite's conftest documents as a double-binding hazard.
    """
    kind = entity.dxftype()
    if kind == "LINE":
        s, e = entity.dxf.start, entity.dxf.end
        return (s[0], s[1]), (e[0], e[1])
    if kind == "ARC":
        return _arc_point(entity, entity.dxf.start_angle), _arc_point(entity, entity.dxf.end_angle)
    if kind == "SPLINE" and not entity.closed:
        pts = _spline_defining_points(entity)  # clamped DXF splines start/end on these
        return (pts[0], pts[-1]) if len(pts) >= 2 else None
    return None


def _two_core(edges: List[Segment]) -> List[int]:
    """Indices of edges that lie on a cycle (degree-1 branches pruned)."""
    adjacency: Dict[Tuple[int, int], Set[int]] = defaultdict(set)
    for i, (a, b) in enumerate(edges):
        if _key(a) != _key(b):
            adjacency[_key(a)].add(i)
            adjacency[_key(b)].add(i)
    alive = set(i for ids in adjacency.values() for i in ids)
    queue = deque(v for v, ids in adjacency.items() if len(ids) < 2)
    while queue:
        vertex = queue.popleft()
        for i in list(adjacency[vertex]):
            other = next(k for k in (_key(edges[i][0]), _key(edges[i][1])) if k != vertex)
            adjacency[vertex].discard(i)
            adjacency[other].discard(i)
            alive.discard(i)
            if len(adjacency[other]) == 1:
                queue.append(other)
    return sorted(alive)


def _dedupe(edges: List[Segment]) -> List[Segment]:
    """Drop repeated edges: a LINE drawn twice is not a closed contour."""
    unique: Dict[frozenset, Segment] = {}
    for a, b in edges:
        unique.setdefault(frozenset((_key(a), _key(b))), (a, b))
    return list(unique.values())


def closed_chain_components(edges: List[Segment]) -> List[List[Segment]]:
    """Connected components of the cycle-bearing part of an edge graph."""
    edges = _dedupe(edges)
    core = _two_core(edges)
    by_vertex: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for i in core:
        by_vertex[_key(edges[i][0])].append(i)
        by_vertex[_key(edges[i][1])].append(i)
    seen: Set[int] = set()
    components: List[List[Segment]] = []
    for start in core:
        if start in seen:
            continue
        stack, members = [start], []
        while stack:
            i = stack.pop()
            if i in seen:
                continue
            seen.add(i)
            members.append(edges[i])
            for end in edges[i]:
                stack.extend(j for j in by_vertex[_key(end)] if j not in seen)
        components.append(members)
    return components


def _bbox(points: Iterable[Point]) -> Optional[BBox]:
    pts = list(points)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def is_simple_cycle(chain: List[Segment]) -> bool:
    """Every vertex joins exactly two edges: one closed contour, no branch or pinch.

    A figure-8 whose lobes share a vertex, or a body with a chord across it,
    has vertices of degree > 2 and is not a single closed contour.
    """
    degree: Dict[Tuple[int, int], int] = defaultdict(int)
    for a, b in chain:
        degree[_key(a)] += 1
        degree[_key(b)] += 1
    return bool(degree) and all(d == 2 for d in degree.values())


def _closed_polyline_points(entity: Any) -> Optional[List[Point]]:
    kind = entity.dxftype()
    if kind == "LWPOLYLINE" and entity.closed:
        return [(p[0], p[1]) for p in entity.get_points("xy")]
    if kind == "POLYLINE" and entity.is_closed:
        return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    return None


@dataclass
class OutlineResult:
    """Outcome of the closed_outline clause for one file."""
    failure: Optional[str]
    covering_chain: List[Segment] = field(default_factory=list)


def check_closed_outline(entities: Sequence[Any], asset_class_spec: Dict[str, Any]) -> OutlineResult:
    """closed_outline: a simple closed contour on an outline layer bounds that layer.

    Closed contours: closed LWPOLYLINE, closed POLYLINE, or a closed chain of
    LINE/ARC/open-SPLINE edges (endpoints snapped to 0.05 mm) that is a simple
    cycle (every vertex joins exactly two edges). CIRCLE never counts.
    "Bounds" is a bounding-box test: the contour's bbox must cover
    `outline_coverage_min` of the outline layer's bbox in both axes, so a small
    closed strip or cavity on the outline layer cannot stand in for the outline.
    Geometric self-crossing is checked by the Files gate's topology_valid.
    """
    layers = set(asset_class_spec["outline_layers"])
    outline = [e for e in entities if e.dxf.layer in layers and e.dxftype() in DRAWABLE_TYPES]
    if not outline:
        return OutlineResult(f"No geometry on an outline layer ({', '.join(sorted(layers))})")
    extent = _outline_extent(outline)
    if extent is None:
        return OutlineResult("Outline-layer geometry has no measurable extent (no usable points)")
    coverage_min = asset_class_spec["outline_coverage_min"]
    candidates, branched = _closed_candidates(outline)
    best = (0.0, 0.0)
    for bbox, chain in candidates:
        cov = _coverage(bbox, extent)
        if min(cov) >= coverage_min:
            return OutlineResult(None, chain)
        if min(cov) > min(best):
            best = cov
    return OutlineResult(_outline_failure(best, extent, coverage_min, branched))


def _outline_failure(best: Tuple[float, float], extent: BBox, coverage_min: float, branched: int) -> str:
    message = (f"No simple closed contour bounds the outline layer: the best closed contour's bbox covers "
               f"{best[0]:.2f} x {best[1]:.2f} of the layer's {extent[2] - extent[0]:.1f} x "
               f"{extent[3] - extent[1]:.1f} mm bbox (need {coverage_min})")
    if branched:
        message += (f"; {branched} closed chain(s) rejected because they branch or touch themselves "
                    f"(a vertex joins more than two edges)")
    return message


def _closed_candidates(outline: Sequence[Any]) -> Tuple[List[Tuple[BBox, List[Segment]]], int]:
    """(bbox, chain) per closed polyline (chain empty) and per simple closed edge chain.

    Returns the candidates and how many closed chains were rejected as
    non-simple. Candidates carry only a bbox: the chain's point order is not
    needed for the coverage test, so none is reconstructed.
    """
    candidates = [(_bbox(pts), []) for pts in (_closed_polyline_points(e) for e in outline) if pts]
    chains = closed_chain_components([s for s in (_edge(e) for e in outline) if s])
    simple = [c for c in chains if is_simple_cycle(c)]
    candidates += [(_bbox(p for seg in c for p in seg), c) for c in simple]
    return candidates, len(chains) - len(simple)


def _arc_points(entity: Any) -> List[Point]:
    start, end = entity.dxf.start_angle, entity.dxf.end_angle
    sweep = (end - start) % 360 or 360
    return [_arc_point(entity, start + sweep * i / 32) for i in range(33)]


def _spline_extent_points(entity: Any) -> List[Point]:
    return [(p[0], p[1]) for p in entity.control_points] or _spline_defining_points(entity)


def _ellipse_points(entity: Any) -> List[Point]:
    c, major, ratio = entity.dxf.center, entity.dxf.major_axis, entity.dxf.ratio
    minor = (-major[1] * ratio, major[0] * ratio)
    return [(c[0] + major[0] * math.cos(t) + minor[0] * math.sin(t),
             c[1] + major[1] * math.cos(t) + minor[1] * math.sin(t))
            for t in (2 * math.pi * i / 32 for i in range(32))]


_EXTENT_POINTS = {
    "LINE": lambda e: list(_edge(e) or ()),
    "LWPOLYLINE": lambda e: [(p[0], p[1]) for p in e.get_points("xy")],
    "POLYLINE": lambda e: [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices],
    "ARC": _arc_points,
    "CIRCLE": lambda e: [_arc_point(e, a) for a in (0, 90, 180, 270)],
    "SPLINE": _spline_extent_points,
    "ELLIPSE": _ellipse_points,
}


def _extent_points(entity: Any) -> List[Point]:
    """Points whose bbox bounds the entity (spline control points bound the curve)."""
    points = _EXTENT_POINTS.get(entity.dxftype())
    return points(entity) if points else []


def _outline_extent(outline: Sequence[Any]) -> Optional[BBox]:
    return _bbox(p for e in outline for p in _extent_points(e))


def _coverage(box: BBox, extent: BBox) -> Tuple[float, float]:
    width = max(extent[2] - extent[0], 1e-9)
    height = max(extent[3] - extent[1], 1e-9)
    return (box[2] - box[0]) / width, (box[3] - box[1]) / height


# -----------------------------------------------------------------------------
# Verdict
# -----------------------------------------------------------------------------

@dataclass
class Verdict:
    """Gate outcome for one file: PASS, QUARANTINED or FAIL."""
    status: str
    asset: Optional[str]
    asset_class: Optional[str]
    failures: Dict[str, List[str]]
    messages: List[str] = field(default_factory=list)

    @property
    def blocks_gate(self) -> bool:
        return self.status == "FAIL"


def judge(asset: Optional[str], asset_class: Optional[str], failures: Dict[str, List[str]],
          evaluated: Set[str], registry: Dict[str, Any], asset_sha256: Optional[str] = None) -> Verdict:
    """Apply the class contract and any quarantine record to clause failures.

    Outcomes, in order:
    - unclassified asset -> FAIL
    - no record: no failures -> PASS, any failure -> FAIL
    - record: QUARANTINED only if all of these hold, otherwise FAIL with the reasons:
      * every failure is a clause the record declares (no extra failure);
      * every declared clause this gate evaluates still fails (no healed clause);
      * the record's asset_class matches the classification;
      * the file's bytes still hash to the record's asset_sha256 (the gates
        always pass it; a changed file must be re-adjudicated).
    """
    if asset_class is None:
        reason = ("File is outside the catalog root the gate scans; it cannot be classified or recorded"
                  if asset is None else
                  "Unclassified catalog asset: add a class_rules entry to dxf_catalog_registry.json")
        return Verdict("FAIL", asset, None, failures, [reason])
    record = quarantine_record(asset, registry)
    if record is None:
        return Verdict("FAIL" if failures else "PASS", asset, asset_class, failures)
    messages = _record_mismatches(asset_class, failures, evaluated, record, asset_sha256)
    if messages:
        return Verdict("FAIL", asset, asset_class, failures, messages)
    return Verdict("QUARANTINED", asset, asset_class, failures, [
        f"QUARANTINED ({record['disposition']}): manufacturing authority "
        f"{record['manufacturing_authority']}; owner {record['owner_stream']}"])


def _record_mismatches(asset_class: str, failures: Dict[str, List[str]], evaluated: Set[str],
                       record: Dict[str, Any], asset_sha256: Optional[str]) -> List[str]:
    """Reasons a quarantine record no longer describes the file (empty = it still does)."""
    declared = set(record["failed_contract"])
    extra = sorted(set(failures) - declared)
    healed = sorted((declared & evaluated) - set(failures))
    messages = []
    if extra:
        messages.append(f"Fails clauses not in its quarantine record: {', '.join(extra)}")
    if healed:
        messages.append(f"Quarantine record lists clauses that now pass: {', '.join(healed)} "
                        f"(exit condition may be met: re-adjudicate and update the record)")
    if record["asset_class"] != asset_class:
        messages.append(f"Quarantine record says asset_class {record['asset_class']!r}, "
                        f"registry classifies it as {asset_class!r}")
    if asset_sha256 is not None and asset_sha256 != record["asset_sha256"]:
        now = f"{asset_sha256[:12]}..." if len(asset_sha256) == 64 else asset_sha256
        messages.append(f"Asset bytes changed since the record was made (recorded sha256 "
                        f"{record['asset_sha256'][:12]}..., now {now}): re-adjudicate "
                        f"and refresh the record")
    return messages


def orphan_records(registry: Dict[str, Any], catalog_root: Path) -> List[str]:
    """Quarantine records whose asset is not in the catalog."""
    return [r["asset"] for r in registry.get("quarantine", []) if not (catalog_root / r["asset"]).is_file()]


def registry_problems(registry: Dict[str, Any], repo_root: Path, catalog_root: Path) -> List[str]:
    """Registry-level failures a gate reports once per run: root mismatch, orphan records."""
    problems = []
    declared = (repo_root / registry["catalog_root"]).resolve()
    if declared != catalog_root.resolve():
        problems.append(f"registry catalog_root {registry['catalog_root']!r} resolves to {declared}, "
                        f"but the gate scans {catalog_root.resolve()}")
    problems += [f"quarantine record for missing asset: {a}" for a in orphan_records(registry, catalog_root)]
    return problems
