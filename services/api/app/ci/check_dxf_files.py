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
  layer (bbox test; every chained vertex joins exactly two edges)
- preflight_valid: DXFPreflight (the runtime export gate's pre-check) reports
  no ERROR on the manufacturing view (declared reference layers removed)
- topology_valid: TopologyValidator reports no ERROR on the manufacturing
  view, and a chained (LINE/ARC) outline does not cross itself

A check that crashes has not passed: a crash is a clause failure.
A file on a quarantine record is QUARANTINED (not failed, not passed) only
while it fails exactly the clauses its record declares.

Exit codes:
- 0: every file PASSED or is QUARANTINED
- 1: one or more files FAILED, or the registry is malformed, names a missing
  asset, or declares a catalog_root other than the one scanned
- 2: runtime error (catalog directory not found)

Usage:
    python -m app.ci.check_dxf_files [--strict] [--json] [--path DIR]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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
    outline_chain: List[Any] = field(default_factory=list)
    _view_bytes: Optional[bytes] = None

    @property
    def manufacturing_entities(self) -> List[Any]:
        reference = set(self.class_spec.get("reference_layers", []))
        return [e for e in self.entities if e.dxf.layer not in reference]

    def view_bytes(self) -> bytes:
        """DXF bytes of the manufacturing view: reference layers removed."""
        if self._view_bytes is None:
            self._view_bytes = self._serialize_view()
        return self._view_bytes

    def _serialize_view(self) -> bytes:
        reference = set(self.class_spec.get("reference_layers", []))
        dropped = [e for e in self.entities if e.dxf.layer in reference]
        if not dropped:
            return self.path.read_bytes()
        msp = self.doc.modelspace()
        for entity in dropped:
            msp.delete_entity(entity)
        stream = io.StringIO()
        self.doc.write(stream)
        return self.doc.encode(stream.getvalue())


def _clause_nonempty(ctx: _Context) -> List[str]:
    return [] if ctx.entities else ["DXF modelspace is empty (no entities found)"]


def _clause_geometry(ctx: _Context) -> List[str]:
    problem = policy.check_geometry_present(ctx.entities)
    return [problem] if problem else []


def _clause_version(ctx: _Context) -> List[str]:
    problem = policy.check_version(ctx.doc.dxfversion, ctx.registry)
    return [problem] if problem else []


def _clause_outline(ctx: _Context) -> List[str]:
    result = policy.check_closed_outline(ctx.manufacturing_entities, ctx.class_spec)
    ctx.outline_chain = result.covering_chain
    return [result.failure] if result.failure else []


def _clause_preflight(ctx: _Context) -> List[str]:
    try:
        report = DXFPreflight(ctx.view_bytes(), ctx.path.name).run_all_checks()
    except Exception as exc:  # fail-closed: a crashed check has not passed
        return [f"Preflight check crashed: {type(exc).__name__}: {exc}"]
    return [i.message for i in report.issues if i.severity == Severity.ERROR]


def _clause_topology(ctx: _Context) -> List[str]:
    try:
        report = TopologyValidator(ctx.view_bytes(), ctx.path.name).check_self_intersections()
    except Exception as exc:  # fail-closed: a crashed check has not passed
        return [f"Topology check crashed: {type(exc).__name__}: {exc}"]
    problems = [i.message for i in report.issues if i.severity == Severity.ERROR]
    return problems + _chain_crossings(ctx.outline_chain)


def _chain_crossings(chain: List[Any]) -> List[str]:
    """A chained outline must not cross itself (shared endpoints are fine)."""
    if not chain:
        return []
    from shapely.geometry import MultiLineString

    if MultiLineString([list(segment) for segment in chain]).is_simple:
        return []
    return ["Outline chain crosses itself (LINE/ARC edges intersect away from their endpoints)"]


CLAUSE_CHECKS: Dict[str, Callable[[_Context], List[str]]] = {
    "nonempty": _clause_nonempty,
    "geometry_present": _clause_geometry,
    "version_allowed": _clause_version,
    "closed_outline": _clause_outline,
    "preflight_valid": _clause_preflight,
    "topology_valid": _clause_topology,
}


def _run_clause(clause: str, ctx: _Context) -> List[str]:
    """One clause check; a crash fails that clause for this file, never the whole run."""
    check = CLAUSE_CHECKS.get(clause)
    if check is None:
        return []  # "readable" is established by _evaluate before any clause runs
    try:
        return check(ctx)
    except Exception as exc:  # fail-closed: a crashed check has not passed
        return [f"{clause} check crashed: {type(exc).__name__}: {exc}"]


def _evaluate(dxf_path: Path, contract: List[str], class_spec: Dict[str, Any],
              registry: Dict[str, Any]) -> Dict[str, List[str]]:
    """Clause failures for one file; stops after readable/nonempty/geometry fail."""
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as exc:  # unreadable is a failure, not a crash of the gate
        return {"readable": [f"Failed to read DXF: {type(exc).__name__}: {exc}"]}
    ctx = _Context(dxf_path, doc, list(doc.modelspace()), class_spec, registry)
    failures: Dict[str, List[str]] = {}
    for clause in contract:
        problems = _run_clause(clause, ctx)
        if problems:
            failures[clause] = problems
            if clause in ("nonempty", "geometry_present"):
                break
    return failures


def validate_dxf_file(dxf_path: Path, registry: Optional[Dict[str, Any]] = None,
                      asset_class: Optional[str] = None) -> Dict[str, Any]:
    """Validate one DXF against its asset-class contract and quarantine record.

    `asset_class` overrides registry classification (used by tests for files
    outside the catalog).
    """
    registry = registry or policy.load_registry()
    asset = policy.relative_asset(dxf_path, CATALOG_ROOT)
    klass = asset_class or policy.classify(asset, registry)
    contract = policy.contract_for(klass, registry) if klass else BASE_CONTRACT
    spec = registry["asset_classes"].get(klass, {}) if klass else {}
    failures = _evaluate(dxf_path, contract, spec, registry)
    evaluated = set(contract) & GATE_CLAUSES
    verdict = policy.judge(asset, klass, failures, evaluated, registry, policy.file_sha256(dxf_path))
    return _result_dict(dxf_path, verdict)


def _result_dict(dxf_path: Path, verdict: policy.Verdict) -> Dict[str, Any]:
    failure_lines = [f"[{c}] {m}" for c, msgs in verdict.failures.items() for m in msgs]
    blocking = verdict.blocks_gate
    return {
        "file": str(dxf_path),
        "asset": verdict.asset,
        "asset_class": verdict.asset_class,
        "status": verdict.status,
        "passed": not blocking,
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
    args = parser.parse_args()

    search_dir = _find_catalog(args.path)
    if not search_dir:
        print("ERROR: Could not find instrument_geometry/ directory")
        return 2

    results, problems = _run(search_dir)

    if args.json:
        print(json.dumps({"results": results, "registry_problems": problems}, indent=2, default=str))
    else:
        _print_report(results, problems, args.strict)

    failed = sum(1 for r in results if r["status"] == "FAIL") + len(problems)
    quarantined = sum(1 for r in results if r["status"] == "QUARANTINED")
    return 1 if failed or (args.strict and quarantined) else 0


if __name__ == "__main__":
    sys.exit(main())
