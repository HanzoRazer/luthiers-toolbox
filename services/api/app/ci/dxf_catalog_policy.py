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

Dependencies: stdlib + ezdxf entity attributes, plus two sibling stdlib
modules: dxf_catalog_schema, which validates the registry at load time, and
dxf_catalog_geometry, the outline geometry model (sampling, vertex tolerance,
edge identity, containment) with the reason for each of its numbers. The asset
gate job installs only ezdxf, so none of them may import shapely or anything
outside app/ci; and they avoid ezdxf's numpy-backed helpers (bbox, flattening),
whose mid-test numpy import is the double-binding hazard documented in
services/api/tests/conftest.py.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from . import dxf_catalog_geometry as geometry
from . import dxf_catalog_schema as schema

REGISTRY_PATH = Path(__file__).with_name("dxf_catalog_registry.json")

DRAWABLE_TYPES = frozenset({"LWPOLYLINE", "POLYLINE", "LINE", "CIRCLE", "ARC", "SPLINE", "ELLIPSE"})
RECORD_FIELDS = schema.RECORD_FIELDS
KNOWN_CLAUSES = schema.KNOWN_CLAUSES
RegistryError = schema.RegistryError

Point = geometry.Point
BBox = geometry.BBox


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


def layer_names(names: Iterable[str]) -> FrozenSet[str]:
    """Layer names as DXF compares them: case-insensitively."""
    return frozenset(name.upper() for name in names)


def on_layer(entity: Any, names: FrozenSet[str]) -> bool:
    return entity.dxf.layer.upper() in names


def manufacturing_entities(entities: Sequence[Any], class_spec: Dict[str, Any]) -> List[Any]:
    """The manufacturing view: every entity not on one of the class's reference layers."""
    reference = layer_names(class_spec.get("reference_layers", []))
    return [e for e in entities if not on_layer(e, reference)]


@dataclass
class OutlineResult:
    """Outcome of the closed_outline clause for one file.

    `chained_ring` is the covering contour's ring when it is a chain of
    LINE/ARC/SPLINE edges (the Files gate checks it for crossings); it is empty
    for a closed polyline, which TopologyValidator checks instead.
    """
    failure: Optional[str]
    chained_ring: List[Point] = field(default_factory=list)


@dataclass
class _Candidate:
    ring: List[Point]
    sources: Set[int]  # indexes of the outline entities that draw it
    chained: bool


def check_closed_outline(entities: Sequence[Any], asset_class_spec: Dict[str, Any]) -> OutlineResult:
    """closed_outline: a simple closed contour on an outline layer bounds that layer.

    The geometry model (sampling, 0.05 mm vertex tolerance, edge identity,
    simple cycles, containment) is documented in dxf_catalog_geometry. A
    contour bounds the layer when its bbox spans `outline_coverage_min` of the
    layer's bbox in both axes and that fraction of the layer's drawn length
    lies inside it or on it. Geometric self-crossing is the Files gate's
    topology_valid.
    """
    layers = layer_names(asset_class_spec["outline_layers"])
    outline = [e for e in entities if on_layer(e, layers) and e.dxftype() in DRAWABLE_TYPES]
    if not outline:
        return OutlineResult(f"No geometry on an outline layer ({', '.join(sorted(layers))})")
    paths = [geometry.entity_path(e) for e in outline]
    extent = geometry.bbox(p for path in paths for p in path)
    if extent is None:
        return OutlineResult("Outline-layer geometry has no measurable extent (no usable points)")
    coverage_min = asset_class_spec["outline_coverage_min"]
    candidates, branched = _closed_candidates(outline)
    found, best_cov, best_enclosed = _bounding_contour(candidates, paths, extent, coverage_min)
    if found is not None:
        return OutlineResult(None, found.ring if found.chained else [])
    return OutlineResult(_outline_failure(best_cov, extent, coverage_min, branched, best_enclosed))


def _bounding_contour(candidates: List[_Candidate], paths: List[List[Point]], extent: BBox, coverage_min: float
                      ) -> Tuple[Optional[_Candidate], Tuple[float, float], Optional[float]]:
    """The first candidate that bounds the layer, else None with the best near misses (for the message)."""
    best_cov, best_enclosed = (0.0, 0.0), None
    for candidate in candidates:
        cov = _coverage(geometry.bbox(candidate.ring), extent)
        best_cov = max(best_cov, cov, key=min)
        if min(cov) < coverage_min:
            continue
        enclosed = _enclosed_fraction(candidate, paths)
        if enclosed >= coverage_min:
            return candidate, best_cov, best_enclosed
        best_enclosed = max(best_enclosed or 0.0, enclosed)
    return None, best_cov, best_enclosed


def _outline_failure(best: Tuple[float, float], extent: BBox, coverage_min: float, branched: int,
                     enclosed: Optional[float]) -> str:
    size = f"{extent[2] - extent[0]:.1f} x {extent[3] - extent[1]:.1f} mm"
    if enclosed is None:
        message = (f"No simple closed contour bounds the outline layer: the best closed contour's bbox covers "
                   f"{best[0]:.2f} x {best[1]:.2f} of the layer's {size} bbox (need {coverage_min})")
    else:
        message = (f"No simple closed contour bounds the outline layer: the closed contour spanning the "
                   f"layer's {size} bbox encloses only {enclosed:.2f} of the layer's drawn length "
                   f"(need {coverage_min})")
    if branched:
        message += (f"; {branched} closed chain(s) rejected because they branch or touch themselves "
                    f"(a vertex joins more than two edges)")
    return message


def _closed_candidates(outline: Sequence[Any]) -> Tuple[List[_Candidate], int]:
    """Closed polylines and simple closed edge chains, plus how many chains were not simple."""
    candidates = [_Candidate(ring, {i}, False)
                  for i, ring in enumerate(geometry.closed_ring(e) for e in outline) if ring]
    components = geometry.closed_components(geometry.build_edges([geometry.edge_path(e) for e in outline]))
    simple = [c for c in components if geometry.is_simple_cycle(c)]
    candidates += [_Candidate(geometry.cycle_ring(c), {edge.source for edge in c}, True) for c in simple]
    return candidates, len(components) - len(simple)


def _enclosed_fraction(candidate: _Candidate, paths: List[List[Point]]) -> float:
    """Share of the layer's drawn length that the contour draws or encloses."""
    total = sum(geometry.path_length(p) for p in paths)
    own = sum(geometry.path_length(paths[i]) for i in candidate.sources)
    others = [p for i, p in enumerate(paths) if i not in candidate.sources]
    return (own + geometry.enclosed_length(candidate.ring, others)) / max(total, 1e-9)


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
          evaluated: Set[str], registry: Dict[str, Any], asset_sha256: Optional[str] = None, *,
          crashed: Iterable[str] = ()) -> Verdict:
    """Apply the class contract and any quarantine record to clause failures.

    `evaluated` is the clauses this gate actually ran; `crashed` the ones whose
    check raised. Outcomes, in order:
    - unclassified asset -> FAIL
    - no record: no failures -> PASS, any failure -> FAIL
    - record: QUARANTINED only if all of these hold, otherwise FAIL with the reasons:
      * every failure is a clause the record declares (no extra failure);
      * no declared clause crashed (a crash is not the recorded nonconformance);
      * every declared clause this gate ran still fails (no healed clause);
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
    messages = _record_mismatches(asset_class, failures, evaluated, record, asset_sha256, set(crashed))
    if messages:
        return Verdict("FAIL", asset, asset_class, failures, messages)
    return Verdict("QUARANTINED", asset, asset_class, failures, [
        f"QUARANTINED ({record['disposition']}): manufacturing authority "
        f"{record['manufacturing_authority']}; owner {record['owner_stream']}"])


def _record_mismatches(asset_class: str, failures: Dict[str, List[str]], evaluated: Set[str],
                       record: Dict[str, Any], asset_sha256: Optional[str], crashed: Set[str]) -> List[str]:
    """Reasons a quarantine record no longer describes the file (empty = it still does)."""
    declared = set(record["failed_contract"])
    extra = sorted(set(failures) - declared)
    healed = sorted((declared & evaluated) - set(failures))
    messages = []
    if extra:
        messages.append(f"Fails clauses not in its quarantine record: {', '.join(extra)}")
    if declared & crashed:
        messages.append(f"Checks for recorded clauses crashed: {', '.join(sorted(declared & crashed))} "
                        f"(a crash is not the recorded nonconformance: fix the check, then re-adjudicate)")
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
