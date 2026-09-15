#!/usr/bin/env python3
"""
DXF Validation Gate for CI: export-readiness of the DXF catalog.

Validates every DXF under instrument_geometry/ against the contract of its
asset class, as declared in app/ci/dxf_catalog_registry.json (shared with
scripts/validate_dxf_assets.py through app/ci/dxf_catalog_policy.py).

Contract clauses (the registry says which apply to which class):
- readable, nonempty, geometry_present
- version_allowed: stored catalog files are R12 (AC1009) only
- closed_outline: a simple closed contour on an outline layer bounds that
  layer (its bbox spans the layer and it encloses the layer's drawn length;
  geometry model: app/ci/dxf_catalog_geometry.py)
- preflight_valid: DXFPreflight (the runtime export gate's pre-check) reports
  no ERROR on the manufacturing view (declared reference layers removed)
- topology_valid: TopologyValidator reports no ERROR on the manufacturing
  view, and a chained (LINE/ARC/SPLINE) outline does not cross itself

A check that crashes has not passed: a crash is a clause failure, and one a
quarantine record cannot cover (a crash is not the recorded nonconformance). Clause
order comes from the registry and never changes a verdict: every clause reads
the same unmodified document, and the outline is computed once, on demand.
A file on a quarantine record is QUARANTINED (not failed, not passed) only
while it fails exactly the clauses its record declares.

Exit codes:
- 0: every file PASSED or is QUARANTINED
- 1: one or more files FAILED, or the registry is malformed, names a missing
  asset, or declares a catalog_root other than the one scanned
- 2: runtime error (catalog directory not found)

Usage:
    python -m app.ci.check_dxf_files [--strict] [--json] [--path DIR] [--report FILE]

JSON (--json / --report): total, passed, quarantined, failed, registry_problems, and
per-file results with status, blocks_gate and export_ready (only PASS is export-ready).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import ezdxf

# Add parent to path for imports
REPO_ROOT = Path(__file__).resolve().parents[4]  # services/api/app/ci -> repo root
sys.path.insert(0, str(REPO_ROOT / "services" / "api"))

from app.ci import dxf_catalog_policy as policy  # noqa: E402
from app.cam.dxf_preflight import DXFPreflight, Severity  # noqa: E402
from app.cam.dxf_advanced_validation import TopologyValidator  # noqa: E402

CATALOG_ROOT = REPO_ROOT / "services" / "api" / "app" / "instrument_geometry"
GATE_CLAUSES = frozenset({
    "readable", "nonempty", "geometry_present", "version_allowed",
    "closed_outline", "preflight_valid", "topology_valid",
})
BASE_CONTRACT = ["readable", "nonempty", "geometry_present", "version_allowed"]


@dataclass
class _Context:
    """Everything the clause checks need for one file."""
    path: Path
    doc: Any
    entities: List[Any]
    class_spec: Dict[str, Any]
    registry: Dict[str, Any]
    _outline: Optional[policy.OutlineResult] = None
    _view_bytes: Optional[bytes] = None

    @property
    def manufacturing_entities(self) -> List[Any]:
        return policy.manufacturing_entities(self.entities, self.class_spec)

    def outline(self) -> policy.OutlineResult:
        """The closed_outline result, computed once for whichever clause asks first."""
        if self._outline is None:
            self._outline = policy.check_closed_outline(self.manufacturing_entities, self.class_spec)
        return self._outline

    def view_bytes(self) -> bytes:
        """DXF bytes of the manufacturing view: reference layers removed."""
        if self._view_bytes is None:
            self._view_bytes = self._serialize_view()
        return self._view_bytes

    def _serialize_view(self) -> bytes:
        """Serialize a fresh copy with reference layers removed; ctx.doc is never mutated.

        Deleting from ctx.doc would destroy the entities that ctx.entities still
        holds, so any clause evaluated afterwards (clause order comes from the
        registry) would crash on them.
        """
        reference = policy.layer_names(self.class_spec.get("reference_layers", []))
        if not any(policy.on_layer(e, reference) for e in self.entities):
            return self.path.read_bytes()
        view = ezdxf.readfile(str(self.path))
        msp = view.modelspace()
        for entity in [e for e in msp if policy.on_layer(e, reference)]:
            msp.delete_entity(entity)
        stream = io.StringIO()
        view.write(stream)
        return view.encode(stream.getvalue())


def _clause_nonempty(ctx: _Context) -> List[str]:
    return [] if ctx.entities else ["DXF modelspace is empty (no entities found)"]


def _clause_geometry(ctx: _Context) -> List[str]:
    problem = policy.check_geometry_present(ctx.entities)
    return [problem] if problem else []


def _clause_version(ctx: _Context) -> List[str]:
    problem = policy.check_version(ctx.doc.dxfversion, ctx.registry)
    return [problem] if problem else []


def _clause_outline(ctx: _Context) -> List[str]:
    failure = ctx.outline().failure
    return [failure] if failure else []


def _clause_preflight(ctx: _Context) -> List[str]:
    report = DXFPreflight(ctx.view_bytes(), ctx.path.name).run_all_checks()
    return [i.message for i in report.issues if i.severity == Severity.ERROR]


def _clause_topology(ctx: _Context) -> List[str]:
    report = TopologyValidator(ctx.view_bytes(), ctx.path.name).check_self_intersections()
    problems = [i.message for i in report.issues if i.severity == Severity.ERROR]
    if "outline_layers" not in ctx.class_spec:  # no outline declared, so no chained outline to check
        return problems
    return problems + _chain_crossings(ctx.outline().chained_ring)


def _chain_crossings(ring: List[Any]) -> List[str]:
    """A chained outline must not cross itself.

    The ring is the sampled contour from the shared geometry model (arcs and
    splines as curves, vertices already snapped), so an ARC crossing is seen
    and two endpoints within the vertex tolerance are one point, not a crossing.
    """
    if len(ring) < 3:
        return []
    from shapely.geometry import LineString

    if LineString(list(ring) + [ring[0]]).is_simple:
        return []
    return ["Outline chain crosses itself (its LINE/ARC/SPLINE edges intersect away from their shared vertices)"]


CLAUSE_CHECKS: Dict[str, Callable[[_Context], List[str]]] = {
    "nonempty": _clause_nonempty,
    "geometry_present": _clause_geometry,
    "version_allowed": _clause_version,
    "closed_outline": _clause_outline,
    "preflight_valid": _clause_preflight,
    "topology_valid": _clause_topology,
}


def _run_clause(clause: str, ctx: _Context) -> Tuple[List[str], bool]:
    """(problems, crashed) for one clause; a crash fails that clause for this file, never the whole run."""
    if clause == "readable":
        return [], False  # established by _evaluate before any clause runs
    check = CLAUSE_CHECKS.get(clause)
    if check is None:  # a typo or future clause must never count as a pass
        return [f"No implementation for contract clause {clause!r} in this gate"], False
    try:
        return check(ctx), False
    except Exception as exc:  # fail-closed: a crashed check has not passed
        return [f"{clause} check crashed: {type(exc).__name__}: {exc}"], True


@dataclass
class _Evaluation:
    """Clause failures for one file, which clauses ran, and which of them crashed."""
    failures: Dict[str, List[str]]
    ran: Set[str]
    crashed: Set[str]


def _evaluate(dxf_path: Path, contract: List[str], class_spec: Dict[str, Any],
              registry: Dict[str, Any]) -> _Evaluation:
    """Evaluate the contract for one file.

    Stops after readable/nonempty/geometry_present fail. Clauses after the stop
    were not run, so a quarantine record cannot call them healed.
    """
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as exc:  # unreadable is a failure, not a crash of the gate
        return _Evaluation({"readable": [f"Failed to read DXF: {type(exc).__name__}: {exc}"]}, {"readable"}, set())
    ctx = _Context(dxf_path, doc, list(doc.modelspace()), class_spec, registry)
    result = _Evaluation({}, {"readable"}, set())
    for clause in contract:
        result.ran.add(clause)
        problems, crashed = _run_clause(clause, ctx)
        if crashed:
            result.crashed.add(clause)
        if problems:
            result.failures[clause] = problems
            if clause in ("nonempty", "geometry_present"):
                break
    return result


def validate_dxf_file(dxf_path: Path, registry: Optional[Dict[str, Any]] = None, *,
                      asset_class: Optional[str] = None) -> Dict[str, Any]:
    """Validate one DXF against its asset-class contract and quarantine record.

    `asset_class` (keyword-only) overrides registry classification. It exists for
    tests of files outside the catalog; the CLI never passes it.
    """
    registry = registry or policy.load_registry()
    asset = policy.relative_asset(dxf_path, CATALOG_ROOT)
    klass = asset_class or policy.classify(asset, registry)
    contract = policy.contract_for(klass, registry) if klass else BASE_CONTRACT
    spec = registry["asset_classes"].get(klass, {}) if klass else {}
    run = _evaluate(dxf_path, contract, spec, registry)
    sha = policy.record_sha256(dxf_path, asset, registry)
    verdict = policy.judge(asset, klass, run.failures, run.ran & GATE_CLAUSES, registry, sha, crashed=run.crashed)
    return _result_dict(dxf_path, verdict)


def _result_dict(dxf_path: Path, verdict: policy.Verdict) -> Dict[str, Any]:
    """Per-file result. `status` is the verdict; there is deliberately no `passed`
    field: QUARANTINED does not fail the gate but is not export-ready either."""
    failure_lines = [f"[{c}] {m}" for c, msgs in verdict.failures.items() for m in msgs]
    blocking = verdict.blocks_gate
    return {
        "file": str(dxf_path),
        "asset": verdict.asset,
        "asset_class": verdict.asset_class,
        "status": verdict.status,
        "blocks_gate": blocking,
        "export_ready": verdict.status == "PASS",
        "errors": (failure_lines + verdict.messages) if blocking else [],
        "warnings": [] if blocking else (failure_lines + verdict.messages),
        "info": {"failed_clauses": sorted(verdict.failures)},
    }


def find_dxf_files(search_dir: Path) -> List[Path]:
    """Find all DXF files in directory tree."""
    return sorted(search_dir.rglob("*.dxf"))


def _find_catalog(path_arg: Optional[str]) -> Optional[Path]:
    if path_arg:
        return Path(path_arg)
    candidates = [
        CATALOG_ROOT,
        Path.cwd() / "services" / "api" / "app" / "instrument_geometry",
        Path.cwd() / "app" / "instrument_geometry",
    ]
    return next((p for p in candidates if p.exists()), None)


_ICONS = {"PASS": "✅", "QUARANTINED": "🔒", "FAIL": "❌"}


def _print_result(result: Dict[str, Any], strict: bool) -> None:
    print(f"{_ICONS[result['status']]} {Path(result['file']).name}")
    for line in result["errors"]:
        print(f"   ❌ {line}")
    if result["status"] == "QUARANTINED" or strict:
        for line in result["warnings"]:
            print(f"   🔒 {line}")


def _print_report(results: List[Dict[str, Any]], problems: List[str], strict: bool) -> None:
    counts = {s: sum(1 for r in results if r["status"] == s) for s in _ICONS}
    print(f"\n{'=' * 60}")
    print("DXF Validation Report - instrument_geometry/ (export readiness)")
    print(f"{'=' * 60}")
    print(f"Total files: {len(results)}")
    print(f"Passed: {counts['PASS']}")
    print(f"Quarantined: {counts['QUARANTINED']} (manufacturing authority BLOCKED)")
    print(f"Failed: {counts['FAIL']}")
    print(f"{'=' * 60}\n")
    for result in results:
        _print_result(result, strict)
    for problem in problems:
        print(f"❌ registry: {problem}")
    failed = counts["FAIL"] + len(problems)
    print(f"\n{'=' * 60}\nRESULT: {'FAILED' if failed else 'PASSED'}\n{'=' * 60}\n")


def _json_report(results: List[Dict[str, Any]], problems: List[str]) -> Dict[str, Any]:
    """Summary counts first, then per-file results; PASS is the only export-ready status."""
    counts = {s: sum(1 for r in results if r["status"] == s) for s in _ICONS}
    return {"total": len(results), "passed": counts["PASS"], "quarantined": counts["QUARANTINED"],
            "failed": counts["FAIL"], "registry_problems": problems, "results": results}


def _run(search_dir: Path) -> "tuple[List[Dict[str, Any]], List[str]]":
    """Validate every DXF under search_dir; registry errors become one failing problem."""
    try:
        registry = policy.load_registry()
        results = [validate_dxf_file(p, registry) for p in find_dxf_files(search_dir)]
    except policy.RegistryError as exc:
        return [], [str(exc)]
    return results, policy.registry_problems(registry, REPO_ROOT, CATALOG_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate DXF files in instrument_geometry/ against the catalog registry"
    )
    parser.add_argument("--strict", action="store_true",
                        help="Also fail on quarantined files")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--path", type=str, default=None,
                        help="Override search path (default: instrument_geometry/)")
    parser.add_argument("--report", type=str, default=None,
                        help="Also write the JSON report to this file (CI uploads it on failure)")
    args = parser.parse_args()

    search_dir = _find_catalog(args.path)
    if not search_dir:
        print("ERROR: Could not find instrument_geometry/ directory")
        return 2

    results, problems = _run(search_dir)
    report = json.dumps(_json_report(results, problems), indent=2, default=str)
    if args.report:
        Path(args.report).write_text(report + "\n", encoding="utf-8")
    if args.json:
        print(report)
    else:
        _print_report(results, problems, args.strict)

    failed = sum(1 for r in results if r["status"] == "FAIL") + len(problems)
    quarantined = sum(1 for r in results if r["status"] == "QUARANTINED")
    return 1 if failed or (args.strict and quarantined) else 0


if __name__ == "__main__":
    sys.exit(main())
