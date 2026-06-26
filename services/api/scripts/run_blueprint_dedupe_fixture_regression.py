#!/usr/bin/env python
"""
Blueprint geometry-dedupe fixture regression — PR validation only.

Runs the REFINED blueprint cleanup/export path on each fixture DXF twice:

  * once with BLUEPRINT_ENABLE_GEOMETRY_DEDUPE=false  (production default)
  * once with BLUEPRINT_ENABLE_GEOMETRY_DEDUPE=true

and checks STRUCTURAL invariants on the exported DXF:

  * both runs succeed
  * output is DXF R12 (AC1009)
  * output contains LINE entities
  * output contains NO LWPOLYLINE
  * geometry does not vanish when dedupe is enabled
  * dedupe stats present iff the flag is on (wiring sanity)

It reports per-fixture entity counts and dedupe deltas. It fails ONLY on
structural regressions — NOT merely because the entity count changed (a change
is the expected effect of dedupe).

The feature flag is read once at import time (frozen on BlueprintLimits), so each
(fixture, flag) combination runs in its own subprocess with the env var set
beforehand. This script is both the orchestrator and the worker (``--worker``).

This script does not enable the flag in production, does not merge anything, and
makes no application-behavior change — it only drives the existing pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

SCRIPT = Path(__file__).resolve()
API_DIR = SCRIPT.parents[1]          # services/api
REPO = SCRIPT.parents[3]             # repository root

FLAG = "BLUEPRINT_ENABLE_GEOMETRY_DEDUPE"

# Per-fixture candidate paths (relative to repo root), in priority order.
# First existing match wins; LINE-based extraction DXFs are preferred because the
# cleanup path chains LINE entities (LWPOLYLINE-only files are not valid raw input).
FIXTURE_CANDIDATES: dict[str, list[str]] = {
    "gibson_explorer": [
        "docs/archive/instrument_references/gibson_explorer/gibson_explorer_blueprint_page2_body_cavities.dxf",
        "services/api/app/instrument_geometry/body/dxf/electric/gibson_explorer_blueprint_page2_body_cavities_phase3.dxf",
    ],
    "melody_maker": [
        "services/api/app/instrument_geometry/body/dxf/electric/Gibson-Melody-Maker_phase3.dxf",
        "phase4_output/melody_maker_geometry_only.dxf",
    ],
    "el_cuatro": [
        "services/api/app/instrument_geometry/body/dxf/other/Cuatro_Venezolano_body.dxf",
        "phase4_output/cuatro_geometry_only.dxf",
    ],
}


def discover_fixtures() -> dict[str, Path]:
    """Find one DXF per fixture; print what was used."""
    found: dict[str, Path] = {}
    for name, cands in FIXTURE_CANDIDATES.items():
        for rel in cands:
            p = REPO / rel
            if p.exists():
                found[name] = p
                break
    return found


# ─── Worker: one cleanup run, JSON to stdout ──────────────────────────────────

def _worker(fixture_path: str, out_path: str) -> int:
    sys.path.insert(0, str(API_DIR))
    import ezdxf
    from app.services.blueprint_clean import clean_blueprint_dxf, CleanupMode

    result: dict = {"flag": os.getenv(FLAG, "")}
    try:
        res = clean_blueprint_dxf(fixture_path, out_path, mode=CleanupMode.REFINED)
        result["success"] = bool(res.success)
        result["error"] = res.error or ""
        result["dedupe"] = res.geometry_deduplication  # None unless flag on + ran
    except Exception as exc:  # pragma: no cover - surfaced as failure in parent
        result["success"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["dedupe"] = None

    types: Counter = Counter()
    version = None
    if Path(out_path).exists():
        try:
            doc = ezdxf.readfile(out_path)
            version = doc.dxfversion
            types = Counter(e.dxftype() for e in doc.modelspace())
        except Exception as exc:  # pragma: no cover
            result["error"] = (result.get("error") or "") + f" | readback: {exc}"
    result["dxfversion"] = version
    result["entity_count"] = sum(types.values())
    result["types"] = dict(types)

    print(json.dumps(result))
    return 0


def _run_one(fixture_path: Path, enabled: bool) -> dict:
    """Spawn a worker subprocess with the flag set; return its parsed JSON."""
    env = dict(os.environ)
    env[FLAG] = "true" if enabled else "false"
    with tempfile.TemporaryDirectory() as td:
        out_path = Path(td) / "out.dxf"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--worker",
             "--fixture", str(fixture_path), "--out", str(out_path)],
            env=env, cwd=str(API_DIR),
            capture_output=True, text=True,
        )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {
            "success": False,
            "error": f"worker exit {proc.returncode}: "
                     f"{(proc.stderr or proc.stdout)[-500:].strip()}",
            "dxfversion": None, "entity_count": 0, "types": {}, "dedupe": None,
        }
    # Worker prints exactly one JSON line; tolerate trailing log noise.
    line = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")][-1]
    return json.loads(line)


# ─── Evaluation ───────────────────────────────────────────────────────────────

def _evaluate(name: str, off: dict, on: dict) -> tuple[bool, list[str]]:
    """Return (passed, structural_failure_reasons)."""
    fails: list[str] = []

    if not off.get("success"):
        fails.append(f"flag-off run failed: {off.get('error')}")
    if not on.get("success"):
        fails.append(f"flag-on run failed: {on.get('error')}")

    for label, run in (("flag-off", off), ("flag-on", on)):
        if run.get("success"):
            if run.get("dxfversion") != "AC1009":
                fails.append(f"{label} not R12 (got {run.get('dxfversion')})")
            tset = set(run.get("types", {}))
            if "LINE" not in tset:
                fails.append(f"{label} has no LINE entities")
            if "LWPOLYLINE" in tset:
                fails.append(f"{label} contains LWPOLYLINE")

    # Geometry must not vanish when dedupe is enabled.
    if off.get("entity_count", 0) > 0 and on.get("entity_count", 0) == 0:
        fails.append("flag-on geometry vanished (0 entities)")

    # Dedupe must not ADD geometry.
    if on.get("entity_count", 0) > off.get("entity_count", 0):
        fails.append(
            f"flag-on entities increased ({off.get('entity_count')} -> "
            f"{on.get('entity_count')})"
        )

    # Wiring sanity: stats present iff flag on.
    if on.get("success") and on.get("dedupe") is None:
        fails.append("flag-on produced no dedupe stats (wiring broken)")
    if off.get("success") and off.get("dedupe") is not None:
        fails.append("flag-off produced dedupe stats (flag leaked)")

    return (not fails), fails


def _main() -> int:
    fixtures = discover_fixtures()

    print("=" * 78)
    print("Blueprint geometry-dedupe fixture regression (PR validation only)")
    print("=" * 78)
    print(f"repo root: {REPO}")
    print("fixtures detected:")
    for want in FIXTURE_CANDIDATES:
        if want in fixtures:
            print(f"  {want:16s} -> {fixtures[want].relative_to(REPO)}")
        else:
            print(f"  {want:16s} -> NOT FOUND")
    print()

    missing = [n for n in FIXTURE_CANDIDATES if n not in fixtures]

    rows: list[tuple] = []
    detail: list[str] = []
    overall_ok = True

    for name, path in fixtures.items():
        off = _run_one(path, enabled=False)
        on = _run_one(path, enabled=True)
        passed, fails = _evaluate(name, off, on)
        overall_ok = overall_ok and passed

        off_n = off.get("entity_count", 0)
        on_n = on.get("entity_count", 0)
        removed = off_n - on_n
        r12_ok = off.get("dxfversion") == "AC1009" and on.get("dxfversion") == "AC1009"
        line_only = all(
            "LINE" in set(r.get("types", {})) and "LWPOLYLINE" not in set(r.get("types", {}))
            for r in (off, on) if r.get("success")
        ) and off.get("success") and on.get("success")
        rows.append((name, off_n, on_n, removed,
                     "yes" if r12_ok else "NO",
                     "yes" if line_only else "NO",
                     "PASS" if passed else "FAIL"))

        d = on.get("dedupe") or {}
        if d:
            detail.append(
                f"  {name}: input_segments={d.get('input_segments')} "
                f"output_segments={d.get('output_segments')} "
                f"exact={d.get('exact_duplicates_removed')} "
                f"reversed={d.get('reversed_duplicates_removed')} "
                f"near={d.get('near_duplicates_removed')} "
                f"overlap={d.get('overlap_duplicates_removed')}"
            )
        if not passed:
            for r in fails:
                detail.append(f"  {name}: STRUCTURAL FAIL — {r}")

    # Table
    header = ("fixture", "flag_off_entities", "flag_on_entities", "removed",
              "r12_ok", "line_only_ok", "status")
    widths = [16, 17, 16, 8, 6, 12, 6]
    line = " | ".join(h.ljust(w) for h, w in zip(header, widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print(" | ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    print()

    if detail:
        print("dedupe stats / failures:")
        print("\n".join(detail))
        print()

    if missing:
        overall_ok = False
        print(f"ERROR: missing fixtures: {', '.join(missing)}")

    # GitHub step summary (if running in Actions)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("### Blueprint geometry-dedupe fixture regression\n\n")
            fh.write("| " + " | ".join(header) + " |\n")
            fh.write("|" + "|".join(["---"] * len(header)) + "|\n")
            for row in rows:
                fh.write("| " + " | ".join(str(c) for c in row) + " |\n")
            if missing:
                fh.write(f"\n**Missing fixtures:** {', '.join(missing)}\n")
            fh.write(f"\n**Overall:** {'PASS' if overall_ok else 'FAIL'}\n")

    print(f"OVERALL: {'PASS' if overall_ok else 'FAIL'}")
    return 0 if overall_ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--fixture", help=argparse.SUPPRESS)
    ap.add_argument("--out", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker:
        return _worker(args.fixture, args.out)
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
